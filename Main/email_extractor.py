import os
import time
from datetime import datetime, timezone
from dotenv import load_dotenv
from email_monitor import EmailMonitor
from fireflies_monitor import FirefliesMonitor

load_dotenv()

class CombinedMonitor:
    def __init__(self):
        self.email_monitor = EmailMonitor()
        self.fireflies_monitor = FirefliesMonitor()
    
    def get_smart_interval(self):
        """Get check interval based on time of day to reduce costs during off-hours"""
        now = datetime.now()
        hour = now.hour
        
        # Off-hours: 9 PM to 5 AM (21:00 to 05:00)
        if hour >= 21 or hour < 5:
            # Night time: check every 5 minutes (300 seconds)
            interval = 300
            period = "night"
        elif (hour >= 17 and hour < 21) or (hour >= 5 and hour < 7):  
            # Evening (5PM-9PM) and early morning (5AM-7AM): check every 2 minutes (120 seconds)
            interval = 120
            period = "evening/early morning"
        else:
            # Business hours (7 AM - 5 PM): check every 30 seconds
            interval = 30
            period = "business hours"
            
        return interval, period
    
    def monitor_all(self, check_transcripts=True):
        """Main monitoring loop for both emails and Fireflies transcripts"""
        user_email = os.getenv('USER_EMAIL', 'your email')
        print(f"Starting smart-scheduled monitor for {user_email}")
        if check_transcripts:
            print(f"Monitoring: Emails + Fireflies transcripts")
        else:
            print(f"📧 Monitoring: Emails only")
        print(f"Smart scheduling: 30s (7AM-5PM), 2min (5-7AM, 5-9PM), 5min (9PM-5AM)")
        print(f"Transcript checks: 1min (business), 10min (evening), 15min (night)\n")
        
        transcript_check_counter = 0
        last_period = ""  # Track when we switch time periods
        
        while True:
            try:
                # Get current smart interval
                check_interval, current_period = self.get_smart_interval()
                
                # Log when switching time periods
                if current_period != last_period:
                    current_time = datetime.now().strftime("%H:%M")
                    print(f"🕒 {current_time} - Switched to {current_period} mode (checking every {check_interval}s)")
                    last_period = current_period
                
                # Adjust transcript check frequency based on current interval
                # During night hours (5min intervals), check transcripts every 3 cycles (15min)
                # During evening hours (2min intervals), check transcripts every 5 cycles (10min) 
                # During business hours (30s intervals), check transcripts every 2 cycles (1min) - fast for post-call updates
                if check_interval >= 300:  # Night mode
                    transcript_check_interval = 3
                elif check_interval >= 120:  # Evening mode
                    transcript_check_interval = 5
                else:  # Business hours
                    transcript_check_interval = 2
                
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
                print(f"\nWaiting {check_interval}s before next check...")
                time.sleep(check_interval)
                
            except KeyboardInterrupt:
                print("\nStopping monitor...")
                break
            except Exception as e:
                check_interval, _ = self.get_smart_interval()
                print(f"\nError: {e}")
                time.sleep(check_interval)

def main():
    # Check if credentials are set
    required_vars = ['CLIENT_ID', 'CLIENT_SECRET', 'TENANT_ID', 'USER_EMAIL']
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        print("ERROR: Missing required environment variables:")
        for var in missing:
            print(f"  - {var}")
        print("\nCreate a .env file with these variables.")
        return
    
    # Check for optional API keys
    if not os.getenv('ANTHROPIC_API_KEY'):
        print("Warning: ANTHROPIC_API_KEY not set - todo extraction will be disabled")
        print("Add ANTHROPIC_API_KEY to your .env file to enable AI analysis")
    
    if not os.getenv('FIREFLIES_API_KEY'):
        print("Warning: FIREFLIES_API_KEY not set - transcript monitoring will be disabled")
        print("Add FIREFLIES_API_KEY to your .env file to enable Fireflies integration")
    
    if os.getenv('ANTHROPIC_API_KEY') or os.getenv('FIREFLIES_API_KEY'):
        print("")  # Add blank line if we showed any warnings
    
    # Start monitoring with smart scheduling
    monitor = CombinedMonitor()
    monitor.monitor_all()  # Smart scheduling automatically adjusts intervals

if __name__ == "__main__":
    main()