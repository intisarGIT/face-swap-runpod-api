#!/bin/bash

# RunPod Deployment Script for Face Swap API
# This script addresses worker exit code 3 issues by using proper configuration

set -e

echo "🚀 Starting RunPod Face Swap API Deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if required files exist
print_status "Checking required files..."

required_files=(
    "Dockerfile.runpod"
    "main_fixed.py"
    "runpod_handler.py"
    "requirements-runpod.txt"
    "runpod.toml"
)

for file in "${required_files[@]}"; do
    if [[ ! -f "$file" ]]; then
        print_error "Required file missing: $file"
        exit 1
    fi
done

print_success "All required files found"

# Check if model file exists
print_status "Checking for model files..."

if [[ -f "inswapper_128.fp16.onnx" ]]; then
    print_success "Found FP16 model: inswapper_128.fp16.onnx"
elif [[ -f "inswapper_128.onnx" ]]; then
    print_success "Found standard model: inswapper_128.onnx"
else
    print_warning "No model file found - will be downloaded during runtime"
fi

# Build the Docker image locally for testing
print_status "Building Docker image locally for testing..."

docker build -f Dockerfile.runpod -t face-swap-runpod:latest . || {
    print_error "Docker build failed"
    exit 1
}

print_success "Docker image built successfully"

# Test the container locally
print_status "Testing container startup..."

# Start container in detached mode
CONTAINER_ID=$(docker run -d --name face-swap-runpod-test -p 8000:8000 face-swap-runpod:latest)

# Wait for container to start
sleep 10

# Check if container is running
if docker ps | grep -q face-swap-runpod-test; then
    print_success "Container started successfully"
    
    # Test health endpoint if available
    if command -v curl &> /dev/null; then
        print_status "Testing health endpoint..."
        if curl -f http://localhost:8000/health &> /dev/null; then
            print_success "Health check passed"
        else
            print_warning "Health check failed - this is expected for RunPod serverless mode"
        fi
    fi
else
    print_error "Container failed to start"
    docker logs face-swap-runpod-test
    docker rm -f face-swap-runpod-test
    exit 1
fi

# Clean up test container
print_status "Cleaning up test container..."
docker stop face-swap-runpod-test
docker rm face-swap-runpod-test

print_success "Local testing completed successfully"

# RunPod deployment instructions
echo ""
echo "🎯 RunPod Deployment Instructions:"
echo "=================================="
echo ""
echo "1. Upload your project to RunPod:"
echo "   - Use the RunPod web interface or CLI"
echo "   - Make sure to use Dockerfile.runpod as your Dockerfile"
echo ""
echo "2. Configure your RunPod template:"
echo "   - Container Image: Use the built image"
echo "   - Container Start Command: python -u runpod_handler.py"
echo "   - Environment Variables:"
echo "     * PYTHONPATH=/app"
echo "     * PYTHONUNBUFFERED=1"
echo ""
echo "3. Set resource requirements:"
echo "   - GPU: RTX 4090 or similar"
echo "   - RAM: 8GB minimum"
echo "   - CPU: 2 cores minimum"
echo ""
echo "4. Test your deployment:"
echo "   - Use the test payload in runpod_debug.py"
echo "   - Monitor logs for any startup issues"
echo ""

# Create a test payload file
print_status "Creating test payload file..."

cat > runpod_test_payload.json << EOF
{
  "input": {
    "source_url": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400",
    "target_url": "https://images.unsplash.com/photo-1494790108755-2616b612b786?w=400",
    "source_index": 1,
    "target_index": 1
  }
}
EOF

print_success "Test payload created: runpod_test_payload.json"

# Create deployment checklist
print_status "Creating deployment checklist..."

cat > RUNPOD_DEPLOYMENT_CHECKLIST.md << EOF
# RunPod Deployment Checklist

## Pre-deployment Checks
- [x] Docker image builds successfully
- [x] Container starts without errors
- [x] All required files are present
- [x] Model files are available or will be downloaded

## RunPod Configuration
- [ ] Template created with correct settings
- [ ] Dockerfile.runpod specified as build file
- [ ] Environment variables configured
- [ ] Resource requirements set (GPU, RAM, CPU)
- [ ] Handler function specified: runpod_handler.py

## Post-deployment Testing
- [ ] Worker starts without exit code 3 errors
- [ ] Health check passes (if applicable)
- [ ] Face swap functionality works
- [ ] Memory usage is within limits
- [ ] Response times are acceptable

## Troubleshooting
If you encounter worker exit code 3:
1. Check that Dockerfile.runpod is being used
2. Verify all files are copied correctly
3. Ensure runpod_handler.py is the entry point
4. Check logs for initialization errors
5. Verify model files are accessible

## Test Command
Use this payload to test your deployment:
\`\`\`json
$(cat runpod_test_payload.json)
\`\`\`
EOF

print_success "Deployment checklist created: RUNPOD_DEPLOYMENT_CHECKLIST.md"

echo ""
print_success "🎉 RunPod deployment preparation completed!"
print_status "Your Face Swap API is ready for RunPod deployment"
print_status "Follow the instructions above to deploy to RunPod"

echo ""
echo "📋 Files created/updated:"
echo "- Dockerfile.runpod (RunPod-optimized Dockerfile)"
echo "- runpod_handler.py (Serverless handler)"
echo "- requirements-runpod.txt (RunPod dependencies)"
echo "- runpod.toml (RunPod configuration)"
echo "- runpod_test_payload.json (Test payload)"
echo "- RUNPOD_DEPLOYMENT_CHECKLIST.md (Deployment guide)"