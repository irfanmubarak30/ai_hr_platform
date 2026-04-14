
import os
import sys
from flask import Flask, jsonify
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from backend.config import config

# Mocking the listener states for the sake of the test
def is_running_mock(): return False

print("--- Data from config object ---")
settings = {
    'gemini_api_key': '***' if config.GEMINI_API_KEY else '',
    'groq_api_key': '***' if config.GROQ_API_KEY else '',
    'apify_api_token': '***' if config.APIFY_API_TOKEN else '',
    'elevenlabs_api_key': '***' if config.ELEVENLABS_API_KEY else '',
    'elevenlabs_agent_id': config.ELEVENLABS_AGENT_ID,
    'elevenlabs_phone_id': config.ELEVENLABS_PHONE_NUMBER_ID,
    'google_sheets_id': config.GOOGLE_SHEETS_ID,
    'google_drive_folder_id': config.GOOGLE_DRIVE_FOLDER_ID,
    'company_email': config.COMPANY_EMAIL,
    'company_name': config.COMPANY_NAME,
    'recruiter_name': config.RECRUITER_NAME,
}
import json
print(json.dumps(settings, indent=2))
print("--- End ---")
