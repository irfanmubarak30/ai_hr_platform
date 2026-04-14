import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ELEVENLABS_API_KEY")
AGENT_ID = os.getenv("ELEVENLABS_AGENT_ID")

headers = {
    "xi-api-key": API_KEY,
    "Content-Type": "application/json"
}

# 1. Fetch current config
resp = requests.get(f"https://api.elevenlabs.io/v1/convai/agents/{AGENT_ID}", headers=headers)
if resp.status_code != 200:
    print(f"Failed to fetch agent: {resp.text}")
    exit(1)

agent_data = resp.json()
config = agent_data.get('conversation_config', {})

# 2. Prepare patch for audio support
# We need to set text_only to false in both conversation and overrides
patch_payload = {
    "conversation_config": {
        "conversation": {
            "text_only": False
        },
        "agent": {
            "prompt": {
                "llm": "gemini-1.5-flash"
            }
        }
    }
}

# Also need to check if there are overrides blocking it
if 'platform_settings' in agent_data and 'overrides' in agent_data['platform_settings']:
    # ElevenLabs sometimes has complex nested overrides
    pass

print("Patching agent to enable audio (text_only = False)...")
try:
    patch_url = f"https://api.elevenlabs.io/v1/convai/agents/{AGENT_ID}"
    resp = requests.patch(patch_url, json=patch_payload, headers=headers)
    print(f"Status Code: {resp.status_code}")
    if resp.status_code == 200:
        print("Successfully enabled audio for the agent!")
    else:
        print(f"Error: {resp.text}")
except Exception as e:
    print(f"Exception: {e}")
