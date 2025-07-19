# RunPod Serverless Face Swap Debugging Guide

## Issue Analysis: Exit Code 3

**Exit code 3** in RunPod typically indicates:
1. **Memory exhaustion** (most common)
2. **Model loading failure**
3. **Dependency issues**
4. **Container startup problems**

## Common Causes & Solutions

### 1. Memory Issues (Most Likely Cause)

**Problem**: InsightFace models require significant memory:
- `buffalo_l` face analysis: ~200MB
- `inswapper_128.onnx`: ~128MB
- Face processing: 500MB-2GB depending on image size

**Solutions**:
```yaml
# In your RunPod serverless configuration
memory: 8192  # Minimum 8GB RAM
gpu_memory: 4096  # Minimum 4GB GPU memory
```

### 2. Model Loading Optimization

**Current Issue**: Models load on every request (expensive)

**Solution**: Implement model caching in your main.py:

```python
# The new `main_fixed.py` script handles all of this automatically.
# It includes model caching, auto-recovery, and FP16 support.
# No manual changes to your script are needed.
```

### 3. Image Size Validation

**Problem**: Large images cause memory issues

**Solution**: Add image validation:

```python
def validate_image_size(image_array):
    """Validate and resize image if too large"""
    height, width = image_array.shape[:2]
    max_dimension = 1024  # Max width or height
    
    if max(height, width) > max_dimension:
        scale = max_dimension / max(height, width)
        new_height = int(height * scale)
        new_width = int(width * scale)
        
        from skimage.transform import resize
        image_array = resize(
            image_array, 
            (new_height, new_width), 
            anti_aliasing=True,
            preserve_range=True
        ).astype(np.uint8)
        
        logging.info(f"Resized image from {width}x{height} to {new_width}x{new_height}")
    
    return image_array
```

### 4. RunPod Deployment Configuration

**Correct RunPod serverless setup**:

```yaml
# runpod-config.yaml
name: "face-swap-api"
image: "your-docker-image:latest"
gpu: "RTX3090"  # or RTX4090, A100
memory: 8192    # 8GB minimum
gpu_memory: 4096 # 4GB GPU memory
ports:
  - 8000
env:
  - PYTHONPATH=/app
  - CUDA_VISIBLE_DEVICES=0
startup_timeout: 300  # 5 minutes for model loading
```

### 5. Dockerfile Optimization

**Updated Dockerfile**:

```dockerfile
# Use Ubuntu base image
FROM ubuntu:20.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    build-essential \
    cmake \
    libopencv-dev \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgl1-mesa-glx \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create working directory
WORKDIR /app

# Copy requirements first for better Docker layer caching
COPY requirements-api.txt .

# Install Python dependencies
RUN pip3 install --no-cache-dir --upgrade pip setuptools wheel
RUN pip3 install --no-cache-dir --timeout 1000 --retries 5 -r requirements-api.txt

# Copy the application code
COPY main_fixed.py .

# Expose the port
EXPOSE 8000

# Health check (the new healthcheck is more robust)
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application with the new fixed script
CMD ["uvicorn", "main_fixed:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
```

## Debugging Steps

### Step 1: Test Locally First

```bash
# 1. Test your API locally
python runpod_debug.py

# 2. Check memory usage
docker stats

# 3. Test with small images first
```

### Step 2: Check RunPod Logs

```bash
# In RunPod dashboard, check:
# 1. Container logs
# 2. System metrics
# 3. GPU utilization
```

### Step 3: Gradual Deployment

1. **Start with minimal configuration**
2. **Test with small images**
3. **Gradually increase complexity**

## Updated Route.ts Integration

Replace your current `runPodFaceSwap` function with this improved version:

```typescript
async function runPodFaceSwap(
  targetImageUrl: string,
  sourceImageUrl: string,
  targetFaceIndex: number
): Promise<string> {
  
  if (!RUNPOD_API_KEY) {
    throw new Error("RUNPOD_API_KEY not configured");
  }
  
  // Your actual RunPod endpoint URL should be:
  // https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/runsync
  const RUNPOD_ENDPOINT = process.env.RUNPOD_ENDPOINT || "https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/runsync";
  
  console.log(`[RunPod] Starting face swap - target face index: ${targetFaceIndex}`);
  
  const requestData = {
    input: {
      source_url: sourceImageUrl,
      target_url: targetImageUrl,
      source_index: 1,
      target_index: targetFaceIndex
    }
  };
  
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 120000); // 2 minute timeout
    
    const response = await fetch(RUNPOD_ENDPOINT, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${RUNPOD_API_KEY}`,
      },
      body: JSON.stringify(requestData),
      signal: controller.signal
    });
    
    clearTimeout(timeoutId);
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error(`[RunPod] API error (${response.status}):`, errorText);
      
      if (response.status === 503) {
        throw new Error("RunPod service temporarily unavailable");
      } else if (response.status === 413) {
        throw new Error("Images too large for processing");
      }
      
      throw new Error(`RunPod API error: ${response.status} - ${errorText}`);
    }
    
    const result = await response.json();
    
    if (!result.output?.success) {
      const errorMessage = result.output?.message || "Unknown error";
      console.error("[RunPod] Face swap failed:", errorMessage);
      
      if (errorMessage.includes("memory") || errorMessage.includes("OOM")) {
        throw new Error("RunPod worker out of memory - try smaller images");
      }
      
      throw new Error(`RunPod face swap failed: ${errorMessage}`);
    }
    
    if (!result.output.image_base64) {
      throw new Error("RunPod API did not return an image");
    }
    
    console.log("[RunPod] Face swap completed successfully");
    return `data:image/png;base64,${result.output.image_base64}`;
    
  } catch (error: any) {
    if (error.name === 'AbortError') {
      throw new Error("RunPod request timeout");
    }
    throw error;
  }
}
```

## Environment Variables

Make sure these are set in your webapp:

```env
RUNPOD_API_KEY=your_runpod_api_key
RUNPOD_ENDPOINT=https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/runsync
```

## Next Steps

1. **Update your RunPod deployment** with higher memory allocation
2. **Pre-load models** in your Docker image
3. **Add image size validation**
4. **Test with the improved error handling**
5. **Monitor RunPod logs** for specific error messages

The exit code 3 is most likely due to insufficient memory allocation in your RunPod serverless configuration.