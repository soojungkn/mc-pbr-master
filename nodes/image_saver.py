import os
import torch
import numpy as np
from PIL import Image
import folder_paths

class PBRTextureExport:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "save_path": ("STRING", {
                    "default": "MicroCreativity_PBR",
                    "folder_picker": True
                }),
                "material_name": ("STRING", {"default": "MC_Material"}),
                "extension": (["png", "tiff", "tga"],),
                "bit_depth": (["8-bit", "16-bit"], {"default": "8-bit"}),
            },
            "optional": {
                "BaseColor": ("IMAGE",),
                "Roughness": ("IMAGE",),
                "Metallic": ("IMAGE",),
                "AmbientOcclusion": ("IMAGE",),
                "ORM": ("IMAGE",),
                "Normal": ("IMAGE",),
                "Displacement": ("IMAGE",),
            }
        }

    RETURN_TYPES = ()
    FUNCTION = "save_pbr_set"
    OUTPUT_NODE = True
    CATEGORY = "MC_PBR_Master"

    def save_pbr_set(self, save_path, material_name, extension, bit_depth, **kwargs):
        # Handle both relative and absolute paths
        if os.path.isabs(save_path):
            output_path = save_path
        else:
            # Relative path - use ComfyUI's output directory as base
            output_path = os.path.join(folder_paths.get_output_directory(), save_path)

        if not os.path.exists(output_path):
            os.makedirs(output_path, exist_ok=True)

        for map_name, image_tensor in kwargs.items():
            if image_tensor is None:
                continue

            batch_size = image_tensor.shape[0]
            for i in range(batch_size):
                img_np = image_tensor[i].cpu().numpy()

                if len(img_np.shape) == 2:
                    img_np = img_np[..., np.newaxis]

                channels = img_np.shape[2]

                if bit_depth == "16-bit" and extension in ["tiff", "png"]:
                    img_data = (np.clip(img_np, 0, 1) * 65535.0).astype(np.uint16)
                    # PIL 16-bit support: I;16 for grayscale. RGB 16-bit not supported directly.
                    if channels == 1:
                        pil_mode = 'I;16'
                    else:
                        print(f"Warning: 16-bit RGB not fully supported by PIL directly, converting {map_name} to 8-bit.")
                        img_data = (np.clip(img_np, 0, 1) * 255.0).astype(np.uint8)
                        pil_mode = 'RGB'
                else:
                    img_data = (np.clip(img_np, 0, 1) * 255.0).astype(np.uint8)
                    pil_mode = 'L' if channels == 1 else 'RGB'
                    if channels == 4: pil_mode = 'RGBA'

                suffix = f"_{map_name}" if batch_size == 1 else f"_{map_name}_{i}"
                filename = f"T_{material_name}{suffix}.{extension}"
                full_path = os.path.join(output_path, filename)
                
                try:
                    if channels == 1:
                        img = Image.fromarray(img_data.squeeze(), mode=pil_mode)
                    else:
                        img = Image.fromarray(img_data, mode=pil_mode)
                    
                    img.save(full_path)
                    print(f"Saved: {full_path}")
                except Exception as e:
                    print(f"Error saving {full_path}: {e}")

        return ()
