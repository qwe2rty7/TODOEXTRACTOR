import os
import time
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import msal
import requests
import anthropic
from todo_manager import TodoManager

load_dotenv()

class EmailMonitor:
    def __init__(self):
        self.client_id = os.getenv('CLIENT_ID')
        self.client_secret = os.getenv('CLIENT_SECRET')
        self.tenant_id = os.getenv('TENANT_ID')
        self.user_email = os.getenv('USER_EMAIL')
        self.claude_api_key = os.getenv('ANTHROPIC_API_KEY')
        
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        self.scope = ["https://graph.microsoft.com/.default"]
        self.graph_url = "https://graph.microsoft.com/v1.0"
        
        # Initialize MSAL app
        self.app = msal.ConfidentialClientApplication(
            self.client_id,
            authority=self.authority,
            client_credential=self.client_secret
        )
        
        # Initialize Claude client
        if self.claude_api_key:
            self.claude_client = anthropic.Anthropic(api_key=self.claude_api_key)
        else:
            self.claude_client = None
        
        # Track last check time - timezone aware
        self.last_check = datetime.now(timezone.utc) - timedelta(minutes=5)
        
        # Initialize todo manager
        self.todo_manager = TodoManager()
        
    def get_access_token(self):
        """Get access token for Graph API"""
        result = self.app.acquire_token_silent(self.scope, account=None)
        if not result:
            result = self.app.acquire_token_for_client(scopes=self.scope)
        
        if "access_token" in result:
            return result['access_token']
        else:
            print(f"Error getting token: {result.get('error')}")
            print(f"Description: {result.get('error_description')}")
            return None
    
    def get_recent_emails(self, minutes_back=5):
        """Fetch emails from the last X minutes"""
        token = self.get_access_token()
        if not token:
            return []
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        # Calculate time filter - using UTC
        from datetime import timezone
        time_filter = (datetime.now(timezone.utc) - timedelta(minutes=minutes_back)).strftime('%Y-%m-%dT%H:%M:%SZ')
        
        # Build query
        endpoint = f"{self.graph_url}/users/{self.user_email}/messages"
        params = {
            '$filter': f"receivedDateTime ge {time_filter}",
            '$select': 'id,subject,from,bodyPreview,body,receivedDateTime,isRead',
            '$orderby': 'receivedDateTime desc',
            '$top': 50
        }
        
        try:
            response = requests.get(endpoint, headers=headers, params=params)
            response.raise_for_status()
            
            emails = response.json().get('value', [])
            return emails
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching emails: {e}")
            return []
    
    def is_actionable_email(self, email):
        """Basic filter to skip obvious spam/newsletters"""
        subject = email.get('subject', '').lower()
        sender = email.get('from', {}).get('emailAddress', {}).get('address', '').lower()
        
        # Skip patterns
        skip_patterns = [
            'unsubscribe',
            'newsletter',
            'no-reply',
            'noreply',
            'notification',
            'alert@',
            'updates@',
            'marketing',
            'promo'
        ]
        
        for pattern in skip_patterns:
            if pattern in subject or pattern in sender:
                return False
        
        return True
    
    def analyze_email_with_claude(self, email):
        """Send email to Claude for todo analysis"""
        if not self.claude_client:
            print("ERROR: Claude API key not configured")
            return []
        
        try:
            # Get email body content
            body = email.get('body', {}).get('content', '')
            if not body:
                body = email.get('bodyPreview', '')
            
            # Prepare the prompt
            prompt = f"""
            Analyze this email and extract any action items or todos that are specifically assigned to or directed at the email recipient (me). 
            
            Email Details:
            From: {email['from']['emailAddress']['name']} <{email['from']['emailAddress']['address']}>
            Subject: {email['subject']}
            
            Email Body:
            {body}
            
            Instructions:
            - Only extract action items that require me to do something, I'd rather you add them to my todo list versus miss something
            - Ignore items where I'm clearly not the target (e.g., CC'd, group emails, spam emails)
            - Format each todo as a clear, actionable statement
            - Include any relevant context or deadlines
            - If there are no actionable items for me, respond with "NO_TODOS"
            
            Format your response as a simple list, one todo per line, starting each with "- "
            """
            
            response = self.claude_client.messages.create(
                model="claude-3-5-sonnet-20241022",  # Use latest non-deprecated model
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            result = response.content[0].text.strip()
            
            if result == "NO_TODOS":
                return []
            
            # Parse todos from response
            todos = []
            for line in result.split('\n'):
                line = line.strip()
                if line.startswith('- '):
                    todo_text = line[2:].strip()
                    # Filter out "no todos found" type messages
                    if not any(phrase in todo_text.lower() for phrase in [
                        'no action items', 'no todos', 'cannot identify', 
                        'no specific action', 'not the target'
                    ]):
                        todos.append(todo_text)
            
            return todos
            
        except Exception as e:
            print(f"ERROR analyzing email with Claude: {e}")
            return []
    
    def check_new_emails(self):
        """Check for new emails and extract todos"""
        print("Checking for new emails...")
        
        # Get recent emails
        emails = self.get_recent_emails(minutes_back=1)
        
        # Filter for new, actionable emails
        new_emails = []
        for email in emails:
            # Parse the ISO format date properly
            received_str = email['receivedDateTime']
            if received_str.endswith('Z'):
                received_time = datetime.fromisoformat(received_str[:-1] + '+00:00')
            else:
                received_time = datetime.fromisoformat(received_str)
            
            # Only process if newer than last check
            if received_time > self.last_check:
                if self.is_actionable_email(email):
                    new_emails.append(email)
        
        # Process new emails for todos
        if new_emails:
            print(f"\nFound {len(new_emails)} new email(s):")
            for email in new_emails:
                print(f"\n--- New Email ---")
                print(f"From: {email['from']['emailAddress']['name']} <{email['from']['emailAddress']['address']}>")
                print(f"Subject: {email['subject']}")
                print(f"Preview: {email['bodyPreview'][:100]}...")
                print(f"Received: {email['receivedDateTime']}")
                
                # Analyze with Claude for todos
                print("Analyzing with Claude...")
                todos = self.analyze_email_with_claude(email)
                
                if todos:
                    print(f"Found {len(todos)} action item(s):")
                    for todo in todos:
                        print(f"  - {todo}")
                    
                    # Save todos using TodoManager
                    sender = email['from']['emailAddress']['name']
                    subject = email['subject']
                    source_info = f"Extracted from email: {sender} - {subject}"
                    self.todo_manager.save_todos_to_file(todos, source_info)
                else:
                    print("No action items found for you")
                    
                print("-" * 50)
        else:
            print(f"No new emails (checked at {datetime.now().strftime('%H:%M:%S')})")
        
        # Update last check time
        self.last_check = datetime.now(timezone.utc)