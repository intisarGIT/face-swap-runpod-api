#!/usr/bin/env python3
"""
Test script to verify model loading works correctly
"""
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_model_paths():
    """Test if we can find the model files"""
    model_paths = ['inswapper_128.fp16.onnx', 'inswapper_128.onnx']
    
    for model_path in model_paths:
        logger.info(f"\n=== Testing model: {model_path} ===")
        
        # Check multiple possible locations
        possible_paths = [
            model_path,  # Current directory
            os.path.abspath(model_path),  # Absolute path in current directory
            os.path.expanduser(f"~/.insightface/models/{model_path}"),  # InsightFace cache
            os.path.expanduser(f"/root/.insightface/models/{model_path}"),  # Docker root cache
        ]
        
        found = False
        for path in possible_paths:
            logger.info(f"Checking: {path}")
            if os.path.exists(path):
                file_size = os.path.getsize(path)
                logger.info(f"✅ FOUND at: {path}")
                logger.info(f"   File size: {file_size:,} bytes ({file_size / (1024*1024):.2f} MB)")
                found = True
                break
            else:
                logger.info(f"   ❌ Not found")
        
        if not found:
            logger.warning(f"❌ Model {model_path} not found in any location")
        
        logger.info("")

def test_onnx_validation():
    """Test ONNX model validation"""
    model_path = "inswapper_128.fp16.onnx"
    
    if not os.path.exists(model_path):
        logger.error(f"Model file not found: {model_path}")
        return False
    
    try:
        logger.info(f"Testing ONNX validation for: {model_path}")
        
        # Try to load with ONNX Runtime (basic validation)
        import onnxruntime as ort
        session = ort.InferenceSession(model_path, providers=['CPUExecutionProvider'])
        logger.info("✅ ONNX model validation passed")
        
        # Get model info
        inputs = session.get_inputs()
        outputs = session.get_outputs()
        
        logger.info(f"Model inputs: {len(inputs)}")
        for i, inp in enumerate(inputs):
            logger.info(f"  Input {i}: {inp.name} - {inp.shape} - {inp.type}")
        
        logger.info(f"Model outputs: {len(outputs)}")
        for i, out in enumerate(outputs):
            logger.info(f"  Output {i}: {out.name} - {out.shape} - {out.type}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ ONNX model validation failed: {e}")
        return False

if __name__ == "__main__":
    logger.info("=== Model Loading Test ===")
    
    # Test 1: Check if model files can be found
    test_model_paths()
    
    # Test 2: Validate ONNX model
    test_onnx_validation()
    
    logger.info("=== Test Complete ===")