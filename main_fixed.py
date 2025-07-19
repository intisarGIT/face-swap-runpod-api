import io
import base64
import logging
import gc
import os
import shutil
from typing import Union
import requests
from PIL import Image
import numpy as np
import insightface
from insightface.app import FaceAnalysis
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional
from functools import lru_cache
import psutil

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure InsightFace version compatibility
assert insightface.__version__ >= '0.7'

app = FastAPI(
    title="Face Swap API - Fixed with Auto-Recovery",
    description="FastAPI backend for face swapping using InsightFace with automatic model corruption recovery",
    version="1.2.0"
)

# Global variables for the face analysis app and swapper model
face_analysis_app = None
swapper_model = None

def log_memory_usage(stage: str):
    """Log current memory usage"""
    try:
        process = psutil.Process(os.getpid())
        memory_mb = process.memory_info().rss / 1024 / 1024
        logger.info(f"[{stage}] Memory usage: {memory_mb:.2f} MB")
    except:
        logger.info(f"[{stage}] Memory usage: Unable to measure")

def validate_onnx_model(model_path: str) -> bool:
    """Validate ONNX model file integrity"""
    try:
        if not os.path.exists(model_path):
            logger.warning(f"Model file does not exist: {model_path}")
            return False
        
        file_size = os.path.getsize(model_path)
        logger.info(f"Model file size: {file_size:,} bytes ({file_size / (1024*1024):.2f} MB)")
        
        # Try to load with ONNX Runtime (basic validation)
        import onnxruntime as ort
        session = ort.InferenceSession(model_path, providers=['CPUExecutionProvider'])
        logger.info("✅ ONNX model validation passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ ONNX model validation failed: {e}")
        return False

def fix_corrupted_model(model_path: str) -> bool:
    """Fix corrupted model by removing it and clearing cache"""
    try:
        logger.info("🔧 Attempting to fix corrupted model...")
        
        # Create backup if file exists
        if os.path.exists(model_path):
            backup_path = f"{model_path}.backup"
            try:
                shutil.copy2(model_path, backup_path)
                logger.info(f"💾 Backup created: {backup_path}")
            except Exception as e:
                logger.warning(f"Could not create backup: {e}")
            
            # Remove corrupted model
            os.remove(model_path)
            logger.info("🗑️ Corrupted model removed")
        
        # Clear InsightFace cache (but don't remove the entire cache, just model files)
        cache_paths = [
            os.path.expanduser("~/.insightface/models"),
            os.path.expanduser("~/.cache/insightface"),
            "/root/.insightface/models",
        ]
        
        for cache_path in cache_paths:
            if os.path.exists(cache_path):
                # Only remove model files, not the entire cache
                model_files = [f for f in os.listdir(cache_path) if f.endswith('.onnx')]
                for model_file in model_files:
                    model_file_path = os.path.join(cache_path, model_file)
                    try:
                        os.remove(model_file_path)
                        logger.info(f"🧹 Removed cached model: {model_file_path}")
                    except Exception as e:
                        logger.warning(f"Could not remove {model_file_path}: {e}")
        
        logger.info("✅ Model corruption fix completed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to fix corrupted model: {e}")
        return False

