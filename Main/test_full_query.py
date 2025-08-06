import os
import json
import requests
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()

def test_full_query():
    api_key = os.getenv('FIREFLIES_API_KEY')
    user_email = os.getenv('USER_EMAIL')
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    from_date = (datetime.now(timezone.utc) - timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    
    print("Testing FULL Fireflies query (as used in fireflies_monitor.py)")
    print("=" * 50)
    
    # This is the exact query from fireflies_monitor.py
    query = """
    query GetRecentTranscripts($fromDate: DateTime!, $participantEmail: String) {
      transcripts(
        fromDate: $fromDate
        participant_email: $participantEmail
        limit: 20
      ) {
        id
        title
        date
        organizer_email
        participants
        summary {
          action_items
          overview
        }
        sentences {
          text
          speaker_name
          speaker_email
        }
      }
    }
    """
    
    variables = {
        "fromDate": from_date,
        "participantEmail": user_email
    }
    
    payload = {
        "query": query,
        "variables": variables
    }
    
    print(f"Variables: {json.dumps(variables, indent=2)}")
    print("\nSending request...")
    
    try:
        response = requests.post("https://api.fireflies.ai/graphql", headers=headers, json=payload)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if 'errors' in data:
                print(f"GraphQL Errors: {json.dumps(data['errors'], indent=2)}")
            else:
                print("SUCCESS!")
                print(f"Response: {json.dumps(data, indent=2)}")
        else:
            print(f"HTTP Error: {response.text}")
            
    except Exception as e:
        print(f"Exception: {e}")
    
    # Now test without participant_email to get ALL transcripts
    print("\n" + "=" * 50)
    print("Testing without participant_email filter:")
    
    query2 = """
    query GetRecentTranscripts($fromDate: DateTime!) {
      transcripts(
        fromDate: $fromDate
        limit: 5
      ) {
        id
        title
        date
        organizer_email
        participants
        summary {
          action_items
          overview
        }
      }
    }
    """
    
    variables2 = {"fromDate": from_date}
    payload2 = {"query": query2, "variables": variables2}
    
    response2 = requests.post("https://api.fireflies.ai/graphql", headers=headers, json=payload2)
    print(f"Status Code: {response2.status_code}")
    
    if response2.status_code == 200:
        data2 = response2.json()
        if 'errors' in data2:
            print(f"GraphQL Errors: {json.dumps(data2['errors'], indent=2)}")
        else:
            print("SUCCESS!")
            transcripts = data2.get('data', {}).get('transcripts', [])
            print(f"Found {len(transcripts)} transcript(s)")
            for t in transcripts:
                print(f"  - {t['title']} (organizer: {t.get('organizer_email', 'unknown')})")

if __name__ == "__main__":
    test_full_query()