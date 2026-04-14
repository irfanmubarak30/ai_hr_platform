import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # AI APIs
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

    # Google APIs
    # Service Account (for Google Workspace)
    GMAIL_CREDENTIALS_FILE = os.getenv("GMAIL_CREDENTIALS_FILE", "credentials/gmail_credentials.json")
    GOOGLE_DRIVE_CREDENTIALS_FILE = os.getenv("GOOGLE_DRIVE_CREDENTIALS_FILE", "credentials/drive_credentials.json")
    GOOGLE_SHEETS_CREDENTIALS_FILE = os.getenv("GOOGLE_SHEETS_CREDENTIALS_FILE", "credentials/sheets_credentials.json")
    GOOGLE_CALENDAR_CREDENTIALS_FILE = os.getenv("GOOGLE_CALENDAR_CREDENTIALS_FILE", "credentials/calendar_credentials.json")
    
    # OAuth2 (for personal Gmail accounts)
    OAUTH2_CREDENTIALS_FILE = os.getenv("OAUTH2_CREDENTIALS_FILE", "credentials/oauth2_credentials.json")
    OAUTH2_TOKEN_FILE = os.getenv("OAUTH2_TOKEN_FILE", "credentials/oauth2_token.json")
    USE_OAUTH2 = os.getenv("USE_OAUTH2", "False").lower() == "true"
    
    GOOGLE_SHEETS_ID = os.getenv("GOOGLE_SHEETS_ID", "")
    GOOGLE_DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "")

    # Apify
    APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN", "")

    # Hugging Face
    HUGGINGFACE_API_TOKEN = os.getenv("HUGGINGFACE_API_TOKEN", "")

    # ElevenLabs
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
    ELEVENLABS_AGENT_ID = os.getenv("ELEVENLABS_AGENT_ID", "")
    ELEVENLABS_PHONE_NUMBER_ID = os.getenv("ELEVENLABS_PHONE_NUMBER_ID", "")

    # Email Config
    COMPANY_EMAIL = os.getenv("COMPANY_EMAIL", "careers@ligenix.com")
    COMPANY_NAME = os.getenv("COMPANY_NAME", "Ligenix")
    RECRUITER_NAME = os.getenv("RECRUITER_NAME", "Lena Babu")

    # LinkedIn
    LINKEDIN_CLIENT_ID = os.getenv("LINKEDIN_CLIENT_ID", "")
    LINKEDIN_CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET", "")
    LINKEDIN_ACCESS_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN", "")
    LINKEDIN_PERSON_ID = os.getenv("LINKEDIN_PERSON_ID", "")
    LINKEDIN_ORGANIZATION_ID = os.getenv("LINKEDIN_ORGANIZATION_ID", "")

    # Flask
    SECRET_KEY = os.getenv("SECRET_KEY", "hr-platform-secret-key-2024")
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"

config = Config()
