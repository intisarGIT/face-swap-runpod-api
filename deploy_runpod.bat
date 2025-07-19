@echo off
REM RunPod Deployment Script for Face Swap API (Windows)
REM This script addresses worker exit code 3 issues by using proper configuration

echo 🚀 Starting RunPod Face Swap API Deployment...

REM Check if required files exist
echo [INFO] Checking required files...

if not exist "Dockerfile.runpod" (
    echo [ERROR] Required file missing: Dockerfile.runpod
    exit /b 1
)

if not exist "main_fixed.py" (
    echo [ERROR] Required file missing: main_fixed.py
    exit /b 1
)

if not exist "runpod_handler.py" (
    echo [ERROR] Required file missing: runpod_handler.py
    exit /b 1
)

if not exist "requirements-runpod.txt" (
    echo [ERROR] Required file missing: requirements-runpod.txt
    exit /b 1
)

if not exist "runpod.toml" (
    echo [ERROR] Required file missing: runpod.toml
    exit /b 1
)

echo [SUCCESS] All required files found

REM Check for model files
echo [INFO] Checking for model files...

if exist "inswapper_128.fp16.onnx" (
    echo [SUCCESS] Found FP16 model: inswapper_128.fp16.onnx
) else if exist "inswapper_128.onnx" (
    echo [SUCCESS] Found standard model: inswapper_128.onnx
) else (
    echo [WARNING] No model file found - will be downloaded during runtime
)

REM Build Docker image
echo [INFO] Building Docker image locally for testing...

docker build -f Dockerfile.runpod -t face-swap-runpod:latest .
if %errorlevel% neq 0 (
    echo [ERROR] Docker build failed
    exit /b 1
)

echo [SUCCESS] Docker image built successfully

REM Create test payload
echo [INFO] Creating test payload file...

echo {> runpod_test_payload.json
echo   "input": {>> runpod_test_payload.json
echo     "source_url": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400",>> runpod_test_payload.json
echo     "target_url": "https://images.unsplash.com/photo-1494790108755-2616b612b786?w=400",>> runpod_test_payload.json
echo     "source_index": 1,>> runpod_test_payload.json
echo     "target_index": 1>> runpod_test_payload.json
echo   }>> runpod_test_payload.json
echo }>> runpod_test_payload.json

echo [SUCCESS] Test payload created: runpod_test_payload.json

echo.
echo 🎯 RunPod Deployment Instructions:
echo ==================================
echo.
echo 1. Upload your project to RunPod:
echo    - Use the RunPod web interface or CLI
echo    - Make sure to use Dockerfile.runpod as your Dockerfile
echo.
echo 2. Configure your RunPod template:
echo    - Container Image: Use the built image
echo    - Container Start Command: python -u runpod_handler.py
echo    - Environment Variables:
echo      * PYTHONPATH=/app
echo      * PYTHONUNBUFFERED=1
echo.
echo 3. Set resource requirements:
echo    - GPU: RTX 4090 or similar
echo    - RAM: 8GB minimum
echo    - CPU: 2 cores minimum
echo.
echo 4. Test your deployment:
echo    - Use the test payload in runpod_test_payload.json
echo    - Monitor logs for any startup issues
echo.

echo [SUCCESS] 🎉 RunPod deployment preparation completed!
echo [INFO] Your Face Swap API is ready for RunPod deployment
echo [INFO] Follow the instructions above to deploy to RunPod

pause