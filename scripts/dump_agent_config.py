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

print(f"Dumping full configuration for Agent: {AGENT_ID}")

try:
    resp = requests.get(f"https://api.elevenlabs.io/v1/convai/agents/{AGENT_ID}", headers=headers)
    if resp.status_code == 200:
        data = resp.json()
        with open("agent_config.json", "w") as f:
            json.dump(data, f, indent=2)
        print("Success: Full agent configuration saved to agent_config.json")
        
        # Quick summary
        name = data.get('name', 'Unknown')
        config = data.get('conversation_config', {})
        if not config:
            config = data.get('agent_config', {})
            
        print(f"Agent Name: {name}")
        
        # Check for first message and prompt
        first_msg = config.get('agent', {}).get('first_message') or config.get('first_message')
        prompt = config.get('agent', {}).get('prompt', {}).get('text') or config.get('prompt', {}).get('text')
        
        print(f"First Message present: {bool(first_msg)}")
        print(f"Prompt present: {bool(prompt)}")
        
        if not first_msg:
            print("WARNING: First Message is MISSING. The agent will not start the conversation.")
        if not prompt:
            print("WARNING: System Prompt is MISSING. The agent won't know what to do.")
            
    else:
        print(f"Error {resp.status_code}: {resp.text}")
except Exception as e:
    print(f"Exception: {e}")
