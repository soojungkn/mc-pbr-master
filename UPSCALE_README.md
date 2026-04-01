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
  - 🔧 Tile-by-tile progress
  - ✅ Complete

- **Progress Bar**: Real-time percentage completion

- **Canvas Preview**: Live visualization of upscaling process
  - Each tile appears as it's processed
  - Builds the final image progressively (like the HTML version)

### Setup

1. **Place ONNX Models** in `models/` folder:
   ```
   models/
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

### Usage

1. Add node: `MC: AI Image Upscale` under `MC_PBR_Master/Adjustment`
2. Connect an image input
3. Configure parameters:
   - **Model**: Choose Swin2SR variant
   - **Output Scale**: x2 or x4
   - **Tile Size**: 128 (high-end), 96 (recommended), 64 (low-end)
   - **Seamless**: Yes for tileable textures, No for photos
4. Queue the workflow
5. Watch the live preview as tiles are processed!

## Preview Panel Layout

```
┌─────────────────────────────────┐
│ ⏳ Loading model: Swin2SR...    │ ← Status
├─────────────────────────────────┤
│ ████████████░░░░░░░░░ 60%      │ ← Progress
├─────────────────────────────────┤
│                                 │
│     [Live Canvas Preview]       │ ← Tile-by-tile render
│                                 │
└─────────────────────────────────┘
```

## Technical Details

### Event System

The node communicates with the frontend via WebSocket events:
- `model_loading` - Model is being loaded
- `model_loaded` - Model ready
- `processing_start` - Upscaling begins
- `tile_progress` - Each tile processed (with preview image)
- `complete` - Processing finished
- `error` - Error occurred

### Preview Generation

- Each tile is encoded as a base64 PNG
- Sent to frontend via WebSocket
- Canvas draws tiles at exact positions
- Creates seamless progressive rendering

## Troubleshooting

**Preview not showing?**
- Ensure JavaScript is enabled
- Check browser console for errors
- Verify ComfyUI server is running

**Slow processing?**
- Reduce tile size (128 → 96 → 64)
- Use GPU acceleration (install onnxruntime-gpu)
- Check model is loaded (status shows checkmark)

**Model not found error?**
- Place .onnx files in `models/` directory
- Check file names match exactly
- Restart ComfyUI

## Performance

| Tile Size | VRAM Usage | Speed      | Quality |
|-----------|------------|------------|---------|
| 128px     | ~512 MB    | Fast       | Best    |
| 96px      | ~288 MB    | Medium     | Good    |
| 64px      | ~128 MB    | Slower     | Good    |

## Comparison with HTML Version

The ComfyUI node provides the same tile-by-tile visualization as the original HTML upscaler:
- ✅ Real-time tile rendering
- ✅ Progress tracking
- ✅ Model status indicators
- ✅ Error handling
- ✅ Seamless padding visualization

**Benefits over HTML:**
- No file upload/download
- Integrates with ComfyUI workflows
- GPU auto-detection
- Batch processing support
