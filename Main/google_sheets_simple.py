import os
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

class GoogleSheetsManager:
    def __init__(self):
        self.creds_path = os.getenv('GOOGLE_SHEETS_CREDS_PATH')
        self.sheet_id = os.getenv('GOOGLE_SHEETS_ID')
        self.enabled = False
        
        if self.creds_path and self.sheet_id and os.path.exists(self.creds_path):
            try:
                self.creds = service_account.Credentials.from_service_account_file(
                    self.creds_path,
                    scopes=['https://www.googleapis.com/auth/spreadsheets']
                )
                self.service = build('sheets', 'v4', credentials=self.creds)
                self.sheet = self.service.spreadsheets()
                self.enabled = True
                print(f"✅ Google Sheets connected: {self.sheet_id}")
                self.setup_headers()
            except Exception as e:
                print(f"❌ Google Sheets setup error: {e}")
    
    def setup_headers(self):
        """Set up column headers if sheet is empty"""
        try:
            result = self.sheet.values().get(
                spreadsheetId=self.sheet_id,
                range='A1:F1'
            ).execute()
            
            if not result.get('values'):
                # Add headers
                headers = [['Date/Time', 'Source', 'Action Item', 'Priority', 'Status', 'Email Subject']]
                self.sheet.values().update(
                    spreadsheetId=self.sheet_id,
                    range='A1:F1',
                    valueInputOption='RAW',
                    body={'values': headers}
                ).execute()
                print("Added headers to Google Sheet")
        except:
            pass
    
    def add_todos(self, todos, source_info):
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
                        source_info,
                        todo.get('action', ''),
                        todo.get('priority', 'Medium'),
                        'New',
                        todo.get('subject', '')
                    ])
                else:
                    # Simple string todo
                    rows.append([
                        timestamp,
                        source_info,
                        todo,
                        'Medium',
                        'New',
                        ''
                    ])
            
            # Append to sheet
            body = {'values': rows}
            result = self.sheet.values().append(
                spreadsheetId=self.sheet_id,
                range='A:F',
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            
            print(f"✅ Added {len(rows)} todos to Google Sheets")
            return True
            
        except Exception as e:
            print(f"❌ Google Sheets append error: {e}")
            return False