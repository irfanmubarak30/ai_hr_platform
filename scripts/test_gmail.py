
import os
import sys
import base64

# Add parent directory to path to import backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend import email_listener

def debug_gmail():
    print("Fetching last 10 messages to see why listener might be missing your email...")
    service = email_listener._get_gmail_service()
    if not service:
        print("❌ Could not get Gmail service.")
        return
    
    try:
        # Search widely first
        results = service.users().messages().list(userId='me', maxResults=10).execute()
        messages = results.get('messages', [])
        
        if not messages:
            print("📭 No messages found at all in the account.")
            return

        print(f"Found {len(messages)} recent messages. Checking details...")
        for msg_ref in messages:
            msg = service.users().messages().get(userId='me', id=msg_ref['id'], format='metadata').execute()
            headers = {h['name'].lower(): h['value'] for h in msg.get('payload', {}).get('headers', [])}
            subject = headers.get('subject', 'No Subject')
            sender = headers.get('from', 'Unknown Sender')
            snippet = msg.get('snippet', '')
            
            # Check for attachments in full format
            full_msg = service.users().messages().get(userId='me', id=msg_ref['id'], format='full').execute()
            parts = email_listener._get_parts(full_msg.get('payload', {}))
            has_pdf = any(p.get('mimeType') == 'application/pdf' for p in parts)
            
            print(f"\n--- Message ID: {msg_ref['id']} ---")
            print(f"From: {sender}")
            print(f"Subject: {subject}")
            print(f"Has PDF: {'Yes' if has_pdf else 'No'}")
            print(f"Snippet: {snippet[:100]}...")
            
    except Exception as e:
        print(f"Error during debug: {e}")

if __name__ == "__main__":
    debug_gmail()
