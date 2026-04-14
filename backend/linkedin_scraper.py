import requests
import time
import logging
from backend.config import config

logger = logging.getLogger(__name__)

APIFY_BASE = "https://api.apify.com/v2"
SEARCH_ACTOR = "harvestapi~linkedin-profile-search"
PROFILE_ACTOR = "harvestapi~linkedin-profile-scraper"

def _headers():
    return {"Content-Type": "application/json"}

def _token():
    return config.APIFY_API_TOKEN

# ─── Core Helpers ─────────────────────────────────────────────────────────────

def _start_actor(actor_id, payload):
    """Start an Apify actor and return the run ID."""
    url = f"{APIFY_BASE}/acts/{actor_id}/runs?token={_token()}"
    resp = requests.post(url, json=payload, timeout=30)
    if resp.status_code not in (200, 201):
        raise RuntimeError(f"Failed to start actor {actor_id}: {resp.status_code} {resp.text}")
    data = resp.json()
    run_id = data.get('data', {}).get('id')
    if not run_id:
        raise RuntimeError(f"No run ID returned from actor {actor_id}: {data}")
    logger.info(f"Started actor {actor_id}, runId={run_id}")
    return run_id


def _poll_run_until_done(run_id, poll_interval=7, timeout=300):
    """
    Poll an Apify run by its runId until it reaches a terminal state.
    Uses the actor-run endpoint: GET /v2/actor-runs/{runId}
    Returns the final status string ('SUCCEEDED', 'FAILED', 'ABORTED', etc.)
    Raises RuntimeError on timeout or failure.
    """
    url = f"{APIFY_BASE}/actor-runs/{run_id}?token={_token()}"
    elapsed = 0

    while elapsed < timeout:
        time.sleep(poll_interval)
        elapsed += poll_interval

        try:
            resp = requests.get(url, timeout=15)
            if resp.status_code != 200:
                logger.warning(f"Poll for run {run_id} got HTTP {resp.status_code}, retrying...")
                continue

            status = resp.json().get('data', {}).get('status', 'UNKNOWN')
            logger.info(f"Run {run_id} status: {status} (elapsed {elapsed}s)")

            if status == 'SUCCEEDED':
                return status
            elif status in ('FAILED', 'ABORTED', 'TIMED-OUT'):
                raise RuntimeError(f"Apify run {run_id} ended with status: {status}")
            # else RUNNING / READY → keep polling
        except requests.RequestException as e:
            logger.warning(f"Network error polling run {run_id}: {e}, retrying...")

    raise RuntimeError(f"Apify run {run_id} timed out after {timeout}s")


def _get_dataset_items(run_id, retries=3, retry_delay=5):
    """
    Fetch dataset items for a specific run by its runId.
    Retries up to retries times with retry_delay seconds between attempts
    to handle Apify's eventual consistency (dataset may be momentarily empty
    right after the run status flips to SUCCEEDED).
    """
    url = f"{APIFY_BASE}/actor-runs/{run_id}/dataset/items?token={_token()}"

    for attempt in range(1, retries + 1):
        resp = requests.get(url, timeout=30)
        if resp.status_code != 200:
            raise RuntimeError(f"Failed to get dataset for run {run_id}: {resp.status_code} {resp.text}")
        items = resp.json()
        if items:
            logger.info(f"Retrieved {len(items)} dataset items for run {run_id} (attempt {attempt})")
            return items
        # Dataset empty — wait and retry
        if attempt < retries:
            logger.info(f"Dataset empty for run {run_id}, retrying in {retry_delay}s (attempt {attempt}/{retries})")
            time.sleep(retry_delay)

    logger.warning(f"Dataset still empty for run {run_id} after {retries} attempts")
    return []


# ─── Sequential Pipeline ─────────────────────────────────────────────────────

