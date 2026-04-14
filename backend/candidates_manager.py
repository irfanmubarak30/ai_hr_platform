import json
import os
import uuid
from datetime import datetime

CANDIDATES_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'candidates.json')
SCRAPED_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'scraped_profiles.json')

def _load(filepath):
    if not os.path.exists(filepath):
        return []
    with open(filepath, 'r') as f:
        return json.load(f)

def _save(filepath, data):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

# ─── Email Candidates ────────────────────────────────────────────────────────

def get_all_candidates():
    return _load(CANDIDATES_FILE)

def save_all_candidates(candidates):
    _save(CANDIDATES_FILE, candidates)

def get_candidate_by_id(cid):
    return next((c for c in _load(CANDIDATES_FILE) if c['id'] == cid), None)

def save_candidate(evaluation_result, cv_drive_url=None, email_subject=None):
    candidates = _load(CANDIDATES_FILE)
    candidate = {
        'id': str(uuid.uuid4()),
        'created_at': datetime.now().isoformat(),
        'source': 'email',
        'cv_url': cv_drive_url,
        'email_subject': email_subject,
        **evaluation_result
    }
    candidates.append(candidate)
    _save(CANDIDATES_FILE, candidates)
    return candidate

def update_candidate(cid, updates):
    candidates = _load(CANDIDATES_FILE)
    for c in candidates:
        if c['id'] == cid:
            c.update(updates)
    _save(CANDIDATES_FILE, candidates)

def delete_candidate(cid):
    """Remove a candidate by ID."""
    candidates = _load(CANDIDATES_FILE)
    candidates = [c for c in candidates if c['id'] != cid]
    _save(CANDIDATES_FILE, candidates)

def get_stats():
    candidates = _load(CANDIDATES_FILE)
    scraped = _load(SCRAPED_FILE)
    from backend.job_manager import get_all_jobs
    jobs = get_all_jobs()
    
    shortlisted = [c for c in candidates if c.get('fit_score', {}).get('breakdown', {}).get('Status') == 'appoint']
    rejected = [c for c in candidates if c.get('fit_score', {}).get('breakdown', {}).get('Status') == 'reject']
    
    return {
        'total_jobs': len([j for j in jobs if j.get('status') == 'open']),
        'total_applications': len(candidates),
        'shortlisted': len(shortlisted),
        'rejected': len(rejected),
        'scraped_profiles': len(scraped)
    }

# ─── Scraped Candidates ───────────────────────────────────────────────────────

def get_scraped_profiles():
    return _load(SCRAPED_FILE)

def save_scraped_profile(profile_data, ai_evaluation=None):
    profiles = _load(SCRAPED_FILE)
    profile = {
        'id': str(uuid.uuid4()),
        'created_at': datetime.now().isoformat(),
        'source': 'linkedin',
        **profile_data
    }
    if ai_evaluation:
        profile['ai_evaluation'] = ai_evaluation
    profiles.append(profile)
    _save(SCRAPED_FILE, profiles)
    return profile

def delete_scraped_profile(profile_id):
    """Remove a scraped profile by ID."""
    profiles = _load(SCRAPED_FILE)
    profiles = [p for p in profiles if p['id'] != profile_id]
    _save(SCRAPED_FILE, profiles)

def get_recent_activity(limit=10):
    candidates = _load(CANDIDATES_FILE)
    candidates.sort(key=lambda c: c.get('created_at', ''), reverse=True)
    return candidates[:limit]
