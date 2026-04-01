@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1

echo ========================================
echo  ComfyUI Custom Node - Dependency Installer
echo ========================================
echo.

REM ============================================
REM Step 1: Detect Python Environment
REM ============================================
echo [Step 1/4] Detecting Python environment...
echo.

set "PYTHON_CMD="
set "INSTALL_TYPE="

REM Current script location
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM Method 1: Portable Version (python_embeded)
REM Structure: ComfyUI_windows_portable/python_embeded/python.exe
REM           ComfyUI_windows_portable/ComfyUI/custom_nodes/YOUR_NODE/
if exist "..\..\python_embeded\python.exe" (
    for %%i in ("..\..\python_embeded\python.exe") do set "PYTHON_CMD=%%~fi"
    set "INSTALL_TYPE=Portable (python_embeded)"
    goto :python_found
)

REM Method 2: Desktop App / Manual Install with venv
REM Structure: ComfyUI/.venv/Scripts/python.exe
REM           ComfyUI/custom_nodes/YOUR_NODE/
if exist "..\..\venv\Scripts\python.exe" (
    for %%i in ("..\..\venv\Scripts\python.exe") do set "PYTHON_CMD=%%~fi"
    set "INSTALL_TYPE=Standard venv"
    goto :python_found
)

if exist "..\..\.venv\Scripts\python.exe" (
    for %%i in ("..\..\.venv\Scripts\python.exe") do set "PYTHON_CMD=%%~fi"
    set "INSTALL_TYPE=Desktop App (.venv)"
    goto :python_found
)

REM Method 3: Check upward directories (up to 5 levels)
for %%d in (1 2 3 4 5) do (
    set "UP_PATH="
    for /l %%i in (1,1,%%d) do (
        set "UP_PATH=!UP_PATH!..\"
    )
    
    if exist "!UP_PATH!python_embeded\python.exe" (
        for %%f in ("!UP_PATH!python_embeded\python.exe") do set "PYTHON_CMD=%%~ff"
        set "INSTALL_TYPE=Portable (Found %%d levels up)"
        goto :python_found
    )
    
    if exist "!UP_PATH!.venv\Scripts\python.exe" (
        for %%f in ("!UP_PATH!.venv\Scripts\python.exe") do set "PYTHON_CMD=%%~ff"
        set "INSTALL_TYPE=Desktop App (Found %%d levels up)"
        goto :python_found
    )
    
    if exist "!UP_PATH!venv\Scripts\python.exe" (
        for %%f in ("!UP_PATH!venv\Scripts\python.exe") do set "PYTHON_CMD=%%~ff"
        set "INSTALL_TYPE=Standard venv (Found %%d levels up)"
        goto :python_found
    )
)

REM Method 4: System Python (Not recommended)
python --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_CMD=python"
    set "INSTALL_TYPE=System Python (WARNING: Not recommended)"
    echo.
    echo ⚠️  WARNING: Using system Python
    echo    This may NOT work correctly with ComfyUI!
    echo    Dependencies will be installed to your system Python.
    echo.
    choice /C YN /M "Do you want to continue anyway"
    if errorlevel 2 goto :error_no_python
    goto :python_found
)

:error_no_python
echo.
echo ========================================
echo  ERROR: Python Not Found
echo ========================================
echo.
echo Could not find ComfyUI's Python environment.
echo.
echo Expected locations:
echo   Portable:    ..\..\python_embeded\python.exe
echo   Desktop App: ..\..\..\.venv\Scripts\python.exe
echo   Standard:    ..\..\venv\Scripts\python.exe
echo.
echo Please verify:
echo   1. ComfyUI is installed correctly
echo   2. This script is in: ComfyUI/custom_nodes/YOUR_NODE/
echo.
pause
exit /b 1

:python_found
echo ✓ Found: !INSTALL_TYPE!
echo   Path: !PYTHON_CMD!
echo.

REM ============================================
REM Step 2: Verify Python
REM ============================================
echo [Step 2/4] Verifying Python installation...
echo.

"!PYTHON_CMD!" --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ ERROR: Python found but failed to execute
    echo    Path: !PYTHON_CMD!
    echo.
    pause
    exit /b 1
)

for /f "delims=" %%i in ('"!PYTHON_CMD!" --version 2^>^&1') do set "PYTHON_VERSION=%%i"
echo ✓ !PYTHON_VERSION!
echo.

REM ============================================
REM Step 3: Select ONNX Runtime Type
REM ============================================
echo [Step 3/5] Select ONNX Runtime for AI Upscale...
echo.
echo The AI Upscale node requires ONNX Runtime.
echo.
echo Choose your installation type:
echo   [1] NVIDIA GPU (CUDA) - For RTX/GTX graphics cards (Recommended)
echo       - Fastest performance
echo       - Requires CUDA-compatible GPU
echo.
echo   [2] CPU Only - For AMD/Intel GPUs or systems without NVIDIA GPU
echo       - Works on all systems
echo       - Slower processing
echo.
choice /C 12 /N /M "Enter your choice (1 or 2): "

