import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ELEVENLABS_API_KEY")
AGENT_ID = os.getenv("ELEVENLABS_AGENT_ID")
PHONE_ID = os.getenv("ELEVENLABS_PHONE_NUMBER_ID")

print(f"Checking ElevenLabs Configuration:")
print(f"API Key: {API_KEY[:5]}...{API_KEY[-5:] if API_KEY else 'None'}")
print(f"Agent ID: {AGENT_ID}")
print(f"Phone ID: {PHONE_ID}")

headers = {
    "xi-api-key": API_KEY,
    "Content-Type": "application/json"
}

# 1. Test API Key by listing voices or agents
print("\n--- Testing API Key (Listing Agents) ---")
try:
    resp = requests.get("https://api.elevenlabs.io/v1/convai/agents", headers=headers)
    print(f"Status Code: {resp.status_code}")
    if resp.status_code == 200:
        agents = resp.json().get('agents', [])
        print(f"Found {len(agents)} agents.")
        for a in agents:
            print(f" - {a.get('name')} ({a.get('agent_id')})")
    else:
        print(f"Error: {resp.text}")
except Exception as e:
    print(f"Exception: {e}")

# 2. Test Specific Agent
if AGENT_ID:
    print(f"\n--- Testing Agent ID: {AGENT_ID} ---")
    try:
        resp = requests.get(f"https://api.elevenlabs.io/v1/convai/agents/{AGENT_ID}", headers=headers)
        print(f"Status Code: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            # print(json.dumps(data, indent=2)) # Uncommment if needed
            print("Agent found successfully.")
            import json
            # Print a few key sections to see the structure
            print(f"Data Keys: {list(data.keys())}")
            agent_config = data.get('conversation_config', {}) # Maybe it's conversation_config?
            if not agent_config:
                 agent_config = data.get('agent_config', {})
            
            print(f"Config Keys: {list(agent_config.keys())}")
            
            # Try to find the prompt in the nested structure
            # Based on ElevenLabs docs, it's often in agent_config -> prompt -> text
            # or conversation_config -> agent -> prompt -> text
            prompt = agent_config.get('agent', {}).get('prompt', {}).get('text') or \
                     agent_config.get('prompt', {}).get('text') or "Unknown"
            print(f"Prompt: {prompt[:100]}...")
            
        else:
            print(f"Error: {resp.text}")
    except Exception as e:
        print(f"Exception: {e}")

# 3. Test Phone Number
if PHONE_ID:
    print(f"\n--- Testing Phone Number ID: {PHONE_ID} ---")
    try:
        resp = requests.get("https://api.elevenlabs.io/v1/convai/phone-numbers", headers=headers)
        print(f"Status Code: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            phones = data if isinstance(data, list) else data.get('phone_numbers', [])
            print(f"Found {len(phones)} phone numbers.")
            for p in phones:
                p_id = p.get('phone_number_id') if isinstance(p, dict) else 'Unknown'
                p_num = p.get('phone_number') if isinstance(p, dict) else 'Unknown'
                print(f" - {p_num} ({p_id})")
        else:
            print(f"Error: {resp.text}")
    except Exception as e:
        print(f"Exception: {e}")

# 4. Test Trigger Call (Simulated)
print("\n--- Testing Trigger Call (to a fake number) ---")
url = "https://api.elevenlabs.io/v1/convai/twilio/outbound-call"
payload = {
    "agent_id": AGENT_ID,
    "agent_phone_number_id": PHONE_ID,
    "to_number": "+15550000000", # Fake number
    "conversation_initiation_data": {
        "dynamic_variables": {
            "candidate_name": "Test Candidate",
            "position": "Software Engineer",
            "company": "Ligenix"
        }
    }
}

try:
    resp = requests.post(url, json=payload, headers=headers)
    print(f"Status Code: {resp.status_code}")
    print(f"Response: {resp.text}")
except Exception as e:
    print(f"Exception: {e}")
