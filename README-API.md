# Face Swap FastAPI Backend

A FastAPI-based backend for face swapping using InsightFace, designed for deployment on RunPod or other cloud platforms.

## Features

- **FastAPI Backend**: RESTful API with automatic documentation
- **Face Swapping**: Uses InsightFace's face detection and swapping models
- **Flexible Response Formats**: Returns either base64-encoded images or direct PNG responses
- **Docker Support**: Ready for containerized deployment
- **GPU Acceleration**: Supports NVIDIA GPU acceleration when available

## API Endpoints

### Health Check
- `GET /` - Basic health check
- `GET /health` - Detailed health status

### Face Swapping
- `POST /swap` - Returns base64-encoded result image
- `POST /swap-image` - Returns direct PNG image
- `POST /runsync` - RunPod serverless endpoint (returns base64-encoded result)

## Request Format

```json
{
  "source_url": "https://example.com/source-image.jpg",
  "target_url": "https://example.com/target-image.jpg",
  "source_index": 1,
  "target_index": 1
}
```

### Parameters
- `source_url`: URL of the source image (contains the face to copy)
- `target_url`: URL of the target image (contains the face to replace)  
- `source_index`: Index of face in source image (1-based, leftmost = 1)
- `target_index`: Index of face in target image (1-based, leftmost = 1)

## Response Formats

### `/swap` endpoint response:
```json
{
  "success": true,
  "image_base64": "iVBORw0KGgoAAAANSUhEUgAA...",
  "message": "Face swap completed successfully"
}
```

### `/swap-image` endpoint:
Returns the PNG image directly with `Content-Type: image/png`

### `/runsync` endpoint (RunPod Serverless):
**Request format:**
```json
{
  "input": {
    "source_url": "https://example.com/source-image.jpg",
    "target_url": "https://example.com/target-image.jpg",
    "source_index": 1,
    "target_index": 1
  }
}
```

**Response format:**
```json
{
  "output": {
    "success": true,
    "image_base64": "iVBORw0KGgoAAAANSUhEUgAA...",
    "message": "Face swap completed successfully"
  }
}
```

**Error response:**
```json
{
  "output": {
    "success": false,
    "message": "Error description here"
  }
}
```

## Quick Start

### Local Development

1. **Install dependencies:**
```bash
pip install -r requirements-api.txt
```

2. **Run the API:**
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

3. **Access the API:**
- API: http://localhost:8000
- Documentation: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc

### Docker Deployment

1. **Build the image:**
```bash
docker build -t face-swap-api .
```

2. **Run the container:**
```bash
docker run -p 8000:8000 face-swap-api
```

3. **With GPU support (if available):**
```bash
docker run --gpus all -p 8000:8000 face-swap-api
```

### Docker Compose

```bash
docker-compose up --build
```

## RunPod Deployment

### Standard RunPod Deployment

#### Method 1: Using Docker Image

1. Build and push your Docker image to a registry (Docker Hub, etc.)
2. Create a new RunPod deployment using your image
3. Set the exposed port to 8000
4. Configure environment variables if needed

#### Method 2: Using RunPod Template

Create a RunPod template with:
- **Base Image**: `nvidia/cuda:11.8-runtime-ubuntu22.04`
- **Startup Script**:
```bash
apt-get update && apt-get install -y python3 python3-pip git
git clone <your-repo-url>
cd <repo-name>
pip install -r requirements-api.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

### RunPod Serverless Deployment

For serverless deployment, use the `/runsync` endpoint which follows RunPod's serverless contract:

#### 1. Create Serverless Endpoint
1. Go to RunPod Serverless dashboard
2. Create a new endpoint
3. Use your Docker image or build from source
4. Set the container port to 8000
5. Configure GPU and memory requirements

#### 2. Endpoint Configuration
- **Container Image**: Your face-swap API Docker image
- **Container Port**: 8000
- **GPU**: Recommended (RTX 3090, RTX 4090, or A100)
- **Memory**: Minimum 8GB RAM
- **Storage**: 10GB+ for models

#### 3. Usage from Your Webapp
```javascript
// Example JavaScript code for calling the serverless endpoint
const response = await fetch('https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/runsync', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer YOUR_API_KEY'
  },
  body: JSON.stringify({
    input: {
      source_url: 'https://example.com/source-face.jpg',
      target_url: 'https://example.com/target-image.jpg',
      source_index: 1,
      target_index: 1
    }
  })
});

const result = await response.json();
if (result.output.success) {
  // Use result.output.image_base64 for the swapped image
  const imageData = `data:image/png;base64,${result.output.image_base64}`;
  // Display or process the image
} else {
  console.error('Face swap failed:', result.output.message);
}
```

#### 4. Python Example
```python
import requests

# Call RunPod serverless endpoint
response = requests.post(
    'https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/runsync',
    headers={
        'Content-Type': 'application/json',
        'Authorization': 'Bearer YOUR_API_KEY'
    },
    json={
        'input': {
            'source_url': 'https://example.com/source-face.jpg',
            'target_url': 'https://example.com/target-image.jpg',
            'source_index': 1,
            'target_index': 1
        }
    }
)

result = response.json()
if result['output']['success']:
    image_base64 = result['output']['image_base64']
    # Process the base64 image data
else:
    print(f"Error: {result['output']['message']}")
```

#### 5. Serverless Benefits
- **Auto-scaling**: Automatically scales based on demand
- **Cost-effective**: Pay only for actual usage
- **GPU acceleration**: Access to high-end GPUs
- **Global deployment**: Low latency worldwide
- **No server management**: Fully managed infrastructure

## Testing

Use the provided test script:

```bash
python test_api.py
```

Or test manually with curl:

```bash
# Health check
curl http://localhost:8000/health

# Face swap (replace URLs with actual image URLs)
curl -X POST "http://localhost:8000/swap" \
  -H "Content-Type: application/json" \
  -d '{
    "source_url": "https://example.com/source.jpg",
    "target_url": "https://example.com/target.jpg",
    "source_index": 1,
    "target_index": 1
  }'
```

## Configuration

### Environment Variables
- `PORT`: API port (default: 8000)
- `HOST`: API host (default: 0.0.0.0)
- `WORKERS`: Number of worker processes (default: 1)

### Model Files
- The `inswapper_128.onnx` file must be present in the application directory
- InsightFace models will be automatically downloaded on first run

## Performance Notes

- **GPU Acceleration**: The API will automatically use GPU if available
- **Memory Usage**: Face detection and swapping are memory-intensive operations
- **Concurrency**: Limited to 1 worker by default due to model loading overhead
- **Model Loading**: Models are loaded once at startup for better performance

## Troubleshooting

### Common Issues

1. **Model Download Errors**: Ensure internet connectivity for automatic model downloads
2. **GPU Issues**: Verify NVIDIA Docker runtime is properly configured
3. **Memory Errors**: Reduce image resolution or increase container memory
4. **Port Conflicts**: Change the port mapping if 8000 is already in use

### Logs
Check container logs for detailed error information:
```bash
docker logs <container-id>
```

## Requirements

- Python 3.8+
- NVIDIA GPU (optional, for acceleration)
- At least 4GB RAM
- Internet connection (for model downloads)

## License

Based on the original InsightFace implementation. Please refer to the InsightFace license for usage terms.
