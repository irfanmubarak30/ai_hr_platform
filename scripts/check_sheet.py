
import os
import sys

# Add parent directory to path to import backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend import google_sheets_service

def check_sheet():
    print("Checking Google Sheet for latest candidates...")
    try:
        service = google_sheets_service._get_service()
        if not service:
            print("❌ Could not get Sheets service.")
            return
            
        from backend.config import config
        result = service.spreadsheets().values().get(
            spreadsheetId=config.GOOGLE_SHEETS_ID,
            range='A1:Z100'
        ).execute()
        
        values = result.get('values', [])
        if not values:
            print("📭 Sheet is empty.")
            return

        print(f"Found {len(values)} rows in sheet.")
        print("Last 3 rows:")
        for row in values[-3:]:
            print(f" - {row}")
            
    except Exception as e:
        print(f"❌ Error checking sheet: {e}")

if __name__ == "__main__":
    check_sheet()
