import argparse
import base64
import io
import os
import json
from PIL import Image
from client import generate_face_image

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Generate images with face consistency using RunPod endpoint")
    parser.add_argument("--reference_image", required=True, help="Path to the reference image")
    parser.add_argument("--prompt", default="portrait of a person, 4k, high quality", help="Prompt for image generation")
    parser.add_argument("--seed", type=int, default=42, help="Seed for reproducibility")
    parser.add_argument("--face_id_weight", type=float, default=0.8, help="Weight for face ID (0.0-1.0)")
    parser.add_argument("--output_dir", default="output", help="Directory to save output images")
    args = parser.parse_args()

    # Your credentials
    API_KEY = "rpa_B0G5QQEK5R0WYMB523MC7TC0D2XWRG4SJ2H2UQWT1vt2p8"
    ENDPOINT_ID = "v8clglpidxjxas"
    
    print(f"Generating image with prompt: {args.prompt}")
    print(f"Using reference image: {args.reference_image}")
    print(f"Face ID weight: {args.face_id_weight}")
    
    # Generate an image with consistent face
    result = generate_face_image(
        endpoint_id=ENDPOINT_ID,
        api_key=API_KEY,
        workflow_path=None,  # We're using the default workflow in the container
        prompt=args.prompt,
        reference_image_path=args.reference_image,
        face_id_weight=args.face_id_weight,
        seed=args.seed
    )

    # Save the output image
    if result and "images" in result:
        os.makedirs(args.output_dir, exist_ok=True)
        for i, img_data in enumerate(result["images"]):
            image_bytes = base64.b64decode(img_data["image"])
            image = Image.open(io.BytesIO(image_bytes))
            
            # Save the image with seed and weight info in filename
            output_path = f"{args.output_dir}/beach_woman_seed-{args.seed}_weight-{args.face_id_weight}.png"
            image.save(output_path)
            print(f"Image saved to {output_path}")
    else:
        print("Failed to generate image:", result)

if __name__ == "__main__":
    main() 