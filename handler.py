import os
import base64
import time
import json
import runpod
import uuid
import subprocess
import requests
import shutil
from io import BytesIO
from PIL import Image

COMFYUI_PORT = 8188
INPUT_DIR = "/ComfyUI/input"
OUTPUT_DIR = "/ComfyUI/output"
WORKFLOW_DIR = "/ComfyUI/workflows"

# Check if ComfyUI is running
def is_comfyui_running():
    max_retries = 5
    retry_delay = 30  # seconds
    
    for attempt in range(max_retries):
        try:
            response = requests.get(f"http://127.0.0.1:{COMFYUI_PORT}/system_stats")
            if response.status_code == 200:
                return True
            else:
                print(f"ComfyUI returned status code {response.status_code}")
        except Exception as e:
            print(f"Attempt {attempt + 1}/{max_retries}: ComfyUI not ready - {str(e)}")
        
        if attempt < max_retries - 1:
            print(f"Waiting {retry_delay} seconds before next attempt...")
            time.sleep(retry_delay)
    
    return False

# Download image from URL or base64
def save_input_image(image_data, filename):
    filepath = os.path.join(INPUT_DIR, filename)
    
    if isinstance(image_data, str):
        if image_data.startswith("http://") or image_data.startswith("https://"):
            # Download from URL
            response = requests.get(image_data, stream=True)
            if response.status_code == 200:
                with open(filepath, 'wb') as f:
                    response.raw.decode_content = True
                    shutil.copyfileobj(response.raw, f)
            else:
                raise Exception(f"Failed to download image: {response.status_code}")
        elif image_data.startswith("data:image"):
            # Decode base64
            image_data = image_data.split(",")[1]
            with open(filepath, "wb") as f:
                f.write(base64.b64decode(image_data))
        else:
            # Assume direct base64
            with open(filepath, "wb") as f:
                f.write(base64.b64decode(image_data))
    else:
        raise ValueError("Image data must be a URL or base64 string")
    
    return filepath

# Save workflow file
def save_workflow(workflow_data, filename):
    filepath = os.path.join(WORKFLOW_DIR, filename)
    
    if isinstance(workflow_data, dict):
        with open(filepath, "w") as f:
            json.dump(workflow_data, f)
    elif isinstance(workflow_data, str):
        if workflow_data.startswith("http://") or workflow_data.startswith("https://"):
            # Download from URL
            response = requests.get(workflow_data)
            if response.status_code == 200:
                with open(filepath, "w") as f:
                    f.write(response.text)
            else:
                raise Exception(f"Failed to download workflow: {response.status_code}")
        else:
            # Assume direct JSON string
            with open(filepath, "w") as f:
                f.write(workflow_data)
    else:
        raise ValueError("Workflow data must be a JSON object or string")
    
    return filepath

