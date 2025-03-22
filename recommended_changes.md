# Recommended Changes for ComfyUI Serverless

## Issue

The ComfyUI service is not starting correctly inside the Docker container, resulting in:

```
HTTPConnectionPool(host='127.0.0.1', port=8188): Max retries exceeded with url: /prompt
```

## Suggestions

### 1. Update the start.sh script

```bash
#!/bin/bash

echo "Worker Initiated"

# Create model directories if they don't exist
mkdir -p /ComfyUI/models/pulid
mkdir -p /ComfyUI/models/gguf
mkdir -p /ComfyUI/models/clip
mkdir -p /ComfyUI/models/vae
mkdir -p /ComfyUI/models/loras
mkdir -p /ComfyUI/workflows

# Download models if they don't exist
# [existing download code...]

# Copy workflow file if it exists in the mounted volume
if [ ! -f "/ComfyUI/workflows/FLUXLORAPULID.json" ]; then
    echo "Copying default workflow"
    cp -f /ComfyUI/workflows/FLUXLORAPULID.json /ComfyUI/workflows/ || echo "No workflow found to copy"
fi

# Start ComfyUI in the background
echo "Starting ComfyUI Server"
cd /ComfyUI
nohup python main.py --listen 0.0.0.0 --port 8188 --api-only > /comfyui.log 2>&1 &

# Wait for ComfyUI to start
echo "Waiting for ComfyUI to initialize..."
sleep 30

# Check if ComfyUI is running
if curl -s http://127.0.0.1:8188/system_stats > /dev/null; then
    echo "ComfyUI is running successfully"
else
    echo "WARNING: ComfyUI may not have started correctly"
    echo "Check logs:"
    tail -n 20 /comfyui.log
fi

# Start the RunPod handler
echo "Starting RunPod Handler"
python -u /handler.py
```

### 2. Modify handler.py

Remove the `start_comfyui()` function and its call since we'll now start ComfyUI from the start.sh script:

```python
# REMOVE THIS CODE
# def start_comfyui():
#     process = subprocess.Popen(
#         ["python", "main.py", "--listen", "0.0.0.0", "--port", str(COMFYUI_PORT), "--api-only"],
#         cwd="/ComfyUI"
#     )
#     # Wait for ComfyUI to start
#     time.sleep(20)  # Increased time to ensure all custom nodes are loaded
#     return process

# REMOVE THIS LINE
# comfyui_process = start_comfyui()
```

### 3. Consider using an established template

If the above changes don't work, consider using one of these Docker images as a base and adapting it:

- `timpietruskyblibla/runpod-worker-comfy:3.4.0-base`
- Check repositories from Ashley Kleynhans or ParticleDog on GitHub for established ComfyUI RunPod templates

### 4. RunPod Support

If you continue to have issues, contact RunPod support with the error logs. They can provide specific guidance for ComfyUI serverless deployments.

### 5. Quick Validation Test

You can add this additional code to the handler.py file to validate that ComfyUI is accessible within the container:

```python
def is_comfyui_running():
    try:
        response = requests.get(f"http://127.0.0.1:{COMFYUI_PORT}/system_stats")
        if response.status_code == 200:
            return True
        return False
    except:
        return False

# Add this near the beginning of the handler function:
if not is_comfyui_running():
    return {"error": "ComfyUI is not running properly"}
```
