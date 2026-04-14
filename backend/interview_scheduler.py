"""
Interview Scheduler
Background thread that ticks every 60s.
When a booked interview slot is due, it:
  1. Triggers the ElevenLabs outbound call
  2. Waits for completion
  3. Fetches transcript + summary + recording
  4. Updates candidate record and Google Sheets
"""

import threading
import time
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def _extract_behavior_score(summary_text):
    """Parse 'overall behaviour score=X' from behavioral summary text."""
    import re
    if not summary_text:
        return None
    match = re.search(r'overall\s+behaviou?r\s+score\s*=\s*(\d+)', summary_text, re.IGNORECASE)
    return int(match.group(1)) if match else None


_scheduler_active = False
_scheduler_thread = None


def _process_due_interviews():
    from backend.availability_manager import get_due_interviews, mark_call_triggered, mark_call_completed
    from backend.candidates_manager import get_candidate_by_id, update_candidate
    from backend.call_service import trigger_interview_call, get_conversation_transcript, format_transcript
    from backend.google_sheets_service import update_conversation
    from backend.voice_analyzer_service import voice_analyzer
    from backend.ai_evaluator import generate_behavioral_summary

    due = get_due_interviews(tolerance_minutes=2)
    if not due:
        return

    for booking in due:
        candidate_id = booking.get('candidate_id')
        booking_id = booking.get('id')

        logger.info(f"[Scheduler] Interview due: {booking['candidate_name']} at {booking['date']} {booking['start_time']}")

        # Mark triggered immediately to prevent double-firing
        mark_call_triggered(booking_id)

        try:
            candidate = get_candidate_by_id(candidate_id)
            if not candidate:
                logger.warning(f"[Scheduler] Candidate {candidate_id} not found")
                continue

            cand_info = candidate.get('candidate', {})
            phone = cand_info.get('phone', '')
            name = booking['candidate_name']
            position = booking['position']

            # ── Trigger the call ──────────────────────────────────────────────
            call_result = trigger_interview_call(phone, name, position)
            
            if "error" in call_result:
                error_msg = call_result["error"]
                logger.error(f"[Scheduler] Call failed for {name}: {error_msg}")
                from backend.availability_manager import mark_call_failed
                mark_call_failed(booking_id, error_msg)
                continue

            conversation_id = call_result.get('conversation_id', '')
            logger.info(f"[Scheduler] Call triggered, conversation_id={conversation_id}")

            # ── Wait for call to complete (poll up to 5 minutes) ──────────────
            if conversation_id and not call_result.get('mock'):
                _wait_for_call_completion(conversation_id)

            # ── Fetch transcript ──────────────────────────────────────────────
            raw = get_conversation_transcript(conversation_id)
            transcript_data = format_transcript(raw)

            # ── Recording link (if available) ─────────────────────────────────
            recording_url = raw.get('recording_url', '') or raw.get('metadata', {}).get('recording_url', '')

            # ── Voice & Behavior Analysis ────────────────────────────────────
            voice_results = {}
            behavioral_summary = ""
            if recording_url or conversation_id:
                logger.info(f"[Scheduler] Analyzing recording for {name}...")
                voice_results = voice_analyzer.download_and_analyze(recording_url, conversation_id) or {}
                if voice_results:
                    logger.info(f"[Scheduler] Voice analysis complete: {voice_results.get('emotion')}")
                    behavioral_summary = generate_behavioral_summary(transcript_data.get('conversation_text', ''), voice_results, transcript_data.get('conversation_summary', ''))

            # ── Re-score candidate based on call ─────────────────────────────
            call_score = _score_from_transcript(raw, candidate)

            # ── Extract overall behavior score from summary ──────────────────
            overall_behavior_score = _extract_behavior_score(behavioral_summary)

            # ── Update candidate record ───────────────────────────────────────
            updates = {
                'interview_completed': True,
                'interview_date': booking['date'],
                'interview_time': booking['start_time'],
                'conversation_id': conversation_id,
                'conversation_text': transcript_data.get('conversation_text', ''),
                'conversation_summary': behavioral_summary if behavioral_summary else transcript_data.get('conversation_summary', ''),
                'recording_url': recording_url,
                'call_duration_seconds': transcript_data.get('duration_seconds', 0),
                'call_score': call_score,
                'overall_behavior_score': overall_behavior_score,
                'interview_status': 'completed',
                'predicted_emotion': voice_results.get('emotion', ''),
                'behavior_confidence': voice_results.get('confidence', 0),
                'behavioral_summary_rich': behavioral_summary
            }
            update_candidate(candidate_id, updates)

            # ── Update Google Sheets ──────────────────────────────────────────
            update_conversation(
                candidate_id,
                transcript_data.get('conversation_text', ''),
                transcript_data.get('conversation_summary', '')
            )

            mark_call_completed(booking_id, conversation_id)
            logger.info(f"[Scheduler] Interview completed for {name}. Score: {call_score}")

        except Exception as e:
            logger.error(f"[Scheduler] Error processing interview for booking {booking_id}: {e}")


def _wait_for_call_completion(conversation_id: str, max_wait_seconds: int = 300):
    """Poll ElevenLabs until the call is done or timeout."""
    import requests
    from backend.config import config

    if not config.ELEVENLABS_API_KEY:
        time.sleep(5)
        return

    url = f"https://api.elevenlabs.io/v1/convai/conversations/{conversation_id}"
    headers = {"xi-api-key": config.ELEVENLABS_API_KEY}

    waited = 0
    while waited < max_wait_seconds:
        try:
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                data = r.json()
                status = data.get('status', '')
                if status in ('done', 'completed', 'ended'):
                    logger.info(f"[Scheduler] Call {conversation_id} completed")
                    return
        except Exception:
            pass
        time.sleep(10)
        waited += 10

    logger.warning(f"[Scheduler] Timed out waiting for call {conversation_id}")


def _score_from_transcript(raw_data: dict, candidate: dict) -> int:
    """
    Derive a post-call score from conversation analysis.
    Uses AI summary sentiment if available, otherwise returns existing score.
    """
    existing_score = candidate.get('fit_score', {}).get('overall', 0)

    analysis = raw_data.get('analysis', {})
    summary = analysis.get('transcript_summary', '') or ''

    # Simple heuristic boost/penalty based on summary keywords
    positive_words = ['enthusiastic', 'excellent', 'great', 'confident', 'available', 'interested', 'confirmed', 'perfect']
    negative_words = ['unavailable', 'declined', 'not interested', 'withdrew', 'wrong number', 'cancel']

    summary_lower = summary.lower()
    boost = sum(1 for w in positive_words if w in summary_lower)
    penalty = sum(2 for w in negative_words if w in summary_lower)

    adjusted = min(10, max(0, existing_score + boost - penalty))
    return adjusted


def _scheduler_loop():
    logger.info("[Scheduler] Background interview scheduler started")
    while _scheduler_active:
        try:
            _process_due_interviews()
        except Exception as e:
            logger.error(f"[Scheduler] Loop error: {e}")
        time.sleep(60)
    logger.info("[Scheduler] Scheduler stopped")


def start_scheduler():
    global _scheduler_active, _scheduler_thread
    if _scheduler_active:
        return
    _scheduler_active = True
    _scheduler_thread = threading.Thread(target=_scheduler_loop, daemon=True, name='InterviewScheduler')
    _scheduler_thread.start()
    logger.info("[Scheduler] Started")


def stop_scheduler():
    global _scheduler_active
    _scheduler_active = False


def is_running():
    return _scheduler_active
