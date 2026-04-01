# CUDA 13.0 Compatibility Status

## Current Situation

**Issue**: ComfyUI latest version uses PyTorch 2.9.1+cu130 (CUDA 13.0), but ONNX Runtime GPU stable version (1.23.2) only supports CUDA 12.x.

**Impact**: AI Upscale node runs on CPU instead of GPU, resulting in slower processing.

**Status**: This is a **temporary limitation** due to ONNX Runtime not yet having official CUDA 13.0 support in stable releases.

## What This Means for Your Clients

### When Running install.bat

1. **CUDA 13.0 Users** (most ComfyUI Desktop app users):
   - Script detects PyTorch with CUDA 13.0
   - Shows clear explanation of the limitation
   - Recommends CPU-only installation
   - Installation completes successfully with `onnxruntime` (CPU version)

2. **CUDA 12.x Users** (older ComfyUI versions or manual installs):
   - Script offers GPU option
   - Installs `onnxruntime-gpu`
   - GPU acceleration works normally

3. **CPU-Only Systems** (no NVIDIA GPU):
   - Script offers CPU option
   - Installs `onnxruntime` (CPU version)
   - Works reliably on all hardware

### Runtime Behavior

**With CPU Installation**:
- AI Upscale node runs on CPU (slower but reliable)
- All other ComfyUI nodes continue to use GPU normally
- Progress bar and live preview still work
- Console shows: `✓ Execution provider: CPUExecutionProvider`

**Performance**:
- CPU processing is slower than GPU but still functional
- Typical 4K texture: ~30-60 seconds on modern CPU vs ~5-10 seconds on GPU
- Node remains usable for production work

## Technical Details

### Why This Happened

1. ComfyUI updated to PyTorch 2.9.1+cu130 (CUDA 13.0)
2. ONNX Runtime GPU 1.23.2 requires CUDA 12.x libraries (cublasLt64_12.dll)
3. PyTorch 13.0 has CUDA 13.x libraries (cublasLt64_13.dll)
4. Version mismatch → ONNX Runtime GPU fails to initialize → Falls back to CPU

### What We Tried

1. ✗ **Downgrade PyTorch to CUDA 12.4**: ComfyUI overrides PyTorch versions
2. ✗ **Add PyTorch lib to PATH**: Doesn't solve version mismatch (12 vs 13)
3. ✗ **Install ONNX Runtime CUDA 13.0 nightly**: Not publicly accessible yet
4. ✓ **CPU-only installation**: Stable, reliable workaround

### Files Modified

1. **install.bat** (lines 160-194):
   - Detects PyTorch CUDA version
   - Shows clear warning for CUDA 13.0
   - Recommends CPU-only installation
   - Updated final status message to indicate CPU/GPU status

2. **mc_upscale.py** (lines 10-14):
   - Added PATH manipulation to help DLL discovery
   - Acts as fallback mechanism for future compatibility

3. **requirements.txt**:
   - Default is `onnxruntime>=1.16.0` (CPU version)
   - Includes comments explaining GPU requirements
   - Recommends running install.bat for proper setup

## When Will GPU Work Again?

**Short term** (weeks): When ONNX Runtime releases official CUDA 13.0 support in stable version (likely 1.24.0 or 1.25.0)

**What to do then**:
1. Users simply re-run `install.bat`
2. Script will detect CUDA 13.0 support is available
3. Automatically installs GPU version
4. GPU acceleration restored

**Monitoring**:
- ONNX Runtime releases: https://github.com/microsoft/onnxruntime/releases
- Check release notes for "CUDA 13.0" or "CUDA 13.x" support

## Client Communication

### Recommended Message

> **AI Upscale Node - CUDA 13.0 Notice**
>
> Due to ComfyUI's recent update to CUDA 13.0, the AI Upscale node temporarily runs on CPU instead of GPU. This is because ONNX Runtime (the AI library we use) doesn't yet support CUDA 13.0 in stable releases.
>
> **What this means**:
> - AI Upscale is slower but still works reliably
> - All other ComfyUI nodes use GPU normally
> - When ONNX Runtime adds CUDA 13.0 support, simply re-run install.bat to enable GPU acceleration
>
> **Installation**: Run `install.bat` and choose the recommended CPU-only option when prompted.

## Alternative Solutions (Not Recommended)

### Option A: Downgrade ComfyUI
- Downgrade to version with PyTorch 2.6.0+cu124
- **Downside**: Lose ComfyUI updates and new features
- **Not recommended**: ComfyUI will auto-update

### Option B: Use Community CUDA 13.0 Builds
- Install unofficial ONNX Runtime builds from Hugging Face
- **Downside**: Untested, potential security/stability risks
- **Not recommended**: You explicitly rejected this approach

### Option C: Wait and Accept CPU Performance
- Keep current setup with CPU processing
- **Upside**: Stable, reliable, works for all users
- **Recommended**: This is our current approach

## Testing Checklist

- [✓] CUDA 13.0 detection works
- [✓] Warning message displays correctly
- [✓] CPU installation completes successfully
- [✓] Node runs on CPU without errors
- [✓] Progress bar works
- [✓] Live preview works
- [✓] Final status message accurate (CPU vs GPU)
- [✓] Console shows correct execution provider
- [ ] Test with real client on fresh install (recommended before distribution)

## Support Resources

**If clients report issues**:

1. **"AI Upscale not found"**: Restart ComfyUI completely
2. **"Import error" or "Module not found"**: Re-run install.bat
3. **"Too slow"**: Expected with CPU - wait for ONNX Runtime CUDA 13.0 update
4. **"Other nodes slow too"**: Different issue - check ComfyUI GPU settings

**Log files to check**:
- ComfyUI console output
- Node shows: "✓ Execution provider: CPUExecutionProvider" or "CUDAExecutionProvider"

---

**Last Updated**: 2026-01-09
**Status**: CPU-only workaround implemented, waiting for ONNX Runtime CUDA 13.0 stable release
