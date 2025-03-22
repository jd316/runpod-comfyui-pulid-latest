import requests
import json
import time
import base64
import os
from PIL import Image
import io

# Your credentials
API_KEY = "rpa_B0G5QQEK5R0WYMB523MC7TC0D2XWRG4SJ2H2UQWT1vt2p8"
ENDPOINT_ID = "v8clglpidxjxas"

# Load the reference image
reference_image_path = r"C:\Users\jdbis\Documents\runpod-fluxpulid-serveless\image (42).png"
with open(reference_image_path, "rb") as f:
    reference_img_base64 = base64.b64encode(f.read()).decode("utf-8")

# Create a simple test payload 
data = {
    "input": {
        "prompt": "woman on a sea beach, photorealistic",
        "face_id_weight": 0.8,
        "seed": 123456,
        "reference_image": reference_img_base64,
        # Add a debug flag to request detailed logs
        "debug_mode": True
    }
}

# Send a synchronous request with retries
url = f"https://api.runpod.ai/v2/{ENDPOINT_ID}/runsync"
    
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

def make_request_with_retries(max_retries=5, initial_delay=10):
    for attempt in range(max_retries):
        try:
            print(f"\nAttempt {attempt + 1}/{max_retries}")
            response = requests.post(url, headers=headers, json=data, timeout=300)
            print(f"Response status code: {response.status_code}")
            
            # If we get a 502, wait and retry
            if response.status_code == 502:
                wait_time = initial_delay * (2 ** attempt)  # Exponential backoff
                print(f"Got 502 error, waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
                continue
                
            # Print raw response content for debugging
            print(f"Raw response content: {response.text}")
            
            # Only try to parse JSON if we have content
            if response.text.strip():
                try:
                    response_data = response.json()
                    print(f"Response data: {json.dumps(response_data, indent=2)}")
                    
                    # If we have output data with images, save them
                    if "output" in response_data and "images" in response_data["output"]:
                        os.makedirs("debug_output", exist_ok=True)
                        
                        for i, img_data in enumerate(response_data["output"]["images"]):
                            img_bytes = base64.b64decode(img_data["image"])
                            img = Image.open(io.BytesIO(img_bytes))
                            output_path = f"debug_output/debug_beach_woman_{i}.png"
                            img.save(output_path)
                            print(f"Image saved to {output_path}")
                            
                    # If we get here without errors, we can return
                    return
                    
                except json.JSONDecodeError as je:
                    print(f"Failed to parse JSON response: {je}")
            else:
                print("Response was empty")
                
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            if attempt < max_retries - 1:
                wait_time = initial_delay * (2 ** attempt)
                print(f"Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
            continue
            
        except Exception as e:
            print(f"Unexpected error: {e}")
            break
    
    print("\nFailed to get a successful response after all retries")

print("Starting test with retries...")
make_request_with_retries() 