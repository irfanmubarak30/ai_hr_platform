import json
import os

def clear_transcripts():
    data_path = os.path.join('data', 'candidates.json')
    if not os.path.exists(data_path):
        print("Candidates file not found.")
        return

    with open(data_path, 'r') as f:
        candidates = json.load(f)

    fields_to_clear = [
        'interview_completed',
        'conversation_id',
        'conversation_text',
        'conversation_summary',
        'recording_url',
        'call_duration_seconds',
        'interview_status',
        'predicted_emotion',
        'behavior_confidence',
        'behavioral_summary_rich',
        'updated_at'
    ]

    cleared_count = 0
    for c in candidates:
        if any(field in c for field in fields_to_clear):
            for field in fields_to_clear:
                if field in c:
                    del c[field]
            cleared_count += 1

    with open(data_path, 'w') as f:
        json.dump(candidates, f, indent=2)

    print(f"Successfully cleared transcript data from {cleared_count} candidates.")

if __name__ == "__main__":
    clear_transcripts()
