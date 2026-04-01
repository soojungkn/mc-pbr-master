import torch
import numpy as np
import os
import time
import random
import folder_paths
from PIL import Image
import comfy.utils

# Add PyTorch's CUDA DLL folder to PATH for ONNX Runtime
# This allows ONNX Runtime to find CUDA 12.x DLLs even when PyTorch has CUDA 13.0
torch_lib_path = os.path.join(os.path.dirname(torch.__file__), 'lib')
if os.path.exists(torch_lib_path) and torch_lib_path not in os.environ.get('PATH', ''):
    os.environ['PATH'] = torch_lib_path + os.pathsep + os.environ.get('PATH', '')

# Try to import onnxruntime with helpful error message
try:
    import onnxruntime as ort
except ImportError as e:
    print("\n" + "="*60)
    print("ERROR: ONNX Runtime not installed!")
    print("="*60)
    print("The MC: AI Upscale node requires ONNX Runtime.")
    print("\nPlease install it:")
    print("  For NVIDIA GPU: pip install onnxruntime-gpu")
    print("  For CPU only:   pip install onnxruntime")
    print("\nAfter installation, restart ComfyUI.")
    print("="*60 + "\n")
    raise ImportError("onnxruntime is required for MC: AI Upscale node. See error message above.") from e

# Model configuration mapping
MODEL_CONFIGS = {
    "High Details": {
        "filename": "swin2SR-classical-sr-x4-64.onnx",
        "native_scale": 4,
        "description": "Best quality for textures"
    },
    "Noise Reduction": {
        "filename": "swin2SR-realworld-sr-x4.onnx",
        "native_scale": 4,
        "description": "Handles noisy/compressed images"
    },
    "Lightweight (2x Only)": {
        "filename": "swin2SR-lightweight-x2-64.onnx",
        "native_scale": 2,
        "description": "Faster processing, 2x only"
    }
}


