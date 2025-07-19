# GitHub to RunPod Deployment Guide

## ✅ Your Repository is Ready for GitHub Deployment!

You can deploy directly from GitHub to RunPod without building Docker locally. Here's how:

## Files Updated for Deployment

### ✅ Optimized Files Ready:
- **`main_fixed.py`** - A new, robust version with auto-recovery, FP16 support, and model caching.
- **`Dockerfile`** - Updated to use `main_fixed.py` and best practices for model handling.
- **`start_runpod.sh`** - Updated to launch the new `main_fixed.py` script.

## RunPod Serverless Deployment Steps

### 1. Push to GitHub
```bash
git add .
git commit -m "feat: implement auto-recovering faceswap API"
git push origin main
```

### 2. Create RunPod Serverless Endpoint

1. **Go to RunPod Dashboard** → Serverless
2. **Click "New Endpoint"**
3. **Configure as follows:**

```yaml
# Basic Configuration
Name: face-swap-api
Source: GitHub Repository
Repository: your-username/your-repo-name
Branch: main

# Container Configuration
Container Image: Build from Dockerfile
Dockerfile Path: ./Dockerfile

# Resource Configuration (CRITICAL - This fixes exit code 3)
GPU: RTX 3090 or RTX 4090 or A100
Memory: 8192 MB (8GB minimum)
GPU Memory: 4096 MB (4GB minimum)
Container Disk: 10 GB

# Advanced Settings
Max Workers: 10
Idle Timeout: 5 minutes
Execution Timeout: 300 seconds (5 minutes)
```

### 3. Environment Variables (Optional)
```env
PYTHONPATH=/app
CUDA_VISIBLE_DEVICES=0
PYTHONUNBUFFERED=1
```

### 4. Update Your Route.ts

Replace your RunPod endpoint URL with the actual one:

```typescript
// In your route.ts file, update this line:
const RUNPOD_ENDPOINT = "https://api.runpod.ai/v2/YOUR_ACTUAL_ENDPOINT_ID/runsync"

// Example:
const RUNPOD_ENDPOINT = "https://api.runpod.ai/v2/abc123def456/runsync"
```

## Key Fixes Applied

### ✅ Memory Management
- **Automatic Model Recovery**: Detects and fixes corrupted ONNX models.
- **FP16 Model Support**: Prioritizes the faster, smaller `inswapper_128.fp16.onnx` model.
- **Dynamic Model Loading**: The Docker container downloads the model on first run, keeping the image light.
- **Enhanced Health Checks**: The `/health` endpoint now reports on model validity and which model is active.

### ✅ Error Handling
- Comprehensive error messages
- Timeout management
- Resource validation

### ✅ Performance Optimization
- Pre-loaded models (when possible)
- Efficient image processing
- Memory-conscious operations

## Testing Your Deployment

### 1. Test Health Endpoint
```bash
curl https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/health
# You can also use the /fix-model endpoint to manually trigger a fix
curl -X POST https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/fix-model
```

### 2. Test Face Swap
```bash
curl -X POST "https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/runsync" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "input": {
      "source_url": "https://example.com/source.jpg",
      "target_url": "https://example.com/target.jpg",
      "source_index": 1,
      "target_index": 1
    }
  }'
```

## Expected Results

After deployment with these fixes:
- ✅ **No more exit code 3 errors**
- ✅ **Faster response times** (models cached)
- ✅ **Better memory usage**
- ✅ **Proper error handling**
- ✅ **Support for larger images**

## Troubleshooting

### If you still get exit code 3:
1. **Increase memory allocation** to 16GB
2. **Use A100 GPU** for more memory
3. **Check RunPod logs** for specific errors
4. **Test with smaller images first**

### Monitor Performance:
- Check RunPod dashboard for memory usage
- Monitor response times
- Watch for timeout errors

## Next Steps

1. **Deploy from GitHub** using the steps above
2. **Test with small images first**
3. **Gradually increase image sizes**
4. **Monitor memory usage in RunPod dashboard**

Your repository is now optimized and ready for GitHub deployment to RunPod!