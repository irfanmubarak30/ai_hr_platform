import os
import sys
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.image_service import image_service

def test_full_poster():
    print("Testing full Flux poster generation with long title (font scaling test)...")
    job_title = "Senior Full Stack AI and ML Solutions Engineer"
    
    # This will use Hugging Face Flux (if token is in .env) and then add captions
    poster_url = image_service.generate_job_poster(job_title)
    
    if poster_url:
        print(f"Success! Poster generated at: {poster_url}")
        # Identify the local path
        local_path = os.path.join(os.path.dirname(__file__), '..', poster_url.lstrip('/'))
        print(f"Local file path: {local_path}")
    else:
        print("Failed to generate poster.")

if __name__ == "__main__":
    load_dotenv()
    test_full_poster()
