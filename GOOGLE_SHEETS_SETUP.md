# Google Sheets Setup

## Quick Setup (5 minutes)

### 1. Create Google Sheet
1. Go to [sheets.google.com](https://sheets.google.com)
2. Create a new blank sheet
3. Name it "Email Todos" or whatever you want
4. Copy the Sheet ID from the URL: `https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit`

### 2. Set up Google Cloud API
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project (or use existing)
3. Enable the "Google Sheets API"
4. Go to "Credentials" → "Create Credentials" → "Service Account"
5. Create a service account with any name
6. Download the JSON key file
7. Share your Google Sheet with the service account email (found in the JSON file)

### 3. Configure the App
Add to your `.env` file:
```
GOOGLE_SHEETS_ID=your_sheet_id_here
GOOGLE_SHEETS_CREDS_PATH=path/to/your/credentials.json
```

For Railway deployment:
1. Upload the credentials.json file to your project
2. Set environment variables in Railway dashboard

### 4. Deploy
The app will automatically:
- Create column headers in your sheet
- Add new todos with timestamp, source, priority
- You can edit/track status directly in Google Sheets

## Column Layout
The sheet will have these columns:
- **Date/Time**: When the todo was found
- **Source**: Which email/meeting it came from  
- **Action Item**: The actual task
- **Priority**: High/Medium/Low
- **Status**: New/In Progress/Done (you can edit this)
- **Email Subject**: Subject of the source email

## Troubleshooting
- Make sure the service account email has edit access to your sheet
- Check Railway logs if todos aren't appearing
- Verify the sheet ID is correct