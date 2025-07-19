#!/usr/bin/env python3
"""
RunPod serverless handler for Face Swap API
This handler integrates with RunPod's serverless architecture to prevent worker exit code 3 errors
"""

import runpod
import asyncio
import logging
import sys
import os

# Add the current directory to Python path
sys.path.append('/app')

# Import our main application
from main_fixed import app, perform_face_swap_logic

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def handler(event):
    """
    RunPod serverless handler function
    
    Args:
        event: RunPod event containing input data
        
    Returns:
        dict: Response with success status and result
    """
    try:
        logger.info("RunPod handler started")
        logger.info(f"Received event: {event}")
        
        # Extract input from event
        input_data = event.get('input', {})
        
        # Validate required parameters
        required_params = ['source_url', 'target_url']
        for param in required_params:
            if param not in input_data:
                return {
                    "error": f"Missing required parameter: {param}",
                    "success": False
                }
        
        # Extract parameters with defaults
        source_url = input_data['source_url']
        target_url = input_data['target_url']
        source_index = input_data.get('source_index', 1)
        target_index = input_data.get('target_index', 1)
        
        logger.info(f"Processing face swap: {source_url} -> {target_url}")
        
        # Run the async face swap logic in a synchronous context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result_base64 = loop.run_until_complete(
                perform_face_swap_logic(
                    source_url=source_url,
                    target_url=target_url,
                    source_index=source_index,
                    target_index=target_index
                )
            )
            
            logger.info("Face swap completed successfully")
            
            return {
                "success": True,
                "image_base64": result_base64,
                "message": "Face swap completed successfully"
            }
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Handler error: {str(e)}")
        return {
            "error": str(e),
            "success": False,
            "message": f"Face swap failed: {str(e)}"
        }

def initialize():
    """
    Initialize the application on worker startup
    This prevents cold start issues and worker exit errors
    """
    try:
        logger.info("Initializing RunPod worker...")
        
        # Import and initialize the models
        from main_fixed import prepare_app
        prepare_app()
        
        logger.info("RunPod worker initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Initialization failed: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("Starting RunPod serverless worker...")
    
    # Initialize the application
    if not initialize():
        logger.error("Failed to initialize worker, exiting...")
        sys.exit(1)
    
    # Start the RunPod serverless worker
    runpod.serverless.start({
        "handler": handler,
        "return_aggregate_stream": True
    })