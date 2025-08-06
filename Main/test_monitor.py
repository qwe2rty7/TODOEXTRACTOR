import sys
import time
import threading
from email_extractor import main

def run_with_timeout(seconds=10):
    """Run the main function for a limited time"""
    
    def stop_after_timeout():
        time.sleep(seconds)
        print(f"\n\n=== Test completed after {seconds} seconds ===")
        sys.exit(0)
    
    # Start timeout thread
    timeout_thread = threading.Thread(target=stop_after_timeout, daemon=True)
    timeout_thread.start()
    
    # Run main
    try:
        main()
    except SystemExit:
        pass

if __name__ == "__main__":
    print("Testing monitor for 10 seconds...")
    print("=" * 50)
    run_with_timeout(10)