def load_swapper_model_with_recovery(model_path: str, max_retries: int = 3):
    """Load swapper model with automatic corruption recovery"""
    swapper_model = None
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Loading swapper model (attempt {attempt + 1}/{max_retries})...")
            
            # Check multiple possible locations for the model
            possible_paths = [
                model_path,  # Current directory
                os.path.abspath(model_path),  # Absolute path in current directory
                os.path.expanduser(f"~/.insightface/models/{model_path}"),  # InsightFace cache
                os.path.expanduser(f"/root/.insightface/models/{model_path}"),  # Docker root cache
            ]
            
            local_model_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    local_model_path = path
                    logger.info(f"Found model at: {local_model_path}")
                    break
            
            if local_model_path is None:
                logger.info(f"Model not found locally at any of these paths: {possible_paths}")
            
            # First, validate the model if it exists
            if local_model_path and os.path.exists(local_model_path):
                if not validate_onnx_model(local_model_path):
                    logger.warning("Model validation failed, attempting to fix...")
                    if not fix_corrupted_model(local_model_path):
                        raise Exception("Failed to fix corrupted model")
                    # After fixing, the model file is gone, so we need to download
                    local_model_path = None
            
            # Load the model
            if local_model_path and os.path.exists(local_model_path):
                # For local files, use the full path directly
                logger.info(f"Loading model from local path: {local_model_path}")
                swapper_model = insightface.model_zoo.get_model(local_model_path, download=False, download_zip=False)
            else:
                # Extract model name without extension for InsightFace download
                model_name = os.path.splitext(model_path)[0]
                logger.info(f"Model not found locally, downloading {model_name}...")
                swapper_model = insightface.model_zoo.get_model(model_name, download=True, download_zip=True)
                # Update local_model_path to the downloaded location
                local_model_path = os.path.expanduser(f"~/.insightface/models/{model_path}")
            
            # Validate that we actually got a model object
            if swapper_model is None:
                raise Exception("Model loading returned None")
            
            logger.info("✅ Swapper model loaded successfully!")
            return swapper_model
            
        except Exception as e:
            logger.error(f"❌ Attempt {attempt + 1} failed: {e}")
            swapper_model = None
            
            if attempt < max_retries - 1:
                logger.info("🔄 Retrying with model fix...")
                if 'local_model_path' in locals() and local_model_path:
                    fix_corrupted_model(local_model_path)
                else:
                    # Try to fix the first possible path
                    fix_corrupted_model(model_path)
            else:
                logger.error("❌ All attempts failed to load swapper model")
                raise Exception(f"Failed to load swapper model after {max_retries} attempts: {e}")
    
    return swapper_model

@lru_cache(maxsize=1)
def get_cached_models():
    """Cache models to avoid reloading on each request"""
    try:
        log_memory_usage("Before model loading")
        
        logger.info("Loading FaceAnalysis model (cached)...")
        face_analysis_app = FaceAnalysis(name='buffalo_l')
        face_analysis_app.prepare(ctx_id=0, det_size=(640, 640))
        
        log_memory_usage("After FaceAnalysis loading")
        
        # Load swapper model with recovery - try FP16 first, then fallback to FP32
        model_paths = ['inswapper_128.fp16.onnx', 'inswapper_128.onnx']
        swapper_model = None
        
        for model_path in model_paths:
            try:
                logger.info(f"Attempting to load model: {model_path}")
                swapper_model = load_swapper_model_with_recovery(model_path)
                logger.info(f"✅ Successfully loaded: {model_path}")
                break
            except Exception as e:
                logger.warning(f"Failed to load {model_path}: {e}")
                continue
        
        if swapper_model is None:
            raise Exception("Failed to load any swapper model variant")
        
        log_memory_usage("After swapper model loading")
        
        logger.info("Models loaded successfully!")
        return face_analysis_app, swapper_model
    except Exception as e:
        logger.error(f"Model loading failed: {e}")
        raise

def prepare_app():
    """Initialize the face analysis app and swapper model."""
    global face_analysis_app, swapper_model
    
    try:
        face_analysis_app, swapper_model = get_cached_models()
        return face_analysis_app, swapper_model
    except Exception as e:
        logger.error(f"Failed to prepare app: {e}")
        raise

def sort_faces(faces):
    """Sort faces by their x-coordinate (left to right)."""
    return sorted(faces, key=lambda x: x.bbox[0])

def get_face(faces, face_id):
    """Get a specific face by its index (1-based)."""
    try:
        if len(faces) < face_id or face_id < 1:
            raise HTTPException(
                status_code=400,
                detail=f"The image includes only {len(faces)} faces, however, you asked for face {face_id}"
            )
        return faces[face_id-1]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

def validate_and_resize_image(image_array: np.ndarray, max_dimension: int = 1024) -> np.ndarray:
    """Validate and resize image if too large to prevent memory issues"""
    height, width = image_array.shape[:2]
    
    if max(height, width) > max_dimension:
        scale = max_dimension / max(height, width)
        new_height = int(height * scale)
        new_width = int(width * scale)
        
        # Use PIL for resizing (more memory efficient than skimage)
        image_pil = Image.fromarray(image_array)
        image_pil = image_pil.resize((new_width, new_height), Image.Resampling.LANCZOS)
        image_array = np.array(image_pil)
        
        logger.info(f"Resized image from {width}x{height} to {new_width}x{new_height}")
    
    return image_array

