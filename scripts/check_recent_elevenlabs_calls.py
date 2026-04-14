import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ELEVENLABS_API_KEY")
headers = {
    "xi-api-key": API_KEY,
    "Content-Type": "application/json"
}

def list_recent_conversations(limit=10):
    url = f"https://api.elevenlabs.io/v1/convai/conversations?page_size={limit}"
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            conversations = data.get('conversations', [])
            print(f"Found {len(conversations)} recent conversations:")
            for conv in conversations:
                conv_id = conv.get('conversation_id')
                status = conv.get('status')
                start_time = conv.get('start_time_unix_secs')
                agent_name = conv.get('agent_name')
                print(f" - ID: {conv_id}, Status: {status}, Agent: {agent_name}, Time: {start_time}")
        else:
            print(f"Error listing conversations: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    list_recent_conversations()