class MC_ImageUpscaleNode:
    """
    GPU-accelerated AI image upscaling using Swin2SR ONNX models with tiled processing.
    """

    # Class-level model cache (shared across instances)
    _model_cache = {}
    _models_dir = None

    # Enable preview UI in the node
    OUTPUT_NODE = True

    def __init__(self):
        """Initialize temp directory for preview images."""
        self.output_dir = folder_paths.get_temp_directory()
        self.type = "temp"
        self.prefix_append = "_mc_upscale_" + ''.join(random.choice('abcdefghijklmnopqrstuvwxyz') for _ in range(5))
        self.compress_level = 4

    @classmethod
    def _get_models_dir(cls):
        """Get the models directory path (lazy initialization)."""
        if cls._models_dir is None:
            package_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            cls._models_dir = os.path.join(package_root, "models")
        return cls._models_dir

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "mode": ([
                    "High Details",
                    "Noise Reduction",
                    "Lightweight (2x Only)"
                ], {"default": "High Details"}),
                "output_scale": (["2x", "4x"], {"default": "4x"}),
                "tile_size": (["128", "256", "512"], {"default": "256"}),
                "seamless": (["Yes", "No"], {"default": "No"}),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("upscaled_image",)
    FUNCTION = "upscale_image"
    CATEGORY = "MC_PBR_Master"

    def upscale_image(
        self,
        image: torch.Tensor,
        mode: str,
        output_scale: str,
        tile_size: str,
        seamless: str
    ):
        """
        Main upscaling entry point with GPU optimization.

        Args:
            image: Input tensor (Batch, H, W, C) in float32 [0, 1]
            mode: Model selection
            output_scale: Target upscale factor ("2x" or "4x")
            tile_size: Tile dimension ("128", "256", "512")
            seamless: "Yes" for seamless texture padding

        Returns:
            Dict with "ui" (preview) and "result" (upscaled tensor)
        """
        start_time = time.time()

        try:
            # Parse parameters
            scale_factor = int(output_scale[:-1])  # "2x" -> 2
            tile_size_int = int(tile_size)

            # Validate input
            if image.dim() != 4:
                raise ValueError(f"Expected 4D tensor (B,H,W,C), got shape: {image.shape}")
            if image.shape[-1] != 3:
                raise ValueError(f"Expected RGB image (3 channels), got {image.shape[-1]} channels")

            # Validate minimum size
            min_size = tile_size_int - (tile_size_int // 8)
            if image.shape[1] < min_size or image.shape[2] < min_size:
                raise ValueError(
                    f"Input image too small ({image.shape[1]}x{image.shape[2]}).\n"
                    f"Minimum size for {tile_size_int}px tiles: {min_size}x{min_size}"
                )

            # Load model with GPU support
            session = self._load_model(mode)
            model_config = MODEL_CONFIGS[mode]
            native_scale = model_config["native_scale"]

            # Warn if scale mismatch
            if scale_factor > native_scale:
                print(f"WARNING: Requested {scale_factor}x but model only supports {native_scale}x.")
                print(f"Output will be {native_scale}x. Please select a {scale_factor}x model.")
                scale_factor = native_scale

            # Process image (GPU-optimized)
            output_tensor = self._process_image_gpu(
                image=image,
                session=session,
                tile_size=tile_size_int,
                target_scale=scale_factor,
                native_scale=native_scale,
                seamless=(seamless == "Yes")
            )

            # Log completion
            duration = time.time() - start_time
            out_h, out_w = output_tensor.shape[1], output_tensor.shape[2]
            print(f"✓ Upscaling complete: {out_w}x{out_h} ({duration:.2f}s)")

            # Save final preview
            final_preview = self._save_final_preview(output_tensor)

            return {
                "ui": {"images": [final_preview]},
                "result": (output_tensor,)
            }

        except Exception as e:
            print(f"✗ Error during upscaling: {str(e)}")
            raise

    def _process_image_gpu(
        self,
        image: torch.Tensor,
        session: ort.InferenceSession,
        tile_size: int,
        target_scale: int,
        native_scale: int,
        seamless: bool
    ) -> torch.Tensor:
        """
        Process image with GPU-optimized tiling.

        Args:
            image: Input tensor (B, H, W, C) on GPU/CPU
            session: ONNX InferenceSession
            tile_size: Tile dimension
            target_scale: Output scale
            native_scale: Model's native scale
            seamless: Use seamless padding

        Returns:
            Upscaled tensor on same device as input
        """
        device = image.device
        batch_size = image.shape[0]

        # Process each image in batch
        output_batch = []
        for idx in range(batch_size):
            if batch_size > 1:
                print(f"Processing image {idx+1}/{batch_size}...")

            # Get single image (H, W, C)
            img = image[idx]

            # Process with tiling
            upscaled = self._process_tiled_gpu(
                img=img,
                session=session,
                tile_size=tile_size,
                target_scale=target_scale,
                native_scale=native_scale,
                seamless=seamless,
                device=device
            )

            output_batch.append(upscaled)

        # Stack batch and return on original device
        output_tensor = torch.stack(output_batch).to(device)
        return output_tensor

    def _process_tiled_gpu(
        self,
        img: torch.Tensor,
        session: ort.InferenceSession,
        tile_size: int,
        target_scale: int,
        native_scale: int,
        seamless: bool,
        device: torch.device
    ) -> torch.Tensor:
        """
        Process single image in tiles with GPU optimization.

        Args:
            img: Input image (H, W, C) tensor
            session: ONNX InferenceSession
            tile_size: Tile dimension
            target_scale: Output scale
            native_scale: Model's native scale
            seamless: Use seamless padding
            device: Device to return result on

        Returns:
            Upscaled image (H*scale, W*scale, C) tensor
        """
        h, w, c = img.shape

        # Calculate margin
        safe_margin = max(4, tile_size // 16)
        use_size = tile_size - (safe_margin * 2)

        print(f"Upscaling {w}x{h} → {w*target_scale}x{h*target_scale} (tile: {tile_size}px, margin: {safe_margin}px)")

        # Convert to numpy for padding (keep on CPU for numpy operations)
        img_np = img.cpu().numpy().astype(np.float32)
        img_np = np.clip(img_np, 0.0, 1.0)

        # Create padded image
        if seamless:
            padded_img = self._create_seamless_padding(img_np, safe_margin)
        else:
            padded_img = self._create_reflection_padding(img_np, safe_margin)

        # Initialize output
        out_h = h * target_scale
        out_w = w * target_scale
        output = np.zeros((out_h, out_w, c), dtype=np.float32)

        # Calculate tile grid
        rows = int(np.ceil(h / use_size))
        cols = int(np.ceil(w / use_size))
        total_tiles = rows * cols

        print(f"Processing {total_tiles} tiles ({rows}x{cols})...")

        # Initialize progress bar
        pbar = comfy.utils.ProgressBar(total_tiles)

        # Check GPU availability
        use_gpu = 'CUDAExecutionProvider' in session.get_providers()

        # Process tiles
        tile_idx = 0
        for row in range(rows):
            for col in range(cols):
                # Extract tile coordinates
                y = row * use_size
                x = col * use_size

                # Extract tile from padded image
                tile = padded_img[y:y+tile_size, x:x+tile_size]

                # Pad edge tiles
                if tile.shape[0] < tile_size or tile.shape[1] < tile_size:
                    tile = np.pad(
                        tile,
                        ((0, tile_size - tile.shape[0]), (0, tile_size - tile.shape[1]), (0, 0)),
                        mode='reflect'
                    )

                # Run GPU-accelerated inference
                upscaled_tile = self._inference_tile_gpu(tile, session, tile_size, native_scale, use_gpu)

                # Calculate stitch coordinates
                src_x = safe_margin * native_scale
                src_y = safe_margin * native_scale
                src_size = use_size * native_scale

                dst_x = x * target_scale
                dst_y = y * target_scale
                dst_size = use_size * target_scale

                # Handle edge tiles
                actual_dst_w = min(dst_size, out_w - dst_x)
                actual_dst_h = min(dst_size, out_h - dst_y)

                # Adjust for scale mismatch
                if native_scale != target_scale:
                    scale_ratio = target_scale / native_scale
                    actual_src_w = int(actual_dst_w / scale_ratio)
                    actual_src_h = int(actual_dst_h / scale_ratio)
                else:
                    actual_src_w = actual_dst_w
                    actual_src_h = actual_dst_h

                # Stitch tile (only inner core, avoiding margin)
                output[dst_y:dst_y+actual_dst_h, dst_x:dst_x+actual_dst_w] = \
                    upscaled_tile[src_y:src_y+actual_src_h, src_x:src_x+actual_src_w]

                # Update progress
                tile_idx += 1
                pbar.update(1)

                # Log progress periodically
                if tile_idx % max(1, total_tiles // 10) == 0 or tile_idx == total_tiles:
                    percent = 100 * tile_idx // total_tiles
                    print(f"  Progress: {tile_idx}/{total_tiles} tiles ({percent}%)")

        # Handle scale mismatch
        if native_scale != target_scale:
            from scipy.ndimage import zoom
            print(f"Downscaling output from {native_scale}x to {target_scale}x...")
            scale_ratio = target_scale / native_scale
            output = zoom(output, (scale_ratio, scale_ratio, 1.0), order=3)

        # Convert back to tensor on original device
        return torch.from_numpy(output).float()

    def _inference_tile_gpu(
        self,
        tile: np.ndarray,
        session: ort.InferenceSession,
        tile_size: int,
        model_scale: int,
        use_gpu: bool
    ) -> np.ndarray:
        """
        Run GPU-optimized ONNX inference on a single tile.

        Args:
            tile: Input tile (H, W, C) numpy array
            session: ONNX InferenceSession
            tile_size: Tile dimension
            model_scale: Model's native scale
            use_gpu: Whether CUDA provider is available

        Returns:
            Upscaled tile (H*scale, W*scale, C) numpy array
        """
        # Convert to ONNX format (NCHW)
        input_tensor = self._to_onnx_tensor(tile, tile_size)

        # Get IO names
        input_name = session.get_inputs()[0].name
        output_name = session.get_outputs()[0].name

        if use_gpu:
            try:
                # GPU-optimized path with IO Binding
                io_binding = session.io_binding()

                # Create GPU tensor
                input_ortvalue = ort.OrtValue.ortvalue_from_numpy(input_tensor, 'cuda', 0)

                # Bind input to GPU
                io_binding.bind_input(
                    name=input_name,
                    device_type='cuda',
                    device_id=0,
                    element_type=np.float32,
                    shape=input_ortvalue.shape(),
                    buffer_ptr=input_ortvalue.data_ptr()
                )

                # Bind output to GPU
                io_binding.bind_output(output_name, 'cuda')

                # Run on GPU
                session.run_with_iobinding(io_binding)

                # Copy result from GPU
                output_tensor = io_binding.copy_outputs_to_cpu()[0]

            except Exception as e:
                # Fallback to standard inference
                print(f"⚠ GPU IO Binding failed, using standard inference: {e}")
                outputs = session.run([output_name], {input_name: input_tensor})
                output_tensor = outputs[0]
        else:
            # CPU inference
            outputs = session.run([output_name], {input_name: input_tensor})
            output_tensor = outputs[0]

        # Convert from NCHW to HWC
        return self._from_onnx_tensor(output_tensor)

    def _to_onnx_tensor(self, img: np.ndarray, tile_size: int) -> np.ndarray:
        """Convert HWC numpy to NCHW tensor."""
        if img.shape[0] != tile_size or img.shape[1] != tile_size:
            raise ValueError(f"Expected ({tile_size}, {tile_size}, 3), got {img.shape}")

        # HWC -> CHW -> NCHW
        img_chw = np.transpose(img, (2, 0, 1))
        img_nchw = np.expand_dims(img_chw, axis=0)
        return np.ascontiguousarray(img_nchw, dtype=np.float32)

    def _from_onnx_tensor(self, tensor: np.ndarray) -> np.ndarray:
        """Convert NCHW tensor to HWC numpy."""
        # NCHW -> CHW -> HWC
        img_chw = tensor[0]
        img_hwc = np.transpose(img_chw, (1, 2, 0))
        return np.clip(img_hwc, 0.0, 1.0).astype(np.float32)

    def _save_final_preview(self, output_tensor: torch.Tensor) -> dict:
        """Save final upscaled image as preview."""
        img = output_tensor[0].cpu().numpy()
        img_uint8 = (np.clip(img, 0, 1) * 255).astype(np.uint8)
        pil_img = Image.fromarray(img_uint8, mode='RGB')

        filename = f"{self.prefix_append}_final.png"
        filepath = os.path.join(self.output_dir, filename)
        pil_img.save(filepath, compress_level=self.compress_level)

        return {
            "filename": filename,
            "subfolder": "",
            "type": self.type
        }

    def _load_model(self, model_name: str) -> ort.InferenceSession:
        """Load and cache ONNX model with GPU support."""
        # Get execution providers
        providers = self._get_execution_providers()
        provider_key = providers[0] if isinstance(providers[0], str) else providers[0][0]

        # Check cache
        cache_key = (model_name, provider_key)
        if cache_key in MC_ImageUpscaleNode._model_cache:
            print(f"Using cached model: {model_name}")
            return MC_ImageUpscaleNode._model_cache[cache_key]

        # Get model path
        model_config = MODEL_CONFIGS[model_name]
        models_dir = self._get_models_dir()
        model_path = os.path.join(models_dir, model_config["filename"])

        # Validate model exists
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Model file not found: {model_path}\n\n"
                f"Please place ONNX models in: {models_dir}\n"
                f"Required files:\n"
                f"  - swin2SR-classical-sr-x4-64.onnx\n"
                f"  - swin2SR-realworld-sr-x4.onnx\n"
                f"  - swin2SR-lightweight-x2-64.onnx"
            )

        print(f"Loading model: {model_config['filename']}...")

        try:
            # Create optimized session
            sess_options = ort.SessionOptions()
            sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            sess_options.enable_mem_pattern = True
            sess_options.enable_cpu_mem_arena = True

            session = ort.InferenceSession(
                model_path,
                sess_options=sess_options,
                providers=providers
            )

            # Verify execution provider
            actual_provider = session.get_providers()[0]
            print(f"✓ Model loaded: {model_name}")
            print(f"✓ Execution provider: {actual_provider}")

            # Warn if fell back to CPU
            if actual_provider == 'CPUExecutionProvider' and provider_key != 'CPUExecutionProvider':
                print(f"⚠ WARNING: GPU requested but using CPU!")
                print(f"   ")
                print(f"   Common causes:")
                print(f"   1. PyTorch is CPU-only (likely after ComfyUI update)")
                print(f"   2. CUDA 12.x Toolkit not installed")
                print(f"   3. Missing CUDA libraries in PATH")
                print(f"   ")
                print(f"   Quick Fix - Reinstall PyTorch with CUDA:")
                print(f"     .venv/Scripts/pip install torch --index-url https://download.pytorch.org/whl/cu124")
                print(f"   ")
                print(f"   Or run install.bat again and choose:")
                print(f"     Option 1 (GPU) -> Option 1 (Reinstall PyTorch with CUDA)")
                print(f"   ")
                print(f"   Alternative - Install CUDA Toolkit manually:")
                print(f"     https://developer.nvidia.com/cuda-downloads")
                print(f"   ")

            # Cache and return
            MC_ImageUpscaleNode._model_cache[cache_key] = session
            return session

        except Exception as e:
            raise RuntimeError(
                f"Failed to load ONNX model: {str(e)}\n\n"
                f"Ensure ONNX Runtime is installed:\n"
                f"  pip install onnxruntime-gpu  (for NVIDIA GPU)\n"
                f"  pip install onnxruntime      (for CPU)"
            )

    def _get_execution_providers(self) -> list:
        """Get ONNX execution providers with GPU priority."""
        available = ort.get_available_providers()

        # Priority: CUDA > DirectML > CPU
        if 'CUDAExecutionProvider' in available:
            return [
                ('CUDAExecutionProvider', {
                    'device_id': 0,
                    'arena_extend_strategy': 'kNextPowerOfTwo',
                    'cudnn_conv_algo_search': 'EXHAUSTIVE',
                    'do_copy_in_default_stream': True,
                }),
                'CPUExecutionProvider'
            ]
        elif 'DmlExecutionProvider' in available:
            return ['DmlExecutionProvider', 'CPUExecutionProvider']
        else:
            return ['CPUExecutionProvider']

    def _create_seamless_padding(self, img: np.ndarray, margin: int) -> np.ndarray:
        """Apply seamless wrap-around padding for tileable textures."""
        h, w, c = img.shape
        padded = np.zeros((h + 2*margin, w + 2*margin, c), dtype=np.float32)

        # Center
        padded[margin:margin+h, margin:margin+w] = img

        # Edges
        padded[0:margin, margin:margin+w] = img[h-margin:h, :]
        padded[margin+h:margin+h+margin, margin:margin+w] = img[0:margin, :]
        padded[margin:margin+h, 0:margin] = img[:, w-margin:w]
        padded[margin:margin+h, margin+w:margin+w+margin] = img[:, 0:margin]

        # Corners
        padded[0:margin, 0:margin] = img[h-margin:h, w-margin:w]
        padded[0:margin, margin+w:margin+w+margin] = img[h-margin:h, 0:margin]
        padded[margin+h:margin+h+margin, 0:margin] = img[0:margin, w-margin:w]
        padded[margin+h:margin+h+margin, margin+w:margin+w+margin] = img[0:margin, 0:margin]

        return padded

    def _create_reflection_padding(self, img: np.ndarray, margin: int) -> np.ndarray:
        """Standard reflection padding for non-tileable images."""
        return np.pad(img, ((margin, margin), (margin, margin), (0, 0)), mode='reflect')


NODE_CLASS_MAPPINGS = {
    "MC_ImageUpscaleNode": MC_ImageUpscaleNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MC_ImageUpscaleNode": "MC: AI Image Upscale"
}