def download_image(url: str) -> np.ndarray:
    """Download an image from URL and convert to numpy array."""
    try:
        logger.info(f"Downloading image from: {url}")
        
        # Add headers to avoid blocking
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, timeout=30, headers=headers)
        response.raise_for_status()
        
        # Check content length
        content_length = response.headers.get('content-length')
        if content_length:
            size_mb = int(content_length) / (1024 * 1024)
            logger.info(f"Image size: {size_mb:.2f} MB")
            
            if size_mb > 10:  # 10MB limit
                raise HTTPException(status_code=413, detail=f"Image too large: {size_mb:.2f} MB (max 10MB)")
        
        # Convert to PIL Image
        image = Image.open(io.BytesIO(response.content))
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Convert to numpy array and validate size
        image_array = np.array(image)
        image_array = validate_and_resize_image(image_array)
        
        logger.info(f"Image processed successfully. Shape: {image_array.shape}")
        return image_array
        
    except requests.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Failed to download image from {url}: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image from {url}: {str(e)}")

def image_to_base64(image_array: np.ndarray) -> str:
    """Convert numpy array image to base64 string."""
    try:
        # Convert numpy array to PIL Image
        image = Image.fromarray(image_array.astype(np.uint8))
        
        # Convert to base64 with compression
        buffer = io.BytesIO()
        image.save(buffer, format='PNG', optimize=True)
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return image_base64
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error converting image to base64: {str(e)}")

class SwapRequest(BaseModel):
    source_url: str
    target_url: str
    source_index: int = 1
    target_index: int = 1

class SwapResponse(BaseModel):
    success: bool
    image_base64: str
    message: str = "Face swap completed successfully"

# RunPod serverless models
class RunPodInput(BaseModel):
    source_url: str
    target_url: str
    source_index: int = 1
    target_index: int = 1

class RunPodRequest(BaseModel):
    input: RunPodInput

class RunPodOutput(BaseModel):
    success: bool
    image_base64: Optional[str] = None
    message: str

class RunPodResponse(BaseModel):
    output: RunPodOutput

@app.on_event("startup")
async def startup_event():
    """Initialize models on startup."""
    logger.info("Starting up Face Swap API with auto-recovery...")
    log_memory_usage("Startup")
    prepare_app()
    log_memory_usage("After model loading")

@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "Face Swap API is running with auto-recovery", "status": "healthy"}

