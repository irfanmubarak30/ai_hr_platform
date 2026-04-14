
import os
import sys

# Add parent directory to path to import backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend import email_listener

def get_current_user():
    service = email_listener._get_gmail_service()
    if not service:
        print("Could not get Gmail service.")
        return
    
    try:
        profile = service.users().getProfile(userId='me').execute()
        print(f"Current authorized email: {profile['emailAddress']}")
    except Exception as e:
        print(f"Error getting profile: {e}")

if __name__ == "__main__":
    get_current_user()
