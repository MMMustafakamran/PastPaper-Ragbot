# Google Cloud Vision API Setup Guide

## Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing one)
3. Enable **Cloud Vision API**:
   - Go to "APIs & Services" > "Library"
   - Search for "Cloud Vision API"
   - Click "Enable"

## Step 2: Create or Use Service Account

### Option A: Use Existing Service Account (if you see "Cloud Vision AI Service Agent")

If you already see a service account like "Cloud Vision AI Service Agent":
1. Click on that service account
2. Go directly to **Step 3: Create and Download Key** below

### Option B: Create New Service Account

1. Go to "IAM & Admin" > "Service Accounts"
2. Click "Create Service Account"
3. Fill in:
   - **Name**: `    ` (or any name)
   - **Description**: OCR for past papers extraction
4. Click "Create and Continue"
5. Grant role: **Cloud Vision API User** (or **Editor** for full access)
6. Click "Continue" then "Done"
7. Click on the service account you just created

## Step 3: Create and Download Key

1. Make sure you're viewing the service account details page
   - If using existing account: Click on "Cloud Vision AI Service Agent" (or similar)
   - If you just created one: You should already be on its page
2. Go to "Keys" tab (at the top)
3. Click "Add Key" > "Create new key"
4. Select **JSON** format
5. Click "Create" - JSON file will download automatically
   - **Important**: Save this file! You won't be able to download it again.
   - Suggested name: `google-vision-credentials.json`

## Step 4: Configure Credentials

### Option A: Using keys.json (Recommended)

1. Save the downloaded JSON file to your project folder (e.g., `google-credentials.json`)
2. Update `keys.json`:
   ```json
   {
     "GEMINI_API_KEY": "AIzaSyAuqjpwopDI-KGcWJz0UwyZVmtnEZVzb54",
     "GOOGLE_CLOUD_VISION_CREDENTIALS_PATH": "google-credentials.json"
   }
   ```

### Option B: Using Environment Variable

1. Save the JSON file anywhere
2. Set environment variable:
   ```powershell
   $env:GOOGLE_APPLICATION_CREDENTIALS="C:\path\to\google-credentials.json"
   ```

## Step 5: Test OCR

Run the test script:
```bash
python test_extraction.py
```

## Pricing

- **Free Tier**: 1,000 pages/month
- **After Free Tier**: $1.50 per 1,000 pages

## Troubleshooting

### Error: "Permission denied"
- Make sure service account has "Cloud Vision API User" role
- Check that Vision API is enabled

### Error: "Invalid credentials"
- Verify JSON file path is correct
- Check JSON file is valid (not corrupted)

### Error: "Quota exceeded"
- You've exceeded free tier (1,000 pages/month)
- Wait for next month or upgrade billing

