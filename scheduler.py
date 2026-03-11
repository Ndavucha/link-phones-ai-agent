#!/usr/bin/env python3
"""
Link Phones AI Agent - Scheduler
Run this script to start 24/7 automated posting.
"""

import sys
import time
import signal
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.logger_config import setup_logger
from src.post_manager import PostManager

logger = setup_logger('scheduler')
running = True

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    global running
    logger.info("⏹️  Shutting down scheduler...")
    running = False

def main():
    """Main scheduler loop"""
    logger.info("=" * 60)
    logger.info("LINK PHONES AI AGENT - SCHEDULER STARTING")
    logger.info("=" * 60)
    
    # Setup signal handler for clean shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Initialize post manager
    logger.info("Initializing Post Manager...")
    manager = PostManager()
    
    # Load inventory
    manager.ai_agent.load_inventory()
    
    # Run once immediately? (optional)
    # logger.info("Running initial test post...")
    # manager.create_and_post()
    
    # Start scheduler
    logger.info("Starting scheduler loop...")
    manager.schedule_posts()  # This will block until interrupted

if __name__ == "__main__":
    main()