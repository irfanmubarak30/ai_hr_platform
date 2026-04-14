import os
import sys
import json
import logging
from datetime import datetime
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, request, jsonify, send_from_directory

from backend.config import config
from backend import job_manager, candidates_manager, cv_parser, ai_evaluator
from backend import linkedin_scraper, google_sheets_service, google_drive_service
from backend import calendar_service, call_service, email_listener
from backend import availability_manager, interview_scheduler
from backend.voice_analyzer_service import voice_analyzer
from backend.ai_evaluator import generate_behavioral_summary
from backend.interview_scheduler import _extract_behavior_score
from backend.image_service import image_service
from backend.nanobanana_service import nanobanana_service
from backend.linkedin_service import linkedin_service

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static', template_folder='frontend')
app.secret_key = config.SECRET_KEY

@app.after_request
def add_cors(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

@app.route('/')
def index():
    return send_from_directory('frontend', 'dashboard.html')

@app.route('/<path:filename>.html')
def serve_html(filename):
    return send_from_directory('frontend', f'{filename}.html')

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

# ── Dashboard ──────────────────────────────────────────────────────────────────

@app.route('/api/dashboard/stats')
def dashboard_stats():
    stats = candidates_manager.get_stats()
    stats['scheduler_running'] = interview_scheduler.is_running()
    stats['email_listener_running'] = email_listener.is_running()
    return jsonify(stats)

@app.route('/api/dashboard/recent')
def recent_activity():
    return jsonify(candidates_manager.get_recent_activity(10))

@app.route('/api/dashboard/upcoming-interviews')
def upcoming_interviews_api():
    return jsonify(availability_manager.get_upcoming_interviews(10))

@app.route('/api/dashboard/completed-calls')
def completed_calls():
    candidates = candidates_manager.get_all_candidates()
    completed = [c for c in candidates if c.get('interview_completed')]
    completed.sort(key=lambda c: c.get('interview_date', ''), reverse=True)
    return jsonify(completed)

# ── Jobs ───────────────────────────────────────────────────────────────────────

@app.route('/api/jobs', methods=['GET'])
def get_jobs():
    return jsonify(job_manager.get_all_jobs())

@app.route('/api/jobs', methods=['POST'])
def create_job():
    data = request.json
    if not data or not data.get('title'):
        return jsonify({'error': 'Job title is required'}), 400
    skills = data.get('skills', [])
    if isinstance(skills, str):
        skills = [s.strip() for s in skills.split(',') if s.strip()]
    data['skills'] = skills
    job = job_manager.create_job(data)
    
    # Pick image service based on config
    provider = os.environ.get('IMAGE_PROVIDER', 'pollinations').lower()
    active_service = nanobanana_service if provider == 'nanobanana' else image_service
    
    # Generate poster and apply link
    poster_url = active_service.generate_job_poster(job['title'])
    apply_link = active_service.generate_apply_link(job['title'])
    
    # Update job with these details
    job_manager.save_jobs([j if j['id'] != job['id'] else {**j, 'poster_url': poster_url, 'apply_link': apply_link} for j in job_manager.get_all_jobs()])
    
    announcement = job_manager.generate_job_announcement(job)
    return jsonify({'job': {**job, 'poster_url': poster_url, 'apply_link': apply_link}, 'announcement': announcement})

@app.route('/api/jobs/<job_id>/poster', methods=['POST'])
def generate_job_poster(job_id):
    job = job_manager.get_job_by_id(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    
    provider = os.environ.get('IMAGE_PROVIDER', 'pollinations').lower()
    active_service = nanobanana_service if provider == 'nanobanana' else image_service
    
    poster_url = active_service.generate_job_poster(job['title'])
    apply_link = active_service.generate_apply_link(job['title'])
    
    # Update job
    jobs = job_manager.get_all_jobs()
    for j in jobs:
        if j['id'] == job_id:
            j['poster_url'] = poster_url
            j['apply_link'] = apply_link
            break
    job_manager.save_jobs(jobs)
    
    return jsonify({'poster_url': poster_url, 'apply_link': apply_link})

@app.route('/api/jobs/<job_id>/linkedin', methods=['POST'])
def post_job_to_linkedin(job_id):
    job = job_manager.get_job_by_id(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    
    provider = os.environ.get('IMAGE_PROVIDER', 'pollinations').lower()
    active_service = nanobanana_service if provider == 'nanobanana' else image_service
    
    poster_url = job.get('poster_url')
    apply_link = job.get('apply_link') or active_service.generate_apply_link(job['title'])
    
    if not poster_url:
        poster_url = active_service.generate_job_poster(job['title'])
    
    result = linkedin_service.post_job_announcement(
        job['title'], 
        poster_url, 
        apply_link,
        include_image=True
    )
    
    if "error" in result:
        return jsonify({"status": "error", "message": result["error"]}), 200
        
    return jsonify(result)

@app.route('/api/jobs/<job_id>/status', methods=['PUT'])
def update_job_status(job_id):
    job_manager.update_job_status(job_id, request.json.get('status', 'open'))
    return jsonify({'success': True})

# ── Candidates ─────────────────────────────────────────────────────────────────

@app.route('/api/candidates', methods=['GET'])
def get_candidates():
    return jsonify(candidates_manager.get_all_candidates())

@app.route('/api/candidates/<cid>')
def get_candidate(cid):
    c = candidates_manager.get_candidate_by_id(cid)
    return jsonify(c) if c else ({'error': 'Not found'}, 404)

@app.route('/api/candidates/<cid>', methods=['DELETE'])
def delete_candidate_route(cid):
    # 1. Cleanup interviews/bookings
    availability_manager.delete_booking_by_candidate_id(cid)
    # 2. Delete candidate record
    candidates_manager.delete_candidate(cid)
    return jsonify({'success': True})

@app.route('/api/candidates/upload', methods=['POST'])
def upload_cv():
    if 'cv' not in request.files:
        return jsonify({'error': 'No CV file uploaded'}), 400
    file = request.files['cv']
    file_bytes = file.read()
    parsed = cv_parser.parse_cv(file_bytes=file_bytes)
    if not parsed:
        return jsonify({'error': 'Could not parse CV'}), 400
    drive_url = google_drive_service.upload_cv(file_bytes, file.filename, parsed.get('email', 'unknown'))
    open_jobs = job_manager.get_open_jobs()
    if not open_jobs:
        return jsonify({'error': 'No open positions available'}), 400
    evaluation = ai_evaluator.evaluate_candidate(parsed.get('raw_text', ''), open_jobs)
    if not evaluation:
        return jsonify({'error': 'AI evaluation failed'}), 500
    candidate = candidates_manager.save_candidate(evaluation, drive_url, file.filename)
    candidate_id = candidate['id']
    google_sheets_service.save_candidate_to_sheet(candidate)
    auto_booking = None
    status = evaluation.get('fit_score', {}).get('breakdown', {}).get('Status', '')
    if status == 'appoint':
        cand_info = evaluation.get('candidate', {})
        name = f"{cand_info.get('first_name','')} {cand_info.get('last_name','')}".strip()
        auto_booking = availability_manager.find_and_book_next_slot(
            candidate_id=candidate_id, candidate_name=name,
            position=evaluation.get('selected_position', {}).get('position_name', ''),
            candidate_email=cand_info.get('email', '')
        )
        if auto_booking:
            candidates_manager.update_candidate(candidate_id, {
                'interview_scheduled': True,
                'interview_date': auto_booking['date'],
                'interview_time': auto_booking['start_time'],
                'booking_id': auto_booking['id'],
                'calendar_event_id': auto_booking.get('calendar_event_id', '')
            })
    return jsonify({'success': True, 'candidate': candidates_manager.get_candidate_by_id(candidate_id), 'auto_booking': auto_booking})

@app.route('/api/candidates/<cid>/call', methods=['POST'])
def call_candidate(cid):
    candidate = candidates_manager.get_candidate_by_id(cid)
    if not candidate:
        return jsonify({'error': 'Candidate not found'}), 404
    
    cand_info = candidate.get('candidate', {})
    name = f"{cand_info.get('first_name','')} {cand_info.get('last_name','')}".strip()
    phone = cand_info.get('phone', '')
    position = candidate.get('selected_position', {}).get('position_name', 'General')
    
    if not config.ELEVENLABS_API_KEY:
        return jsonify({'mock': True, 'message': 'Demo mode: ElevenLabs not configured'})
        
    call_result = call_service.trigger_interview_call(phone, name, position)
    if "error" in call_result:
        return jsonify({"status": "error", "message": call_result["error"]}), 400
    return jsonify(call_result)

# ── Availability ───────────────────────────────────────────────────────────────

@app.route('/api/availability/slots', methods=['GET'])
def get_slots():
    return jsonify(availability_manager.get_weekly_slots())

@app.route('/api/availability/slots', methods=['POST'])
def add_slot():
    data = request.json
    slot = availability_manager.add_slot(
        day_of_week=int(data['day_of_week']),
        start_time=data['start_time'],
        end_time=data['end_time'],
        duration_minutes=int(data.get('duration_minutes', 60))
    )
    return jsonify(slot)

@app.route('/api/availability/slots/<slot_id>', methods=['DELETE'])
def delete_slot(slot_id):
    availability_manager.remove_slot(slot_id)
    return jsonify({'success': True})

@app.route('/api/availability/slots/<slot_id>/toggle', methods=['PUT'])
def toggle_slot(slot_id):
    availability_manager.toggle_slot(slot_id, request.json.get('active', True))
    return jsonify({'success': True})

@app.route('/api/availability/booked', methods=['GET'])
def get_booked():
    return jsonify(availability_manager.get_booked_slots())

@app.route('/api/availability/upcoming', methods=['GET'])
def get_upcoming_route():
    return jsonify(availability_manager.get_upcoming_interviews())

@app.route('/api/interviews/schedule', methods=['POST'])
def manual_schedule_interview():
    data = request.json
    cid = data.get('candidate_id')
    date = data.get('date')
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    meeting_type = data.get('meeting_type', 'online')
    
    candidate = candidates_manager.get_candidate_by_id(cid)
    if not candidate:
        return jsonify({'error': 'Candidate not found'}), 404
        
    cand_info = candidate.get('candidate', {})
    name = f"{cand_info.get('first_name','')} {cand_info.get('last_name','')}".strip()
    email = cand_info.get('email', '')
    position = candidate.get('selected_position', {}).get('position_name', 'General')
    
    event = calendar_service.schedule_interview(
        candidate_name=name,
        candidate_email=email,
        position=position,
        date=date,
        start_time=start_time,
        end_time=end_time,
        meeting_type=meeting_type
    )
    
    if not event.get('error'):
        candidates_manager.update_candidate(cid, {
            'interview_scheduled': True,
            'interview_date': date,
            'interview_time': start_time,
            'calendar_event_id': event.get('id', '')
        })
        
    return jsonify({'success': True, 'event': event})

# ── Scheduler ──────────────────────────────────────────────────────────────────

@app.route('/api/scheduler/status', methods=['GET'])
def scheduler_status():
    return jsonify({'running': interview_scheduler.is_running(), 'due_now': availability_manager.get_due_interviews()})

@app.route('/api/scheduler/toggle', methods=['POST'])
def toggle_scheduler():
    if interview_scheduler.is_running():
        interview_scheduler.stop_scheduler()
        return jsonify({'running': False})
    interview_scheduler.start_scheduler()
    return jsonify({'running': True})

@app.route('/api/calls/sync', methods=['POST'])
def sync_calls():
    """Manually sync transcripts from recent ElevenLabs calls."""
    try:
        recent = call_service.list_recent_conversations(limit=30)
        synced_count = 0
        candidates = candidates_manager.get_all_candidates()
        synced_cids = set() # Track candidates updated in this run
        
        for conv in recent:
            conv_id = conv.get('conversation_id')
            # Only process if status is done and it's outbound/inbound with a call duration
            if conv.get('status') != 'done':
                continue
            
            # Check if any candidate already has this conversation_id
            if any(c.get('conversation_id') == conv_id for c in candidates):
                continue
            
            # Fetch full transcript to find phone number in metadata
            raw_data = call_service.get_conversation_transcript(conv_id)
            if not raw_data:
                continue
            
            # Phone number often stored in metadata from outbound trigger
            called_number = raw_data.get('conversation_initiation_client_data', {}).get('dynamic_variables', {}).get('system__called_number')
            
            if not called_number:
                continue
                
            # Clean number for matching
            match_num = "".join(filter(str.isdigit, called_number))
            
            # Try to match candidate
            for c in candidates:
                if c['id'] in synced_cids:
                    continue
                c_phone = "".join(filter(str.isdigit, c.get('candidate', {}).get('phone', '')))
                if c_phone and (c_phone in match_num or match_num in c_phone):
                    # Found a match!
                    synced_cids.add(c['id'])
                    formatted = call_service.format_transcript(raw_data)
                    recording_url = raw_data.get('recording_url', '')
                    
                    # ── Voice & Behavior Analysis ────────────────────────────
                    voice_results = {}
                    behavioral_summary = ""
                    if recording_url or conv_id:
                        voice_results = voice_analyzer.download_and_analyze(recording_url, conv_id) or {}
                        if voice_results:
                            behavioral_summary = generate_behavioral_summary(formatted.get('conversation_text', ''), voice_results, formatted.get('conversation_summary', ''))

                    overall_behavior_score = _extract_behavior_score(behavioral_summary)
                    c.update({
                        'interview_completed': True,
                        'conversation_id': conv_id,
                        'conversation_text': formatted['conversation_text'],
                        'conversation_summary': behavioral_summary if behavioral_summary else formatted['conversation_summary'],
                        'recording_url': recording_url,
                        'call_duration_seconds': formatted['duration_seconds'],
                        'interview_status': 'completed',
                        'predicted_emotion': voice_results.get('emotion', ''),
                        'behavior_confidence': voice_results.get('confidence', 0),
                        'behavioral_summary_rich': behavioral_summary,
                        'overall_behavior_score': overall_behavior_score,
                        'updated_at': datetime.now().isoformat()
                    })
                    candidates_manager.save_all_candidates(candidates)
                    synced_count += 1
                    break
                    
        return jsonify({'status': 'ok', 'synced': synced_count})
    except Exception as e:
        logger.error(f"Sync error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/scheduler/trigger-now/<booking_id>', methods=['POST'])
def trigger_now(booking_id):
    booked = availability_manager.get_booked_slots()
    booking = next((b for b in booked if b['id'] == booking_id), None)
    if not booking:
        return jsonify({'error': 'Booking not found'}), 404
    cand = candidates_manager.get_candidate_by_id(booking['candidate_id'])
    phone = cand.get('candidate', {}).get('phone', '') if cand else ''
    
    # ── Trigger the call ──────────────────────────────────────────────
    call_result = call_service.trigger_interview_call(phone, booking['candidate_name'], booking['position'])
    
    if "error" in call_result:
        error_msg = call_result["error"]
        availability_manager.mark_call_failed(booking_id, error_msg)
        return jsonify({"success": False, "error": error_msg}), 400

    conversation_id = call_result.get('conversation_id', '')
    raw = call_service.get_conversation_transcript(conversation_id)
    transcript_data = call_service.format_transcript(raw)
    recording_url = raw.get('recording_url', '')
    
    availability_manager.mark_call_triggered(booking_id)
    availability_manager.mark_call_completed(booking_id, conversation_id)
    if cand:
        # ── Voice & Behavior Analysis ────────────────────────────
        voice_results = {}
        behavioral_summary = ""
        if recording_url or conversation_id:
            voice_results = voice_analyzer.download_and_analyze(recording_url, conversation_id) or {}
            if voice_results:
                behavioral_summary = generate_behavioral_summary(transcript_data.get('conversation_text', ''), voice_results, transcript_data.get('conversation_summary', ''))

        overall_behavior_score = _extract_behavior_score(behavioral_summary)
        candidates_manager.update_candidate(booking['candidate_id'], {
            'interview_completed': True, 
            'conversation_id': conversation_id,
            'conversation_text': transcript_data.get('conversation_text', ''),
            'conversation_summary': behavioral_summary if behavioral_summary else transcript_data.get('conversation_summary', ''),
            'recording_url': recording_url,
            'call_duration_seconds': transcript_data.get('duration_seconds', 0),
            'interview_status': 'completed',
            'predicted_emotion': voice_results.get('emotion', ''),
            'behavior_confidence': voice_results.get('confidence', 0),
            'behavioral_summary_rich': behavioral_summary,
            'overall_behavior_score': overall_behavior_score
        })
    return jsonify({'success': True, 'conversation_id': conversation_id, **transcript_data})

# ── LinkedIn ───────────────────────────────────────────────────────────────────

@app.route('/api/scraper/search', methods=['POST'])
def search_linkedin():
    data = request.json
    position, location, experience = data.get('position',''), data.get('location',''), data.get('experience','3')
    if not position or not location:
        return jsonify({'error': 'Position and location are required'}), 400
    if not config.APIFY_API_TOKEN:
        profiles = linkedin_scraper.get_mock_profiles(position, location)
        saved = [candidates_manager.save_scraped_profile(p, ai_evaluator.evaluate_linkedin_profile(p, position)) for p in profiles]
        return jsonify({'profiles': saved, 'count': len(saved), 'source': 'demo'})
    # Use the sequential pipeline: search → poll → get URLs → scrape → poll → get profiles
    result = linkedin_scraper.search_and_scrape_pipeline(position, location, experience)
    if result.get('error'):
        return jsonify(result), 500
    # Evaluate and save each scraped profile
    saved = []
    for profile in result.get('profiles', []):
        evaluation = ai_evaluator.evaluate_linkedin_profile(profile, position)
        saved_profile = candidates_manager.save_scraped_profile(profile, evaluation)
        saved.append(saved_profile)
    return jsonify({'profiles': saved, 'count': len(saved), 'source': result.get('source', 'apify')})

@app.route('/api/scraper/profiles', methods=['GET'])
def get_scraped_profiles():
    return jsonify(candidates_manager.get_scraped_profiles())

@app.route('/api/scraper/save/<profile_id>', methods=['POST'])
def save_scraped_as_candidate(profile_id):
    profiles = candidates_manager.get_scraped_profiles()
    profile = next((p for p in profiles if p['id'] == profile_id), None)
    if not profile:
        return jsonify({'error': 'Profile not found'}), 404
    evaluation = profile.get('ai_evaluation') or ai_evaluator.evaluate_linkedin_profile(profile, profile.get('headline','General'))
    candidate = candidates_manager.save_candidate(evaluation, source='linkedin')
    google_sheets_service.save_candidate_to_sheet(candidate)
    return jsonify({'success': True, 'candidate': candidate})

@app.route('/api/scraper/profiles/<profile_id>', methods=['DELETE'])
def delete_scraped_profile_route(profile_id):
    candidates_manager.delete_scraped_profile(profile_id)
    return jsonify({'success': True})

# ── Settings ───────────────────────────────────────────────────────────────────

@app.route('/api/settings', methods=['GET'])
def get_settings():
    return jsonify({
        'gemini_api_key': '***' if config.GEMINI_API_KEY else '',
        'groq_api_key': '***' if config.GROQ_API_KEY else '',
        'apify_api_token': '***' if config.APIFY_API_TOKEN else '',
        'elevenlabs_api_key': '***' if config.ELEVENLABS_API_KEY else '',
        'elevenlabs_agent_id': config.ELEVENLABS_AGENT_ID,
        'elevenlabs_phone_id': config.ELEVENLABS_PHONE_NUMBER_ID,
        'google_sheets_id': config.GOOGLE_SHEETS_ID,
        'google_drive_folder_id': config.GOOGLE_DRIVE_FOLDER_ID,
        'company_email': config.COMPANY_EMAIL,
        'company_name': config.COMPANY_NAME,
        'recruiter_name': config.RECRUITER_NAME,
        'email_listener_active': email_listener.is_running(),
        'scheduler_active': interview_scheduler.is_running()
    })

@app.route('/api/settings', methods=['POST'])
def update_settings():
    data = request.json
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    env_map = {
        'gemini_api_key':'GEMINI_API_KEY','groq_api_key':'GROQ_API_KEY',
        'apify_api_token':'APIFY_API_TOKEN','elevenlabs_api_key':'ELEVENLABS_API_KEY',
        'elevenlabs_agent_id':'ELEVENLABS_AGENT_ID','elevenlabs_phone_id':'ELEVENLABS_PHONE_NUMBER_ID',
        'google_sheets_id':'GOOGLE_SHEETS_ID','google_drive_folder_id':'GOOGLE_DRIVE_FOLDER_ID',
        'company_email':'COMPANY_EMAIL','company_name':'COMPANY_NAME','recruiter_name':'RECRUITER_NAME'
    }
    env_lines = {}
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    k, v = line.split('=', 1)
                    env_lines[k] = v
    for field, env_key in env_map.items():
        if field in data and data[field] and data[field] != '***':
            env_lines[env_key] = data[field]
            # Update config object in memory as well
            setattr(config, env_key, data[field])
            
    with open(env_path, 'w') as f:
        for k, v in env_lines.items():
            f.write(f"{k}={v}\n")
            
    return jsonify({'success': True, 'message': 'Settings saved successfully.'})

# ── OAuth2 Setup (Personal Gmail) ─────────────────────────────────────────

@app.route('/api/oauth2/setup', methods=['GET'])
def oauth2_setup():
    """Run full OAuth2 authorization flow using InstalledAppFlow (opens browser)."""
    try:
        if not os.path.exists(config.OAUTH2_CREDENTIALS_FILE):
            return jsonify({
                'error': 'OAuth2 credentials file not found',
                'message': f'Place your OAuth2 credentials JSON at: {config.OAUTH2_CREDENTIALS_FILE}'
            }), 400

        from google_auth_oauthlib.flow import InstalledAppFlow
        flow = InstalledAppFlow.from_client_secrets_file(
            config.OAUTH2_CREDENTIALS_FILE,
            scopes=[
                'https://www.googleapis.com/auth/gmail.readonly',
                'https://www.googleapis.com/auth/gmail.modify',
                'https://www.googleapis.com/auth/drive',
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/calendar'
            ]
        )

        # Opens browser, waits for user consent, handles callback internally
        creds = flow.run_local_server(port=0, open_browser=True)

        # Save token
        os.makedirs(os.path.dirname(config.OAUTH2_TOKEN_FILE), exist_ok=True)
        with open(config.OAUTH2_TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

        # Enable OAuth2 in .env
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        env_lines = {}
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if '=' in line and not line.startswith('#'):
                        k, v = line.split('=', 1)
                        env_lines[k] = v

        env_lines['USE_OAUTH2'] = 'true'
        with open(env_path, 'w') as f:
            for k, v in env_lines.items():
                f.write(f"{k}={v}\n")

        return jsonify({
            'success': True,
            'message': 'OAuth2 authorization successful! Please restart the server.'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/oauth2/status', methods=['GET'])
def oauth2_status():
    """Check OAuth2 authorization status."""
    oauth2_active = os.path.exists(config.OAUTH2_TOKEN_FILE) and config.USE_OAUTH2
    return jsonify({
        'oauth2_active': oauth2_active,
        'token_exists': os.path.exists(config.OAUTH2_TOKEN_FILE),
        'use_oauth2_setting': config.USE_OAUTH2,
        'token_file': config.OAUTH2_TOKEN_FILE
    })

@app.route('/api/email-listener/toggle', methods=['POST'])
def toggle_email_listener():
    if email_listener.is_running():
        email_listener.stop_listener()
        return jsonify({'active': False})
    email_listener.start_listener(_on_new_cv_email)
    return jsonify({'active': True})

def _on_new_cv_email(cv_data):
    try:
        logger.info(f"Processing new CV from email: {cv_data.get('filename')} (Subject: {cv_data.get('subject')})")
        parsed = cv_parser.parse_cv(file_bytes=cv_data['pdf_bytes'])
        if not parsed:
            logger.warning("CV parsing failed - no data extracted")
            return
            
        logger.info(f"Parsed CV. Name: {parsed.get('name')} | Email: {parsed.get('email')}")
        
        drive_url = google_drive_service.upload_cv(cv_data['pdf_bytes'], cv_data['filename'], parsed.get('email',''))
        logger.info(f"Uploaded to Drive: {drive_url}")
        
        open_jobs = job_manager.get_open_jobs()
        if not open_jobs: 
            logger.warning("No open jobs found - stopping processing")
            return
            
        logger.info(f"Evaluating against {len(open_jobs)} jobs...")
        evaluation = ai_evaluator.evaluate_candidate(parsed.get('raw_text',''), open_jobs)
        if not evaluation: 
            logger.warning("AI Evaluation failed")
            return
            
        logger.info(f"Evaluation complete. Fit score: {evaluation.get('fit_score',{}).get('overall')}")
        
        candidate = candidates_manager.save_candidate(evaluation, drive_url, cv_data.get('subject'))
        logger.info(f"Candidate saved to local JSON: {candidate.get('id')}")
        
        if google_sheets_service.save_candidate_to_sheet(candidate):
            logger.info("Successfully saved to Google Sheets")
        else:
            logger.error("Failed to save to Google Sheets")
        if evaluation.get('fit_score',{}).get('breakdown',{}).get('Status','') == 'appoint':
            logger.info("Shortlisted! Attempting to book interview...")
            cand_info = evaluation.get('candidate',{})
            name = f"{cand_info.get('first_name','')} {cand_info.get('last_name','')}".strip()
            booking = availability_manager.find_and_book_next_slot(
                candidate_id=candidate['id'], candidate_name=name,
                position=evaluation.get('selected_position',{}).get('position_name',''),
                candidate_email=cand_info.get('email','')
            )
            if booking:
                logger.info(f"Auto-booked for {booking['date']} at {booking['start_time']}")
                candidates_manager.update_candidate(candidate['id'], {
                    'interview_scheduled': True, 'interview_date': booking['date'],
                    'interview_time': booking['start_time'], 'booking_id': booking['id']
                })
    except Exception as e:
        logger.error(f"Email CV processing error: {e}", exc_info=True)

# ── Startup ────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    os.makedirs('data', exist_ok=True)
    os.makedirs('credentials', exist_ok=True)
    interview_scheduler.start_scheduler()
    email_listener.start_listener(_on_new_cv_email)

    print("\n" + "-"*52)
    print("  *   Ligenix AI HR Platform")
    print("  ->  http://localhost:5000")
    print("-"*52 + "\n")
    app.run(debug=config.DEBUG, host='0.0.0.0', port=5000, use_reloader=False)
