
import os
import sys

# Add parent directory to path to import backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend import email_listener

def diagnose_gmail_filters():
    print("Diagnosing Gmail Filters...")
    service = email_listener._get_gmail_service()
    if not service:
        print("❌ Could not get Gmail service.")
        return
    
    try:
        # 1. List Labels
        print("\n1. Listing user labels:")
        labels_results = service.users().labels().list(userId='me').execute()
        labels = labels_results.get('labels', [])
        processed_label_exists = False
        for label in labels:
            print(f" - {label['name']}")
            if label['name'].lower() == 'processed':
                processed_label_exists = True
        
        # 2. Test the specific query
        query = 'has:attachment filename:pdf -label:processed'
        print(f"\n2. Testing query: {query}")
        results = service.users().messages().list(userId='me', q=query, maxResults=5).execute()
        messages = results.get('messages', [])
        print(f"   Found {len(messages)} messages matching this query.")
        
        # 3. Test a broader query
        query_broad = 'has:attachment pdf'
        print(f"\n3. Testing broader query: {query_broad}")
        results_broad = service.users().messages().list(userId='me', q=query_broad, maxResults=5).execute()
        messages_broad = results_broad.get('messages', [])
        print(f"   Found {len(messages_broad)} messages matching broader query.")
        
        for msg_ref in messages_broad:
            msg = service.users().messages().get(userId='me', id=msg_ref['id'], format='metadata').execute()
            headers = {h['name'].lower(): h['value'] for h in msg.get('payload', {}).get('headers', [])}
            print(f"   - ID: {msg_ref['id']} | Subject: {headers.get('subject')} | Labels: {msg.get('labelIds')}")

    except Exception as e:
        print(f"❌ Diagnostic error: {e}")

if __name__ == "__main__":
    diagnose_gmail_filters()
