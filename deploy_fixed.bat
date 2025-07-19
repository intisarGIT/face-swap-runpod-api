@echo off
echo 🚀 Starting Face Swap API deployment with fixes...

REM Check if main_fixed.py exists
if not exist "main_fixed.py" (
    echo ❌ Error: main_fixed.py not found in current directory
    echo Current directory contents:
    dir
    exit /b 1
)

echo ✅ main_fixed.py found

REM Check if requirements-api.txt exists
if not exist "requirements-api.txt" (
    echo ❌ Error: requirements-api.txt not found
    exit /b 1
)

echo ✅ requirements-api.txt found

REM Check if model file exists (optional)
if exist "inswapper_128.fp16.onnx" (
    echo ✅ Model file found: inswapper_128.fp16.onnx
    for %%A in ("inswapper_128.fp16.onnx") do echo    Model size: %%~zA bytes
) else (
    echo ⚠️  Model file not found - will be downloaded on first run
)

REM Build the Docker image
echo 🔨 Building Docker image...
docker build -f Dockerfile.fixed -t face-swap-fixed:latest .

if %errorlevel% neq 0 (
    echo ❌ Docker build failed!
    exit /b 1
)

echo ✅ Docker build successful!

REM Test the container
echo 🧪 Testing container startup...
docker run --rm -d --name face-swap-test -p 8000:8000 face-swap-fixed:latest

REM Wait for startup
echo ⏳ Waiting for application to start...
timeout /t 10 /nobreak >nul

REM Check health endpoint
echo 🏥 Checking health endpoint...
curl -s http://localhost:8000/health

REM Stop test container
docker stop face-swap-test

echo 🎉 Deployment test complete!
echo.
echo To run the container:
echo docker run -d --name face-swap -p 8000:8000 face-swap-fixed:latest
echo.
echo To check logs:
echo docker logs face-swap
echo.
echo To test the API:
echo curl http://localhost:8000/health