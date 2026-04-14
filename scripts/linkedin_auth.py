import os
import http.server
import socketserver
import webbrowser
import urllib.parse
import requests
from dotenv import load_dotenv

# Redefine redirect URI to match LinkedIn Console
REDIRECT_URI = "http://localhost:3001/"

load_dotenv()

class OAuthHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        query_components = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        if 'code' in query_components:
            code = query_components['code'][0]
            self.wfile.write(b"<h1>Authorization Successful!</h1><p>You can close this tab and return to the terminal.</p>")
            self.server.authorization_code = code

def get_linkedin_token():
    client_id = os.getenv('LINKEDIN_CLIENT_ID')
    client_secret = os.getenv('LINKEDIN_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        print("Error: LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET must be set in your .env file.")
        return

    # 1. Direct the user to the authorization URL
    scopes = urllib.parse.quote('w_member_social openid profile email')
    auth_url = (
        f"https://www.linkedin.com/oauth/v2/authorization?"
        f"response_type=code&client_id={client_id}&redirect_uri={urllib.parse.quote(REDIRECT_URI)}&"
        f"scope={scopes}&state=Drandom_string"
    )

    print(f"\n1. Opening browser for authorization...")
    print(f"URL: {auth_url}\n")
    
    # Start a local server to handle the redirect
    handler = OAuthHandler
    try:
        with socketserver.TCPServer(("", 3001), handler) as httpd:
            httpd.allow_reuse_address = True
            httpd.authorization_code = None
            webbrowser.open(auth_url)
            
            print("Waiting for callback on http://localhost:3001/...")
            httpd.handle_request()
            code = httpd.authorization_code
    except Exception as e:
        print(f"Server error: {e}")
        return

    if not code:
        print("Failed to get authorization code.")
        return

    # 2. Exchange authorization code for an access token
    print("2. Exchanging code for Access Token...")
    token_url = "https://www.linkedin.com/oauth/v2/accessToken"
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'client_id': client_id,
        'client_secret': client_secret
    }
    
    response = requests.post(token_url, data=data)
    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data.get('access_token')
        print(f"\n--- SUCCESS! ---")
        print(f"ACCESS TOKEN: {access_token}")
        print("\nCOPY the token above and paste it into your .env file as LINKEDIN_ACCESS_TOKEN")
        
        # 3. Get Person ID (URN)
        print("\n3. Fetching your Person ID...")
        profile_url = "https://api.linkedin.com/v2/userinfo"
        headers = {'Authorization': f'Bearer {access_token}'}
        profile_res = requests.get(profile_url, headers=headers)
        if profile_res.status_code == 200:
            profile_data = profile_res.json()
            person_id = profile_data.get('sub')
            
            print(f"\n✅ AUTHORIZATION COMPLETE!")
            print(f"====================================================")
            print(f"COPY AND PASTE THESE LINES INTO YOUR .env FILE:")
            print(f"====================================================")
            print(f"LINKEDIN_ACCESS_TOKEN={access_token}")
            print(f"LINKEDIN_PERSON_ID={person_id}")
            print(f"====================================================")
        else:
            print(f"Error fetching Person ID: {profile_res.text}")
            print(f"\n--- SUCCESS (Partial) ---")
            print(f"ACCESS TOKEN: {access_token}")
            print("Copy the token above into .env as LINKEDIN_ACCESS_TOKEN")

if __name__ == "__main__":
    get_linkedin_token()
