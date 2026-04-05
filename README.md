# MicroCreativity PBR Master

A professional **ComfyUI custom node pack** for end-to-end PBR texture generation. Generate, adjust, pack, upscale, and preview PBR maps — all inside ComfyUI.
It's free to use in personal and commercial projects, BUT you cannot redistribute, bundle, or resell it.
Please read the [LICENSE](LICENSE) for more information.

---

## 🌐 Workflow Presets

Looking for one-click workflows setup and prompt editors for creatives?
Now available on **MicroCreativity Hub**:

👉 **[hub.microcreativity.xyz](https://hub.microcreativity.xyz)**

Download a preset, drop it into ComfyUI, and start creating immediately.

---

## ✨ Features

### 🗺️ Map Generation
| Node | Description |
|------|-------------|
| **MC: Albedo Prompt Engine** | Prompt builder for generating albedo/base color maps |
| **MC: Height Map** | Extract a height map from any image with channel selection, levels, and gamma correction |
| **MC: Roughness** | Derive a roughness map with levels and gamma controls |
| **MC: Metallic** | Derive a metallic map with levels and gamma controls |
| **MC: Grayscale Map** | Convert any image to a calibrated grayscale map |
| **MC: Height to Normal** | Convert a height map to a tangent-space normal map |
| **MC: Ambient Occlusion** | Generate an ambient occlusion map from a height map |

### 🎨 Image Processing
| Node | Description |
|------|-------------|
| **MC: Image Blur** | Gaussian blur with adjustable radius |
| **MC: Image Sharpen** | Unsharp-mask sharpening with strength control |
| **MC: Value Control** | Universal float/int value slider — wire into any numeric input |
| **MC: Image Preview Pass** | Pass-through node that emits a live preview without interrupting the workflow |

### 📦 Packing & Export
| Node | Description |
|------|-------------|
| **MC: RGB Channel Packer** | Pack up to three grayscale maps into a single RGB texture (e.g. ORM: Occlusion/Roughness/Metallic) |
| **MC: PBR Texture Export** | Save all PBR maps to disk with a chosen material name, format (PNG/TIFF/TGA), and bit-depth (8-bit / 16-bit) |

### 🔬 Preview & Validation
| Node | Description |
|------|-------------|
| **MC: 3D Texture Preview** | Real-time WebGL preview of your texture set on a Sphere, Cube, or Plane — powered by Three.js |
| **MC: Tile Checker** | Render your texture tiled (2×2 up to 5×5) to check seamless tiling |

### ⬆️ AI Upscaling
| Node | Description |
|------|-------------|
| **MC: AI Image Upscale** | GPU-accelerated 2× or 4× upscaling via Swin2SR ONNX models with tiled processing and seamless texture support |

---

## 🤖 AI Upscale Models

The **MC: AI Image Upscale** node requires Swin2SR ONNX model files placed in the `models/upscale_models/` folder in ComfyUI:

| File | Mode | Scale | Best For |
|------|------|-------|----------|
| `swin2SR-classical-sr-x4-64.onnx` | High Details | 4× | Clean textures, maximum quality |
| `swin2SR-realworld-sr-x4.onnx` | Noise Reduction | 4× | Noisy or compressed images |
| `swin2SR-lightweight-x2-64.onnx` | Lightweight | 2× | Faster processing |

## 🔗 Model links (for AI Image Upscale Node)
- Download "model.onnx" from each link, and rename the files to each model name.

**swin2SR models**
- [swin2SR-classical-sr-x4-64](https://huggingface.co/Xenova/swin2SR-classical-sr-x4-64/tree/main/onnx)
- [swin2SR-realworld-sr-x4](https://huggingface.co/Xenova/swin2SR-realworld-sr-x4-64-bsrgan-psnr/tree/main/onnx)
- [swin2SR-lightweight-x2-64](https://huggingface.co/Xenova/swin2SR-lightweight-x2-64/tree/main/onnx)

Download the ONNX model files and place them in:
```
📂 ComfyUI/
└── 📂 models/
      └── 📂 upscale_models/
             ├── swin2SR-classical-sr-x4-64.onnx
             ├── swin2SR-realworld-sr-x4.onnx
             └── swin2SR-lightweight-x2-64.onnx

```

> **CUDA note:** The upscaler supports CUDA → DirectML → CPU execution in priority order. If GPU inference silently falls back to CPU, re-run `install.bat` or reinstall PyTorch with CUDA:
> ```bash
> pip install torch --index-url https://download.pytorch.org/whl/cu124
> ```

---

## 📋 Requirements

| Dependency | Purpose |
|------------|---------|
| `torch` | Tensor operations, GPU support |
| `numpy` | Array processing |
| `opencv-python` | Image processing kernels |
| `Pillow` | Image I/O |
| `scipy` | Scale-ratio resampling for upscaling |
| `onnxruntime-gpu` *(recommended)* | GPU inference for AI Upscale |
| `onnxruntime` *(CPU fallback)* | CPU inference for AI Upscale |

---

## 🚀 Installation

1. Clone this repository into your `ComfyUI/custom_nodes/` folder

2. **Run `install.bat`** — it will:
   - Detect whether your PyTorch has CUDA support
   - Ask you to choose GPU or CPU mode
   - Install the correct `onnxruntime` version
   - Validate GPU activation

3. Restart ComfyUI.

---

## 🗂️ Node Categories

All nodes appear under the **`MC_PBR_Master`** category in the ComfyUI node browser. Map generation nodes appear under **`MC_PBR_Master/Map Generation`**.

---

## 🧩 Typical Workflow

```
[Image / AI Generation]
        │
        ├─► MC: Height Map ──► MC: Height to Normal
        │         │
        │         └──► MC: Ambient Occlusion
        │
        ├─► MC: Roughness
        ├─► MC: Metallic
        │
        ├─► MC: RGB Channel Packer  (ORM texture)
        │
        ├─► MC: AI Image Upscale    (optional)
        ├─► MC: Tile Checker        (validate seamless)
        ├─► MC: 3D Texture Preview  (real-time WebGL)
        │
        └─► MC: PBR Texture Export  (save to disk)
```
---

## 🛠️ Troubleshooting

**Nodes not appearing in ComfyUI**
- Confirm the folder is inside `ComfyUI/custom_nodes/`
- Check the ComfyUI console for import errors
- Make sure all dependencies are installed in the same Python environment ComfyUI uses

**AI Upscale node fails**
- Run `install.bat` to install `onnxruntime` automatically
- Verify ONNX model files exist in the `models/` folder
- For GPU: ensure `onnxruntime-gpu` is installed and your CUDA drivers are up to date

**16-bit export shows a warning**
- 16-bit export is supported for **grayscale** maps (PNG/TIFF). RGB maps will fall back to 8-bit due to PIL limitations.

---

## 📄 License

This project uses a **custom license**. See [LICENSE](LICENSE) for the full terms.

**In short:**
- ✅ Free to use in personal and commercial projects (as a tool/workflow)
- ❌ Redistribution, bundling, and resale are prohibited

---

*Made with ❤️ by MicroCreativity*
