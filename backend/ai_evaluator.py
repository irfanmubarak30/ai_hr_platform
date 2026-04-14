import json
import os
import requests
from backend.config import config

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

EVALUATION_SCHEMA = {
    "candidate": {"first_name": "", "last_name": "", "email": "", "phone": ""},
    "selected_position": {"position_name": "", "selection_reason": ""},
    "summary": {
        "years_experience": 0, "current_role": "", "key_achievements": [],
        "technical_skills": [], "overall_summary": "", "draft_mail": ""
    },
    "fit_score": {
        "overall": 0,
        "breakdown": {"experience": 0, "technical_skills": 0, "achievements": 0, "education": 0, "Status": "reject"}
    }
}

def build_evaluation_prompt(cv_text, jobs):
    jobs_text = "\n".join([f"- {j['title']}: {j.get('description', '')[:200]}" for j in jobs])
    return f"""You are an expert HR assistant. Analyze this candidate CV against the available positions.

Available Positions:
{jobs_text}

Candidate CV:
{cv_text[:3000]}

Instructions:
1. Select the BEST matching position for this candidate
2. Score them 0-10 overall (≥6 = appoint, <6 = reject)
3. Break down scores: experience, technical_skills, achievements, education (each 0-10)
4. Draft a professional email FROM recruiter {config.RECRUITER_NAME} at {config.COMPANY_NAME} TO the candidate
5. Status must be exactly "appoint" or "reject"

Return ONLY valid JSON matching this exact structure:
{json.dumps(EVALUATION_SCHEMA, indent=2)}

Replace all values with real data. Return ONLY the JSON, no markdown."""

def call_gemini(prompt):
    if not config.GEMINI_API_KEY:
        print("Gemini API key not found in config.")
        return None
    try:
        resp = requests.post(
            f"{GEMINI_URL}?key={config.GEMINI_API_KEY}",
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=60
        )
        if resp.status_code == 200:
            text = resp.json()['candidates'][0]['content']['parts'][0]['text']
            text = text.strip().replace('```json', '').replace('```', '').strip()
            return json.loads(text)
        else:
            print(f"Gemini API returned status {resp.status_code}: {resp.text}")
    except Exception as e:
        print(f"Gemini error: {e}")
    return None

def call_groq(prompt):
    if not config.GROQ_API_KEY:
        return None
    try:
        resp = requests.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {config.GROQ_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": "You are an expert HR assistant. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 2000
            },
            timeout=60
        )
        if resp.status_code == 200:
            text = resp.json()['choices'][0]['message']['content']
            text = text.strip().replace('```json', '').replace('```', '').strip()
            return json.loads(text)
    except Exception as e:
        print(f"Groq error: {e}")
    return None

def call_ai_text(prompt):
    """Fallback-ready text generation (no JSON parsing)."""
    if config.GEMINI_API_KEY:
        try:
            resp = requests.post(f"{GEMINI_URL}?key={config.GEMINI_API_KEY}", json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=60)
            if resp.status_code == 200:
                return resp.json()['candidates'][0]['content']['parts'][0]['text'].strip()
        except: pass
    if config.GROQ_API_KEY:
        try:
            resp = requests.post(GROQ_URL, headers={"Authorization": f"Bearer {config.GROQ_API_KEY}", "Content-Type": "application/json"}, json={"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": prompt}]}, timeout=60)
            if resp.status_code == 200:
                return resp.json()['choices'][0]['message']['content'].strip()
        except: pass
    return None

