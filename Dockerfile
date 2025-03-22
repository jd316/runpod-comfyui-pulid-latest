FROM runpod/base:0.4.0-cuda11.8.0 AS builder

ENV PYTHONUNBUFFERED=1
WORKDIR /

# Install system dependencies for Python and venv
RUN apt-get update && apt-get install -y python3 python3-pip python3-venv git

# Create and activate virtual environment
RUN python3 -m venv /venv
ENV PATH="/venv/bin:$PATH"

# Install required Python packages
RUN pip install runpod==0.9.12 \
    torch==2.0.1+cu118 torchvision==0.15.2+cu118 torchaudio==2.0.2 --extra-index-url https://download.pytorch.org/whl/cu118 \
    scipy==1.11.1 transformers==4.25.1 matplotlib==3.7.2 opencv-python==4.8.0.74 safetensors==0.3.2 \
    pillow==9.5.0 requests==2.31.0 aiohttp==3.8.4 psutil==5.9.5 onnxruntime-gpu

# Install ComfyUI
COPY custom_repos/ComfyUI /ComfyUI
WORKDIR /ComfyUI

# Install ComfyUI dependencies
RUN pip install -r requirements.txt

# Create directories for models and workflows
RUN mkdir -p /ComfyUI/models/checkpoints \
    /ComfyUI/models/vae \
    /ComfyUI/models/loras \
    /ComfyUI/models/clip \
    /ComfyUI/models/controlnet \
    /ComfyUI/models/unet \
    /ComfyUI/models/pulid \
    /ComfyUI/models/insightface \
    /ComfyUI/models/gguf \
    /ComfyUI/input \
    /ComfyUI/output \
    /ComfyUI/workflows

# Install PuLID Flux custom nodes
WORKDIR /ComfyUI/custom_nodes
COPY custom_repos/comfyui-faceless-node /ComfyUI/custom_nodes/comfyui-faceless-node
COPY custom_repos/rgthree-comfy /ComfyUI/custom_nodes/rgthree-comfy
COPY custom_repos/ComfyUI-Custom-Scripts /ComfyUI/custom_nodes/ComfyUI-Custom-Scripts
COPY custom_repos/ComfyUI-PuLID-Flux /ComfyUI/custom_nodes/comfyui-pulid-flux

# Install PuLID dependencies
WORKDIR /ComfyUI/custom_nodes/comfyui-faceless-node
RUN pip install -r requirements.txt

# Clean up apt caches and temp files to reduce image size
RUN apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Start from a fresh base image for the final stage
FROM runpod/base:0.4.0-cuda11.8.0

WORKDIR /

# Copy the virtual environment
COPY --from=builder /venv /venv
ENV PATH="/venv/bin:$PATH"

# Copy ComfyUI and custom nodes
COPY --from=builder /ComfyUI /ComfyUI

# Copy workflow file
COPY FLUXLORAPULID.json /ComfyUI/workflows/

# Copy handler script and startup script
COPY handler.py /handler.py
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Set up the entrypoint
ENTRYPOINT ["/start.sh"] 