import requests
import json
import base64
import os
import random
from PIL import Image
import io
import argparse
import time

def generate_face_image(endpoint_id, api_key, workflow_path, prompt, reference_image_path, face_id_weight=0.8, seed=None):
    url = f"https://api.runpod.ai/v2/{endpoint_id}/run"
    
    # Load workflow if provided
    workflow = None
    if workflow_path:
        with open(workflow_path, "r") as f:
            workflow = json.load(f)
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    # Generate random seed if not provided
    if seed is None:
        seed = random.randint(0, 2**32 - 1)
    
    data = {
        "input": {
            "prompt": prompt,
            "face_id_weight": face_id_weight,
            "seed": seed
        }
    }
    
    # Add workflow if provided
    if workflow:
        data["input"]["workflow"] = workflow
    
    # Add reference image (required for PuLID)
    if not reference_image_path:
        raise ValueError("Reference image is required for PuLID face consistency")
    
    with open(reference_image_path, "rb") as img_file:
        encoded_string = base64.b64encode(img_file.read()).decode("utf-8")
        data["input"]["reference_image"] = encoded_string
    
    # Submit the job
    print(f"Submitting job with seed {seed}...")
    response = requests.post(url, headers=headers, json=data)
    response_data = response.json()
    
    if "id" not in response_data:
        print("Error submitting job:", response_data)
        return None
    
    job_id = response_data["id"]
    print(f"Job submitted with ID: {job_id}")
    
    # Poll for job status
    status_url = f"https://api.runpod.ai/v2/{endpoint_id}/status/{job_id}"
    
    while True:
        print("Checking job status...")
        status_response = requests.get(status_url, headers=headers)
        status_data = status_response.json()
        
        if status_data["status"] == "COMPLETED":
            print("Job completed!")
            break
        elif status_data["status"] in ["FAILED", "CANCELLED"]:
            print(f"Job {status_data['status']}: {status_data.get('error', 'Unknown error')}")
            return None
        
        print(f"Job status: {status_data['status']}. Waiting 10 seconds...")
        time.sleep(10)
    
    # Get the results
    print("Retrieving results...")
    result_url = f"https://api.runpod.ai/v2/{endpoint_id}/output/{job_id}"
    result_response = requests.get(result_url, headers=headers)
    result_data = result_response.json()
    
    return result_data.get("output")

def save_output_images(output, output_dir):
    if not output or "images" not in output:
        print("No images in output")
        return
    
    os.makedirs(output_dir, exist_ok=True)
    
    seed = output.get("seed", "unknown")
    face_id_weight = output.get("face_id_weight", 0.8)
    
    for i, img_data in enumerate(output["images"]):
        image_bytes = base64.b64decode(img_data["image"])
        image = Image.open(io.BytesIO(image_bytes))
        
        # Save the image with seed and weight info in filename
        base_filename = os.path.splitext(img_data["filename"])[0]
        output_path = os.path.join(output_dir, f"{base_filename}_seed-{seed}_weight-{face_id_weight}.png")
        image.save(output_path)
        print(f"Saved image {i+1}/{len(output['images'])}: {output_path}")

def main():
    parser = argparse.ArgumentParser(description="RunPod Flux-PuLID Face Consistency Client")
    parser.add_argument("--endpoint", required=True, help="RunPod endpoint ID")
    parser.add_argument("--api-key", required=True, help="RunPod API key")
    parser.add_argument("--reference", required=True, help="Path to reference face image")
    parser.add_argument("--prompt", required=True, help="Text prompt for image generation")
    parser.add_argument("--workflow", help="Path to custom workflow JSON file (optional)")
    parser.add_argument("--face-id-weight", type=float, default=0.8, help="Weight of the face ID influence (0.0-1.0, default: 0.8)")
    parser.add_argument("--seed", type=int, help="Random seed for reproducible results (optional)")
    parser.add_argument("--output-dir", default="output", help="Directory to save output images (default: 'output')")
    parser.add_argument("--batch", type=int, default=1, help="Number of images to generate in sequence (default: 1)")
    
    args = parser.parse_args()
    
    for i in range(args.batch):
        if args.batch > 1:
            print(f"\nGenerating image {i+1}/{args.batch}")
            # Use different seeds for batch generation if seed not specified
            current_seed = args.seed if args.seed is not None else random.randint(0, 2**32 - 1)
        else:
            current_seed = args.seed
            
        output = generate_face_image(
            args.endpoint,
            args.api_key,
            args.workflow,
            args.prompt,
            args.reference,
            args.face_id_weight,
            current_seed
        )
        
        if output:
            save_output_images(output, args.output_dir)
            if args.batch > 1:
                # Add small delay between batch requests
                time.sleep(3)
        else:
            print(f"Failed to generate image {i+1}")
    
    print("Done!")

if __name__ == "__main__":
    main() 