def search_and_scrape_pipeline(position, location, experience_level="3"):
    """
    Full sequential pipeline:
      1. Start linkedin-profile-search actor
      2. Poll until SUCCEEDED
      3. Retrieve search dataset items
      4. Extract linkedinUrl values
      5. Start linkedin-profile-scraper actor
      6. Poll until SUCCEEDED
      7. Retrieve scraped profile dataset items
      8. Parse into standard profile format

    Returns:
        dict with 'profiles' (list of parsed profiles) and 'count',
        or dict with 'error' on failure.
    """
    if not _token():
        return {"error": "Apify API token not configured"}

    try:
        # ── Step 1: Start search actor ────────────────────────────────────
        logger.info(f"Pipeline: starting search for '{position}' in '{location}'")
        search_payload = {
            "autoQuerySegmentation": False,
            "locations": [location],
            "maxItems": 5,
            "profileScraperMode": "Short",
            "recentlyChangedJobs": False,
            "searchQuery": position,
            "yearsOfExperienceIds": [experience_level]
        }
        search_run_id = _start_actor(SEARCH_ACTOR, search_payload)

        # ── Step 2: Poll search until done ────────────────────────────────
        _poll_run_until_done(search_run_id, poll_interval=7, timeout=300)

        # Brief pause for Apify dataset propagation
        time.sleep(3)

        # ── Step 3: Retrieve search results (with retry) ─────────────────
        search_items = _get_dataset_items(search_run_id, retries=3, retry_delay=5)
        if not search_items:
            logger.info("Search completed but returned no profiles")
            return {"profiles": [], "count": 0, "source": "apify", "message": "No profiles found for this search"}

        # ── Step 4: Extract LinkedIn URLs ─────────────────────────────────
        profile_urls = []
        for item in search_items:
            url = item.get('linkedinUrl') or item.get('linkedin_url') or item.get('url') or ''
            if url and url.startswith('http'):
                profile_urls.append(url)

        profile_urls = list(dict.fromkeys(profile_urls))  # deduplicate, preserve order
        logger.info(f"Pipeline: extracted {len(profile_urls)} unique profile URLs")

        if not profile_urls:
            # Return search results as-is if no URLs could be extracted
            parsed = [parse_apify_profile(item) for item in search_items]
            return {"profiles": parsed, "count": len(parsed), "source": "search_only"}

        # ── Step 5: Start profile scraper actor ───────────────────────────
        scrape_payload = {
            "profileScraperMode": "Profile details + email search ($10 per 1k)",
            "queries": profile_urls
        }
        scrape_run_id = _start_actor(PROFILE_ACTOR, scrape_payload)

        # ── Step 6: Poll scraper until done ───────────────────────────────
        _poll_run_until_done(scrape_run_id, poll_interval=7, timeout=300)

        # Brief pause for Apify dataset propagation
        time.sleep(3)

        # ── Step 7: Retrieve scraped profiles (with retry) ────────────────
        profile_items = _get_dataset_items(scrape_run_id, retries=3, retry_delay=5)
        if not profile_items:
            return {"error": "Scraper completed but returned no profile data"}

        # ── Step 8: Parse profiles ────────────────────────────────────────
        parsed_profiles = [parse_apify_profile(p) for p in profile_items]
        logger.info(f"Pipeline: completed with {len(parsed_profiles)} profiles")

        return {"profiles": parsed_profiles, "count": len(parsed_profiles), "source": "apify"}

    except RuntimeError as e:
        logger.error(f"Pipeline error: {e}")
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Unexpected pipeline error: {e}")
        return {"error": f"Pipeline failed: {str(e)}"}


# ─── Legacy Functions (kept for backward compatibility) ───────────────────────

def search_linkedin_people(position, location, experience_level="3"):
    """Start a LinkedIn people search via Apify. (Legacy – prefer search_and_scrape_pipeline)"""
    if not _token():
        return {"error": "Apify API token not configured"}, None

    url = f"{APIFY_BASE}/acts/{SEARCH_ACTOR}/runs?token={_token()}"
    payload = {
        "autoQuerySegmentation": False,
        "locations": [location],
        "maxItems": 5,
        "profileScraperMode": "Short",
        "recentlyChangedJobs": False,
        "searchQuery": position,
        "yearsOfExperienceIds": [experience_level]
    }
    resp = requests.post(url, json=payload, timeout=30)
    if resp.status_code in (200, 201):
        data = resp.json()
        return {"run_id": data.get('data', {}).get('id'), "status": "started"}, data
    return {"error": f"Failed to start search: {resp.text}"}, None

