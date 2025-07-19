#!/usr/bin/env python3
"""
Debug script to test RunPod face swap API locally before deployment
"""
import requests
import json
import base64
from PIL import Image
import io

def test_runpod_local():
    """Test the local RunPod endpoint"""
    
    # Test with small example images first
    payload = {
        "input": {
            "source_url": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400",  # Small test image
            "target_url": "https://images.unsplash.com/photo-1494790108755-2616b612b786?w=400",  # Small test image
            "source_index": 1,
            "target_index": 1
        }
    }
    
    try:
        print("Testing local RunPod endpoint...")
        response = requests.post(
            "http://localhost:8000/runsync",
            json=payload,
            timeout=60
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Success: {result['output']['success']}")
            print(f"Message: {result['output']['message']}")
            
            if result['output']['success'] and result['output'].get('image_base64'):
                # Save result
                image_data = base64.b64decode(result['output']['image_base64'])
                image = Image.open(io.BytesIO(image_data))
                image.save("debug_result.png")
                print("✓ Result saved as 'debug_result.png'")
            else:
                print("✗ No image data returned")
        else:
            print(f"✗ Error: {response.text}")
            
    except Exception as e:
        print(f"✗ Request failed: {e}")

def test_memory_usage():
    """Test memory usage during face swap"""
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    
    print(f"Initial memory usage: {process.memory_info().rss / 1024 / 1024:.2f} MB")
    
    # Test the endpoint
    test_runpod_local()
    
    print(f"Final memory usage: {process.memory_info().rss / 1024 / 1024:.2f} MB")

if __name__ == "__main__":
    print("=== RunPod Debug Script ===")
    test_memory_usage()