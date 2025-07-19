#!/usr/bin/env python3
"""
Verification script to test the model loading fix
"""
import os
import sys
import logging

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_model_discovery():
    """Test if the model files can be discovered"""
    logger.info("=== Testing Model Discovery ===")
    
    model_paths = ['inswapper_128.fp16.onnx', 'inswapper_128.onnx']
    
    for model_path in model_paths:
        logger.info(f"\nTesting model: {model_path}")
        
        # Check multiple possible locations (same logic as in main_fixed.py)
        possible_paths = [
            model_path,  # Current directory
            os.path.abspath(model_path),  # Absolute path in current directory
            os.path.expanduser(f"~/.insightface/models/{model_path}"),  # InsightFace cache
            os.path.expanduser(f"/root/.insightface/models/{model_path}"),  # Docker root cache
        ]
        
        found = False
        for path in possible_paths:
            logger.info(f"  Checking: {path}")
            if os.path.exists(path):
                file_size = os.path.getsize(path)
                logger.info(f"  ✅ FOUND at: {path}")
                logger.info(f"     File size: {file_size:,} bytes ({file_size / (1024*1024):.2f} MB)")
                found = True
                break
            else:
                logger.info(f"     ❌ Not found")
        
        if not found:
            logger.warning(f"❌ Model {model_path} not found in any location")
        else:
            logger.info(f"✅ Model {model_path} discovered successfully")

def test_model_loading_logic():
    """Test the model loading logic from main_fixed.py"""
    logger.info("\n=== Testing Model Loading Logic ===")
    
    try:
        # Import the function from main_fixed.py
        from main_fixed import load_swapper_model_with_recovery
        
        # Test loading the FP16 model
        logger.info("Testing FP16 model loading...")
        try:
            swapper_model = load_swapper_model_with_recovery('inswapper_128.fp16.onnx', max_retries=1)
            logger.info("✅ FP16 model loaded successfully!")
            return True
        except Exception as e:
            logger.warning(f"FP16 model loading failed: {e}")
            
            # Test loading the FP32 model as fallback
            logger.info("Testing FP32 model loading as fallback...")
            try:
                swapper_model = load_swapper_model_with_recovery('inswapper_128.onnx', max_retries=1)
                logger.info("✅ FP32 model loaded successfully!")
                return True
            except Exception as e2:
                logger.error(f"FP32 model loading also failed: {e2}")
                return False
                
    except ImportError as e:
        logger.error(f"Failed to import from main_fixed.py: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during model loading test: {e}")
        return False

def main():
    """Main verification function"""
    logger.info("Starting model loading verification...")
    
    # Test 1: Model discovery
    test_model_discovery()
    
    # Test 2: Model loading logic (only if dependencies are available)
    try:
        import insightface
        import onnxruntime
        success = test_model_loading_logic()
        
        if success:
            logger.info("\n🎉 ALL TESTS PASSED! The model loading fix should work correctly.")
        else:
            logger.error("\n❌ Model loading tests failed. Check the error messages above.")
            
    except ImportError as e:
        logger.warning(f"\n⚠️  Cannot test model loading logic due to missing dependencies: {e}")
        logger.info("This is expected if running outside the container environment.")
        logger.info("The model discovery test above shows if the files can be found.")
    
    logger.info("\nVerification complete.")

if __name__ == "__main__":
    main()