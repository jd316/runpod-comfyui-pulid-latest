#!/bin/bash

echo "Worker Initiated"

# Set environment variables
export PYTHONUNBUFFERED=1
export PYTHONPATH=/ComfyUI
export PATH="/venv/bin:$PATH"

# HuggingFace token for authentication
HF_TOKEN="${HF_TOKEN:-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}"
AUTH_HEADER="Authorization: Bearer $HF_TOKEN"

# Function to download model with verification and retries
download_model() {
    local url=$1
    local output=$2
    local max_retries=5  # Increased retries
    local retry_count=0
    local success=false

    echo "Downloading $(basename $output)..."
    mkdir -p "$(dirname "$output")"

    while [ $retry_count -lt $max_retries ] && [ "$success" = false ]; do
        echo "Attempt $((retry_count + 1)) of $max_retries"
        
        if curl -L -H "$AUTH_HEADER" -o "$output" "$url" 2>/tmp/curl_error.log; then
            if [ -f "$output" ]; then
                local file_size=$(stat -f%z "$output" 2>/dev/null || stat -c%s "$output" 2>/dev/null)
                if [ "$file_size" -gt 1000000 ]; then  # File should be at least 1MB
                    echo "✓ Successfully downloaded $(basename $output) (${file_size} bytes)"
                    success=true
                    break
                else
                    echo "✗ Downloaded file is too small (${file_size} bytes)"
                fi
            else
                echo "✗ Output file was not created"
            fi
        fi
        
        echo "Download failed. Curl error output:"
        cat /tmp/curl_error.log
        
        echo "Cleaning up and retrying..."
        rm -f "$output"
        retry_count=$((retry_count + 1))
        
        if [ $retry_count -lt $max_retries ]; then
            sleep_time=$((retry_count * 5))  # Progressive backoff
            echo "Waiting ${sleep_time} seconds before next attempt..."
            sleep $sleep_time
        fi
    done

    if [ "$success" = false ]; then
        echo "✗ Failed to download $(basename $output) after $max_retries attempts"
        return 1
    fi
    
    return 0
}

# Create model directories
mkdir -p /ComfyUI/{models/{pulid,gguf,clip,vae,loras},workflows,input,output}
chmod -R 777 /ComfyUI

# Download required models
MODELS=(
    "https://huggingface.co/guozinan/PuLID/resolve/main/pulid_flux_v0.9.1.safetensors|/ComfyUI/models/pulid/pulid_flux_v0.9.1.safetensors"
    "https://huggingface.co/sayakpaul/FLUX.1-merged/resolve/main/flux1-dev-Q4_0.gguf|/ComfyUI/models/gguf/flux1-dev-Q4_0.gguf"
    "https://huggingface.co/guozinan/PuLID/resolve/main/clip_l.safetensors|/ComfyUI/models/clip/clip_l.safetensors"
    "https://huggingface.co/guozinan/PuLID/resolve/main/t5xxl_fp8_e4m3fn.safetensors|/ComfyUI/models/clip/t5xxl_fp8_e4m3fn.safetensors"
    "https://huggingface.co/guozinan/PuLID/resolve/main/ae.safetensors|/ComfyUI/models/vae/ae.safetensors"
    "https://huggingface.co/guozinan/PuLID/resolve/main/flux_realism_lora.safetensors|/ComfyUI/models/loras/flux_realism_lora.safetensors"
)

DOWNLOAD_FAILED=0
for model in "${MODELS[@]}"; do
    IFS="|" read -r url path <<< "$model"
    if [ ! -f "$path" ]; then
        echo "Downloading: $url"
        echo "Target path: $path"
        if ! download_model "$url" "$path"; then
            DOWNLOAD_FAILED=1
            echo "✗ Failed to download: $(basename $path)"
        fi
    else
        echo "✓ Model $(basename $path) already exists"
    fi
done

if [ $DOWNLOAD_FAILED -eq 1 ]; then
    echo "ERROR: Some models failed to download. Check the logs above."
    exit 1
fi

# Copy workflow file
if [ -f "/ComfyUI/workflows/FLUXLORAPULID.json" ]; then
    echo "✓ Workflow already exists"
else
    echo "Copying default workflow..."
    cp -f /ComfyUI/workflows/FLUXLORAPULID.json /ComfyUI/workflows/ || {
        echo "✗ ERROR: Failed to copy workflow file"
        exit 1
    }
fi

# Function to start ComfyUI
start_comfyui() {
    echo "Starting ComfyUI Server..."
    cd /ComfyUI
    python main.py --listen 0.0.0.0 --port 8188 --api-only --disable-metadata > /comfyui.log 2>&1 &
    COMFYUI_PID=$!
    echo "ComfyUI process started with PID: $COMFYUI_PID"
}

# Function to check if ComfyUI is running
check_comfyui() {
    local timeout=10
    local start_time=$(date +%s)
    
    while true; do
        if curl -s http://127.0.0.1:8188/system_stats > /dev/null; then
            return 0
        fi
        
        local current_time=$(date +%s)
        if [ $((current_time - start_time)) -ge $timeout ]; then
            return 1
        fi
        sleep 1
    done
}

# Start ComfyUI and wait for it to be ready
echo "Starting ComfyUI..."
start_comfyui

# Initial wait for startup
echo "Waiting for initial startup (60 seconds)..."
sleep 60

# Check if ComfyUI is running, retry if needed
MAX_RETRIES=3
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    echo "Checking ComfyUI status (attempt $((RETRY_COUNT + 1)))"
    if check_comfyui; then
        echo "SUCCESS: ComfyUI is running and responding to API calls"
        break
    else
        echo "WARNING: ComfyUI not responding on attempt $((RETRY_COUNT + 1))"
        echo "Latest ComfyUI logs:"
        tail -n 50 /comfyui.log
        
        if [ $RETRY_COUNT -lt $((MAX_RETRIES - 1)) ]; then
            echo "Restarting ComfyUI..."
            kill $COMFYUI_PID 2>/dev/null || true
            sleep 10
            start_comfyui
            sleep 60
        fi
        RETRY_COUNT=$((RETRY_COUNT + 1))
    fi
done

if ! check_comfyui; then
    echo "ERROR: ComfyUI failed to start properly after $MAX_RETRIES attempts"
    echo "Full ComfyUI logs:"
    cat /comfyui.log
    exit 1
fi

# Start the RunPod handler
echo "Starting RunPod Handler"
python -u /handler.py