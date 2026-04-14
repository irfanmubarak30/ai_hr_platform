import json
import os
from backend.config import config

try:
    from google.oauth2.credentials import Credentials
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

SHEET_HEADERS = [
    'ID', 'First Name', 'Last Name', 'Email', 'Phone',
    'Position', 'Overall Summary', 'Final Score', 'Status',
    'Experience Score', 'Skills Score', 'Achievements Score', 'Education Score',
    'Draft Email', 'Source', 'Created At', 'Conversation Transcript', 'Conversation Summary'
]

from backend.google_auth import get_credentials

def _get_service():
    if not GOOGLE_AVAILABLE:
        return None
    
    try:
        # Priority 1: OAuth2 User Token (Unified via google_auth)
        if config.USE_OAUTH2:
            creds = get_credentials()
            if creds:
                return build('sheets', 'v4', credentials=creds)
            
        # Priority 2: Service Account
        if config.GOOGLE_SHEETS_CREDENTIALS_FILE and os.path.exists(config.GOOGLE_SHEETS_CREDENTIALS_FILE):
            creds = service_account.Credentials.from_service_account_file(
                config.GOOGLE_SHEETS_CREDENTIALS_FILE, scopes=SCOPES
            )
            return build('sheets', 'v4', credentials=creds)
            
        return None
    except Exception as e:
        print(f"Sheets service error: {e}")
        return None

def ensure_headers(service):
    """Make sure the sheet has headers in row 1."""
    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=config.GOOGLE_SHEETS_ID, range='A1:R1'
        ).execute()
        if not result.get('values'):
            service.spreadsheets().values().update(
                spreadsheetId=config.GOOGLE_SHEETS_ID,
                range='A1', valueInputOption='RAW',
                body={'values': [SHEET_HEADERS]}
            ).execute()
    except Exception as e:
        print(f"Header error: {e}")

def save_candidate_to_sheet(candidate):
    """Append a candidate row to Google Sheets."""
    service = _get_service()
    if not service or not config.GOOGLE_SHEETS_ID:
        print("Google Sheets not configured — skipping sheet save")
        return False
    
    try:
        ensure_headers(service)
        c = candidate
        breakdown = c.get('fit_score', {}).get('breakdown', {})
        summary_data = c.get('summary', {})
        cand_info = c.get('candidate', {})
        
        row = [
            c.get('id', ''),
            cand_info.get('first_name', c.get('first_name', '')),
            cand_info.get('last_name', c.get('last_name', '')),
            cand_info.get('email', c.get('email', '')),
            cand_info.get('phone', c.get('phone', '')),
            c.get('selected_position', {}).get('position_name', ''),
            summary_data.get('overall_summary', ''),
            c.get('fit_score', {}).get('overall', 0),
            breakdown.get('Status', ''),
            breakdown.get('experience', 0),
            breakdown.get('technical_skills', 0),
            breakdown.get('achievements', 0),
            breakdown.get('education', 0),
            summary_data.get('draft_mail', ''),
            c.get('source', 'email'),
            c.get('created_at', ''),
            c.get('conversation_transcript', ''),
            c.get('conversation_summary', '')
        ]
        
        response = service.spreadsheets().values().append(
            spreadsheetId=config.GOOGLE_SHEETS_ID,
            range='A1', valueInputOption='RAW',
            insertDataOption='INSERT_ROWS',
            body={'values': [row]}
        ).execute()
        print(f"DEBUG: Google Sheets Response: {response}")
        return True
    except Exception as e:
        print(f"Sheet save error: {e}")
        return False

def update_conversation(candidate_id, transcript, summary):
    """Update conversation data for a candidate in sheets."""
    service = _get_service()
    if not service or not config.GOOGLE_SHEETS_ID:
        return False
    
    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=config.GOOGLE_SHEETS_ID, range='A:A'
        ).execute()
        rows = result.get('values', [])
        for i, row in enumerate(rows):
            if row and row[0] == candidate_id:
                service.spreadsheets().values().update(
                    spreadsheetId=config.GOOGLE_SHEETS_ID,
                    range=f'Q{i+1}:R{i+1}', valueInputOption='RAW',
                    body={'values': [[transcript, summary]]}
                ).execute()
                return True
    except Exception as e:
        print(f"Update conversation error: {e}")
    return False

def clear_all_candidates():
    """Clear all data from the spreadsheet except headers."""
    service = _get_service()
    if not service or not config.GOOGLE_SHEETS_ID:
        return False
    
    try:
        # Clear everything from row 2 onwards
        service.spreadsheets().values().clear(
            spreadsheetId=config.GOOGLE_SHEETS_ID,
            range='A2:R1000'
        ).execute()
        return True
    except Exception as e:
        print(f"Clear sheet error: {e}")
        return False
