# 🚀 Ligenix AI HR Recruitment Platform

A complete AI-powered HR recruitment automation platform built with Python/Flask and vanilla HTML/CSS/JS.

## Features

| Feature | Description |
|---|---|
| 📋 Job Management | Create, publish, and manage job postings with auto-generated announcements |
| 📧 Email CV Collection | Gmail listener polls inbox every minute for CV submissions |
| 🤖 AI CV Analysis | Gemini/Groq AI scores candidates 0-10 against job requirements |
| 📊 Google Sheets | All candidates stored automatically in Google Sheets |
| 🔍 LinkedIn Scraper | Search LinkedIn via Apify and evaluate scraped profiles |
| 📅 Interview Scheduling | Google Calendar integration with automatic invites |
| 📞 AI Voice Calls | ElevenLabs automated calls for appointed candidates |
| 🎙️ Transcripts | Call transcripts stored in Google Sheets |

---

## 🛠 Installation

```bash
# 1. Clone or download the project
cd ai_hr_platform

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env .env.local
# Edit .env with your API keys

# 4. Start the server
python app.py
```

Open **http://localhost:5000** in your browser.

---

## ⚙️ Configuration

### Required: AI API (at least one)

| Service | Where to get | .env key |
|---|---|---|
| Google Gemini | [makersuite.google.com](https://makersuite.google.com) | `GEMINI_API_KEY` |
| Groq | [console.groq.com](https://console.groq.com) | `GROQ_API_KEY` |

### Optional: Google Services

**Choose ONE method:**

#### Option 1: Service Account (Google Workspace) - Recommended for organizations
Place service account JSON credential files in the `credentials/` folder:

```
credentials/
  gmail_credentials.json
  drive_credentials.json
  sheets_credentials.json
  calendar_credentials.json
```

Set these in `.env`:
```
GMAIL_CREDENTIALS_FILE=credentials/gmail_credentials.json
COMPANY_EMAIL=your-workspace-email@yourdomain.com
GOOGLE_SHEETS_ID=<your-sheet-id>
GOOGLE_DRIVE_FOLDER_ID=<your-folder-id>
USE_OAUTH2=false
```

#### Option 2: OAuth2 (Personal Gmail) - Recommended for individuals
Follow the [OAuth2 Setup Guide](OAUTH2_SETUP.md) for personal Gmail accounts.

```
credentials/
  oauth2_credentials.json    # Download from Google Cloud
  oauth2_token.json          # Auto-generated after auth
```

Set these in `.env`:
```
USE_OAUTH2=true
OAUTH2_CREDENTIALS_FILE=credentials/oauth2_credentials.json
GOOGLE_SHEETS_ID=<your-sheet-id>
GOOGLE_DRIVE_FOLDER_ID=<your-folder-id>
```

### Optional: Apify LinkedIn Scraper

```
APIFY_API_TOKEN=apify_api_...
```

Without this, demo/mock profiles are used.

### Optional: ElevenLabs AI Calls

```
ELEVENLABS_API_KEY=sk_...
ELEVENLABS_AGENT_ID=agent_...
ELEVENLABS_PHONE_NUMBER_ID=phnum_...
```

---

## 🗂 Project Structure

```
ai_hr_platform/
├── app.py                    # Flask application & API routes
├── backend/
│   ├── config.py             # Configuration management
│   ├── job_manager.py        # Job CRUD & announcement generation
│   ├── cv_parser.py          # PDF parsing with pdfplumber
│   ├── ai_evaluator.py       # Gemini/Groq candidate scoring
│   ├── candidates_manager.py # Candidate data management
│   ├── email_listener.py     # Gmail inbox monitoring
│   ├── linkedin_scraper.py   # Apify LinkedIn integration
│   ├── google_sheets_service.py
│   ├── google_drive_service.py
│   ├── calendar_service.py   # Google Calendar events
│   └── call_service.py       # ElevenLabs voice calls
├── frontend/
│   ├── dashboard.html        # Overview with stats & quick upload
│   ├── jobs.html             # Job posting management
│   ├── candidates.html       # Candidate pipeline with AI scores
│   ├── scraped_candidates.html # LinkedIn profiles dashboard
│   ├── schedule_interview.html # Calendar scheduling
│   └── settings.html         # API credentials & config
├── static/
│   ├── css/style.css         # Full design system
│   └── js/utils.js           # Shared frontend utilities
├── data/
│   ├── jobs.json
│   ├── candidates.json
│   └── scraped_profiles.json
├── credentials/              # Google service account files
├── .env                      # Environment variables
└── requirements.txt
```

---

## 🔄 How It Works

### Email CV Flow
1. Gmail listener checks inbox every 60 seconds
2. CV PDF extracted from email attachment
3. CV uploaded to Google Drive
4. `pdfplumber` extracts text content
5. AI (Gemini/Groq) evaluates against all open jobs
6. Candidate scored 0-10, status = appoint/reject
7. Record saved to Google Sheets
8. If appointed → ElevenLabs AI call triggered

### LinkedIn Sourcing Flow
1. HR enters position, location, experience level
2. Apify LinkedIn Search API finds matching profiles
3. Apify Profile Scraper gets full details
4. AI evaluates each profile against job requirements
5. Profiles displayed in Scraped Candidates dashboard

### AI Scoring
- Score ≥ 6 → **Appointed** (Shortlisted)
- Score < 6 → **Rejected**

Breakdown: Experience + Technical Skills + Achievements + Education

---

## 🌐 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/dashboard/stats` | Dashboard statistics |
| GET | `/api/jobs` | List all jobs |
| POST | `/api/jobs` | Create job posting |
| GET | `/api/candidates` | List all candidates |
| POST | `/api/candidates/upload` | Upload & analyze CV |
| POST | `/api/scraper/search` | Search LinkedIn |
| GET | `/api/scraper/profiles` | Get scraped profiles |
| POST | `/api/interviews/schedule` | Schedule interview |
| GET | `/api/settings` | Get current settings |
| POST | `/api/settings` | Update settings |

---

## 🎨 Tech Stack

- **Backend**: Python 3.11+ · Flask · pdfplumber
- **Frontend**: Vanilla HTML · CSS · JavaScript
- **Fonts**: Syne (headings) · DM Sans (body)
- **AI**: Google Gemini 1.5 Flash · Groq Llama 3.3
- **Integrations**: Gmail API · Google Drive · Sheets · Calendar · Apify · ElevenLabs

---

*Built for Ligenix HR Team · Recruiter: Lena Babu*
