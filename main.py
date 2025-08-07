#!/usr/bin/env python3
"""
Email Todo Extractor - Main Entry Point
Monitors emails and extracts action items
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Main'))

from email_monitor import EmailMonitor
from fireflies_monitor import FirefliesMonitor
import time
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('email_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Main entry point for the application"""
    logger.info("Starting Email Todo Extractor...")
    
    # Debug environment variables first
    import subprocess
    print("\n=== DEBUGGING RAILWAY ENVIRONMENT ===")
    subprocess.run([sys.executable, "debug_env.py"])
    print("=== END DEBUG ===\n")
    
    try:
        # Initialize monitors
        logger.info("Initializing EmailMonitor...")
        email_monitor = EmailMonitor()
        logger.info("EmailMonitor initialized successfully")
        
        logger.info("Initializing FirefliesMonitor...")
        fireflies_monitor = FirefliesMonitor()
        logger.info("FirefliesMonitor initialized successfully")
        
        logger.info("All monitors initialized successfully")
        logger.info(f"Monitoring email: {email_monitor.user_email}")
        
        # Main monitoring loop
        while True:
            try:
                # Check emails
                email_monitor.check_new_emails()
                
                # Check Fireflies transcripts
                fireflies_monitor.check_new_transcripts()
                
                # Wait before next check
                logger.info(f"Waiting 30 seconds before next check...")
                time.sleep(30)
                
            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                logger.info("Continuing after error...")
                time.sleep(30)
                
    except Exception as e:
        logger.error(f"Failed to initialize monitors: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()