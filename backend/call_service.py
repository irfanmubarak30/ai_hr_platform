import requests
import time
from backend.config import config

ELEVENLABS_BASE = "https://api.elevenlabs.io/v1"

def _headers():
    return {
        "xi-api-key": config.ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }

def trigger_interview_call(phone_number, candidate_name, position):
    """Trigger an outbound AI call via ElevenLabs + Twilio."""
    if not config.ELEVENLABS_API_KEY or not config.ELEVENLABS_AGENT_ID:
        print("ElevenLabs not configured — simulating call")
        return {
            "conversation_id": f"mock-conv-{candidate_name.replace(' ', '-').lower()}",
            "status": "simulated",
            "mock": True
        }
    
    url = f"{ELEVENLABS_BASE}/convai/twilio/outbound-call"
    payload = {
        "agent_id": config.ELEVENLABS_AGENT_ID,
        "agent_phone_number_id": config.ELEVENLABS_PHONE_NUMBER_ID,
        "to_number": phone_number,
        "conversation_initiation_data": {
            "dynamic_variables": {
                "candidate_name": candidate_name,
                "position": position,
                "company": config.COMPANY_NAME
            }
        }
    }
    
    try:
        resp = requests.post(url, json=payload, headers=_headers(), timeout=30)
        if resp.status_code in (200, 201):
            data = resp.json()
            if data.get('success') is False:
                error_msg = data.get('message', 'Unknown ElevenLabs error')
                return {"error": f"Call rejected: {error_msg}"}
            return data
        return {"error": f"Call failed: Status {resp.status_code} - {resp.text}"}
    except Exception as e:
        return {"error": f"Call exception: {str(e)}"}

def list_recent_conversations(limit=20):
    """List recent ElevenLabs conversations to sync history."""
    if not config.ELEVENLABS_API_KEY:
        return []
    
    url = f"{ELEVENLABS_BASE}/convai/conversations?page_size={limit}"
    try:
        resp = requests.get(url, headers=_headers(), timeout=15)
        if resp.status_code == 200:
            return resp.json().get('conversations', [])
    except Exception as e:
        print(f"List conversations error: {e}")
    return []

def get_conversation_transcript(conversation_id):
    """Retrieve transcript from a completed ElevenLabs conversation."""
    if not config.ELEVENLABS_API_KEY or conversation_id.startswith('mock-'):
        return {
            "transcript": [
                {"role": "agent", "message": f"Hello, this is the recruitment assistant from {config.COMPANY_NAME}. Your profile has been shortlisted. We would like to schedule your interview. Please confirm your availability.", "time_in_call_secs": 0},
                {"role": "user", "message": "Yes, I'm available. Thank you for reaching out!", "time_in_call_secs": 8}
            ],
            "analysis": {"transcript_summary": "Candidate confirmed availability for the interview and expressed enthusiasm about the opportunity."},
            "metadata": {"call_duration_secs": 45}
        }
    
    url = f"{ELEVENLABS_BASE}/convai/conversations/{conversation_id}"
    try:
        resp = requests.get(url, headers=_headers(), timeout=15)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        print(f"Transcript error: {e}")
    return None

def format_transcript(raw_data):
    """Format raw conversation data into text."""
    transcript = raw_data.get('transcript', [])
    conversation_text = '\n\n'.join([
        f"{'Agent' if t['role'] == 'agent' else 'Candidate'}: {t['message']}"
        for t in transcript
    ])
    summary = raw_data.get('analysis', {}).get('transcript_summary', '')
    duration = raw_data.get('metadata', {}).get('call_duration_secs', 0)
    
    return {
        'conversation_text': conversation_text,
        'conversation_summary': summary,
        'duration_seconds': duration,
        'total_turns': len(transcript)
    }
