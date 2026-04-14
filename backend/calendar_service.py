import os
from backend.config import config
from datetime import datetime

try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False

SCOPES = ['https://www.googleapis.com/auth/calendar']

from backend.google_auth import get_credentials

def _get_service():
    if not GOOGLE_AVAILABLE:
        return None
    
    try:
        # Priority 1: OAuth2 User Token (Unified via google_auth)
        if config.USE_OAUTH2:
            creds = get_credentials()
            if creds:
                return build('calendar', 'v3', credentials=creds)
            
        # Priority 2: Service Account
        if config.GOOGLE_CALENDAR_CREDENTIALS_FILE and os.path.exists(config.GOOGLE_CALENDAR_CREDENTIALS_FILE):
            creds = service_account.Credentials.from_service_account_file(
                config.GOOGLE_CALENDAR_CREDENTIALS_FILE, scopes=SCOPES
            )
            return build('calendar', 'v3', credentials=creds)
            
        return None
    except Exception as e:
        print(f"Calendar search error: {e}")
        return []

def delete_event(event_id):
    """Delete a Google Calendar event by ID."""
    if not event_id:
        return False
    service = _get_service()
    if not service:
        return False
    try:
        service.events().delete(calendarId='primary', eventId=event_id).execute()
        return True
    except Exception as e:
        print(f"Calendar delete error: {e}")
        return False

def schedule_interview(candidate_name, candidate_email, position, date, start_time, end_time, meeting_type="online"):
    """Create a Google Calendar event for an interview."""
    service = _get_service()
    
    # Build datetime strings
    try:
        start_dt = datetime.strptime(f"{date} {start_time}", "%Y-%m-%d %H:%M").isoformat()
        end_dt = datetime.strptime(f"{date} {end_time}", "%Y-%m-%d %H:%M").isoformat()
    except ValueError:
        start_dt = f"{date}T{start_time}:00"
        end_dt = f"{date}T{end_time}:00"

    event_body = {
        'summary': f"Interview with {candidate_name} – {position} Role",
        'description': f"""
Interview Details:
• Candidate: {candidate_name}
• Position: {position}
• Type: Office Phone Call

There will be a call FROM THE OFFICE at this scheduled time. Please be available at your provided phone number.

This interview has been scheduled by {config.RECRUITER_NAME} at {config.COMPANY_NAME}.
        """.strip(),
        'start': {'dateTime': start_dt, 'timeZone': 'UTC'},
        'end': {'dateTime': end_dt, 'timeZone': 'UTC'},
        'attendees': [
            {'email': candidate_email},
            {'email': config.COMPANY_EMAIL}
        ]
    }
    
    if not service:
        # Return mock event for demo
        return {
            'id': f"mock-event-{candidate_email}",
            'htmlLink': 'https://calendar.google.com/calendar/event?mock=true',
            'summary': event_body['summary'],
            'status': 'confirmed',
            'mock': True
        }
    
    try:
        event = service.events().insert(
            calendarId='primary',
            body=event_body,
            conferenceDataVersion=0,
            sendUpdates='all'
        ).execute()
        return event
    except Exception as e:
        print(f"Calendar event error: {e}")
        return {'error': str(e)}

def cleanup_calendar_events():
    """Delete upcoming events scheduled by Ligenix."""
    service = _get_service()
    if not service:
        return False
        
    try:
        # Get upcoming events
        now = datetime.utcnow().isoformat() + 'Z'
        events_result = service.events().list(
            calendarId='primary', timeMin=now,
            maxResults=50, singleEvents=True,
            orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])
        
        deleted_count = 0
        for event in events:
            summary = event.get('summary', '')
            description = event.get('description', '')
            # Match our signature
            if "Ligenix" in summary or "Ligenix" in description or "Interview with" in summary:
                service.events().delete(calendarId='primary', eventId=event['id']).execute()
                deleted_count += 1
        
        print(f"Deleted {deleted_count} calendar events.")
        return True
    except Exception as e:
        print(f"Calendar cleanup error: {e}")
        return False
