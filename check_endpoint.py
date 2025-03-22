import requests
import json

# Your credentials
API_KEY = "rpa_B0G5QQEK5R0WYMB523MC7TC0D2XWRG4SJ2H2UQWT1vt2p8"
ENDPOINT_ID = "v8clglpidxjxas"

# Check endpoint health
url = f"https://api.runpod.ai/v2/{ENDPOINT_ID}/health"
    
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

try:
    response = requests.get(url, headers=headers)
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")

# Check endpoint status
url = f"https://api.runpod.ai/v2/{ENDPOINT_ID}"
    
try:
    response = requests.get(url, headers=headers)
    print(f"\nEndpoint Status:")
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}") 