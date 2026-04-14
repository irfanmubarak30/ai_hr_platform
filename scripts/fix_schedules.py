
import os
import sys

# Add parent directory to path to import backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend import candidates_manager, availability_manager

def fix_unscheduled_candidates():
    candidates = candidates_manager.get_all_candidates()
    appointed_unscheduled = [
        c for c in candidates 
        if c.get('fit_score', {}).get('breakdown', {}).get('Status') == 'appoint' 
        and not c.get('interview_scheduled')
    ]
    
    if not appointed_unscheduled:
        print("No unscheduled 'appoint' candidates found.")
        return

    print(f"Found {len(appointed_unscheduled)} appointed candidates without a schedule. Attempting to book slots...")
    
    for c in appointed_unscheduled:
        name = f"{c.get('candidate', {}).get('first_name', '')} {c.get('candidate', {}).get('last_name', '')}".strip()
        print(f"Booking for: {name} ({c['id']})")
        
        booking = availability_manager.find_and_book_next_slot(
            candidate_id=c['id'],
            candidate_name=name,
            position=c.get('selected_position', {}).get('position_name', ''),
            candidate_email=c.get('candidate', {}).get('email', '')
        )
        
        if booking:
            candidates_manager.update_candidate(c['id'], {
                'interview_scheduled': True,
                'interview_date': booking['date'],
                'interview_time': booking['start_time'],
                'booking_id': booking['id'],
                'calendar_event_id': booking.get('calendar_event_id', '')
            })
            print(f"  [SUCCESS] Scheduled for {booking['date']} at {booking['start_time']}")
        else:
            print(f"  [FAILED] No available slots found in the next 30 days for {name}")

if __name__ == "__main__":
    fix_unscheduled_candidates()
