#!/usr/bin/env python3
"""
Link Phones AI Agent - Main Test Script
Run this to test the complete workflow once.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.logger_config import setup_logger
from src.post_manager import PostManager
from src.ai_agent import AIAgent
from src.instagram_client import InstagramClient

def test_ai_agent():
    """Test AI agent separately"""
    print("\n🔍 TESTING AI AGENT...")
    ai = AIAgent()
    
    # Load inventory
    phones = ai.load_inventory()
    print(f"✅ Found {len(phones)} phones")
    
    # Generate a caption
    phone = ai.get_next_phone()
    if phone:
        caption = ai.generate_caption(phone)
        print(f"\n📝 SAMPLE CAPTION:\n{caption}\n")
        print("-" * 50)
    
    return True

def test_instagram_connection():
    """Test Instagram connection separately"""
    print("\n🔍 TESTING INSTAGRAM CONNECTION...")
    ig = InstagramClient()
    
    if ig.login():
        print("✅ Login successful")
        if ig.test_connection():
            print("✅ Connection test passed")
            return True
    else:
        print("❌ Login failed")
    return False

def test_full_workflow():
    """Test complete workflow once"""
    print("\n🚀 TESTING FULL WORKFLOW...")
    
    # Setup logging
    logger = setup_logger('test')
    
    # Create post manager
    manager = PostManager()
    
    # Run once
    success = manager.create_and_post()
    
    if success:
        print("\n✅ Full workflow test PASSED!")
    else:
        print("\n❌ Full workflow test FAILED")
    
    return success

if __name__ == "__main__":
    print("=" * 60)
    print("LINK PHONES AI AGENT - INTEGRATION TEST")
    print("=" * 60)
    
    # Test each component
    test_ai_agent()
    
    print("\n" + "=" * 60)
    input("Press Enter to test Instagram connection...")
    test_instagram_connection()
    
    print("\n" + "=" * 60)
    input("Press Enter to test full workflow (will post to Instagram!)...")
    print("⚠️  This will actually post to Instagram!")
    confirm = input("Type 'YES' to continue: ")
    
    if confirm == 'YES':
        test_full_workflow()
    else:
        print("Test cancelled")