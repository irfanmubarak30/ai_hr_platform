import os
import requests
import urllib.parse
import time
import logging
from PIL import Image, ImageDraw, ImageFont
from backend.config import config

logger = logging.getLogger(__name__)

class ImageService:
    def __init__(self, output_dir=None):
        if output_dir is None:
            # Save in static/posters for easy access by frontend
            self.output_dir = os.path.join(os.path.dirname(__file__), '..', 'static', 'posters')
        else:
            self.output_dir = output_dir
            
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def generate_job_poster(self, job_title):
        """Generate a professional job poster with AI background and text overlay."""
        # AI Image generation prompt
        prompt = f"Professional commercial photography of a confident {job_title}, friendly smile, sharp focus on face, cinematic lighting, modern office background, high-end aesthetic, 8k resolution, photorealistic, no text"
        
        # Fallback image URL (reliable professional office)
        FALLBACK_IMAGE_URL = "https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=1024&h=1024"
        
        # 1. Try Hugging Face Flux model (Free & High quality)
        if config.HUGGINGFACE_API_TOKEN:
            try:
                logger.info(f"AI Generation ({job_title}) - Attempting Hugging Face FLUX model...")
                API_URL = "https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-schnell"
                headers = {"Authorization": f"Bearer {config.HUGGINGFACE_API_TOKEN}"}
                
                # Flux Schnell works great with 4 steps on Hugging Face
                payload = {"inputs": prompt}
                
                start_time = time.time()
                temp_response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
                elapsed = time.time() - start_time
                
                if temp_response.status_code == 200:
                    logger.info(f"Hugging Face FLUX model succeeded in {elapsed:.2f}s")
                    response = temp_response
                elif temp_response.status_code == 503:
                    logger.warning("Hugging Face model is loading (503). Falling back to Pollinations/Unsplash.")
                else:
                    logger.warning(f"Hugging Face returned status {temp_response.status_code}: {temp_response.text}")
            except Exception as e:
                logger.warning(f"Hugging Face attempt failed: {e}")

        # 2. Fallback to Pollinations if Hugging Face is not configured or fails
        if not response:
            models = ["flux", "turbo"]
            for model in models:
                seed = int(time.time())
                current_prompt = prompt if model == "flux" else f"Professional office {job_title}, photorealistic, modern aesthetic"
                encoded = urllib.parse.quote(current_prompt)
                url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&nologo=true&seed={seed}&model={model}"
                
                try:
                    logger.info(f"AI Generation ({job_title}) - Attempting Pollinations {model.upper()} fallback...")
                    start_time = time.time()
                    temp_response = requests.get(url, timeout=60)
                    elapsed = time.time() - start_time
                    
                    if temp_response.status_code == 200 and 'image' in temp_response.headers.get('Content-Type', ''):
                        logger.info(f"Pollinations {model.upper()} model succeeded in {elapsed:.2f}s")
                        response = temp_response
                        break
                except Exception as e:
                    logger.warning(f"Pollinations {model.upper()} attempt failed: {e}")

        try:
                temp_filename = f"base_{int(time.time())}.jpg"
                temp_path = os.path.join(self.output_dir, temp_filename)
                
                logger.info(f"Saving base image content ({len(response.content)} bytes) to {temp_path}...")
                with open(temp_path, 'wb') as f:
                    f.write(response.content)
                
                size = len(response.content)
                
                if size < 1000:
                    logger.error(f"Downloaded file too small ({size} bytes). Likely invalid image.")
                    if os.path.exists(temp_path): os.remove(temp_path)
                    return None

                # Add Text Overlay using Pillow
                logger.info(f"Adding professional text overlay for {job_title}...")
                try:
                    img = Image.open(temp_path)
                    img.verify() # Verify it's an image
                    img = Image.open(temp_path) # Re-open for processing
                except Exception as e:
                    logger.error(f"Invalid image file downloaded: {e}")
                    if os.path.exists(temp_path): os.remove(temp_path)
                    return None

                draw = ImageDraw.Draw(img, "RGBA")
                width, height = img.size

                # Font selection (try common Windows paths)
                font_paths = [
                    "C:\\Windows\\Fonts\\arialbd.ttf",
                    "C:\\Windows\\Fonts\\segoeuib.ttf",
                    "C:\\Windows\\Fonts\\Inter-Bold.ttf",
                    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
                ]
                
                def get_font(size):
                    for fp in font_paths:
                        if os.path.exists(fp):
                            return ImageFont.truetype(fp, size)
                    return ImageFont.load_default()

                # Dynamic font scaling
                v_large_size = 110
                large_size = 70
                max_width = width - 80 # 40px padding on each side
                
                font_v_large = get_font(v_large_size)
                font_large = get_font(large_size)
                
                # Shrink title font if too wide
                text_bottom = job_title.upper()
                w_bottom = draw.textlength(text_bottom, font=font_v_large)
                
                while w_bottom > max_width and v_large_size > 40:
                    v_large_size -= 5
                    font_v_large = get_font(v_large_size)
                    w_bottom = draw.textlength(text_bottom, font=font_v_large)
                
                # Semi-transparent overlay at the bottom
                overlay_height = 280
                draw.rectangle([0, height - overlay_height, width, height], fill=(0, 0, 0, 160))

                # Text Content
                text_top = "WE ARE HIRING"
                
                # Positioning
                w_top = draw.textlength(text_top, font=font_large)
                
                # Draw text shadows
                shadow_offset = 2
                draw.text(((width - w_top) / 2 + shadow_offset, height - 210 + shadow_offset), text_top, font=font_large, fill=(0,0,0,120))
                draw.text(((width - w_bottom) / 2 + shadow_offset, height - 130 + shadow_offset), text_bottom, font=font_v_large, fill=(0,0,0,120))

                # Draw main text
                draw.text(((width - w_top) / 2, height - 210), text_top, font=font_large, fill="white")
                draw.text(((width - w_bottom) / 2, height - 130), text_bottom, font=font_v_large, fill="#f59e0b") # Bananya yellow

                # Final save
                safe_title = "".join(x for x in job_title if x.isalnum() or x in " -_").replace(" ", "_").lower()
                final_filename = f"poster_{safe_title}_{int(time.time())}.jpg"
                final_path = os.path.join(self.output_dir, final_filename)
                
                img.save(final_path, quality=95)
                os.remove(temp_path)
                
                logger.info(f"Poster saved: {final_path}")
                return f"/static/posters/{final_filename}"
        except Exception as e:
            logger.error(f"Poster generation processing error: {e}", exc_info=True)
            return None

    def generate_apply_link(self, job_title):
        """Generates a Google Mail compose link for applying."""
        hr_email = config.COMPANY_EMAIL
        subject = f"Application for {job_title}"
        body = f"Hi Recruitment Team,\n\nI am interested in applying for the {job_title} position. Please find my resume attached."
        
        params = urllib.parse.urlencode({'view': 'cm', 'fs': '1', 'to': hr_email, 'su': subject, 'body': body})
        return f"https://mail.google.com/mail/?{params}"

image_service = ImageService()
