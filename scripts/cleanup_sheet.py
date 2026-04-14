
import os
import sys

# Add parent directory to path to import backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend import google_sheets_service
from backend.config import config

def cleanup_sheet():
    print(f"Cleaning Google Sheet: {config.GOOGLE_SHEETS_ID}")
    try:
        service = google_sheets_service._get_service()
        if not service:
            print("❌ Could not get Sheets service.")
            return
            
        # We want to keep the header (row 1), so we clear everything from A2 onwards
        # Using a large range to ensure everything is caught
        range_name = 'A2:Z1000'
        
        service.spreadsheets().values().clear(
            spreadsheetId=config.GOOGLE_SHEETS_ID,
            range=range_name
        ).execute()
        
        print("Done: Sheet cleared successfully (headers preserved).")
            
    except Exception as e:
        print(f"Error cleaning sheet: {e}")

if __name__ == "__main__":
    cleanup_sheet()
