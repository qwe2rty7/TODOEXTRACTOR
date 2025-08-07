import os
import sys
sys.path.append('./Main')
from google_sheets_simple import GoogleSheetsManager
from datetime import datetime

# Initialize Google Sheets
print("Initializing Google Sheets Manager...")
sheets = GoogleSheetsManager()

# Test data
test_todos = [
    {
        'action': 'Test TODO from direct script',
        'details': 'This is a test to verify Google Sheets is working',
        'priority': 'High',
        'subject': 'Direct Test'
    },
    {
        'action': 'Second test item',
        'details': 'Another test item to verify batch writing',
        'priority': 'Medium',
        'subject': 'Direct Test'
    }
]

# Try to add todos
print(f"\nAttempting to add {len(test_todos)} test todos...")
success = sheets.add_todos(test_todos, "Manual Test Script")

if success:
    print("\n[SUCCESS] Test todos added to Google Sheet!")
    print("Check your sheet at: https://docs.google.com/spreadsheets/d/12QlUM83Ne0L4Szhuv_dNxas-QpI0PhqaCQp6EY7CZh8")
else:
    print("\n[FAILED] Could not add todos to Google Sheet")
    print("Check the error messages above for details")