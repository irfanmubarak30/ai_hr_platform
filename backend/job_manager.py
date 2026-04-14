import json
import os
import uuid
from datetime import datetime

DATA_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'jobs.json')

def _load_jobs():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_jobs(jobs):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, 'w') as f:
        json.dump(jobs, f, indent=2)

def get_all_jobs():
    return _load_jobs()

def get_open_jobs():
    return [j for j in _load_jobs() if j.get('status') == 'open']

def get_job_by_id(job_id):
    jobs = _load_jobs()
    return next((j for j in jobs if j['id'] == job_id), None)

def create_job(data):
    jobs = _load_jobs()
    job = {
        'id': str(uuid.uuid4()),
        'title': data.get('title', ''),
        'department': data.get('department', ''),
        'description': data.get('description', ''),
        'skills': data.get('skills', []),
        'min_experience': data.get('min_experience', 0),
        'salary_range': data.get('salary_range', ''),
        'location': data.get('location', ''),
        'employment_type': data.get('employment_type', 'Full-time'),
        'status': 'open',
        'created_at': datetime.now().isoformat(),
        'applications': 0
    }
    jobs.append(job)
    save_jobs(jobs)
    return job

def update_job_status(job_id, status):
    jobs = _load_jobs()
    for job in jobs:
        if job['id'] == job_id:
            job['status'] = status
            break
    save_jobs(jobs)

def increment_applications(job_id):
    jobs = _load_jobs()
    for job in jobs:
        if job['id'] == job_id:
            job['applications'] = job.get('applications', 0) + 1
            break
    save_jobs(jobs)

def generate_job_announcement(job):
    skills_text = '\n'.join([f'• {s}' for s in job.get('skills', [])])
    return f"""🚀 We Are Hiring!

Position: {job['title']}
Department: {job['department']}
Location: {job['location']}
Type: {job['employment_type']}
Salary: {job['salary_range']}

About the Role:
{job['description']}

Requirements:
{skills_text}
• Minimum {job['min_experience']}+ years of experience

Interested? Send your CV to {os.getenv('COMPANY_EMAIL', 'careers@ligenix.com')}

#{job['title'].replace(' ', '')} #Hiring #{job['department']} #Jobs"""
