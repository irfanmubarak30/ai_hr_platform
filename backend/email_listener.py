import base64
import json
import os
import threading
import time
from backend.config import config

try:
    from google.oauth2.credentials import Credentials
    from google.oauth2 import service_account
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.modify']
PROCESSED_IDS_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'processed_emails.json')

_listener_active = False
_listener_thread = None

def _load_processed():
    if not os.path.exists(PROCESSED_IDS_FILE):
        return set()
    with open(PROCESSED_IDS_FILE) as f:
        return set(json.load(f))

def _save_processed(ids):
    os.makedirs(os.path.dirname(PROCESSED_IDS_FILE), exist_ok=True)
    with open(PROCESSED_IDS_FILE, 'w') as f:
        json.dump(list(ids), f)

from backend.google_auth import get_credentials

def _get_oauth2_credentials():
    """Get OAuth2 credentials for personal Gmail account."""
    return get_credentials()

def _get_gmail_service():
    """Get Gmail service using either OAuth2 (personal) or Service Account (Workspace)."""
    if not GOOGLE_AVAILABLE:
        return None
    
    # Try OAuth2 first if enabled
    if config.USE_OAUTH2:
        try:
            creds = _get_oauth2_credentials()
            if creds:
                return build('gmail', 'v1', credentials=creds)
            else:
                print("OAuth2 credentials not available. Run setup first.")
                return None
        except Exception as e:
            print(f"OAuth2 service error: {e}")
            return None
    
    # Fall back to Service Account
    if not config.GMAIL_CREDENTIALS_FILE:
        return None
    try:
        creds = service_account.Credentials.from_service_account_file(
            config.GMAIL_CREDENTIALS_FILE, scopes=SCOPES
        )
        delegated = creds.with_subject(config.COMPANY_EMAIL)
        return build('gmail', 'v1', credentials=delegated)
    except Exception as e:
        print(f"Gmail service error: {e}")
        return None

def check_for_new_cvs():
    """Check inbox for new CV emails and process them."""
    service = _get_gmail_service()
    if not service:
        return []
    
    processed = _load_processed()
    new_candidates = []
    
    try:
        results = service.users().messages().list(
            userId='me', q='has:attachment filename:pdf -label:processed', maxResults=10
        ).execute()
        
        messages = results.get('messages', [])
        
        for msg_ref in messages:
            if msg_ref['id'] in processed:
                continue
            
            msg = service.users().messages().get(userId='me', id=msg_ref['id'], format='full').execute()
            candidate_data = _process_email(msg, service)
            
            if candidate_data:
                new_candidates.append(candidate_data)
            
            processed.add(msg_ref['id'])
        
        _save_processed(processed)
    except Exception as e:
        print(f"Gmail check error: {e}")
    
    return new_candidates

def _process_email(message, service):
    """Extract CV and info from an email message."""
    payload = message.get('payload', {})
    headers = {h['name'].lower(): h['value'] for h in payload.get('headers', [])}
    
    subject = headers.get('subject', '')
    sender = headers.get('from', '')
    
    # Extract PDF attachment
    parts = _get_parts(payload)
    pdf_bytes = None
    filename = None
    
    for part in parts:
        if part.get('mimeType') == 'application/pdf':
            body = part.get('body', {})
            filename = part.get('filename', 'cv.pdf')
            attachment_id = body.get('attachmentId')
            
            # Fetch data from attachmentId if not directly in the part
            data = body.get('data')
            if not data and attachment_id:
                try:
                    attachment = service.users().messages().attachments().get(
                        userId='me', messageId=message['id'], id=attachment_id
                    ).execute()
                    data = attachment.get('data')
                except Exception as e:
                    print(f"Error fetching attachment {attachment_id}: {e}")
            
            if data:
                pdf_bytes = base64.urlsafe_b64decode(data + '==')
                break # Found the PDF
    
    if not pdf_bytes:
        return None
    
    return {
        'subject': subject,
        'sender': sender,
        'filename': filename,
        'pdf_bytes': pdf_bytes
    }

def _get_parts(payload):
    """Recursively get all message parts."""
    parts = []
    if 'parts' in payload:
        for part in payload['parts']:
            parts.extend(_get_parts(part))
    else:
        parts.append(payload)
    return parts

def start_listener(callback=None):
    """Start background email listening thread."""
    global _listener_active, _listener_thread
    _listener_active = True
    
    def listen_loop():
        while _listener_active:
            try:
                new_cvs = check_for_new_cvs()
                if new_cvs and callback:
                    for cv_data in new_cvs:
                        callback(cv_data)
            except Exception as e:
                print(f"Listener error: {e}")
            time.sleep(60)  # Check every minute
    
    _listener_thread = threading.Thread(target=listen_loop, daemon=True)
    _listener_thread.start()
    print("Email listener started")

def stop_listener():
    global _listener_active
    _listener_active = False
    print("Email listener stopped")

def is_running():
    return _listener_active
