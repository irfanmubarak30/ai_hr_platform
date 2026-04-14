import os
import requests
import time
from dotenv import load_dotenv

# Load env vars
load_dotenv()

def test_huggingface_flux():
    token = os.getenv("HUGGINGFACE_API_TOKEN")
    if not token or token == "your_token_here":
        print("❌ HUGGINGFACE_API_TOKEN not found or not set in .env")
        return

    print("Testing Hugging Face FLUX integration...")
    API_URL = "https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-schnell"
    headers = {"Authorization": f"Bearer {token}"}
    
    prompt = "Cinematic photography of a software engineer at work in a modern office, highly detailed 8k"
    payload = {"inputs": prompt}
    
    try:
        start_time = time.time()
        response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            output_path = "test_flux_hf.jpg"
            with open(output_path, "wb") as f:
                f.write(response.content)
            print(f"Success! Image generated in {elapsed:.2f}s and saved to {output_path}")
        elif response.status_code == 503:
            print("Model is loading (503). Try again in 30 seconds.")
        else:
            print(f"Failed with status {response.status_code}: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_huggingface_flux()
