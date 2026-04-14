# 🔐 OAuth2 Setup Guide for Personal Gmail

This guide explains how to set up OAuth2 authentication to use your **personal Gmail account** with the AI HR Platform instead of Google Workspace service accounts.

## Why OAuth2?

- ✅ Works with **personal Gmail accounts** (not just Google Workspace)
- ✅ More secure - no need to store full credentials
- ✅ User-friendly authorization flow
- ❌ Cannot work with service accounts (use service account method instead)

---

## 📋 Prerequisites

1. A **personal Gmail account** (or any Google account)
2. Access to [Google Cloud Console](https://console.cloud.google.com)
3. The platform already installed and running

---

## 🔧 Step-by-Step Setup

### Step 1: Create OAuth2 Credentials in Google Cloud

1. Go to [Google Cloud Console](https://console.cloud.google.com)

2. **Create a new project** (or select existing):
   - Click "Select a project" → "New Project"
   - Name it "AI HR Platform"
   - Click "Create"

3. **Enable Gmail API**:
   - Go to "APIs & Services" → "Library"
   - Search for "Gmail API"
   - Click on it and press "Enable"

4. **Create OAuth2 Credentials**:
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth 2.0 Client IDs"
   - If prompted, configure the OAuth consent screen first:
     - User Type: "External"
     - Click "Create"
     - Fill in App details (name, email, etc.)
     - Add scopes: Search for "gmail" and select these:
       - `https://www.googleapis.com/auth/gmail.readonly`
       - `https://www.googleapis.com/auth/gmail.modify`
     - Save and continue
   
5. **Download Credentials**:
   - After consent screen is set up, go back to "Credentials"
   - Click "Create Credentials" → "OAuth 2.0 Client IDs"
   - Application type: "Desktop application"
   - Click "Create"
   - Click "Download JSON" button
   - Save the file

### Step 2: Add Credentials to Platform

1. **Place the JSON file**:
   ```bash
   # Move the downloaded credentials to:
   credentials/oauth2_credentials.json
   ```

2. **Enable OAuth2 in `.env`**:
   ```bash
   # Edit your .env file and add:
   USE_OAUTH2=true
   OAUTH2_CREDENTIALS_FILE=credentials/oauth2_credentials.json
   ```

### Step 3: Authorize Your Account

1. **Start the platform**:
   ```bash
   python app.py
   ```

2. **Open the platform**:
   - Go to http://localhost:5000
   - Navigate to **Settings** page

3. **Click "Setup OAuth2"** button
   - This will open a Google authorization page
   - **Sign in with your Gmail account**
   - Click "Allow" to grant access
   - You'll be redirected back to the platform

4. **Restart the server**:
   ```bash
   # Stop the current server (Ctrl+C)
   # Start it again:
   python app.py
   ```

---

## ✅ Verification

After setup, verify OAuth2 is working:

1. Go to http://localhost:5000/api/oauth2/status
   - Should show `"oauth2_active": true`

2. Check the **Settings** page:
   - Should show "OAuth2 Active" status

3. Test CV collection:
   - Send a test email with PDF attachment to your Gmail
   - The system should automatically collect it

---

## 📁 File Structure

After setup, your credentials folder should look like:
```
credentials/
├── oauth2_credentials.json      # Downloaded from Google Cloud
└── oauth2_token.json            # Auto-generated after authorization
```

---

## 🔄 Switching Between OAuth2 and Service Account

### Use OAuth2 (Personal Gmail)
```env
USE_OAUTH2=true
OAUTH2_CREDENTIALS_FILE=credentials/oauth2_credentials.json
```

### Use Service Account (Google Workspace)
```env
USE_OAUTH2=false
GMAIL_CREDENTIALS_FILE=credentials/gmail_credentials.json
COMPANY_EMAIL=your-workspace-email@yourdomain.com
```

---

## ❌ Troubleshooting

### "OAuth2 credentials file not found"
- Download credentials from Google Cloud Console
- Place at: `credentials/oauth2_credentials.json`

### "OAuth2 token not found"
- Run through Step 3 (Authorize Your Account)
- Check that `credentials/oauth2_token.json` exists

### Authorization page won't open
- Make sure `localhost:5000` is accessible
- Try accessing the setup URL manually:
  ```
  http://localhost:5000/api/oauth2/setup
  ```

### Token expired
- The system automatically refreshes tokens
- If issues persist, delete `credentials/oauth2_token.json` and re-authorize

### Still getting service account errors
- Make sure `USE_OAUTH2=true` in `.env`
- Restart the server
- Check platform logs for errors

---

## 🔒 Security Notes

- **oauth2_token.json**: Contains user access token. Keep secure!
- **oauth2_credentials.json**: Download from Google Cloud. Never commit to git!
- Add to `.gitignore`:
  ```
  credentials/oauth2_*.json
  credentials/oauth2_token.json
  ```

---

## 📞 Support

If you encounter issues:
1. Check Google Cloud Console for API enablement
2. Verify credentials file is in correct location
3. Check server logs for detailed error messages
4. Try re-authorizing (delete token file and repeat Step 3)
