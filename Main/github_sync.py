import os
import subprocess
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class GitHubSync:
    def __init__(self):
        self.repo_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.setup_git_config()
        
    def setup_git_config(self):
        """Configure git for automated commits"""
        try:
            os.chdir(self.repo_path)
            # Set git config for automated commits
            subprocess.run(['git', 'config', 'user.name', 'Todo Bot'], capture_output=True)
            subprocess.run(['git', 'config', 'user.email', 'bot@todoextractor.com'], capture_output=True)
            
            # Set remote URL with token if available (for Railway)
            if self.github_token:
                subprocess.run(['git', 'remote', 'set-url', 'origin', 
                              f'https://{self.github_token}@github.com/qwe2rty7/TODOEXTRACTOR.git'],
                              capture_output=True)
        except Exception as e:
            print(f"Git config error: {e}")
        
    def sync_todos(self):
        """Commit and push todos to GitHub"""
        try:
            os.chdir(self.repo_path)
            
            # Check if there are changes
            result = subprocess.run(['git', 'status', '--porcelain', 'todos.txt', 'structured_todos/'], 
                                  capture_output=True, text=True)
            
            if result.stdout.strip():
                # Stage changes
                subprocess.run(['git', 'add', 'todos.txt', 'structured_todos/'])
                
                # Commit
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
                subprocess.run(['git', 'commit', '-m', f'Auto-update todos - {timestamp}'])
                
                # Push
                result = subprocess.run(['git', 'push'], capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"✅ Todos synced to GitHub at {timestamp}")
                    return True
                else:
                    print(f"Push failed: {result.stderr}")
                    return False
            return False
        except Exception as e:
            print(f"GitHub sync error: {e}")
            return False