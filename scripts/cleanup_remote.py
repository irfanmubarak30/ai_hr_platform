import os
import sys

# Add the project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.google_sheets_service import clear_all_candidates
from backend.calendar_service import cleanup_calendar_events

def run_cleanup():
    print("--- Remote Data Cleanup ---")
    
    # Sheets
    print("\n1. Clearing Google Sheets candidates...")
    try:
        if clear_all_candidates():
            print("[SUCCESS] Google Sheets cleared (headers preserved).")
        else:
            print("[FAILED] Failed to clear Google Sheets.")
    except Exception as e:
        print(f"[ERROR] Sheets cleanup failed: {e}")
        
    # Calendar
    print("\n2. Cleaning up Google Calendar interviews...")
    try:
        if cleanup_calendar_events():
            print("[SUCCESS] Upcoming Ligenix interviews deleted.")
        else:
            print("[FAILED] Failed to cleanup Google Calendar.")
    except Exception as e:
        print(f"[ERROR] Calendar cleanup failed: {e}")
        
    print("\n--- Remote Cleanup Finished ---")

if __name__ == "__main__":
    run_cleanup()