if errorlevel 2 goto :cpu_install
if errorlevel 1 goto :gpu_install

:gpu_install
set "ONNX_PACKAGE=onnxruntime-gpu"
set "INSTALL_NIGHTLY=0"
echo.
echo Selected: NVIDIA GPU (CUDA) installation
echo.

REM Check PyTorch CUDA version for compatibility
"!PYTHON_CMD!" -c "import torch; print(torch.version.cuda if hasattr(torch.version, 'cuda') and torch.version.cuda else 'none')" >temp_cuda.txt 2>nul
set /p TORCH_CUDA_VER=<temp_cuda.txt
del temp_cuda.txt 2>nul

if "!TORCH_CUDA_VER!"=="13.0" (
    echo.
    echo ========================================
    echo  CUDA 13.0 Compatibility Issue
    echo ========================================
    echo.
    echo Your ComfyUI has PyTorch with CUDA 13.0
    echo.
    echo Unfortunately, ONNX Runtime GPU currently only supports CUDA 12.x
    echo The CUDA 13.0 nightly builds are not publicly accessible yet.
    echo.
    echo This means AI Upscale will run on CPU ^(slower^).
    echo Other nodes in ComfyUI will still use GPU normally.
    echo.
    echo Options:
    echo   [1] Install CPU-only ONNX Runtime ^(Recommended^)
    echo       - AI Upscale runs on CPU
    echo       - Other nodes use GPU normally
    echo       - Stable and works reliably
    echo.
    echo   [2] Cancel installation
    echo.
    echo Note: When ONNX Runtime adds official CUDA 13.0 support,
    echo       you can run install.bat again to enable GPU for AI Upscale.
    echo.
    choice /C 12 /N /M "Enter your choice (1 or 2): "

    if errorlevel 2 exit /b 0
    if errorlevel 1 goto :cpu_install
)

goto :install_deps

:cpu_install
set "ONNX_PACKAGE=onnxruntime"
echo.
echo Selected: CPU-only installation
echo.
goto :install_deps

REM ============================================
REM Step 4: Install Python Dependencies
REM ============================================
:install_deps
echo [Step 4/5] Installing Python dependencies...
echo.

if not exist "requirements.txt" (
    echo ❌ ERROR: requirements.txt not found
    echo    Location: %cd%
    echo.
    echo Please ensure requirements.txt exists in this directory.
    echo.
    pause
    exit /b 1
)

echo Installing base dependencies from requirements.txt...
echo ----------------------------------------
"!PYTHON_CMD!" -m pip install --upgrade pip >nul 2>&1

REM Install base packages (excluding onnxruntime-gpu from requirements.txt)
"!PYTHON_CMD!" -m pip install torch numpy opencv-python Pillow scipy

echo.
echo Installing %ONNX_PACKAGE%...
echo ----------------------------------------

if defined INSTALL_CUDA13 (
    echo Installing from CUDA 13.0 nightly feed...
    "!PYTHON_CMD!" -m pip install --pre onnxruntime-gpu --index-url https://aiinfra.pkgs.visualstudio.com/PublicPackages/_packaging/ort-cuda-13-nightly/pypi/simple/

    if !errorlevel! neq 0 (
        echo.
        echo ⚠ CUDA 13.0 nightly installation failed
        echo Falling back to CPU version...
        echo.
        "!PYTHON_CMD!" -m pip install onnxruntime>=1.16.0
        set "ONNX_PACKAGE=onnxruntime"
    )
) else (
    "!PYTHON_CMD!" -m pip install %ONNX_PACKAGE%>=1.16.0

    if %errorlevel% neq 0 (
        echo.
        echo ========================================
        echo  ⚠️  Installation Completed with Warnings
        echo ========================================
        echo.
        echo Some packages may have failed to install.
        echo Please check the error messages above.
        echo.
        goto :download_threejs
    )
)

echo.
echo ✓ Python dependencies installed successfully
echo.

REM ============================================
REM Step 5: Download Three.js Libraries
REM ============================================
:download_threejs
echo [Step 5/5] Downloading Three.js libraries...
echo.

set "JS_DIR=js"
if not exist "%JS_DIR%" (
    echo Creating js directory...
    mkdir "%JS_DIR%"
)

REM Check if files already exist
set "THREEJS_EXISTS=0"
set "GLTFLOADER_EXISTS=0"

if exist "%JS_DIR%\three.min.js" (
    set "THREEJS_EXISTS=1"
    echo [SKIP] three.min.js already exists
)

if exist "%JS_DIR%\GLTFLoader.js" (
    set "GLTFLOADER_EXISTS=1"
    echo [SKIP] GLTFLoader.js already exists
)

