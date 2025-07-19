#!/bin/bash

# Fixed deployment script for Face Swap API
set -e

echo "🚀 Starting Face Swap API deployment with fixes..."

# Check if main_fixed.py exists
if [ ! -f "main_fixed.py" ]; then
    echo "❌ Error: main_fixed.py not found in current directory"
    echo "Current directory contents:"
    ls -la
    exit 1
fi

echo "✅ main_fixed.py found"

# Check if requirements-api.txt exists
if [ ! -f "requirements-api.txt" ]; then
    echo "❌ Error: requirements-api.txt not found"
    exit 1
fi

echo "✅ requirements-api.txt found"

# Check if model file exists (optional)
if [ -f "inswapper_128.fp16.onnx" ]; then
    echo "✅ Model file found: inswapper_128.fp16.onnx"
    MODEL_SIZE=$(stat -f%z "inswapper_128.fp16.onnx" 2>/dev/null || stat -c%s "inswapper_128.fp16.onnx" 2>/dev/null || echo "unknown")
    echo "   Model size: $MODEL_SIZE bytes"
else
    echo "⚠️  Model file not found - will be downloaded on first run"
fi

# Build the Docker image
echo "🔨 Building Docker image..."
docker build -f Dockerfile.fixed -t face-swap-fixed:latest .

if [ $? -eq 0 ]; then
    echo "✅ Docker build successful!"
else
    echo "❌ Docker build failed!"
    exit 1
fi

# Test the container
echo "🧪 Testing container startup..."
docker run --rm -d --name face-swap-test -p 8000:8000 face-swap-fixed:latest

# Wait for startup
echo "⏳ Waiting for application to start..."
sleep 10

# Check health endpoint
echo "🏥 Checking health endpoint..."
HEALTH_CHECK=$(curl -s http://localhost:8000/health || echo "failed")

if [[ $HEALTH_CHECK == *"healthy"* ]]; then
    echo "✅ Health check passed!"
    echo "Health status: $HEALTH_CHECK"
else
    echo "❌ Health check failed!"
    echo "Response: $HEALTH_CHECK"
    
    # Show container logs for debugging
    echo "📋 Container logs:"
    docker logs face-swap-test
fi

# Stop test container
docker stop face-swap-test

echo "🎉 Deployment test complete!"
echo ""
echo "To run the container:"
echo "docker run -d --name face-swap -p 8000:8000 face-swap-fixed:latest"
echo ""
echo "To check logs:"
echo "docker logs face-swap"
echo ""
echo "To test the API:"
echo "curl http://localhost:8000/health"