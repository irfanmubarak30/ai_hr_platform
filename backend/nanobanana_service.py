import os
import time
import requests
import logging
from PIL import Image, ImageDraw, ImageFont
import urllib.parse
from backend.config import config

logger = logging.getLogger(__name__)

class NanobananaService:
    def __init__(self, output_dir=None):
        if output_dir is None:
            self.output_dir = os.path.join(os.path.dirname(__file__), '..', 'static', 'posters')
        else:
            self.output_dir = output_dir
            
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def _generate_base_image(self, job_title):
        logger.info(f"Generating image using Nanobanana 2.0 for: {job_title}")
        api_key = os.environ.get('NANOBANANA_API_KEY')
        if not api_key:
            logger.warning("NANOBANANA_API_KEY not found in environment, returning None")
            return None
            
        prompt = f"Cinematic photography of a {job_title} at work in a modern office, highly detailed 8k"
        
        # Using Nano Banana (Gemini 2.5 Flash Image Preview)
        # This is the direct Google API endpoint for image generation
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent?key={api_key}"
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ],
            "generationConfig": {
                "responseModalities": ["IMAGE"]
            }
        }
        
        try:
            start_time = time.time()
            logger.info(f"Nanobanana requesting generation via Gemini 3.1 Flash Image...")
            response = requests.post(url, json=payload, timeout=90)
            elapsed = time.time() - start_time
            logger.info(f"Nanobanana (Nano Banana 2) responded in {elapsed:.2f}s (Status: {response.status_code})")
            
            if response.status_code == 200:
                result = response.json()
                # Nano Banana returns image in candidates[0].content.parts[0].inlineData
                try:
                    parts = result['candidates'][0]['content']['parts']
                    for part in parts:
                        if 'inlineData' in part:
                            import base64
                            b64_data = part['inlineData'].get('data')
                            if b64_data:
                                return base64.b64decode(b64_data)
                except (KeyError, IndexError) as e:
                    logger.error(f"Failed to parse Nanobanana response: {e}")
            else:
                logger.error(f"Nanobanana API error: {response.status_code} - {response.text}")
        except Exception as e:
            logger.warning(f"Nanobanana attempt failed: {e}")
            
        return None

    def generate_job_poster(self, job_title):
        """Generate a professional job poster with AI background and text overlay using Nanobanana."""
        image_content = self._generate_base_image(job_title)
        
        if not image_content:
            logger.info("Nanobanana generation failed. Using FAST fallback image.")
            FALLBACK_IMAGE_URL = "https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=1024&h=1024"
            try:
                response = requests.get(FALLBACK_IMAGE_URL, timeout=15)
                if response.status_code == 200:
                    image_content = response.content
                else:
                    return None
            except Exception as e:
                logger.error(f"Fallback error: {e}")
                return None

        try:
            temp_filename = f"base_{int(time.time())}.jpg"
            temp_path = os.path.join(self.output_dir, temp_filename)
            
            logger.info(f"Saving base image content ({len(image_content)} bytes) to {temp_path}...")
            with open(temp_path, 'wb') as f:
                f.write(image_content)
            
            size = len(image_content)
            if size < 1000:
                logger.error(f"Downloaded file too small ({size} bytes). Likely invalid image.")
                if os.path.exists(temp_path): os.remove(temp_path)
                return None

            # Add Text Overlay using Pillow
            try:
                img = Image.open(temp_path)
                img.verify() 
                img = Image.open(temp_path) 
            except Exception as e:
                logger.error(f"Invalid image file downloaded: {e}")
                if os.path.exists(temp_path): os.remove(temp_path)
                return None

            draw = ImageDraw.Draw(img, "RGBA")
            width, height = img.size

            font_paths = [
                "C:\\Windows\\Fonts\\arialbd.ttf",
                "C:\\Windows\\Fonts\\segoeuib.ttf",
                "C:\\Windows\\Fonts\\Inter-Bold.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
            ]
            font_v_large = None
            font_large = None
            
            for fp in font_paths:
                if os.path.exists(fp):
                    font_v_large = ImageFont.truetype(fp, 120)
                    font_large = ImageFont.truetype(fp, 80)
                    break
            
            if not font_v_large:
                font_v_large = ImageFont.load_default()
                font_large = ImageFont.load_default()

            overlay_height = 320
            draw.rectangle([0, height - overlay_height, width, height], fill=(0, 0, 0, 180))

            text_top = "WE ARE HIRING"
            text_bottom = job_title.upper()
            
            w_top = draw.textlength(text_top, font=font_large)
            w_bottom = draw.textlength(text_bottom, font=font_v_large)
            
            shadow_offset = 3
            draw.text(((width - w_top) / 2 + shadow_offset, height - 250 + shadow_offset), text_top, font=font_large, fill=(0,0,0,100))
            draw.text(((width - w_bottom) / 2 + shadow_offset, height - 150 + shadow_offset), text_bottom, font=font_v_large, fill=(0,0,0,100))

            draw.text(((width - w_top) / 2, height - 250), text_top, font=font_large, fill="white")
            draw.text(((width - w_bottom) / 2, height - 150), text_bottom, font=font_v_large, fill="#f59e0b") # Bananya yellow

            safe_title = "".join(x for x in job_title if x.isalnum() or x in " -_").replace(" ", "_").lower()
            final_filename = f"poster_{safe_title}_{int(time.time())}.jpg"
            final_path = os.path.join(self.output_dir, final_filename)
            
            img.save(final_path, quality=95)
            os.remove(temp_path)
            
            logger.info(f"Poster saved via Nanobanana: {final_path}")
            return f"/static/posters/{final_filename}"
        except Exception as e:
            logger.error(f"Poster generation processing error (Nanobanana): {e}", exc_info=True)
            return None

    def generate_apply_link(self, job_title):
        hr_email = config.COMPANY_EMAIL
        subject = f"Application for {job_title}"
        body = f"Hi Recruitment Team,\n\nI am interested in applying for the {job_title} position. Please find my resume attached."
        params = urllib.parse.urlencode({'view': 'cm', 'fs': '1', 'to': hr_email, 'su': subject, 'body': body})
        return f"https://mail.google.com/mail/?{params}"

nanobanana_service = NanobananaService()