@app.get("/health")
async def health_check():
    """Detailed health check."""
    global face_analysis_app, swapper_model
    
    is_healthy = face_analysis_app is not None and swapper_model is not None
    
    # Memory info
    process = psutil.Process(os.getpid())
    memory_mb = process.memory_info().rss / 1024 / 1024
    
    # Model validation - check both variants in multiple locations
    model_valid = False
    active_model = None
    model_paths = ['inswapper_128.fp16.onnx', 'inswapper_128.onnx']
    
    for model_path in model_paths:
        # Check multiple possible locations
        possible_paths = [
            model_path,  # Current directory
            os.path.abspath(model_path),  # Absolute path in current directory
            os.path.expanduser(f"~/.insightface/models/{model_path}"),  # InsightFace cache
            os.path.expanduser(f"/root/.insightface/models/{model_path}"),  # Docker root cache
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                if validate_onnx_model(path):
                    model_valid = True
                    active_model = path
                    break
        
        if model_valid:
            break
    
    return {
        "status": "healthy" if is_healthy else "unhealthy",
        "face_analysis_ready": face_analysis_app is not None,
        "swapper_model_ready": swapper_model is not None,
        "model_file_valid": model_valid,
        "active_model": active_model,
        "memory_usage_mb": round(memory_mb, 2),
        "insightface_version": insightface.__version__
    }

@app.post("/fix-model")
async def fix_model_endpoint():
    """Manual endpoint to fix corrupted model"""
    try:
        model_path = 'inswapper_128.onnx'
        success = fix_corrupted_model(model_path)
        
        if success:
            # Clear the cache to force reload
            get_cached_models.cache_clear()
            global face_analysis_app, swapper_model
            face_analysis_app = None
            swapper_model = None
            
            return {"success": True, "message": "Model fix completed. Restart the application to reload models."}
        else:
            return {"success": False, "message": "Model fix failed"}
            
    except Exception as e:
        logger.error(f"Manual model fix failed: {e}")
        return {"success": False, "message": f"Model fix failed: {str(e)}"}

async def perform_face_swap_logic(source_url: str, target_url: str, source_index: int, target_index: int) -> str:
    """
    Core face swap logic that can be reused by different endpoints.
    
    Returns:
        Base64-encoded PNG image with the face swap applied
    """
    global face_analysis_app, swapper_model
    
    if face_analysis_app is None or swapper_model is None:
        raise HTTPException(status_code=500, detail="Models not initialized")
    
    logger.info(f"Processing face swap: source_index={source_index}, target_index={target_index}")
    log_memory_usage("Before face swap")
    
    try:
        # Download images
        source_image = download_image(source_url)
        target_image = download_image(target_url)
        
        log_memory_usage("After image download")
        
        # Detect faces in both images
        logger.info("Detecting faces in source image...")
        source_faces = sort_faces(face_analysis_app.get(source_image))
        
        logger.info("Detecting faces in target image...")
        target_faces = sort_faces(face_analysis_app.get(target_image))
        
        logger.info(f"Found {len(source_faces)} faces in source image, {len(target_faces)} faces in target image")
        log_memory_usage("After face detection")
        
        # Get specific faces
        source_face = get_face(source_faces, source_index)
        target_face = get_face(target_faces, target_index)
        
        # Perform face swap
        logger.info("Performing face swap...")
        result_image = swapper_model.get(target_image, target_face, source_face, paste_back=True)
        
        log_memory_usage("After face swap")
        
        # Convert result to base64
        result_base64 = image_to_base64(result_image)
        
        # Clean up memory
        del source_image, target_image, result_image
        gc.collect()
        
        log_memory_usage("After cleanup")
        logger.info("Face swap completed successfully!")
        return result_base64
        
    except Exception as e:
        # Clean up memory on error
        gc.collect()
        logger.error(f"Face swap failed: {str(e)}")
        raise

@app.post("/swap", response_model=SwapResponse)
async def swap_faces(request: SwapRequest):
    """
    Swap faces between source and target images.
    """
    try:
        result_base64 = await perform_face_swap_logic(
            source_url=request.source_url,
            target_url=request.target_url,
            source_index=request.source_index,
            target_index=request.target_index
        )
        
        return SwapResponse(
            success=True,
            image_base64=result_base64,
            message="Face swap completed successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during face swap: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Face swap failed: {str(e)}")

@app.post("/runsync", response_model=RunPodResponse)
async def runsync_face_swap(request: RunPodRequest):
    """
    RunPod serverless endpoint for face swapping.
    
    This endpoint follows the RunPod serverless contract with enhanced error handling.
    """
    try:
        logger.info("Processing RunPod /runsync face swap request")
        log_memory_usage("RunPod request start")
        
        # Extract input parameters
        input_data = request.input
        
        # Perform face swap using shared logic
        result_base64 = await perform_face_swap_logic(
            source_url=input_data.source_url,
            target_url=input_data.target_url,
            source_index=input_data.source_index,
            target_index=input_data.target_index
        )
        
        log_memory_usage("RunPod request complete")
        
        # Return in RunPod format
        return RunPodResponse(
            output=RunPodOutput(
                success=True,
                image_base64=result_base64,
                message="Face swap completed successfully"
            )
        )
        
    except HTTPException as e:
        logger.error(f"HTTP error in RunPod endpoint: {e.detail}")
        return RunPodResponse(
            output=RunPodOutput(
                success=False,
                message=e.detail
            )
        )
    except Exception as e:
        logger.error(f"Unexpected error in RunPod endpoint: {str(e)}")
        return RunPodResponse(
            output=RunPodOutput(
                success=False,
                message=f"Face swap failed: {str(e)}"
            )
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)