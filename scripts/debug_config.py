
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from backend.config import config

print("--- Current Config State ---")
print(f"ELEVENLABS_API_KEY: {'[SET]' if config.ELEVENLABS_API_KEY else '[EMPTY]'}")
print(f"ELEVENLABS_AGENT_ID: {config.ELEVENLABS_AGENT_ID}")
print(f"ELEVENLABS_PHONE_NUMBER_ID: {config.ELEVENLABS_PHONE_NUMBER_ID}")
print(f"APIFY_API_TOKEN: {'[SET]' if config.APIFY_API_TOKEN else '[EMPTY]'}")
print("----------------------------")
