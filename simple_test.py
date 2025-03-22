import requests
import json
import time
import base64

# Your credentials
API_KEY = "rpa_B0G5QQEK5R0WYMB523MC7TC0D2XWRG4SJ2H2UQWT1vt2p8"
ENDPOINT_ID = "v8clglpidxjxas"

url = f"https://api.runpod.ai/v2/{ENDPOINT_ID}/run"
    
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

# Load the reference image
reference_image_path = r"C:\Users\jdbis\Documents\runpod-fluxpulid-serveless\image (42).png"
with open(reference_image_path, "rb") as f:
    reference_img_base64 = base64.b64encode(f.read()).decode("utf-8")

# Simple payload with reference image
data = {
    "input": {
        "prompt": "woman on a sea beach",
        "face_id_weight": 0.8,
        "seed": 42,
        "reference_image": reference_img_base64
    }
}

# Submit the job
print("Submitting job with reference image...")
try:
    response = requests.post(url, headers=headers, json=data)
    response_data = response.json()
    print(f"Response: {response_data}")
    
    if "id" in response_data:
        job_id = response_data["id"]
        print(f"Job submitted with ID: {job_id}")
        
        # Poll for job status
        status_url = f"https://api.runpod.ai/v2/{ENDPOINT_ID}/status/{job_id}"
        
        max_attempts = 20
        attempts = 0
        
        while attempts < max_attempts:
            print("Checking job status...")
            status_response = requests.get(status_url, headers=headers)
            status_data = status_response.json()
            print(f"Status data: {status_data}")
            
            if status_data.get("status") == "COMPLETED":
                print("Job completed!")
                
                # Get the output
                output_url = f"https://api.runpod.ai/v2/{ENDPOINT_ID}/output/{job_id}"
                output_response = requests.get(output_url, headers=headers)
                output_data = output_response.json()
                print(f"Output available: {output_data}")
                
                # Save the output image if available
                if "output" in output_data and "images" in output_data["output"]:
                    import os
                    from PIL import Image
                    import io
                    
                    os.makedirs("output", exist_ok=True)
                    
                    for i, img_data in enumerate(output_data["output"]["images"]):
                        img_bytes = base64.b64decode(img_data["image"])
                        img = Image.open(io.BytesIO(img_bytes))
                        output_path = f"output/beach_woman_seed-42_weight-0.8_{i}.png"
                        img.save(output_path)
                        print(f"Image saved to {output_path}")
                
                break
            elif status_data.get("status") in ["FAILED", "CANCELLED"]:
                print(f"Job {status_data.get('status')}: {status_data.get('error', 'Unknown error')}")
                break
            
            print(f"Job status: {status_data.get('status')}. Waiting 10 seconds...")
            time.sleep(10)
            attempts += 1
    else:
        print("No job ID in response")
except Exception as e:
    print(f"Error: {e}") 