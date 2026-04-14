import sys
import os
import json

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from backend.call_service import get_conversation_transcript

def dump_conv(conv_id):
    print(f"Fetching raw data for conversation: {conv_id}")
    data = get_conversation_transcript(conv_id)
    if not data:
        print("Error: Could not fetch conversation data.")
        return
    
    # Save to a temporary file for analysis
    with open('tmp/raw_conv.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    print("Keys found in raw data:")
    print(list(data.keys()))
    
    print("\nRecording URL value:")
    print(f"recording_url: {data.get('recording_url')}")
    print(f"audio_url: {data.get('audio_url')}") # Just in case

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/dump_conv.py <conversation_id>")
    else:
        os.makedirs('tmp', exist_ok=True)
        dump_conv(sys.argv[1])
