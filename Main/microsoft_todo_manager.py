import os
import requests
import msal
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

class MicrosoftTodoManager:
    def __init__(self):
        self.client_id = os.getenv('CLIENT_ID')
        self.client_secret = os.getenv('CLIENT_SECRET')
        self.tenant_id = os.getenv('TENANT_ID')
        self.user_email = os.getenv('USER_EMAIL')
        
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        self.scope = ["https://graph.microsoft.com/.default"]
        self.graph_url = "https://graph.microsoft.com/v1.0"
        
        # Initialize MSAL app
        self.app = msal.ConfidentialClientApplication(
            self.client_id,
            authority=self.authority,
            client_credential=self.client_secret
        )
        
        # Default list name
        self.default_list_name = "Email Tasks"
        self.default_list_id = None
    
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
    
    def get_or_create_task_list(self, list_name=None):
        """Get or create a task list in Microsoft To Do"""
        if list_name is None:
            list_name = self.default_list_name
            
        token = self.get_access_token()
        if not token:
            return None
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        # Get all task lists
        endpoint = f"{self.graph_url}/users/{self.user_email}/todo/lists"
        
        try:
            response = requests.get(endpoint, headers=headers)
            response.raise_for_status()
            
            lists = response.json().get('value', [])
            
            # Check if our list already exists
            for task_list in lists:
                if task_list.get('displayName') == list_name:
                    print(f"Found existing task list: {list_name}")
                    self.default_list_id = task_list['id']
                    return task_list['id']
            
            # Create new list if it doesn't exist
            create_data = {
                "displayName": list_name
            }
            
            response = requests.post(endpoint, headers=headers, json=create_data)
            response.raise_for_status()
            
            new_list = response.json()
            print(f"Created new task list: {list_name}")
            self.default_list_id = new_list['id']
            return new_list['id']
            
        except requests.exceptions.RequestException as e:
            print(f"Error managing task list: {e}")
            if hasattr(e.response, 'text'):
                print(f"Response: {e.response.text}")
            return None
    
    def add_task(self, title, body=None, importance="normal", due_date=None, list_id=None):
        """Add a task to Microsoft To Do"""
        token = self.get_access_token()
        if not token:
            return False
        
        # Get or create list if not specified
        if list_id is None:
            list_id = self.get_or_create_task_list()
            if not list_id:
                print("Failed to get task list")
                return False
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        # Build task data
        task_data = {
            "title": title,
            "importance": importance  # low, normal, high
        }
        
        # Add body/details if provided
        if body:
            task_data["body"] = {
                "content": body,
                "contentType": "text"
            }
        
        # Add due date if provided
        if due_date:
            task_data["dueDateTime"] = {
                "dateTime": due_date.isoformat(),
                "timeZone": "UTC"
            }
        
        # Create the task
        endpoint = f"{self.graph_url}/users/{self.user_email}/todo/lists/{list_id}/tasks"
        
        try:
            response = requests.post(endpoint, headers=headers, json=task_data)
            response.raise_for_status()
            
            task = response.json()
            print(f"✅ Added task to Microsoft To Do: {title}")
            return task
            
        except requests.exceptions.RequestException as e:
            print(f"Error adding task: {e}")
            if hasattr(e.response, 'text'):
                print(f"Response: {e.response.text}")
            return False
    
    def add_tasks_batch(self, tasks, list_name=None):
        """Add multiple tasks to Microsoft To Do"""
        # Get or create list
        list_id = self.get_or_create_task_list(list_name)
        if not list_id:
            print("Failed to get task list")
            return False
        
        success_count = 0
        for task in tasks:
            if isinstance(task, dict):
                title = task.get('action', task.get('title', ''))
                body = task.get('details', task.get('body', ''))
                importance = task.get('importance', 'normal')
                due_date = task.get('due_date')
            else:
                # Simple string task
                title = str(task)
                body = None
                importance = 'normal'
                due_date = None
            
            if title:
                result = self.add_task(title, body, importance, due_date, list_id)
                if result:
                    success_count += 1
        
        print(f"Successfully added {success_count}/{len(tasks)} tasks to Microsoft To Do")
        return success_count > 0
    
    def check_duplicate_task(self, title, list_id=None):
        """Check if a task with the same title already exists"""
        token = self.get_access_token()
        if not token:
            return False
        
        if list_id is None:
            list_id = self.default_list_id or self.get_or_create_task_list()
            if not list_id:
                return False
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        # Get all tasks in the list
        endpoint = f"{self.graph_url}/users/{self.user_email}/todo/lists/{list_id}/tasks"
        
        try:
            response = requests.get(endpoint, headers=headers)
            response.raise_for_status()
            
            tasks = response.json().get('value', [])
            
            # Check for duplicates (case-insensitive)
            title_lower = title.lower().strip()
            for task in tasks:
                if task.get('title', '').lower().strip() == title_lower:
                    # Only consider incomplete tasks as duplicates
                    if task.get('status') != 'completed':
                        return True
            
            return False
            
        except requests.exceptions.RequestException as e:
            print(f"Error checking for duplicate: {e}")
            return False
    
    def add_structured_todos(self, structured_todos, list_name=None):
        """Add structured todos with metadata to Microsoft To Do"""
        if not structured_todos:
            return False
        
        # Get or create list
        list_id = self.get_or_create_task_list(list_name)
        if not list_id:
            print("Failed to get task list")
            return False
        
        success_count = 0
        skipped_count = 0
        
        for todo in structured_todos:
            title = todo.get('action', '')
            
            # Check for duplicate
            if self.check_duplicate_task(title, list_id):
                print(f"⏭️  Skipping duplicate task: {title}")
                skipped_count += 1
                continue
            
            # Build detailed body with metadata
            body_parts = []
            
            # Add details if present
            if todo.get('details'):
                body_parts.append(f"Details: {todo['details']}")
            
            # Add email metadata if present
            if 'email_metadata' in todo:
                metadata = todo['email_metadata']
                body_parts.append("\n--- Source Email ---")
                body_parts.append(f"From: {metadata.get('from', 'Unknown')}")
                body_parts.append(f"Subject: {metadata.get('subject', 'No subject')}")
                body_parts.append(f"Received: {metadata.get('received_time', 'Unknown')}")
                body_parts.append(f"Source: {metadata.get('source', 'email')}")
            
            body = "\n".join(body_parts) if body_parts else None
            
            # Determine importance based on certain keywords
            importance = "normal"
            if any(word in title.lower() for word in ['urgent', 'asap', 'critical', 'important']):
                importance = "high"
            
            # Add the task
            result = self.add_task(title, body, importance, None, list_id)
            if result:
                success_count += 1
        
        print(f"\n📊 Summary: Added {success_count} new tasks, skipped {skipped_count} duplicates")
        return success_count > 0