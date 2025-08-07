import os
import json
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build

load_dotenv()

def test_google_sheets():
    print("Testing Google Sheets connection...\n")
    
    # Check environment variables
    creds_path = os.getenv('GOOGLE_SHEETS_CREDS_PATH')
    creds_json = os.getenv('GOOGLE_SHEETS_CREDS_JSON')
    sheet_id = os.getenv('GOOGLE_SHEETS_ID')
    
    print(f"1. Environment variables:")
    print(f"   GOOGLE_SHEETS_ID: {sheet_id or 'NOT SET'}")
    print(f"   GOOGLE_SHEETS_CREDS_PATH: {creds_path or 'NOT SET'}")
    print(f"   GOOGLE_SHEETS_CREDS_JSON: {'SET' if creds_json else 'NOT SET'}")
    
    if not sheet_id:
        print("\n[ERROR] GOOGLE_SHEETS_ID not set!")
        return
    
    # Check credentials file
    if creds_path:
        print(f"\n2. Checking credentials file: {creds_path}")
        if os.path.exists(creds_path):
            print(f"   [OK] File exists")
            try:
                with open(creds_path, 'r') as f:
                    creds_data = json.load(f)
                    print(f"   [OK] Valid JSON")
                    print(f"   Service account: {creds_data.get('client_email', 'Unknown')}")
            except Exception as e:
                print(f"   [ERROR] Error reading file: {e}")
        else:
            print(f"   [ERROR] File does not exist!")
    
    # Try to connect
    print(f"\n3. Attempting connection...")
    
    try:
        # Try file-based credentials first
        if creds_path and os.path.exists(creds_path):
            print("   Using file-based credentials...")
            creds = service_account.Credentials.from_service_account_file(
                creds_path,
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )
        # Try JSON env var
        elif creds_json:
            print("   Using JSON env var credentials...")
            creds_data = json.loads(creds_json)
            creds = service_account.Credentials.from_service_account_info(
                creds_data,
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )
        else:
            print("   [ERROR] No valid credentials found!")
            return
        
        # Build service
        service = build('sheets', 'v4', credentials=creds)
        sheet = service.spreadsheets()
        
        # Test read access
        print(f"\n4. Testing read access to sheet {sheet_id}...")
        result = sheet.values().get(
            spreadsheetId=sheet_id,
            range='A1:F1'
        ).execute()
        
        values = result.get('values', [])
        if values:
            print(f"   [OK] Successfully read sheet! Headers: {values[0]}")
        else:
            print(f"   [OK] Successfully connected! Sheet is empty.")
        
        # Test write access
        print(f"\n5. Testing write access...")
        test_data = [['TEST', 'CONNECTION', 'SUCCESS', 'High', 'Test', 'Test Email']]
        result = sheet.values().append(
            spreadsheetId=sheet_id,
            range='A:F',
            valueInputOption='RAW',
            insertDataOption='INSERT_ROWS',
            body={'values': test_data}
        ).execute()
        print(f"   [OK] Successfully wrote test data!")
        
        print(f"\n[OK] ALL TESTS PASSED! Google Sheets is working correctly.")
        
    except Exception as e:
        print(f"\n[ERROR] Connection failed: {e}")
        print(f"\nTroubleshooting:")
        print(f"1. Make sure you shared the sheet with the service account email")
        print(f"2. Check that the sheet ID is correct")
        print(f"3. Verify the credentials JSON is valid")

if __name__ == "__main__":
    test_google_sheets()