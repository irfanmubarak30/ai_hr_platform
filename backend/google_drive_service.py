import io
import os
from backend.config import config

try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseUpload
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False

SCOPES = ['https://www.googleapis.com/auth/drive']

from backend.google_auth import get_credentials

def _get_service():
    if not GOOGLE_AVAILABLE:
        return None
    
    try:
        # Priority 1: OAuth2 User Token (Unified via google_auth)
        if config.USE_OAUTH2:
            creds = get_credentials()
            if creds:
                return build('drive', 'v3', credentials=creds)
            
        # Priority 2: Service Account (Requires storage quota)
        if config.GOOGLE_DRIVE_CREDENTIALS_FILE and os.path.exists(config.GOOGLE_DRIVE_CREDENTIALS_FILE):
            creds = service_account.Credentials.from_service_account_file(
                config.GOOGLE_DRIVE_CREDENTIALS_FILE, scopes=SCOPES
            )
            return build('drive', 'v3', credentials=creds)
            
        return None
    except Exception as e:
        print(f"Drive service error: {e}")
        return None

def upload_cv(file_bytes, filename, candidate_email=""):
    """Upload a CV file to Google Drive and return the web link."""
    service = _get_service()
    if not service:
        print("Google Drive not configured — returning placeholder URL")
        return f"https://drive.google.com/placeholder/{filename}"
    
    try:
        folder_id = config.GOOGLE_DRIVE_FOLDER_ID
        metadata = {'name': f"{candidate_email}_{filename}", 'mimeType': 'application/pdf'}
        if folder_id:
            metadata['parents'] = [folder_id]
        
        media = MediaIoBaseUpload(io.BytesIO(file_bytes), mimetype='application/pdf')
        file = service.files().create(
            body=metadata, media_body=media, fields='id,webContentLink,webViewLink'
        ).execute()
        
        # Make it publicly readable
        service.permissions().create(
            fileId=file['id'],
            body={'type': 'anyone', 'role': 'reader'}
        ).execute()
        
        return file.get('webViewLink', file.get('webContentLink', ''))
    except Exception as e:
        print(f"Drive upload error: {e}")
        return ""
