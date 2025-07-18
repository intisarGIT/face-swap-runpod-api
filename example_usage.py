"""
Example usage of the Face Swap API
"""

import requests
import json
import base64
from PIL import Image
import io

# Configuration
API_URL = "http://localhost:8000"  # Change this to your deployed API URL

def example_1_base64_response():
    """Example using local example images and base64 response."""
    
    # For this example, you'll need to upload your example images to a public URL
    # or use a service like imgur, github raw files, etc.
    
    payload = {
        "source_url": "https://raw.githubusercontent.com/your-repo/examples/rihanna.jpg",
        "target_url": "https://raw.githubusercontent.com/your-repo/examples/margaret_thatcher.jpg", 
        "source_index": 1,
        "target_index": 1
    }
    
    print("Sending face swap request...")
    response = requests.post(f"{API_URL}/swap", json=payload)
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Face swap successful!")
        
        # Decode and save the result
        image_data = base64.b64decode(result['image_base64'])
        image = Image.open(io.BytesIO(image_data))
        image.save("face_swap_result.png")
        print("💾 Result saved as 'face_swap_result.png'")
        
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)

def example_2_direct_image():
    """Example using direct image response."""
    
    payload = {
        "source_url": "https://raw.githubusercontent.com/your-repo/examples/game_of_thrones.jpg",
        "target_url": "https://raw.githubusercontent.com/your-repo/examples/game_of_thrones.jpg",
        "source_index": 5,
        "target_index": 4
    }
    
    print("Sending face swap request (direct image)...")
    response = requests.post(f"{API_URL}/swap-image", json=payload)
    
    if response.status_code == 200:
        # Save the image directly
        with open("face_swap_direct.png", "wb") as f:
            f.write(response.content)
        print("✅ Face swap successful!")
        print("💾 Result saved as 'face_swap_direct.png'")
        
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)

def check_api_health():
    """Check if the API is running and healthy."""
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print("✅ API is healthy!")
            print(f"   Status: {health_data['status']}")
            print(f"   Face Analysis Ready: {health_data['face_analysis_ready']}")
            print(f"   Swapper Model Ready: {health_data['swapper_model_ready']}")
            return True
        else:
            print(f"❌ API health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to API: {e}")
        return False

if __name__ == "__main__":
    print("🔄 Face Swap API Example\n")
    
    # Check API health first
    if not check_api_health():
        print("\n⚠️  Make sure the API is running at", API_URL)
        print("   Run: uvicorn main:app --host 0.0.0.0 --port 8000")
        exit(1)
    
    print("\n" + "="*50)
    print("📝 Note: Update the image URLs in this script with actual URLs")
    print("   You can upload your example images to GitHub, Imgur, or any public host")
    print("="*50 + "\n")
    
    # Uncomment these lines when you have valid image URLs:
    # example_1_base64_response()
    # example_2_direct_image()
    
    print("🎉 Example complete!")
