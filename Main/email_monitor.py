import os
import time
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import msal
import requests
import anthropic
from todo_manager import TodoManager
from google_sheets_simple import GoogleSheetsManager

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
        
        # Initialize Google Sheets
        self.sheets_manager = GoogleSheetsManager()
        
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
        """Basic filter to skip obvious spam/newsletters and meeting responses"""
        subject = email.get('subject', '').lower()
        
        # Skip meeting responses and calendar items
        if subject.startswith(('accepted:', 'declined:', 'tentative:', 'canceled:', 'updated:')):
            return False
        
        # Skip outbound emails (emails FROM the monitored user)
        if 'from' in email:
            sender = email.get('from', {}).get('emailAddress', {}).get('address', '').lower()
            if sender == self.user_email.lower():
                print(f"Skipping outbound email from {sender} (user's own email)")
                return False
        else:
            sender = ''
        
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
            'promo',
            'out of office',
            'automatic reply'
        ]
        
        for pattern in skip_patterns:
            if pattern in subject or (sender and pattern in sender):
                return False
        
        # Skip emails with no meaningful content
        body = email.get('body', {}).get('content', '')
        body_preview = email.get('bodyPreview', '')
        
        # Check if email has any actual text content (not just HTML/whitespace)
        import re
        text_content = re.sub(r'<[^>]+>', '', body)  # Strip HTML
        text_content = text_content.strip()
        
        if not text_content and not body_preview:
            return False
            
        return True
    
    def analyze_email_with_claude_no_sender(self, email):
        """Send email to Claude for todo analysis when sender is unknown"""
        if not self.claude_client:
            print("ERROR: Claude API key not configured")
            return []
        
        try:
            # Get email body content
            body = email.get('body', {}).get('content', '')
            if not body:
                body = email.get('bodyPreview', '')
            
            # Prepare the prompt for emails without sender
            prompt = f"""
            You are {self.user_email} analyzing a forwarded email sent TO you. Extract action items for YOU to do.
            
            IMPORTANT: This may be an email chain/thread. Focus on the LATEST/NEWEST message at the top, but use the older messages below for context to understand what's being discussed.
            
            Email Details:
            From: Unknown (Forwarded Email)  
            Subject: {email.get('subject', 'No subject')}
            Recipient: {self.user_email} (YOU)
            
            Email Body (newest message first, older replies below):
            {body}
            
            Instructions:
            Extract action items for YOU ({self.user_email}) from the NEWEST/LATEST message only.
            Use the older messages for context only - DO NOT extract action items from older parts of the email chain.
            Remember: YOU are {self.user_email}, so don't refer to yourself in third person.
            
            Look for action items:
            
            1. ACTION ITEMS (things I need to do) - FROM THE LATEST MESSAGE ONLY:
            ONLY extract action items that require SIGNIFICANT effort or are BUSINESS-CRITICAL.
            
            DO extract:
            - Direct requests or tasks assigned to me that require substantial work
            - Important decisions I need to make that affect business outcomes
            - Follow-ups with high business impact or urgency
            - Information I need to provide that requires research or preparation
            - Important people I should contact for business purposes
            
            DO NOT extract routine/trivial tasks like:
            - Joining scheduled calls/meetings (that's just calendar management)
            - Clicking links to view content (too trivial)
            - Simple acknowledgments or "thanks" replies
            - Routine meeting preparations unless specifically complex
            - Basic calendar scheduling or rescheduling
            
            2. KEY NOTES (important context to remember) - CAN BE FROM ANY MESSAGE IN THE CHAIN:
            - Important opinions or feedback shared (from any message)
            - Key concerns or risks mentioned (from any message)
            - Financial details or numbers (from any message)
            - Decisions made or positions taken (from any message)
            - Important dates or deadlines (from any message)
            - Context that helps understand the current situation
            
            BE SELECTIVE about action items - only extract items that require significant effort, planning, or have business impact. 
            It's better to miss trivial tasks than to clutter the todo list with routine activities.
            This is a forwarded email, so pay attention to the forwarded content for context.
            
            IMPORTANT: Keep action items SHORT and ACTION-ORIENTED (like "Call John", "Review contract", "Send proposal"). 
            Each action item should include its specific details/context.
            
            Format your response as JSON EXACTLY like this:
            
            {{
              "action_items": [
                {{
                  "action": "Concise action description",
                  "details": "Specific context, who, what, when, why details"
                }}
              ]
            }}
            
            If there are no action items, return: {{"action_items": []}}
            """
            
            response = self.claude_client.messages.create(
                model="claude-opus-4-20250514",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            result = response.content[0].text.strip()
            
            # Parse the JSON response
            try:
                import json
                # Extract just the JSON part (Claude sometimes adds extra text after)
                json_start = result.find('{')
                json_end = result.rfind('}') + 1
                if json_start != -1 and json_end != 0:
                    json_text = result[json_start:json_end]
                    data = json.loads(json_text)
                else:
                    data = json.loads(result)  # Fallback to original
                action_items = data.get('action_items', [])
                
                # Convert to structured format with email metadata
                structured_todos = []
                for item in action_items:
                    structured_todo = {
                        'action': item.get('action', ''),
                        'details': item.get('details', ''),
                        'email_metadata': {
                            'from': 'Unknown (Forwarded Email)',
                            'subject': email.get('subject', 'No subject'),
                            'received_time': email.get('receivedDateTime', 'Unknown'),
                            'source': 'forwarded_email'
                        }
                    }
                    structured_todos.append(structured_todo)
                
                # Print structured todos
                if structured_todos:
                    print(f"\n✅ Found {len(structured_todos)} ACTION ITEM(S) from forwarded email:")
                    for todo in structured_todos:
                        print(f"  📌 {todo['action']}")
                        if todo['details']:
                            print(f"     Details: {todo['details']}")
                
                return structured_todos
                
            except json.JSONDecodeError as e:
                print(f"ERROR parsing JSON response: {e}")
                print(f"Raw response: {result}")
                return []
            
        except Exception as e:
            print(f"ERROR analyzing email with Claude: {e}")
            return []
    
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
            You are {self.user_email} analyzing an email sent TO you. Extract action items for YOU to do.
            
            IMPORTANT: This may be an email chain/thread. Focus on the LATEST/NEWEST message at the top, but use the older messages below for context to understand what's being discussed.
            
            Email Details:
            From: {email['from']['emailAddress']['name']} <{email['from']['emailAddress']['address']}>
            Subject: {email['subject']}
            Recipient: {self.user_email} (YOU)
            
            Email Body (newest message first, older replies below):
            {body}
            
            Instructions:
            Extract action items for YOU ({self.user_email}) from the NEWEST/LATEST message only.
            Use the older messages for context only - DO NOT extract action items from older parts of the email chain.
            Remember: YOU are {self.user_email}, so don't refer to yourself in third person.
            
            Look for action items:
            
            1. ACTION ITEMS (things I need to do) - FROM THE LATEST MESSAGE ONLY:
            ONLY extract action items that require SIGNIFICANT effort or are BUSINESS-CRITICAL. 
            
            DO extract:
            - Direct requests or tasks assigned to me that require substantial work
            - Important decisions I need to make that affect business outcomes
            - Follow-ups with high business impact or urgency
            - Information I need to provide that requires research or preparation
            - Important people I should contact for business purposes
            
            DO NOT extract routine/trivial tasks like:
            - Joining scheduled calls/meetings (that's just calendar management)
            - Clicking links to view content (too trivial)
            - Simple acknowledgments or "thanks" replies
            - Routine meeting preparations unless specifically complex
            - Basic calendar scheduling or rescheduling
            - spam/marketing messages 
            
            2. KEY NOTES (important context to remember) - CAN BE FROM ANY MESSAGE IN THE CHAIN:
            - Important opinions or feedback shared (from any message)
            - Key concerns or risks mentioned (from any message)
            - Financial details or numbers (from any message)
            - Decisions made or positions taken (from any message)
            - Important dates or deadlines (from any message)
            - Context that helps understand the current situation
            
            BE SELECTIVE about action items - only extract items that require significant effort, planning, or have business impact. 
            Yet, it's still better to add a trivial task than to miss something on the todo list.

            IMPORTANT: Keep action items SHORT and ACTION-ORIENTED (like "Call John about...", "Review contract terms ...", "Send proposal about ..."). 
            Each action item should include its specific details/context.
            
            Format your response as JSON EXACTLY like this:
            
            {{
              "action_items": [
                {{
                  "action": "Concise action description",
                  "details": "Specific context, who, what, when, why details"
                }}
              ]
            }}
            
            If there are no action items, return: {{"action_items": []}}
            """
            
            response = self.claude_client.messages.create(
                model="claude-opus-4-20250514",  # Use latest non-deprecated model
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            result = response.content[0].text.strip()
            
            # Parse the JSON response
            try:
                import json
                # Extract just the JSON part (Claude sometimes adds extra text after)
                json_start = result.find('{')
                json_end = result.rfind('}') + 1
                if json_start != -1 and json_end != 0:
                    json_text = result[json_start:json_end]
                    data = json.loads(json_text)
                else:
                    data = json.loads(result)  # Fallback to original
                action_items = data.get('action_items', [])
                
                # Convert to structured format with email metadata
                structured_todos = []
                for item in action_items:
                    structured_todo = {
                        'action': item.get('action', ''),
                        'details': item.get('details', ''),
                        'email_metadata': {
                            'from': email['from']['emailAddress']['name'] + " <" + email['from']['emailAddress']['address'] + ">",
                            'subject': email['subject'],
                            'received_time': email['receivedDateTime'],
                            'source': 'email'
                        }
                    }
                    structured_todos.append(structured_todo)
                
                # Print structured todos
                if structured_todos:
                    print(f"\n✅ Found {len(structured_todos)} ACTION ITEM(S):")
                    for todo in structured_todos:
                        print(f"  📌 {todo['action']}")
                        if todo['details']:
                            print(f"     Details: {todo['details']}")
                
                return structured_todos
                
            except json.JSONDecodeError as e:
                print(f"ERROR parsing JSON response: {e}")
                print(f"Raw response: {result}")
                return []
            
        except Exception as e:
            print(f"ERROR analyzing email with Claude: {e}")
            return []
    
    def save_structured_todos(self, structured_todos):
        """Save structured todos to JSON file for future integrations"""
        if not structured_todos:
            return
            
        try:
            import json
            import os
            
            # Create structured data directory if it doesn't exist
            structured_dir = os.path.join(os.path.dirname(self.todo_manager.todo_file), 'structured_todos')
            os.makedirs(structured_dir, exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"todos_{timestamp}.json"
            filepath = os.path.join(structured_dir, filename)
            
            # Save structured todos
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(structured_todos, f, indent=2, ensure_ascii=False)
                
            print(f"Saved {len(structured_todos)} structured todo(s) to {filepath}")
            
            # Upload to secure storage
            if self.secure_storage:
                if hasattr(self.secure_storage, 'upload_todos'):
                    self.secure_storage.upload_todos(structured_todos)
                elif hasattr(self.secure_storage, 'save_todos'):
                    self.secure_storage.save_todos(structured_todos)
            
        except Exception as e:
            print(f"ERROR saving structured todos: {e}")
    
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
                
                # Handle emails without 'from' field (e.g., some forwarded emails)
                if 'from' not in email:
                    print(f"Processing email without sender info")
                    print(f"Subject: {email.get('subject', 'No subject')}")
                    
                    # For forwarded emails, we can still process them
                    subject = email.get('subject', '')
                    if subject.upper().startswith('FW:'):
                        print("This is a forwarded email - processing anyway")
                        
                        # Print email details with fallback values
                        print(f"From: (Forwarded email - sender unknown)")
                        print(f"Subject: {subject}")
                        print(f"Preview: {email.get('bodyPreview', '')[:100]}...")
                        print(f"Received: {email.get('receivedDateTime', 'Unknown time')}")
                        
                        # Print full email body for debugging
                        body = email.get('body', {}).get('content', '')
                        if not body:
                            body = email.get('bodyPreview', '')
                        
                        # Clean HTML for better readability
                        import re
                        clean_body = re.sub(r'<style[^>]*>.*?</style>', '', body, flags=re.DOTALL)
                        clean_body = re.sub(r'<script[^>]*>.*?</script>', '', clean_body, flags=re.DOTALL)
                        clean_body = re.sub(r'<[^>]+>', ' ', clean_body)
                        clean_body = re.sub(r'\s+', ' ', clean_body).strip()
                        
                        print(f"\n=== FULL EMAIL CONTENT (CLEANED) ===")
                        print(clean_body[:2000])
                        if len(clean_body) > 2000:
                            print(f"... (truncated, {len(clean_body) - 2000} more characters)")
                        print("=== END EMAIL CONTENT ===\n")
                        
                        # Still analyze forwarded emails
                        print("Analyzing forwarded email with Claude...")
                        structured_todos = self.analyze_email_with_claude_no_sender(email)
                        
                        if structured_todos:
                            # Save structured todos with JSON format
                            self.save_structured_todos(structured_todos)
                            
                            # Also save to text file for backward compatibility
                            simple_todos = [todo['action'] for todo in structured_todos]
                            subject = email['subject']
                            source_info = f"Extracted from forwarded email: {subject}"
                            self.todo_manager.save_todos_to_file(simple_todos, source_info)
                            
                            # Add to Google Sheets
                            self.sheets_manager.add_todos(simple_todos, source_info)
                        else:
                            print("\n❌ No action items found for you")
                        
                        print("-" * 50)
                    else:
                        print(f"Skipping email without 'from' field: {subject}")
                    continue
                
                print(f"From: {email['from']['emailAddress']['name']} <{email['from']['emailAddress']['address']}>")
                print(f"Subject: {email['subject']}")
                print(f"Preview: {email['bodyPreview'][:100]}...")
                print(f"Received: {email['receivedDateTime']}")
                
                # Print full email body for debugging
                body = email.get('body', {}).get('content', '')
                if not body:
                    body = email.get('bodyPreview', '')
                
                # Clean HTML for better readability
                import re
                # Remove HTML tags but keep text
                clean_body = re.sub(r'<style[^>]*>.*?</style>', '', body, flags=re.DOTALL)
                clean_body = re.sub(r'<script[^>]*>.*?</script>', '', clean_body, flags=re.DOTALL)
                clean_body = re.sub(r'<[^>]+>', ' ', clean_body)
                clean_body = re.sub(r'\s+', ' ', clean_body).strip()
                
                print(f"\n=== FULL EMAIL CONTENT (CLEANED) ===")
                print(clean_body[:2000])  # Limit to 2000 chars to avoid flooding terminal
                if len(clean_body) > 2000:
                    print(f"... (truncated, {len(clean_body) - 2000} more characters)")
                print("=== END EMAIL CONTENT ===\n")
                
                # Analyze with Claude for todos
                print("Analyzing with Claude...")
                structured_todos = self.analyze_email_with_claude(email)
                
                if structured_todos:
                    # Save structured todos with JSON format
                    self.save_structured_todos(structured_todos)
                    
                    # Also save to text file for backward compatibility
                    simple_todos = [todo['action'] for todo in structured_todos]
                    sender = email['from']['emailAddress']['name']
                    subject = email['subject']
                    source_info = f"Extracted from email: {sender} - {subject}"
                    self.todo_manager.save_todos_to_file(simple_todos, source_info)
                    
                    # Add to Google Sheets
                    self.sheets_manager.add_todos(simple_todos, source_info)
                else:
                    print("\n❌ No action items found for you")
                    
                print("-" * 50)
        else:
            print(f"No new emails (checked at {datetime.now().strftime('%H:%M:%S')})")
        
        # Update last check time
        self.last_check = datetime.now(timezone.utc)