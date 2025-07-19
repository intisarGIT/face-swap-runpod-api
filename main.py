import io
import base64
import logging
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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure InsightFace version compatibility
assert insightface.__version__ >= '0.7'

app = FastAPI(
    title="Face Swap API",
    description="FastAPI backend for face swapping using InsightFace with RunPod serverless support",
    version="1.0.0"
)

# Global variables for the face analysis app and swapper model
face_analysis_app = None
swapper_model = None

def prepare_app():
    """Initialize the face analysis app and swapper model."""
    global face_analysis_app, swapper_model
    
    logger.info("Initializing FaceAnalysis app...")
    face_analysis_app = FaceAnalysis(name='buffalo_l')
    face_analysis_app.prepare(ctx_id=0, det_size=(640, 640))
    
    logger.info("Loading face swapper model...")
    swapper_model = insightface.model_zoo.get_model('inswapper_128.onnx', download=True, download_zip=True)
    
    logger.info("Face swap models initialized successfully!")
    return face_analysis_app, swapper_model

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

def download_image(url: str) -> np.ndarray:
    """Download an image from URL and convert to numpy array."""
    try:
        logger.info(f"Downloading image from: {url}")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Convert to PIL Image
        image = Image.open(io.BytesIO(response.content))
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Convert to numpy array
        image_array = np.array(image)
        logger.info(f"Image downloaded successfully. Shape: {image_array.shape}")
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
        
        # Convert to base64
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
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
    prepare_app()

@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "Face Swap API is running", "status": "healthy"}

@app.get("/health")
async def health_check():
    """Detailed health check."""
    global face_analysis_app, swapper_model
    
    is_healthy = face_analysis_app is not None and swapper_model is not None
    
    return {
        "status": "healthy" if is_healthy else "unhealthy",
        "face_analysis_ready": face_analysis_app is not None,
        "swapper_model_ready": swapper_model is not None
    }

@app.post("/swap", response_model=SwapResponse)
async def swap_faces(request: SwapRequest):
    """
    Swap faces between source and target images.
    
    Args:
        source_url: URL of the source image (contains the face to copy)
        target_url: URL of the target image (contains the face to replace)
        source_index: Index of face in source image (1-based, leftmost = 1)
        target_index: Index of face in target image (1-based, leftmost = 1)
    
    Returns:
        Base64-encoded PNG image with the face swap applied
    """
    try:
        # Use shared face swap logic
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

@app.post("/swap-image", response_class=Response)
async def swap_faces_image(request: SwapRequest):
    """
    Swap faces and return the result as a PNG image.
    
    Alternative endpoint that returns the image directly instead of base64.
    """
    global face_analysis_app, swapper_model
    
    if face_analysis_app is None or swapper_model is None:
        raise HTTPException(status_code=500, detail="Models not initialized")
    
    try:
        logger.info(f"Processing face swap request (image response): source_index={request.source_index}, target_index={request.target_index}")
        
        # Download images
        source_image = download_image(request.source_url)
        target_image = download_image(request.target_url)
        
        # Detect faces in both images
        source_faces = sort_faces(face_analysis_app.get(source_image))
        target_faces = sort_faces(face_analysis_app.get(target_image))
        
        # Get specific faces
        source_face = get_face(source_faces, request.source_index)
        target_face = get_face(target_faces, request.target_index)
        
        # Perform face swap
        result_image = swapper_model.get(target_image, target_face, source_face, paste_back=True)
        
        # Convert to PNG bytes
        image = Image.fromarray(result_image.astype(np.uint8))
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        
        return Response(content=buffer.getvalue(), media_type="image/png")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during face swap: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Face swap failed: {str(e)}")

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
    
    # Download images
    source_image = download_image(source_url)
    target_image = download_image(target_url)
    
    # Detect faces in both images
    logger.info("Detecting faces in source image...")
    source_faces = sort_faces(face_analysis_app.get(source_image))
    
    logger.info("Detecting faces in target image...")
    target_faces = sort_faces(face_analysis_app.get(target_image))
    
    logger.info(f"Found {len(source_faces)} faces in source image, {len(target_faces)} faces in target image")
    
    # Get specific faces
    source_face = get_face(source_faces, source_index)
    target_face = get_face(target_faces, target_index)
    
    # Perform face swap
    logger.info("Performing face swap...")
    result_image = swapper_model.get(target_image, target_face, source_face, paste_back=True)
    
    # Convert result to base64
    result_base64 = image_to_base64(result_image)
    
    logger.info("Face swap completed successfully!")
    return result_base64

@app.post("/runsync", response_model=RunPodResponse)
async def runsync_face_swap(request: RunPodRequest):
    """
    RunPod serverless endpoint for face swapping.
    
    This endpoint follows the RunPod serverless contract:
    - Accepts input in the format: {"input": {"source_url": "...", "target_url": "...", "source_index": 1, "target_index": 1}}
    - Returns output in the format: {"output": {"success": true, "image_base64": "...", "message": "..."}}
    
    Args:
        request: RunPod request containing input parameters
    
    Returns:
        RunPod response with success status, base64 image, and message
    """
    try:
        logger.info("Processing RunPod /runsync face swap request")
        
        # Extract input parameters
        input_data = request.input
        
        # Perform face swap using shared logic
        result_base64 = await perform_face_swap_logic(
            source_url=input_data.source_url,
            target_url=input_data.target_url,
            source_index=input_data.source_index,
            target_index=input_data.target_index
        )
        
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
