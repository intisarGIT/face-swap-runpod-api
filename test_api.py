import requests
import json
import base64
from PIL import Image
import io

# API endpoint
API_BASE_URL = "http://localhost:8000"

def test_health_check():
    """Test the health check endpoint."""
    print("Testing health check...")
    response = requests.get(f"{API_BASE_URL}/health")
    print(f"Health check status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_face_swap_base64():
    """Test face swap with base64 response."""
    print("Testing face swap (base64 response)...")
    
    # Example payload
    payload = {
        "source_url": "https://example.com/source-image.jpg",
        "target_url": "https://example.com/target-image.jpg",
        "source_index": 1,
        "target_index": 1
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/swap", json=payload)
        
        if response.status_code == 200:
            result = response.json()
            print(f"Success: {result['success']}")
            print(f"Message: {result['message']}")
            
            # Save the result image
            image_data = base64.b64decode(result['image_base64'])
            image = Image.open(io.BytesIO(image_data))
            image.save("result_base64.png")
            print("Result saved as 'result_base64.png'")
        else:
            print(f"Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    print()

def test_face_swap_image():
    """Test face swap with direct image response."""
    print("Testing face swap (direct image response)...")
    
    # Example payload
    payload = {
        "source_url": "https://example.com/source-image.jpg",
        "target_url": "https://example.com/target-image.jpg",
        "source_index": 1,
        "target_index": 1
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/swap-image", json=payload)
        
        if response.status_code == 200:
            # Save the image directly
            with open("result_image.png", "wb") as f:
                f.write(response.content)
            print("Result saved as 'result_image.png'")
        else:
            print(f"Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    print()

def test_runsync_face_swap():
    """Test RunPod serverless /runsync endpoint."""
    print("Testing RunPod /runsync endpoint...")
    
    # RunPod format payload
    payload = {
        "input": {
            "source_url": "https://example.com/source-image.jpg",
            "target_url": "https://example.com/target-image.jpg",
            "source_index": 1,
            "target_index": 1
        }
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/runsync", json=payload)
        
        if response.status_code == 200:
            result = response.json()
            print(f"Success: {result['output']['success']}")
            print(f"Message: {result['output']['message']}")
            
            if result['output']['success'] and result['output'].get('image_base64'):
                # Save the result image
                image_data = base64.b64decode(result['output']['image_base64'])
                image = Image.open(io.BytesIO(image_data))
                image.save("result_runsync.png")
                print("Result saved as 'result_runsync.png'")
            else:
                print("No image data in successful response")
        else:
            print(f"Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    print()

def test_runsync_error_handling():
    """Test RunPod /runsync endpoint error handling."""
    print("Testing RunPod /runsync error handling...")
    
    # Invalid payload (missing required fields)
    payload = {
        "input": {
            "source_url": "invalid-url",
            "target_url": "invalid-url",
            "source_index": 1,
            "target_index": 1
        }
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/runsync", json=payload)
        
        if response.status_code == 200:
            result = response.json()
            print(f"Success: {result['output']['success']}")
            print(f"Message: {result['output']['message']}")
            
            if not result['output']['success']:
                print("✓ Error handling working correctly")
            else:
                print("⚠ Expected error but got success")
        else:
            print(f"HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    print()

def main():
    """Run all tests."""
    print("=== Face Swap API Test Script ===\n")
    
    # Test health check first
    test_health_check()
    
    # Note: The face swap tests will fail without valid image URLs
    # Replace the URLs in the test functions with actual image URLs to test
    print("Note: Face swap tests require valid image URLs to work.")
    print("Update the 'source_url' and 'target_url' in the test functions with real image URLs.")
    
    # Uncomment these lines to run face swap tests with valid URLs:
    # test_face_swap_base64()
    # test_face_swap_image()

if __name__ == "__main__":
    main()