def check_run_status(actor, run_id=None):
    """Check the status of an Apify run. (Legacy – prefer _poll_run_until_done)"""
    if run_id:
        url = f"{APIFY_BASE}/acts/{actor}/runs/{run_id}?token={_token()}"
    else:
        url = f"{APIFY_BASE}/acts/{actor}/runs?token={_token()}"
    resp = requests.get(url, timeout=15)
    if resp.status_code == 200:
        data = resp.json()
        if run_id:
            return data.get('data', {}).get('status')
        items = data.get('data', {}).get('items', [])
        return items[0].get('status') if items else 'UNKNOWN'
    return 'ERROR'

def get_search_results():
    """Get results from the last LinkedIn search run. (Legacy – prefer _get_dataset_items)"""
    url = f"{APIFY_BASE}/acts/{SEARCH_ACTOR}/runs/last/dataset/items?token={_token()}"
    resp = requests.get(url, timeout=15)
    if resp.status_code == 200:
        return resp.json()
    return []

def scrape_profiles(profile_urls):
    """Scrape full profile details from LinkedIn URLs. (Legacy – prefer search_and_scrape_pipeline)"""
    if not _token():
        return {"error": "Apify API token not configured"}, None

    url = f"{APIFY_BASE}/acts/{PROFILE_ACTOR}/runs?token={_token()}"
    payload = {
        "profileScraperMode": "Profile details + email search ($10 per 1k)",
        "queries": profile_urls
    }
    resp = requests.post(url, json=payload, timeout=30)
    if resp.status_code in (200, 201):
        return {"status": "scraping_started"}, resp.json()
    return {"error": f"Failed to start scrape: {resp.text}"}, None

def get_profile_results():
    """Get results from the last profile scraping run. (Legacy – prefer _get_dataset_items)"""
    url = f"{APIFY_BASE}/acts/{PROFILE_ACTOR}/runs/last/dataset/items?token={_token()}"
    resp = requests.get(url, timeout=15)
    if resp.status_code == 200:
        return resp.json()
    return []


# ─── Profile Parser ──────────────────────────────────────────────────────────

def parse_apify_profile(raw_profile):
    """Convert Apify LinkedIn profile to our standard format."""
    return {
        'name': f"{raw_profile.get('firstName', '')} {raw_profile.get('lastName', '')}".strip(),
        'first_name': raw_profile.get('firstName', ''),
        'last_name': raw_profile.get('lastName', ''),
        'headline': raw_profile.get('headline', ''),
        'location': raw_profile.get('location', {}).get('linkedinText', '') if isinstance(raw_profile.get('location'), dict) else raw_profile.get('location', ''),
        'about': raw_profile.get('about', ''),
        'linkedin_url': raw_profile.get('linkedinUrl', ''),
        'profile_image': raw_profile.get('profilePicture', ''),
        'experience': [
            {
                'position': e.get('position', ''),
                'company': e.get('companyName', ''),
                'duration': e.get('duration', ''),
                'description': e.get('description', '')
            }
            for e in raw_profile.get('experience', [])
        ],
        'education': [
            {
                'school': e.get('schoolName', ''),
                'degree': e.get('degree', ''),
                'field': e.get('fieldOfStudy', ''),
                'period': e.get('period', '')
            }
            for e in raw_profile.get('education', [])
        ],
        'skills': [s.get('name', s) if isinstance(s, dict) else s for s in raw_profile.get('skills', [])],
        'certifications': [c.get('title', '') for c in raw_profile.get('certifications', [])],
        'email': raw_profile.get('email', '')
    }