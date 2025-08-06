"""
Google Sheets Todo Sync
Syncs todos to a Google Sheet for easy monitoring

Setup:
1. Go to Google Cloud Console
2. Enable Google Sheets API
3. Create credentials (Service Account)
4. Download JSON key file
5. Share your Google Sheet with the service account email
6. Set GOOGLE_SHEETS_CREDS_PATH and GOOGLE_SHEETS_ID in .env
"""

import os
import json
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

class GoogleSheetsSync:
    def __init__(self):
        creds_path = os.getenv('GOOGLE_SHEETS_CREDS_PATH')
        self.sheet_id = os.getenv('GOOGLE_SHEETS_ID')
        
        if creds_path and self.sheet_id:
            try:
                self.creds = service_account.Credentials.from_service_account_file(
                    creds_path,
                    scopes=['https://www.googleapis.com/auth/spreadsheets']
                )
                self.service = build('sheets', 'v4', credentials=self.creds)
                self.enabled = True
            except Exception as e:
                print(f"Google Sheets init error: {e}")
                self.enabled = False
        else:
            self.enabled = False
            
    def add_todos(self, todos, source):
        """Add todos to Google Sheet"""
        if not self.enabled or not todos:
            return False
            
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Prepare rows
            rows = []
            for todo in todos:
                if isinstance(todo, dict):
                    rows.append([
                        timestamp,
                        source,
                        todo.get('action', ''),
                        todo.get('priority', 'Medium'),
                        todo.get('deadline', ''),
                        'Pending'
                    ])
                else:
                    rows.append([timestamp, source, todo, 'Medium', '', 'Pending'])
            
            # Append to sheet
            body = {'values': rows}
            result = self.service.spreadsheets().values().append(
                spreadsheetId=self.sheet_id,
                range='A:F',
                valueInputOption='RAW',
                body=body
            ).execute()
            
            print(f"✅ Added {len(rows)} todos to Google Sheets")
            return True
            
        except Exception as e:
            print(f"Google Sheets sync error: {e}")
            return False