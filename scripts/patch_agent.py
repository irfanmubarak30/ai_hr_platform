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

# The goal is to:
# 1. Correct the LLM to a known working one (gemini-1.5-flash)
# 2. Clean up the quotes in the first message
# 3. Ensure the prompt is correctly structured

# Re-read the current config to be safe
resp = requests.get(f"https://api.elevenlabs.io/v1/convai/agents/{AGENT_ID}", headers=headers)
if resp.status_code != 200:
    print(f"Failed to fetch agent: {resp.text}")
    exit(1)

agent_data = resp.json()
config = agent_data.get('conversation_config', {})

# Clean first message
old_first_msg = config.get('agent', {}).get('first_message', "")
new_first_msg = old_first_msg.strip('"').strip("'").strip()

# Update LLM
old_llm = config.get('agent', {}).get('prompt', {}).get('llm')
new_llm = "gemini-1.5-flash" # Known working model

print(f"Old LLM: {old_llm} -> New LLM: {new_llm}")
print(f"Old First Message: {old_first_msg[:50]}...")
print(f"New First Message: {new_first_msg[:50]}...")

# Construct patch payload
# Note: Patching often requires the nested structure or a specific 'conversation_config' update
patch_payload = {
    "conversation_config": {
        "agent": {
            "first_message": new_first_msg,
            "prompt": {
                "llm": new_llm
            }
        }
    }
}

print("\nPatching agent...")
try:
    # ElevenLabs PATCH /agents/{agent_id} expects the fields you want to change
    patch_url = f"https://api.elevenlabs.io/v1/convai/agents/{AGENT_ID}"
    resp = requests.patch(patch_url, json=patch_payload, headers=headers)
    print(f"Status Code: {resp.status_code}")
    if resp.status_code == 200:
        print("Successfully updated agent configuration!")
    else:
        print(f"Error: {resp.text}")
except Exception as e:
    print(f"Exception: {e}")
