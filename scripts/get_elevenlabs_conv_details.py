import requests
import os
from dotenv import load_dotenv
import json

load_dotenv()

API_KEY = os.getenv("ELEVENLABS_API_KEY")
headers = {
    "xi-api-key": API_KEY,
    "Content-Type": "application/json"
}

def get_conversation_details(conversation_id):
    url = f"https://api.elevenlabs.io/v1/convai/conversations/{conversation_id}"
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            print(json.dumps(data, indent=2))
        else:
            print(f"Error getting conversation details: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    # Using the most recent failed ID
    conv_id = "conv_5501kktd6h1demf87sejj250v87y"
    get_conversation_details(conv_id)
