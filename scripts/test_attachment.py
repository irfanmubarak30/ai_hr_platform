
import os
import sys
import base64

# Add parent directory to path to import backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend import email_listener

def debug_attachment_extraction():
    print("Debugging attachment extraction...")
    service = email_listener._get_gmail_service()
    if not service:
        print("❌ Could not get Gmail service.")
        return
    
    try:
        # Search for the specific email from the user
        query = 'has:attachment pdf "Am intrested in job"'
        results = service.users().messages().list(userId='me', q=query).execute()
        messages = results.get('messages', [])
        
        if not messages:
            print("📭 Message not found with that query.")
            return

        msg_id = messages[0]['id']
        print(f"Checking message ID: {msg_id}")
        
        msg = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
        payload = msg.get('payload', {})
        parts = email_listener._get_parts(payload)
        
        for part in parts:
            mime_type = part.get('mimeType')
            filename = part.get('filename')
            body = part.get('body', {})
            data = body.get('data')
            attach_id = body.get('attachmentId')
            
            print(f"\nPart: {mime_type} | Filename: {filename}")
            print(f" - Has data field: {'Yes' if data else 'No'}")
            print(f" - Has attachmentId: {'Yes' if attach_id else 'No'}")
            
            if attach_id and not data:
                print(" ⚠️ Found attachmentId but NO data. Fetching manually...")
                attachment = service.users().messages().attachments().get(
                    userId='me', messageId=msg_id, id=attach_id
                ).execute()
                actual_data = attachment.get('data')
                print(f" - Manually fetched data length: {len(actual_data) if actual_data else '0'}")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_attachment_extraction()
