import os
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from backend.config import config

# Unified scopes for all Google services used by the platform
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/drive'
]

def get_credentials():
    """Get valid user credentials from storage or by running the OAuth2 flow."""
    creds = None
    
    # Load existing token if available
    if os.path.exists(config.OAUTH2_TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(config.OAUTH2_TOKEN_FILE, SCOPES)
        except Exception as e:
            print(f"Error loading OAuth2 token: {e}")
            creds = None

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Error refreshing OAuth2 token: {e}")
                creds = None
        
        if not creds:
            if not os.path.exists(config.OAUTH2_CREDENTIALS_FILE):
                raise FileNotFoundError(f"Missing OAuth2 credentials file: {config.OAUTH2_CREDENTIALS_FILE}")
                
            flow = InstalledAppFlow.from_client_secrets_file(config.OAUTH2_CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
            
        # Save the credentials for the next run
        with open(config.OAUTH2_TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
            
    return creds