# Execute ComfyUI API request
def execute_comfyui_workflow(workflow_path, prompt, input_images=None, face_id_weight=0.8, seed=None):
    # Load workflow
    with open(workflow_path, "r") as f:
        workflow = json.load(f)
    
    # Replace input image paths in the workflow if needed
    if input_images and len(input_images) > 0:
        # Look for LoadImage nodes in the workflow
        for node_id, node in workflow.items():
            if "class_type" in node and node["class_type"] == "LoadImage":
                if "inputs" in node and "image" in node["inputs"]:
                    # Replace with the first input image
                    node["inputs"]["image"] = os.path.basename(input_images[0])
    
    # Replace prompt if needed
    for node_id, node in workflow.items():
        if "class_type" in node and node["class_type"] == "CLIPTextEncode":
            if "inputs" in node and "text" in node["inputs"] and "_meta" in node and "title" in node["_meta"] and "Positive" in node["_meta"]["title"]:
                node["inputs"]["text"] = prompt
    
    # Set PuLID weight if ApplyPulidFlux node exists
    for node_id, node in workflow.items():
        if "class_type" in node and node["class_type"] == "ApplyPulidFlux":
            if "inputs" in node and "weight" in node["inputs"]:
                node["inputs"]["weight"] = face_id_weight
    
    # Set random seed if provided
    if seed is not None:
        for node_id, node in workflow.items():
            if "class_type" in node and node["class_type"] == "RandomNoise":
                if "inputs" in node and "noise_seed" in node["inputs"]:
                    node["inputs"]["noise_seed"] = seed
    
    # Save the modified workflow
    modified_workflow_path = os.path.join(WORKFLOW_DIR, f"modified_{os.path.basename(workflow_path)}")
    with open(modified_workflow_path, "w") as f:
        json.dump(workflow, f)
    
    # Queue the prompt to ComfyUI
    api_endpoint = f"http://127.0.0.1:{COMFYUI_PORT}/prompt"
    response = requests.post(api_endpoint, json={"prompt": workflow})
    if response.status_code != 200:
        raise Exception(f"Failed to queue prompt: {response.text}")
    
    prompt_id = response.json()["prompt_id"]
    
    # Wait for execution to complete
    history_endpoint = f"http://127.0.0.1:{COMFYUI_PORT}/history/{prompt_id}"
    max_attempts = 90  # Increased for potentially longer PuLID generation
    for attempt in range(max_attempts):
        time.sleep(3)  # Increased wait time between checks
        history_response = requests.get(history_endpoint)
        if history_response.status_code == 200:
            history = history_response.json()
            if prompt_id in history:
                if history[prompt_id]["status"]["completed"]:
                    break
        if attempt == max_attempts - 1:
            raise Exception("Timeout waiting for ComfyUI to complete execution")
    
    # Get output images
    output_images = []
    for node_id, node_output in history[prompt_id]["outputs"].items():
        if "images" in node_output:
            for img_data in node_output["images"]:
                img_path = os.path.join(OUTPUT_DIR, img_data["filename"])
                output_images.append(img_path)
    
    return output_images

# Convert output images to base64
def images_to_base64(image_paths):
    result = []
    for img_path in image_paths:
        with open(img_path, "rb") as img_file:
            encoded_string = base64.b64encode(img_file.read()).decode("utf-8")
            result.append({
                "image": encoded_string,
                "filename": os.path.basename(img_path)
            })
    return result

# Main handler for RunPod
def handler(event):
    try:
        # Check if ComfyUI is running
        if not is_comfyui_running():
            return {
                "error": "ComfyUI is not running properly. Please check container logs."
            }
            
        # Extract input parameters
        job_input = event["input"]
        
        reference_image = job_input.get("reference_image")
        workflow_data = job_input.get("workflow")
        prompt = job_input.get("prompt", "")
        face_id_weight = float(job_input.get("face_id_weight", 0.8))
        seed = job_input.get("seed")
        
        if seed is not None:
            try:
                seed = int(seed)
            except ValueError:
                return {"error": "Seed must be an integer"}
        
        if not workflow_data:
            # Use default FLUXLORAPULID workflow if none provided
            default_workflow = "/ComfyUI/workflows/FLUXLORAPULID.json"
            if os.path.exists(default_workflow):
                workflow_data = default_workflow
            else:
                return {
                    "error": "No workflow provided and default FLUXLORAPULID workflow not found"
                }
        
        if not reference_image:
            return {
                "error": "Reference image is required for face consistency with PuLID"
            }
        
        if not prompt or prompt.strip() == "":
            return {
                "error": "Prompt is required for image generation"
            }
        
        # Generate unique IDs for files
        run_id = str(uuid.uuid4())
        
        # Process input files
        input_image_paths = []
        if reference_image:
            img_filename = f"{run_id}_reference.png"
            img_path = save_input_image(reference_image, img_filename)
            input_image_paths.append(img_path)
        
        # If workflow is a string path to a file, use that directly
        if isinstance(workflow_data, str) and os.path.exists(workflow_data):
            workflow_path = workflow_data
        else:
            # Otherwise save the workflow
            workflow_filename = f"{run_id}_workflow.json"
            workflow_path = save_workflow(workflow_data, workflow_filename)
        
        # Execute ComfyUI workflow
        output_images = execute_comfyui_workflow(
            workflow_path, 
            prompt, 
            input_image_paths, 
            face_id_weight,
            seed
        )
        
        # Convert output images to base64
        base64_images = images_to_base64(output_images)
        
        # Return the results
        return {
            "output": {
                "images": base64_images,
                "prompt": prompt,
                "face_id_weight": face_id_weight,
                "seed": seed
            }
        }
    except Exception as e:
        return {
            "error": str(e)
        }

# Start the runpod handler
runpod.serverless.start({
    "handler": handler
}) 