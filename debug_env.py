import os
import json

print("\n=== ALL ENVIRONMENT VARIABLES ===")
print("Total env vars:", len(os.environ))
print("\n--- Google Sheets Related ---")

# Check for any Google Sheets related vars
for key in sorted(os.environ.keys()):
    if 'GOOGLE' in key.upper() or 'SHEET' in key.upper() or 'CREDS' in key.upper():
        value = os.environ[key]
        if 'CREDS_JSON' in key:
            # Truncate JSON for display
            print(f"{key}: {value[:50]}..." if len(value) > 50 else f"{key}: {value}")
        else:
            print(f"{key}: {value}")

print("\n--- All Other Vars (first 20) ---")
count = 0
for key in sorted(os.environ.keys()):
    if not ('GOOGLE' in key.upper() or 'SHEET' in key.upper() or 'CREDS' in key.upper()):
        value = os.environ[key]
        # Truncate long values
        if len(value) > 100:
            print(f"{key}: {value[:100]}...")
        else:
            print(f"{key}: {value}")
        count += 1
        if count >= 20:
            print("... and more")
            break

print("\n=== SPECIFIC CHECKS ===")
print(f"GOOGLE_SHEETS_ID exists: {'GOOGLE_SHEETS_ID' in os.environ}")
print(f"GOOGLE_SHEETS_CREDS_JSON exists: {'GOOGLE_SHEETS_CREDS_JSON' in os.environ}")
print(f"GOOGLE_SHEETS_CREDS_PATH exists: {'GOOGLE_SHEETS_CREDS_PATH' in os.environ}")

# Try to parse JSON if it exists
if 'GOOGLE_SHEETS_CREDS_JSON' in os.environ:
    try:
        creds = json.loads(os.environ['GOOGLE_SHEETS_CREDS_JSON'])
        print(f"\nJSON is valid! Service account: {creds.get('client_email', 'Unknown')}")
    except Exception as e:
        print(f"\nJSON parsing error: {e}")
        print(f"First 200 chars: {os.environ['GOOGLE_SHEETS_CREDS_JSON'][:200]}")