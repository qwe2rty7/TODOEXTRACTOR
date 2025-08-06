import os
import time
from datetime import datetime
from dotenv import load_dotenv
from email_monitor import EmailMonitor
from fireflies_monitor import FirefliesMonitor

load_dotenv()

class CombinedMonitor:
    def __init__(self):
        self.email_monitor = EmailMonitor()
        self.fireflies_monitor = FirefliesMonitor()
    
    def monitor_all(self, check_interval=30, check_transcripts=True):
        """Main monitoring loop for both emails and Fireflies transcripts"""
        user_email = os.getenv('USER_EMAIL', 'your email')
        print(f"📧 Starting combined monitor for {user_email}")
        if check_transcripts:
            print(f"📧 Monitoring: Emails + Fireflies transcripts")
        else:
            print(f"📧 Monitoring: Emails only")
        print(f"Checking every {check_interval} seconds...\n")
        
        transcript_check_counter = 0  # Check transcripts less frequently
        transcript_check_interval = 2  # Check transcripts every 2 cycles (60 seconds if email check is 30s)
        
        while True:
            try:
                # Check for new emails
                self.email_monitor.check_new_emails()
                
                # Check for new Fireflies transcripts (less frequently)
                if check_transcripts and transcript_check_counter >= transcript_check_interval:
                    try:
                        self.fireflies_monitor.check_new_transcripts()
                        transcript_check_counter = 0  # Reset counter
                    except Exception as e:
                        print(f"❌ Error checking transcripts: {e}")
                        transcript_check_counter = 0  # Reset counter on error too
                else:
                    transcript_check_counter += 1
                
                # Wait before next check
                print(f"\n💤 Waiting {check_interval}s before next check...")
                time.sleep(check_interval)
                
            except KeyboardInterrupt:
                print("\n👋 Stopping monitor...")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                time.sleep(check_interval)

def main():
    # Check if credentials are set
    required_vars = ['CLIENT_ID', 'CLIENT_SECRET', 'TENANT_ID', 'USER_EMAIL']
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        print("❌ Missing required environment variables:")
        for var in missing:
            print(f"  - {var}")
        print("\nCreate a .env file with these variables.")
        return
    
    # Check for optional API keys
    if not os.getenv('ANTHROPIC_API_KEY'):
        print("⚠️  Warning: ANTHROPIC_API_KEY not set - todo extraction will be disabled")
        print("Add ANTHROPIC_API_KEY to your .env file to enable AI analysis")
    
    if not os.getenv('FIREFLIES_API_KEY'):
        print("⚠️  Warning: FIREFLIES_API_KEY not set - transcript monitoring will be disabled")
        print("Add FIREFLIES_API_KEY to your .env file to enable Fireflies integration")
    
    if os.getenv('ANTHROPIC_API_KEY') or os.getenv('FIREFLIES_API_KEY'):
        print("")  # Add blank line if we showed any warnings
    
    # Start monitoring
    monitor = CombinedMonitor()
    monitor.monitor_all(check_interval=30)  # Check every 30 seconds

if __name__ == "__main__":
    main()