import os
import json
import requests
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()

def test_fireflies_connection():
    """Test basic Fireflies API connection"""
    api_key = os.getenv('FIREFLIES_API_KEY')
    user_email = os.getenv('USER_EMAIL')
    
    print("Testing Fireflies API Connection")
    print(f"API Key: {'Found' if api_key else 'Missing'}")
    print(f"User Email: {user_email}")
    print("-" * 50)
    
    if not api_key:
        print("ERROR: No API key found. Please check your .env file")
        return
    
    # Test 1: Simple user query
    print("\nTest 1: Getting user info...")
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    query = """
    query {
        user {
            email
            name
        }
    }
    """
    
    payload = {
        "query": query
    }
    
    try:
        response = requests.post("https://api.fireflies.ai/graphql", headers=headers, json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code != 200:
            print(f"\nERROR: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")
    
    print("-" * 50)
    
    # Test 2: Get recent transcripts without date filter
    print("\nTest 2: Getting recent transcripts (no date filter)...")
    
    query = """
    query {
        transcripts(limit: 5) {
            id
            title
            date
        }
    }
    """
    
    payload = {
        "query": query
    }
    
    try:
        response = requests.post("https://api.fireflies.ai/graphql", headers=headers, json=payload)
        print(f"Status Code: {response.status_code}")
        data = response.json()
        
        if 'errors' in data:
            print(f"GraphQL Errors: {json.dumps(data['errors'], indent=2)}")
        else:
            print(f"Response: {json.dumps(data, indent=2)}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    print("-" * 50)
    
    # Test 3: Get transcripts with date filter
    print("\nTest 3: Getting transcripts with date filter...")
    
    # Try different date formats
    from_date = (datetime.now(timezone.utc) - timedelta(days=7)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    print(f"Using fromDate: {from_date}")
    
    query = """
    query GetRecentTranscripts($fromDate: DateTime!) {
        transcripts(
            fromDate: $fromDate
            limit: 5
        ) {
            id
            title
            date
        }
    }
    """
    
    variables = {
        "fromDate": from_date
    }
    
    payload = {
        "query": query,
        "variables": variables
    }
    
    try:
        response = requests.post("https://api.fireflies.ai/graphql", headers=headers, json=payload)
        print(f"Status Code: {response.status_code}")
        data = response.json()
        
        if 'errors' in data:
            print(f"GraphQL Errors: {json.dumps(data['errors'], indent=2)}")
        else:
            print(f"Response: {json.dumps(data, indent=2)}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    print("-" * 50)
    
    # Test 4: Get ALL transcripts to see what's available
    print("\nTest 4: Getting ALL available transcripts...")
    
    query = """
    query {
        transcripts(limit: 5) {
            id
            title
            date
            participants
            organizer_email
        }
    }
    """
    
    payload = {
        "query": query
    }
    
    try:
        response = requests.post("https://api.fireflies.ai/graphql", headers=headers, json=payload)
        print(f"Status Code: {response.status_code}")
        data = response.json()
        
        if 'errors' in data:
            print(f"GraphQL Errors: {json.dumps(data['errors'], indent=2)}")
        else:
            print(f"Response: {json.dumps(data, indent=2)}")
            
    except Exception as e:
        print(f"Exception: {e}")
    
    print("-" * 50)
    
    # Test 5: Get transcripts for specific user email
    print(f"\nTest 5: Getting transcripts for {user_email}...")
    
    query = """
    query GetUserTranscripts($email: String) {
        transcripts(
            participant_email: $email
            limit: 5
        ) {
            id
            title
            date
            participants
            organizer_email
        }
    }
    """
    
    variables = {
        "email": user_email
    }
    
    payload = {
        "query": query,
        "variables": variables
    }
    
    try:
        response = requests.post("https://api.fireflies.ai/graphql", headers=headers, json=payload)
        print(f"Status Code: {response.status_code}")
        data = response.json()
        
        if 'errors' in data:
            print(f"GraphQL Errors: {json.dumps(data['errors'], indent=2)}")
        else:
            print(f"Response: {json.dumps(data, indent=2)}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_fireflies_connection()