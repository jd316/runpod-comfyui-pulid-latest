# ComfyUI with FluxPuLID for RunPod Serverless

This repository contains a pre-configured setup for running ComfyUI with the FluxPuLID model on RunPod's serverless infrastructure. This setup enables consistent face generation across multiple images.

## Manual Deployment Instructions

### 1. GitHub Repository Setup
The code is already pushed to GitHub at: https://github.com/jd316/runpod-comfyui-pulid-latest.git

### 2. Deploy on RunPod Serverless
1. Go to [RunPod Serverless Console](https://www.runpod.io/console/serverless)
2. Click "New Endpoint"
3. Enter the following settings:
   - **Name**: "comfyui-pulid" (or any name you prefer)
   - **Select GPU**: NVIDIA RTX A4000 (or better)
   - **Worker Count**: Min: 0, Max: 1 (adjust based on your needs)
   - **Advanced Options**: Enable if you want to adjust memory/storage
   - **Container**: 
     - **Source**: GitHub
     - **Source URL**: https://github.com/jd316/runpod-comfyui-pulid-latest.git
   - **Environment Variables**:
     - **Key**: HF_TOKEN
     - **Value**: Your HuggingFace token from https://huggingface.co/settings/tokens

4. Click "Deploy"

### 3. Testing Your Endpoint
Once the endpoint is deployed and the worker is built (this can take 15-20 minutes for the first build as it downloads all models), you can test it using the RunPod API.

### Important Notes
- The first build will take time as it needs to download all the models (about 15-20 minutes)
- Make sure your HuggingFace token has proper permissions to download the required models
- For better performance, you might want to increase the worker count or use a more powerful GPU

## Advanced: Using API to Deploy

If you prefer to use the RunPod API to deploy your endpoint:

1. Edit the `config.py` file with your RunPod API key and HuggingFace token
2. Run the `create_endpoint.py` script:
   ```
   python create_endpoint.py
   ```

## Troubleshooting

- If you encounter errors related to model downloads, check that your HuggingFace token is valid and has the proper permissions
- If the container fails to build, check the build logs in the RunPod console for specific errors

## Features

- Ready-to-deploy RunPod serverless endpoint for face consistency
- Uses official ComfyUI Flux-PuLID workflow with specialized nodes
- Face identity preservation using reference images
- Adjustable face ID weight for controlling similarity
- Reproducible results with seed control
- Support for NSFW and realism LoRAs

## About Flux-PuLID

Flux-PuLID is a specialized model that combines Pure and Lightning ID Customization with Contrastive Alignment to generate images with consistent facial features. It's especially useful for:

- Creating a consistent character across multiple images
- Maintaining facial identity when changing other aspects (clothing, pose, scene)
- Generating variations of a character while keeping recognizable features

## Setup Instructions

### 1. Create a RunPod Account

If you don't already have an account, sign up at [RunPod.io](https://runpod.io).

### 2. Build and Deploy the Docker Image

#### Option 1: Build the Docker Image Locally

```bash
docker build -t your-dockerhub-username/runpod-comfyui-pulid:latest .
docker push your-dockerhub-username/runpod-comfyui-pulid:latest
```

#### Option 2: Use a Pre-built Docker Image

While there isn't an official pre-built Flux-PuLID image, you can build from our Dockerfile which automatically downloads the required models and custom nodes.

### 3. Create a RunPod Serverless Endpoint

1. Go to the [RunPod Console](https://runpod.io/console/serverless)
2. Click "New Endpoint"
3. Select "Docker Image" and enter your Docker image URL
4. Configure the endpoint:
   - Name: Flux-PuLID
   - Min VRAM: 12 GB (recommended minimum for Flux-PuLID)
   - Select GPU type based on your needs and budget (A10/A100/H100 recommended)
   - Idle Timeout: 5 minutes (adjust as needed)
   - Max Workers: Based on your needs
5. Click "Deploy"

## Usage

### API Reference

The endpoint accepts HTTP POST requests with the following JSON structure:

```json
{
  "input": {
    "reference_image": "https://example.com/face.jpg",
    "prompt": "portrait of a woman with blonde hair in a forest",
    "face_id_weight": 0.8,
    "seed": 1234567890
  }
}
```

#### Input Parameters

- `reference_image` (required): URL or base64-encoded image data of the reference face
- `prompt` (required): Text prompt to use for image generation
- `face_id_weight` (optional): Weight of the face ID influence (0.0-1.0, default: 0.8)
- `seed` (optional): Integer seed for reproducible results
- `workflow` (optional): Custom workflow JSON (if not provided, default FLUXLORAPULID workflow is used)

#### Response

```json
{
  "output": {
    "images": [
      {
        "image": "base64-encoded-image-data",
        "filename": "ComfyUI_00001.png"
      }
    ],
    "prompt": "portrait of a woman with blonde hair in a forest",
    "face_id_weight": 0.8,
    "seed": 1234567890
  }
}
```

### Example Usage with cURL

```bash
curl -X POST "https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/run" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "input": {
      "reference_image": "https://example.com/face.jpg",
      "prompt": "portrait of a woman with blonde hair in a forest",
      "face_id_weight": 0.75,
      "seed": 1234567890
    }
  }'
```

### Example Usage with Python Client

Our included Python client makes it easy to generate images with face consistency:

```bash
python client.py \
  --endpoint YOUR_ENDPOINT_ID \
  --api-key YOUR_API_KEY \
  --reference reference_face.jpg \
  --prompt "portrait of a woman with blonde hair in a forest" \
  --face-id-weight 0.8 \
  --seed 1234567890 \
  --output-dir output
```

#### Batch Generation

You can generate multiple images with different seeds in a single command:

```bash
python client.py \
  --endpoint YOUR_ENDPOINT_ID \
  --api-key YOUR_API_KEY \
  --reference reference_face.jpg \
  --prompt "portrait of a woman with blonde hair in a forest" \
  --face-id-weight 0.8 \
  --batch 5 \
  --output-dir output
```

## Adjusting Face Consistency

The `face_id_weight` parameter controls how strongly the generated image resembles the reference face:

- Higher values (0.8-1.0): Strong resemblance to reference face
- Medium values (0.5-0.7): Moderate resemblance that balances with prompt
- Lower values (0.1-0.4): Subtle resemblance, giving more weight to the prompt

## About the FLUXLORAPULID Workflow

The default workflow (`FLUXLORAPULID.json`) includes:

- Official PuLID Flux implementation with GGUF model support
- Specialized PuLID nodes for face analysis and application
- LoRA support including realism enhancement
- Full Flux-dev backend with advanced sampling

## Customization

You can modify the `Dockerfile`
