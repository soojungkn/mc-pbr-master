# MC: AI Upscale (Swin2SR) - Live Preview Guide

## Features

The AI Upscale node includes real-time progress visualization, showing:

1. **Model Loading Status** - Visual indicator when models are being loaded
2. **Live Tile Processing** - Watch each tile being upscaled in real-time
3. **Progress Bar** - Visual progress with percentage
4. **Processing Stats** - Tile count, output size, and processing duration

## How It Works

### Visual Indicators

The node displays a live preview panel showing:

- **Status Bar**: Current operation status
  - ⏳ Model loading
  - ✓ Model loaded
  - 🚀 Processing started
  - ✅ Complete

- **Progress Bar**: Real-time percentage completion

### Setup

1. **Place ONNX Models** in ComfyUI's standard `upscale_models` folder:
   ```
   ComfyUI/models/upscale_models/
   ├── swin2SR-classical-sr-x4-64.onnx
   ├── swin2SR-realworld-sr-x4.onnx
   └── swin2SR-lightweight-x2-64.onnx
   ```

2. **Install Dependencies**:
   ```bash
   pip install onnxruntime-gpu  # For NVIDIA GPU
   # OR
   pip install onnxruntime      # For CPU
   ```

3. **Restart ComfyUI** to load the node

## Troubleshooting

**Slow processing?**
- Reduce tile size (512 → 256 → 128)
- Use GPU acceleration (install onnxruntime-gpu)
- Check model is loaded (status shows checkmark)

**Model not found error?**
- Place .onnx files in `ComfyUI/models/upscale_models/`
- Check file names match exactly
- Restart ComfyUI