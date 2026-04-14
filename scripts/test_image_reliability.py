
import os
import sys
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.image_service import image_service
from backend.config import config

logging.basicConfig(level=logging.INFO)

def test_reliability():
    print(f"Testing Multi-Model Image Reliability...")
    print(f"Current IMAGE_PROVIDER: {os.getenv('IMAGE_PROVIDER')}")
    
    # This should trigger the new Flux -> Turbo -> Unsplash logic
    result = image_service.generate_job_poster("Senior Cloud Engineer")
    if result:
        print(f"SUCCESS! Poster generated at: {result}")
    else:
        print("FAILED to generate poster.")

if __name__ == "__main__":
    test_reliability()
