import os
import runpod
import json
import requests
from config import RUNPOD_API_KEY as CONFIG_RUNPOD_API_KEY, HF_TOKEN as CONFIG_HF_TOKEN

# Try to get API keys from environment first, fallback to config
RUNPOD_API_KEY = os.environ.get("RUNPOD_API_KEY", CONFIG_RUNPOD_API_KEY)
HF_TOKEN = os.environ.get("HF_TOKEN", CONFIG_HF_TOKEN)

# Set your RunPod API key
if not RUNPOD_API_KEY or RUNPOD_API_KEY == "YOUR_RUNPOD_API_KEY_HERE":
    raise ValueError("Please set your RunPod API key in config.py or as environment variable")

print(f"API Key (masked): {'*' * (len(RUNPOD_API_KEY) - 4) + RUNPOD_API_KEY[-4:] if RUNPOD_API_KEY else 'Not Set'}")
print(f"HF Token (masked): {'*' * (len(HF_TOKEN) - 4) + HF_TOKEN[-4:] if HF_TOKEN and HF_TOKEN != 'YOUR_HF_TOKEN_HERE' else 'Not Set'}")

# Using direct API request since runpod.create_endpoint() isn't available
def create_serverless_endpoint():
    try:
        # Define endpoint configuration
        endpoint_config = {
            "name": "comfyui-pulid",
            "gpuIds": ["NVIDIA RTX A4000"],
            "minCount": 0,
            "maxCount": 1,
            "idleTimeout": 300,
            "networkVolumeEnabled": False,
            "template": {
                "env": {
                    "HF_TOKEN": HF_TOKEN if HF_TOKEN != "YOUR_HF_TOKEN_HERE" else ""
                },
                "container": {
                    "url": "https://github.com/jd316/runpod-comfyui-pulid-latest.git"
                }
            }
        }

        print("Creating RunPod serverless endpoint...")
        
        # Test API key with a simple query first
        headers = {
            "Authorization": f"Bearer {RUNPOD_API_KEY}",
            "Content-Type": "application/json"
        }
        
        print("Testing API key with a simple query...")
        test_response = requests.post(
            "https://api.runpod.io/graphql",
            headers=headers,
            json={
                "query": "{ myself { id email } }"
            }
        )
        
        if test_response.status_code != 200:
            print(f"API key test failed with status code: {test_response.status_code}")
            print(f"Response: {test_response.text}")
            return None
            
        test_data = test_response.json()
        if "errors" in test_data:
            print(f"API key test returned errors: {json.dumps(test_data['errors'], indent=2)}")
            return None
            
        print(f"API key test successful! Connected as: {test_data.get('data', {}).get('myself', {}).get('email', 'Unknown')}")
        
        # Make the main API request
        graphql_query = """
        mutation createServerlessEndpoint($input: ServerlessInput!) {
            createServerlessEndpoint(input: $input) {
                id
                name
                status
            }
        }
        """
        
        json_data = {
            "query": graphql_query,
            "variables": {
                "input": endpoint_config
            }
        }
        
        print("Sending API request to create endpoint...")
        response = requests.post(
            "https://api.runpod.io/graphql",
            headers=headers,
            json=json_data
        )
        
        # Print raw response for debugging
        print(f"Response status code: {response.status_code}")
        print(f"Response content: {response.text[:500]}")
        
        # Parse response
        response_json = response.json()
        if "errors" in response_json:
            print(f"Error: {json.dumps(response_json['errors'], indent=2)}")
            return None
            
        # Extract endpoint details
        if "data" not in response_json or response_json["data"] is None:
            print("Error: API response does not contain data")
            print(f"Full response: {json.dumps(response_json, indent=2)}")
            return None
            
        endpoint_data = response_json["data"]["createServerlessEndpoint"]
        print(f"Endpoint created successfully!")
        print(f"Endpoint ID: {endpoint_data['id']}")
        print(f"Endpoint Name: {endpoint_data['name']}")
        print(f"Endpoint Status: {endpoint_data['status']}")
        
        return endpoint_data
    except Exception as e:
        print(f"Error creating endpoint: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    endpoint = create_serverless_endpoint() 