#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.post_manager import PostManager
import logging

logging.basicConfig(level=logging.INFO)

def test_multi_platform():
    print("=" * 60)
    print("TESTING MULTI-PLATFORM POSTING")
    print("=" * 60)
    
    manager = PostManager()
    
    # Test posting to multiple platforms
    platforms = ["twitter", "facebook"]  # Start with these
    print(f"\n📤 Posting to: {', '.join(platforms)}")
    
    success = manager.create_and_post_multi(platforms=platforms)
    
    if success:
        print("\n✅ Multi-platform test PASSED!")
        print("Check your social media accounts!")
    else:
        print("\n❌ Multi-platform test FAILED")

if __name__ == "__main__":
    test_multi_platform()