import os
import requests
import time
from urllib.parse import quote
from backend.config import config

class LinkedInService:
    def __init__(self):
        self.access_token = config.LINKEDIN_ACCESS_TOKEN
        self.person_id = config.LINKEDIN_PERSON_ID
        self.org_id = config.LINKEDIN_ORGANIZATION_ID
        self.base_url = "https://api.linkedin.com/v2"

    def post_job_announcement(self, job_title, image_path, apply_link, include_image=True):
        if not self.access_token:
            return {"error": "LinkedIn access token missing."}
        
        if self.org_id:
            author_urn = f"urn:li:organization:{self.org_id}"
        elif self.person_id:
            author_urn = f"urn:li:person:{self.person_id}"
        else:
            return {"error": "Neither Person ID nor Organization ID found."}

        text = f"🚀 We're hiring for {job_title}!\n\nSend your resume via the link below to apply:\n{apply_link}\n\n#Hiring #{job_title.replace(' ', '')} #Recruitment #Careers"

        url = f"{self.base_url}/ugcPosts"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-Restli-Protocol-Version': '2.0.0',
            'Content-Type': 'application/json'
        }

        if include_image and image_path:
            # Handle absolute path for reading
            if image_path.startswith('/static/'):
                full_image_path = os.path.join(os.path.dirname(__file__), '..', image_path.lstrip('/'))
            else:
                full_image_path = image_path

            image_urn = self._register_image(full_image_path, author_urn)
            if not image_urn:
                return {"error": "Failed to upload image to LinkedIn."}
            
            share_content = {
                "shareCommentary": {"text": text},
                "shareMediaCategory": "IMAGE",
                "media": [
                    {
                        "status": "READY",
                        "description": {"text": f"Hiring for {job_title}"},
                        "media": image_urn,
                        "title": {"text": f"Join our team as {job_title}"}
                    }
                ]
            }
        else:
            share_content = {
                "shareCommentary": {"text": text},
                "shareMediaCategory": "NONE"
            }

        post_data = {
            "author": author_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": share_content
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }

        try:
            response = requests.post(url, headers=headers, json=post_data, timeout=30)
            if response.status_code == 201:
                data = response.json()
                post_urn = data.get('id', '')
                numeric_id = post_urn.split(':')[-1] if post_urn else ""
                activity_url = f"https://www.linkedin.com/feed/update/urn:li:activity:{numeric_id}"
                return {"status": "success", "url": activity_url, "id": post_urn}
            else:
                print(f"LinkedIn API Error: {response.text}")
                return {"error": response.text}
        except Exception as e:
            return {"error": str(e)}

    def _register_image(self, image_path, owner_urn):
        url = f"{self.base_url}/assets?action=registerUpload"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'X-Restli-Protocol-Version': '2.0.0',
            'Content-Type': 'application/json'
        }
        
        register_data = {
            "registerUploadRequest": {
                "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                "owner": owner_urn,
                "serviceRelationships": [
                    {
                        "relationshipType": "OWNER",
                        "identifier": "urn:li:userGeneratedContent"
                    }
                ]
            }
        }

        try:
            response = requests.post(url, headers=headers, json=register_data, timeout=20)
            if response.status_code != 200:
                print(f"LinkedIn Register Image Error ({response.status_code}): {response.text}")
                return None

            data = response.json()
            upload_url = data['value']['uploadMechanism']['com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest']['uploadUrl']
            asset_urn = data['value']['asset']

            # Upload binary
            with open(image_path, 'rb') as f:
                upload_response = requests.put(
                    upload_url, 
                    data=f, 
                    headers={
                        'Authorization': f'Bearer {self.access_token}',
                        'Content-Type': 'image/jpeg'
                    },
                    timeout=60
                )
                if upload_response.status_code != 201:
                    print(f"LinkedIn Upload Binary Error ({upload_response.status_code}): {upload_response.text}")
                    return None

            # LinkedIn needs a few seconds to process
            time.sleep(5)
            return asset_urn
        except Exception as e:
            print(f"LinkedIn Image Upload Error: {e}")
            return None

linkedin_service = LinkedInService()
