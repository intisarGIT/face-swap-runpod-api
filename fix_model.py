#!/usr/bin/env python3
"""
Script to fix the corrupted ONNX model issue by removing and re-downloading the model
"""
import os
import shutil
import logging
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_corrupted_model():
    """Fix the corrupted inswapper_128.onnx model"""
    
    model_path = "inswapper_128.onnx"
    backup_path = "inswapper_128.onnx.backup"
    
    logger.info("🔧 Starting model corruption fix...")
    
    # Step 1: Check if model exists
    if os.path.exists(model_path):
        file_size = os.path.getsize(model_path)
        logger.info(f"📁 Found existing model: {file_size:,} bytes ({file_size / (1024*1024):.2f} MB)")
        
        # Step 2: Create backup
        try:
            logger.info("💾 Creating backup of corrupted model...")
            shutil.copy2(model_path, backup_path)
            logger.info(f"✅ Backup created: {backup_path}")
        except Exception as e:
            logger.warning(f"⚠️ Could not create backup: {e}")
        
        # Step 3: Remove corrupted model
        try:
            logger.info("🗑️ Removing corrupted model...")
            os.remove(model_path)
            logger.info("✅ Corrupted model removed")
        except Exception as e:
            logger.error(f"❌ Failed to remove corrupted model: {e}")
            return False
    else:
        logger.info("📁 No existing model found")
    
    # Step 4: Clear InsightFace cache
    try:
        logger.info("🧹 Clearing InsightFace model cache...")
        
        # Common InsightFace cache locations
        cache_paths = [
            os.path.expanduser("~/.insightface"),
            os.path.expanduser("~/.cache/insightface"),
            "/root/.insightface",  # Docker/Linux
            "C:/Users/*/AppData/Local/insightface",  # Windows
        ]
        
        for cache_path in cache_paths:
            if os.path.exists(cache_path):
                logger.info(f"🗑️ Removing cache: {cache_path}")
                shutil.rmtree(cache_path, ignore_errors=True)
        
        logger.info("✅ Cache cleared")
    except Exception as e:
        logger.warning(f"⚠️ Could not clear cache completely: {e}")
    
    logger.info("🎉 Model corruption fix completed!")
    logger.info("📝 Next steps:")
    logger.info("   1. Restart your application")
    logger.info("   2. The model will be automatically re-downloaded")
    logger.info("   3. Monitor the logs for successful model loading")
    
    return True

def verify_python_environment():
    """Verify that we have the necessary Python environment"""
    logger.info("🔍 Verifying Python environment...")
    
    try:
        import insightface
        logger.info(f"✅ InsightFace version: {insightface.__version__}")
    except ImportError:
        logger.error("❌ InsightFace not installed")
        return False
    
    try:
        import onnxruntime
        logger.info(f"✅ ONNX Runtime available")
    except ImportError:
        logger.warning("⚠️ ONNX Runtime not available for validation")
    
    return True

if __name__ == "__main__":
    logger.info("🚀 Face Swap Model Fix Tool")
    logger.info("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists("main.py") and not os.path.exists("app.py"):
        logger.error("❌ Please run this script from the face-swap project directory")
        sys.exit(1)
    
    # Verify environment
    if not verify_python_environment():
        logger.error("❌ Python environment verification failed")
        logger.info("💡 Make sure you have activated the correct conda/virtual environment")
        sys.exit(1)
    
    # Fix the model
    if fix_corrupted_model():
        logger.info("✅ Fix completed successfully!")
        sys.exit(0)
    else:
        logger.error("❌ Fix failed!")
        sys.exit(1)