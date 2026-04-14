"""
Availability Manager
- HR defines recurring weekly slots (day + start + end)
- When a candidate is appointed, auto-books next free slot
- Returns booked slots so scheduler can trigger calls at the right time
"""

import json
import os
from datetime import datetime, date, timedelta

AVAILABILITY_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'availability.json')
BOOKED_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'booked_slots.json')

DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

# ─── Weekly Template Slots ────────────────────────────────────────────────────

def _load(path, default):
    if not os.path.exists(path):
        return default
    with open(path) as f:
        return json.load(f)

def _save(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def get_weekly_slots():
    """Return list of recurring weekly slot templates."""
    return _load(AVAILABILITY_FILE, [])

def save_weekly_slots(slots):
    """
    slots: list of {
        id, day_of_week (0=Mon..6=Sun), start_time (HH:MM), end_time (HH:MM),
        duration_minutes, active
    }
    """
    _save(AVAILABILITY_FILE, slots)

def add_slot(day_of_week: int, start_time: str, end_time: str, duration_minutes: int = 60):
    import uuid
    slots = get_weekly_slots()
    slot = {
        'id': str(uuid.uuid4()),
        'day_of_week': day_of_week,
        'day_name': DAYS[day_of_week],
        'start_time': start_time,
        'end_time': end_time,
        'duration_minutes': duration_minutes,
        'active': True
    }
    slots.append(slot)
    _save(AVAILABILITY_FILE, slots)
    return slot

def remove_slot(slot_id: str):
    slots = [s for s in get_weekly_slots() if s['id'] != slot_id]
    _save(AVAILABILITY_FILE, slots)

def toggle_slot(slot_id: str, active: bool):
    slots = get_weekly_slots()
    for s in slots:
        if s['id'] == slot_id:
            s['active'] = active
    _save(AVAILABILITY_FILE, slots)

# ─── Booked Slots ─────────────────────────────────────────────────────────────

def get_booked_slots():
    return _load(BOOKED_FILE, [])

def _is_slot_taken(date_str: str, start_time: str) -> bool:
    booked = get_booked_slots()
    return any(b['date'] == date_str and b['start_time'] == start_time for b in booked)

def book_slot(candidate_id: str, candidate_name: str, position: str,
              date_str: str, start_time: str, end_time: str, calendar_event_id: str = ''):
    import uuid
    booked = get_booked_slots()
    entry = {
        'id': str(uuid.uuid4()),
        'candidate_id': candidate_id,
        'candidate_name': candidate_name,
        'position': position,
        'date': date_str,
        'start_time': start_time,
        'end_time': end_time,
        'calendar_event_id': calendar_event_id,
        'call_triggered': False,
        'call_completed': False,
        'booked_at': datetime.now().isoformat()
    }
    booked.append(entry)
    _save(BOOKED_FILE, booked)
    return entry

def mark_call_triggered(booking_id: str):
    booked = get_booked_slots()
    for b in booked:
        if b['id'] == booking_id:
            b['call_triggered'] = True
            b['triggered_at'] = datetime.now().isoformat()
    _save(BOOKED_FILE, booked)

def mark_call_completed(booking_id: str, conversation_id: str = ''):
    booked = get_booked_slots()
    for b in booked:
        if b['id'] == booking_id:
            b['call_completed'] = True
            b['conversation_id'] = conversation_id
            b['completed_at'] = datetime.now().isoformat()
    _save(BOOKED_FILE, booked)

def mark_call_failed(booking_id: str, error_msg: str):
    booked = get_booked_slots()
    for b in booked:
        if b['id'] == booking_id:
            b['call_triggered'] = False  # Reset so it can be re-triggered or just marked as error
            b['call_failed'] = True
            b['error_message'] = error_msg
            b['failed_at'] = datetime.now().isoformat()
    _save(BOOKED_FILE, booked)

# ─── Auto-booking: Find next free slot ───────────────────────────────────────

def find_and_book_next_slot(candidate_id: str, candidate_name: str, position: str,
                             candidate_email: str = '', days_ahead: int = 30):
    """
    Scan weekly templates from today onwards for the next free slot.
    Returns the booked slot dict, or None if no slots available.
    """
    from backend import calendar_service

    weekly = [s for s in get_weekly_slots() if s.get('active', True)]
    if not weekly:
        print("DEBUG: No active availability slots found in availability.json")
        return None

    today = date.today()

    for offset in range(days_ahead):
        check_date = today + timedelta(days=offset)
        weekday = check_date.weekday()  # 0=Mon

        for slot in weekly:
            if slot['day_of_week'] != weekday:
                continue

            date_str = check_date.strftime('%Y-%m-%d')
            start_t = slot['start_time']
            end_t = slot['end_time']

            # Skip slots in the past (today only)
            if offset == 0:
                now_time = datetime.now().strftime('%H:%M')
                if start_t <= now_time:
                    continue

            if _is_slot_taken(date_str, start_t):
                continue

            # Found a free slot — create calendar event
            event = calendar_service.schedule_interview(
                candidate_name=candidate_name,
                candidate_email=candidate_email,
                position=position,
                date=date_str,
                start_time=start_t,
                end_time=end_t,
                meeting_type='online'
            )

            event_id = event.get('id', '') if isinstance(event, dict) else ''

            booked = book_slot(
                candidate_id=candidate_id,
                candidate_name=candidate_name,
                position=position,
                date_str=date_str,
                start_time=start_t,
                end_time=end_t,
                calendar_event_id=event_id
            )
            booked['calendar_event'] = event
            return booked

    return None  # No free slot found in window

# ─── Scheduler: find interviews due RIGHT NOW ─────────────────────────────────

def get_due_interviews(tolerance_minutes: int = 2):
    """
    Return booked slots whose scheduled time is within `tolerance_minutes` of now
    and whose call has not been triggered yet.
    """
    now = datetime.now()
    now_date = now.strftime('%Y-%m-%d')
    now_time_str = now.strftime('%H:%M')

    due = []
    for b in get_booked_slots():
        if b.get('call_triggered'):
            continue
        if b['date'] != now_date:
            continue

        # Compare times
        slot_dt = datetime.strptime(f"{b['date']} {b['start_time']}", '%Y-%m-%d %H:%M')
        diff = (now - slot_dt).total_seconds() / 60  # positive = past, negative = future

        if -tolerance_minutes <= diff <= tolerance_minutes:
            due.append(b)

    return due

def get_upcoming_interviews(limit: int = 20):
    """Return future booked slots sorted by date/time."""
    now = datetime.now()
    upcoming = []
    for b in get_booked_slots():
        try:
            slot_dt = datetime.strptime(f"{b['date']} {b['start_time']}", '%Y-%m-%d %H:%M')
            if slot_dt >= now:
                upcoming.append({**b, '_dt': slot_dt.isoformat()})
        except Exception:
            pass
    upcoming.sort(key=lambda x: x['_dt'])
    return upcoming[:limit]

def delete_booking_by_candidate_id(candidate_id):
    """Remove booking for a candidate and delete their calendar event."""
    from backend import calendar_service
    booked = get_booked_slots()
    
    # Find and delete calendar event if it exists
    for b in booked:
        if b['candidate_id'] == candidate_id:
            event_id = b.get('calendar_event_id')
            if event_id:
                calendar_service.delete_event(event_id)
    
    # Remove from local JSON
    new_booked = [b for b in booked if b['candidate_id'] != candidate_id]
    if len(new_booked) != len(booked):
        _save(BOOKED_FILE, new_booked)
        return True
    return False
