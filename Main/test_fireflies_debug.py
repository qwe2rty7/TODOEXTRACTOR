import os
import json
import requests
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()

def test_fireflies_queries():
    api_key = os.getenv('FIREFLIES_API_KEY')
    user_email = os.getenv('USER_EMAIL')
    
    print("Debugging Fireflies GraphQL Queries")
    print("=" * 50)
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    # Test 1: Simplest query - just get transcripts
    print("\n1. Simple query (no variables):")
    query = """
    query {
        transcripts(limit: 5) {
            id
            title
            date
        }
    }
    """
    
    payload = {"query": query}
    
    response = requests.post("https://api.fireflies.ai/graphql", headers=headers, json=payload)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("SUCCESS - Simple query works")
    else:
        print(f"FAILED: {response.text}")
    
    # Test 2: Query with fromDate variable
    print("\n2. Query with fromDate:")
    from_date = (datetime.now(timezone.utc) - timedelta(hours=24)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    
    query = """
    query GetTranscripts($fromDate: DateTime!) {
        transcripts(fromDate: $fromDate, limit: 5) {
            id
            title
            date
        }
    }
    """
    
    variables = {"fromDate": from_date}
    payload = {"query": query, "variables": variables}
    
    response = requests.post("https://api.fireflies.ai/graphql", headers=headers, json=payload)
    print(f"Status: {response.status_code}")
    print(f"fromDate used: {from_date}")
    if response.status_code == 200:
        print("SUCCESS - fromDate query works")
    else:
        print(f"FAILED: {response.text}")
    
    # Test 3: Query with participant_email
    print("\n3. Query with participant_email:")
    
    query = """
    query GetTranscripts($email: String) {
        transcripts(participant_email: $email, limit: 5) {
            id
            title
            date
            participants
        }
    }
    """
    
    variables = {"email": user_email}
    payload = {"query": query, "variables": variables}
    
    response = requests.post("https://api.fireflies.ai/graphql", headers=headers, json=payload)
    print(f"Status: {response.status_code}")
    print(f"Email used: {user_email}")
    if response.status_code == 200:
        print("SUCCESS - participant_email query works")
    else:
        print(f"FAILED: {response.text}")
    
    # Test 4: Combined query (the one that's failing)
    print("\n4. Combined query (fromDate + participant_email):")
    
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
        }
    }
    """
    
    variables = {
        "fromDate": from_date,
        "participantEmail": user_email
    }
    payload = {"query": query, "variables": variables}
    
    response = requests.post("https://api.fireflies.ai/graphql", headers=headers, json=payload)
    print(f"Status: {response.status_code}")
    print(f"Variables: {json.dumps(variables, indent=2)}")
    if response.status_code == 200:
        print("SUCCESS - Combined query works")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    else:
        print(f"FAILED: {response.text}")

if __name__ == "__main__":
    test_fireflies_queries()