REM Download if not exists
if !THREEJS_EXISTS! equ 0 (
    echo Downloading three.min.js...
    "!PYTHON_CMD!" -c "import urllib.request; urllib.request.urlretrieve('https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js', 'js/three.min.js'); print('Downloaded successfully')" 2>nul
    
    if %errorlevel% equ 0 (
        echo ✓ three.min.js downloaded
    ) else (
        echo ⚠️  Failed to download three.min.js
        echo    You can manually download from:
        echo    https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js
        echo    and save to: %JS_DIR%\three.min.js
        echo.
    )
)

if !GLTFLOADER_EXISTS! equ 0 (
    echo Downloading GLTFLoader.js...
    "!PYTHON_CMD!" -c "import urllib.request; urllib.request.urlretrieve('https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/GLTFLoader.js', 'js/GLTFLoader.js'); print('Downloaded successfully')" 2>nul
    
    if %errorlevel% equ 0 (
        echo ✓ GLTFLoader.js downloaded
    ) else (
        echo ⚠️  Failed to download GLTFLoader.js
        echo    You can manually download from:
        echo    https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/GLTFLoader.js
        echo    and save to: %JS_DIR%\GLTFLoader.js
        echo.
    )
)

echo.
echo ========================================
echo  ✓ Installation Completed!
echo ========================================
echo.
echo Installed Dependencies:
echo   ✓ torch
echo   ✓ numpy
echo   ✓ opencv-python
echo   ✓ Pillow
echo   ✓ scipy
echo   ✓ %ONNX_PACKAGE% ^>= 1.16.0
echo.
echo JavaScript Libraries:
if exist "%JS_DIR%\three.min.js" (
    echo   ✓ js/three.min.js
) else (
    echo   ✗ js/three.min.js [MISSING - 3D preview may not work]
)
if exist "%JS_DIR%\GLTFLoader.js" (
    echo   ✓ js/GLTFLoader.js
) else (
    echo   ✗ js/GLTFLoader.js [MISSING - 3D preview may not work]
)
echo.
echo ========================================
echo  AI Upscale Models Status
echo ========================================
echo.
echo Checking for ONNX models in: models\
echo.

REM Create models directory if it doesn't exist
if not exist "models\" (
    echo Creating models directory...
    mkdir models
    echo.
)

REM Check for models
set MODEL_COUNT=0

if exist "models\swin2SR-classical-sr-x4-64.onnx" (
    set /a MODEL_COUNT+=1
    echo   ✓ swin2SR-classical-sr-x4-64.onnx
) else (
    echo   ✗ swin2SR-classical-sr-x4-64.onnx [MISSING]
)

if exist "models\swin2SR-realworld-sr-x4.onnx" (
    set /a MODEL_COUNT+=1
    echo   ✓ swin2SR-realworld-sr-x4.onnx
) else (
    echo   ✗ swin2SR-realworld-sr-x4.onnx [MISSING]
)

if exist "models\swin2SR-lightweight-x2-64.onnx" (
    set /a MODEL_COUNT+=1
    echo   ✓ swin2SR-lightweight-x2-64.onnx
) else (
    echo   ✗ swin2SR-lightweight-x2-64.onnx [MISSING]
)

echo.
if %MODEL_COUNT%==3 (
    echo Models: All found! [3/3] ✓
    echo AI Upscale node is ready to use!
) else (
    echo Models: %MODEL_COUNT%/3 found
    echo.
    echo ⚠️  WARNING: Some ONNX models are missing!
    echo.
    echo Please place the following files in: %CD%\models\
    echo   - swin2SR-classical-sr-x4-64.onnx
    echo   - swin2SR-realworld-sr-x4.onnx
    echo   - swin2SR-lightweight-x2-64.onnx
    echo.
    echo The AI Upscale node will not work without these models.
)

echo.
echo ========================================
echo  Next Steps
echo ========================================
echo.
echo 1. Restart ComfyUI completely
echo 2. Refresh your browser/app
echo 3. Find "MC: AI Image Upscale" in: MC_PBR_Master/Adjustment
echo.
echo Features Available:
echo   ✓ Live tile-by-tile preview
echo   ✓ Progress tracking with percentage
echo   ✓ 3 Swin2SR models (2x/4x upscaling)
echo   ✓ Seamless texture padding

if "%ONNX_PACKAGE%"=="onnxruntime-gpu" (
    echo   ✓ GPU acceleration (CUDA)
) else (
    echo   ℹ CPU processing (onnxruntime)
    echo     Note: AI Upscale will run on CPU. Other ComfyUI nodes still use GPU.
)
echo.
echo If you encounter any issues, please check:
echo   - ComfyUI console for error messages
echo   - Custom node documentation (UPSCALE_README.md)
echo.
pause
exit /b 0