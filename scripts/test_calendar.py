import os
import sys
from datetime import datetime, timedelta

# Add parent directory to path to import backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend import calendar_service

def test_calendar():
    print("Testing Google Calendar integration...")
    
    # Mock candidate data
    candidate_name = "Test Candidate"
    candidate_email = "test@example.com"
    position = "Software Engineer"
    
    # Schedule for 1 hour from now
    now = datetime.now()
    test_date = now.strftime("%Y-%m-%d")
    start_time = (now + timedelta(hours=1)).strftime("%H:%M")
    end_time = (now + timedelta(hours=1, minutes=30)).strftime("%H:%M")
    
    print(f"Attempting to schedule interview for {candidate_name} on {test_date} at {start_time}...")
    
    try:
        event = calendar_service.schedule_interview(
            candidate_name=candidate_name,
            candidate_email=candidate_email,
            position=position,
            date=test_date,
            start_time=start_time,
            end_time=end_time
        )
        
        if 'error' in event:
            print(f"[ERROR] Calendar error: {event['error']}")
        elif event.get('mock'):
            print("[WARNING] Service returned a MOCK event. Check authentication/credentials.")
            print(f"Mock Link: {event.get('htmlLink')}")
        else:
            print(f"[SUCCESS] Event created.")
            print(f"Event ID: {event.get('id')}")
            print(f"Event Link: {event.get('htmlLink')}")
            
    except Exception as e:
        print(f"[EXCEPTION] Exception during calendar test: {e}")

if __name__ == "__main__":
    test_calendar()
