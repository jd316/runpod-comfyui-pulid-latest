# Instructions for Rebuilding and Redeploying

Here are the steps to rebuild your Docker image with the fixed ComfyUI startup and redeploy it to RunPod:

## 1. Rebuild the Docker Image

From your project directory, run:

```bash
docker build -t btclayer/runpod-comfyui-pulid:latest .
```

## 2. Push to Docker Hub

```bash
docker login
docker push btclayer/runpod-comfyui-pulid:latest
```

## 3. Update the RunPod Endpoint

You have two options:

### Option 1: Update the Existing Endpoint

1. Go to your RunPod Dashboard: <https://www.runpod.io/console/serverless/user/apis>
2. Find your endpoint ID `v8clglpidxjxas`
3. Click on "Edit"
4. Under "Advanced", click "Clear Cache" to ensure the latest image is used
5. Click "Save"

### Option 2: Create a New Endpoint

1. Go to RunPod Serverless: <https://www.runpod.io/console/serverless/user/apis>
2. Click "New Endpoint"
3. Select the appropriate options:
   - Container Image: `btclayer/runpod-comfyui-pulid:latest`
   - Select GPU type (A10/A100/etc)
   - Name: "FluxPuLID"
   - Min VRAM: 24 GB
   - Advanced Options:
     - Worker Concurrency: 1
     - Container Disk: 25 GB
     - Flash Boot: Enabled
     - Max Workers: 3+ (depending on your needs)
4. Click "Deploy"

## 4. Test the Updated Endpoint

Use your `test_endpoint.py` script to verify that everything is working correctly:

```bash
python test_endpoint.py --reference_image "C:\Users\jdbis\Documents\runpod-fluxpulid-serveless\image (42).png" --prompt "woman on a sea beach"
```

## What Changed?

1. **start.sh**: Now properly starts ComfyUI in the background and waits for it to initialize before starting the handler
2. **handler.py**: Removed the duplicate ComfyUI start code and added a check to verify ComfyUI is running

These changes ensure that ComfyUI is fully initialized and available on port 8188 when the handler starts processing requests.

## Troubleshooting

If you still encounter issues:

1. Check the RunPod logs for the endpoint/worker
2. Verify ComfyUI is starting correctly by checking for the "ComfyUI is running successfully" message
3. If ComfyUI isn't starting, check the `/comfyui.log` file in the container
