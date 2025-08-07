import os
import json
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

class GoogleSheetsManager:
    def __init__(self):
        self.creds_path = os.getenv('GOOGLE_SHEETS_CREDS_PATH')
        self.creds_json = os.getenv('GOOGLE_SHEETS_CREDS_JSON')  # For Railway - store JSON as env var
        self.sheet_id = os.getenv('GOOGLE_SHEETS_ID')
        self.enabled = False
        
        # Debug output
        print("\n=== Google Sheets Configuration ===")
        print(f"GOOGLE_SHEETS_ID: {'SET' if self.sheet_id else 'NOT SET'}")
        print(f"GOOGLE_SHEETS_CREDS_JSON: {'SET' if self.creds_json else 'NOT SET'}")
        print(f"GOOGLE_SHEETS_CREDS_PATH: {self.creds_path or 'NOT SET'}")
        if self.creds_path:
            print(f"  File exists: {os.path.exists(self.creds_path)}")
        
        # Try JSON environment variable first (for Railway)
        if self.creds_json and self.sheet_id:
            try:
                print("Attempting to connect via GOOGLE_SHEETS_CREDS_JSON...")
                print(f"JSON length: {len(self.creds_json)} chars")
                
                # Handle potential newline issues in Railway
                cleaned_json = self.creds_json.replace('\\n', '\n')
                print(f"Cleaned JSON length: {len(cleaned_json)} chars")
                
                creds_data = json.loads(cleaned_json)
                print(f"Parsed JSON keys: {list(creds_data.keys())}")
                
                self.creds = service_account.Credentials.from_service_account_info(
                    creds_data,
                    scopes=['https://www.googleapis.com/auth/spreadsheets']
                )
                self.service = build('sheets', 'v4', credentials=self.creds)
                self.sheet = self.service.spreadsheets()
                self.enabled = True
                print(f"[OK] Google Sheets connected (via env): {self.sheet_id}")
                self.setup_headers()
            except json.JSONDecodeError as e:
                print(f"[ERROR] JSON parsing error: {e}")
                print(f"First 100 chars of JSON: {self.creds_json[:100]}")
            except Exception as e:
                print(f"[ERROR] Google Sheets env setup error: {e}")
                import traceback
                print(f"Full traceback: {traceback.format_exc()}")
        # Fall back to file path
        elif self.creds_path and self.sheet_id and os.path.exists(self.creds_path):
            try:
                print("Attempting to connect via file path...")
                self.creds = service_account.Credentials.from_service_account_file(
                    self.creds_path,
                    scopes=['https://www.googleapis.com/auth/spreadsheets']
                )
                self.service = build('sheets', 'v4', credentials=self.creds)
                self.sheet = self.service.spreadsheets()
                self.enabled = True
                print(f"[OK] Google Sheets connected (via file): {self.sheet_id}")
                self.setup_headers()
            except Exception as e:
                print(f"[ERROR] Google Sheets file setup error: {e}")
        else:
            print("[ERROR] Google Sheets not configured - missing credentials or sheet ID")
            if not self.sheet_id:
                print("  - GOOGLE_SHEETS_ID not set")
            if not self.creds_json and not (self.creds_path and os.path.exists(self.creds_path)):
                print("  - No valid credentials (neither JSON env var nor file path)")
        print("===================================\n")
    
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
        if not self.enabled:
            print("[WARNING] Google Sheets not enabled - check credentials")
            return False
        if not todos:
            print("[WARNING] No todos to add to Google Sheets")
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
            
            print(f"[OK] Added {len(rows)} todos to Google Sheets")
            return True
            
        except Exception as e:
            print(f"[ERROR] Google Sheets append error: {e}")
            return False