def get_fallback_evaluation(cv_text, jobs):
    """Return a demo evaluation when no API key is configured."""
    import random
    score = random.randint(4, 9)
    status = "appoint" if score >= 6 else "reject"
    job = jobs[0] if jobs else {"title": "General Position"}
    return {
        "candidate": {"first_name": "Demo", "last_name": "Candidate", "email": "demo@example.com", "phone": "+1234567890"},
        "selected_position": {"position_name": job['title'], "selection_reason": "Best matching profile based on skills analysis"},
        "summary": {
            "years_experience": 3, "current_role": "Software Engineer",
            "key_achievements": ["Led product development", "Increased team efficiency by 30%"],
            "technical_skills": ["Python", "Machine Learning", "API Development"],
            "overall_summary": "Strong candidate with relevant technical background and good communication skills.",
            "draft_mail": f"Dear Candidate,\n\nThank you for your interest in the {job['title']} role at {config.COMPANY_NAME}.\n\n{'We are pleased to inform you that your profile has been shortlisted.' if status == 'appoint' else 'After careful review, we regret to inform you that we will not be moving forward at this time.'}\n\nBest regards,\n{config.RECRUITER_NAME}\n{config.COMPANY_NAME}"
        },
        "fit_score": {
            "overall": score,
            "breakdown": {"experience": score, "technical_skills": score-1, "achievements": score-2, "education": score, "Status": status}
        }
    }

def evaluate_candidate(cv_text, jobs):
    """Main evaluation function - tries Gemini, then Groq, then fallback."""
    if not jobs:
        return None
    
    prompt = build_evaluation_prompt(cv_text, jobs)
    
    result = call_gemini(prompt) or call_groq(prompt)
    
    if not result:
        result = get_fallback_evaluation(cv_text, jobs)
    
    # Ensure status consistency
    overall = result.get('fit_score', {}).get('overall', 0)
    status = "appoint" if overall >= 6 else "reject"
    if 'fit_score' in result and 'breakdown' in result['fit_score']:
        result['fit_score']['breakdown']['Status'] = status
    
    return result

def evaluate_linkedin_profile(profile_data, position):
    """Evaluate a LinkedIn-scraped profile."""
    cv_text = f"""
Name: {profile_data.get('name', '')}
Headline: {profile_data.get('headline', '')}
Location: {profile_data.get('location', '')}
About: {profile_data.get('about', '')}
Experience: {json.dumps(profile_data.get('experience', []))}
Education: {json.dumps(profile_data.get('education', []))}
Skills: {', '.join(profile_data.get('skills', []))}
"""
    jobs = [{'title': position, 'description': f'Looking for {position} professional'}]
    return evaluate_candidate(cv_text, jobs)

def generate_behavioral_summary(transcript_text, voice_analysis, elevenlabs_summary=""):
    """
    Synthesizes a concise, emotionally-aware behavioral summary from the interview
    transcript, ElevenLabs summary, and voice analysis results.
    """
    if not transcript_text:
        return "No transcript available for analysis."

    emotion = voice_analysis.get('emotion', 'unknown')
    confidence = voice_analysis.get('confidence', 0)
    
    prompt = f"""You are an AI assistant that creates concise, emotionally-aware summaries.

Inputs:
1. Transcript: {transcript_text[:5000]}
2. Summary generated by ElevenLabs: {elevenlabs_summary}
3. Emotion analysis from the emotion model: Primary Emotion: {emotion} (Confidence: {confidence:.2f})

Task:
1. Read the ElevenLabs summary and the emotion analysis.
2. Identify the key message of the content.
3. Use the detected emotional tone (e.g., happy, angry, sad, neutral, excited) to shape and inform your summary, but do NOT explicitly mention the RAVDESS model or the raw emotion label.
4. Combine both sources into a single clear summary.
5. Keep the summary short and natural.

Output Requirements:
- Format the response EXACTLY as follows:
[Maximum 2-3 sentences. Preserve the main information from the ElevenLabs summary. Reflect the emotional tone naturally in your writing style. Avoid repeating information. Write in simple, natural language.]
...............................
overall behaviour score=[Insert a score 0-10 based on leadership, confidence, and clarity]

- Do NOT include any "ravdess result" line or raw emotion labels.
- Do NOT use any other formatting or headers.
"""
    
    summary = call_ai_text(prompt)
    if not summary:
        return f"Behavioral interview completed. Tone was generally {emotion}.\n...............................\noverall behaviour score=5"
        
    return summary
