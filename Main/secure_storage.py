"""
Secure Storage Solutions for Private Todos
"""

import os
import json
import base64
from datetime import datetime
from cryptography.fernet import Fernet
from dotenv import load_dotenv
import dropbox
import boto3

load_dotenv()

class SecureStorage:
    """Base class for secure storage implementations"""
    
    def __init__(self):
        # Generate or load encryption key
        self.encryption_key = os.getenv('ENCRYPTION_KEY')
        if not self.encryption_key:
            # Generate a new key if none exists
            self.encryption_key = Fernet.generate_key().decode()
            print(f"Generated new encryption key. Add to .env: ENCRYPTION_KEY={self.encryption_key}")
        
        self.cipher = Fernet(self.encryption_key.encode())
    
    def encrypt_data(self, data):
        """Encrypt data before storage"""
        if isinstance(data, dict) or isinstance(data, list):
            data = json.dumps(data)
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt_data(self, encrypted_data):
        """Decrypt data after retrieval"""
        return self.cipher.decrypt(encrypted_data.encode()).decode()


class DropboxStorage(SecureStorage):
    """Store encrypted todos in Dropbox"""
    
    def __init__(self):
        super().__init__()
        self.access_token = os.getenv('DROPBOX_ACCESS_TOKEN')
        if self.access_token:
            self.dbx = dropbox.Dropbox(self.access_token)
            self.enabled = True
        else:
            self.enabled = False
            print("Dropbox storage not configured. Add DROPBOX_ACCESS_TOKEN to .env")
    
    def upload_todos(self, todos, filename=None):
        """Upload encrypted todos to Dropbox"""
        if not self.enabled:
            return False
        
        try:
            if not filename:
                filename = f"/todos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.enc"
            
            # Encrypt the data
            encrypted = self.encrypt_data(todos)
            
            # Upload to Dropbox
            self.dbx.files_upload(
                encrypted.encode(),
                filename,
                mode=dropbox.files.WriteMode.overwrite
            )
            
            print(f"✅ Encrypted todos uploaded to Dropbox: {filename}")
            return True
        except Exception as e:
            print(f"Dropbox upload error: {e}")
            return False
    
    def download_todos(self, filename="/todos_latest.enc"):
        """Download and decrypt todos from Dropbox"""
        if not self.enabled:
            return None
        
        try:
            # Download from Dropbox
            _, response = self.dbx.files_download(filename)
            encrypted_data = response.content.decode()
            
            # Decrypt
            decrypted = self.decrypt_data(encrypted_data)
            return json.loads(decrypted)
        except Exception as e:
            print(f"Dropbox download error: {e}")
            return None


class S3Storage(SecureStorage):
    """Store encrypted todos in AWS S3"""
    
    def __init__(self):
        super().__init__()
        self.bucket_name = os.getenv('S3_BUCKET_NAME')
        self.aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
        self.aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        self.aws_region = os.getenv('AWS_REGION', 'us-east-1')
        
        if self.bucket_name and self.aws_access_key and self.aws_secret_key:
            self.s3 = boto3.client(
                's3',
                aws_access_key_id=self.aws_access_key,
                aws_secret_access_key=self.aws_secret_key,
                region_name=self.aws_region
            )
            self.enabled = True
        else:
            self.enabled = False
            print("S3 storage not configured. Add S3_BUCKET_NAME, AWS_ACCESS_KEY_ID, and AWS_SECRET_ACCESS_KEY to .env")
    
    def upload_todos(self, todos, key=None):
        """Upload encrypted todos to S3"""
        if not self.enabled:
            return False
        
        try:
            if not key:
                key = f"todos/todos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.enc"
            
            # Encrypt the data
            encrypted = self.encrypt_data(todos)
            
            # Upload to S3
            self.s3.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=encrypted.encode(),
                ServerSideEncryption='AES256'
            )
            
            print(f"✅ Encrypted todos uploaded to S3: s3://{self.bucket_name}/{key}")
            return True
        except Exception as e:
            print(f"S3 upload error: {e}")
            return False


class PrivateGitHub(SecureStorage):
    """Store encrypted todos in a PRIVATE GitHub repo"""
    
    def __init__(self):
        super().__init__()
        self.token = os.getenv('GITHUB_PRIVATE_TOKEN')
        self.private_repo = os.getenv('GITHUB_PRIVATE_REPO')  # e.g., "username/private-todos"
        
        if self.token and self.private_repo:
            self.enabled = True
        else:
            self.enabled = False
            print("Private GitHub not configured. Add GITHUB_PRIVATE_TOKEN and GITHUB_PRIVATE_REPO to .env")
    
    def upload_todos(self, todos):
        """Upload encrypted todos to private GitHub repo"""
        if not self.enabled:
            return False
        
        try:
            import requests
            
            # Encrypt the data
            encrypted = self.encrypt_data(todos)
            
            # Create or update file in private repo
            url = f"https://api.github.com/repos/{self.private_repo}/contents/todos.enc"
            
            # Get current file (if exists) to get SHA
            response = requests.get(
                url,
                headers={
                    'Authorization': f'token {self.token}',
                    'Accept': 'application/vnd.github.v3+json'
                }
            )
            
            sha = None
            if response.status_code == 200:
                sha = response.json()['sha']
            
            # Update or create file
            data = {
                'message': f'Update todos - {datetime.now().strftime("%Y-%m-%d %H:%M")}',
                'content': base64.b64encode(encrypted.encode()).decode(),
            }
            
            if sha:
                data['sha'] = sha
            
            response = requests.put(
                url,
                json=data,
                headers={
                    'Authorization': f'token {self.token}',
                    'Accept': 'application/vnd.github.v3+json'
                }
            )
            
            if response.status_code in [200, 201]:
                print(f"✅ Encrypted todos uploaded to private GitHub repo")
                return True
            else:
                print(f"GitHub API error: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"Private GitHub upload error: {e}")
            return False


class LocalEncrypted(SecureStorage):
    """Store encrypted todos locally (for Railway with persistent volume)"""
    
    def __init__(self):
        super().__init__()
        self.storage_path = os.getenv('ENCRYPTED_STORAGE_PATH', '/app/data/encrypted_todos')
        os.makedirs(self.storage_path, exist_ok=True)
    
    def save_todos(self, todos):
        """Save encrypted todos locally"""
        try:
            filename = os.path.join(
                self.storage_path,
                f"todos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.enc"
            )
            
            # Encrypt the data
            encrypted = self.encrypt_data(todos)
            
            # Save to file
            with open(filename, 'w') as f:
                f.write(encrypted)
            
            # Also save as latest
            latest_file = os.path.join(self.storage_path, 'todos_latest.enc')
            with open(latest_file, 'w') as f:
                f.write(encrypted)
            
            print(f"✅ Encrypted todos saved locally: {filename}")
            return True
        except Exception as e:
            print(f"Local encryption error: {e}")
            return False
    
    def load_latest_todos(self):
        """Load and decrypt latest todos"""
        try:
            latest_file = os.path.join(self.storage_path, 'todos_latest.enc')
            if os.path.exists(latest_file):
                with open(latest_file, 'r') as f:
                    encrypted = f.read()
                
                decrypted = self.decrypt_data(encrypted)
                return json.loads(decrypted)
            return None
        except Exception as e:
            print(f"Local decryption error: {e}")
            return None