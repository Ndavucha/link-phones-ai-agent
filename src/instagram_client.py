from instagrapi import Client
from instagrapi.exceptions import LoginRequired, PleaseWaitFewMinutes, ChallengeRequired, ReloginAttemptExceeded
import os
import time
import json
import logging
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

class InstagramClient:
    def __init__(self, username=None, password=None, session_file='session.json'):
        self.username = username or os.getenv('INSTAGRAM_USERNAME')
        self.password = password or os.getenv('INSTAGRAM_PASSWORD')
        self.session_file = session_file
        self.client = Client()
        self.logger = logging.getLogger(__name__)
        
        # Set a custom challenge handler
        self.client.challenge_code_handler = self._challenge_code_handler
        
    def _challenge_code_handler(self, username, choice):
        """
        Handle Instagram challenge codes (phone/email verification)
        This will prompt the user to enter the code sent by Instagram
        """
        self.logger.info("=" * 50)
        self.logger.info("🔐 INSTAGRAM VERIFICATION REQUIRED")
        self.logger.info("=" * 50)
        self.logger.info(f"📱 Instagram sent a verification code to your phone/email")
        self.logger.info(f"👤 Username: {username}")
        self.logger.info(f"📨 Check your Instagram app, SMS, or email for the code")
        self.logger.info("=" * 50)
        
        # Prompt for the code
        code = input("➡️  Enter the 6-digit verification code: ").strip()
        
        # Validate input
        while not code.isdigit() or len(code) != 6:
            self.logger.warning("⚠️  Invalid code. Please enter a 6-digit number.")
            code = input("➡️  Enter the 6-digit verification code: ").strip()
        
        self.logger.info("✅ Code received, verifying...")
        return code
    
    def login(self):
        """Login to Instagram with session persistence and challenge handling"""
        try:
            # Try to load existing session
            if Path(self.session_file).exists():
                self.logger.info("📂 Loading existing session...")
                self.client.load_settings(self.session_file)
                
                # Try to login with loaded session
                try:
                    self.client.login(self.username, self.password)
                    
                    # Verify login worked by getting timeline
                    self.client.get_timeline_feed()
                    self.logger.info("✅ Session loaded successfully")
                    return True
                    
                except LoginRequired:
                    self.logger.info("⚠️ Session expired, will perform fresh login")
                    # Session expired, remove it and continue to fresh login
                    Path(self.session_file).unlink(missing_ok=True)
                    
                except Exception as e:
                    self.logger.warning(f"⚠️ Session invalid: {e}")
                    Path(self.session_file).unlink(missing_ok=True)
            
            # Fresh login with challenge handling
            self.logger.info("🔐 Performing fresh login...")
            
            # Attempt login
            self.client.login(self.username, self.password)
            
            # Verify login worked
            self.client.get_timeline_feed()
            
            # Save session for next time
            self.client.dump_settings(self.session_file)
            self.logger.info("✅ Login successful! Session saved")
            return True
                
        except ChallengeRequired:
            self.logger.info("🔐 Challenge required - waiting for user input...")
            try:
                # The challenge_code_handler will automatically be called
                # by instagrapi when a challenge is required
                self.client.challenge_resolve(self.client.last_json)
                
                # After challenge, try logging in again
                self.client.login(self.username, self.password)
                
                # Save session
                self.client.dump_settings(self.session_file)
                self.logger.info("✅ Challenge resolved and login successful!")
                return True
                
            except Exception as e:
                self.logger.error(f"❌ Challenge resolution failed: {e}")
                return False
                
        except ReloginAttemptExceeded:
            self.logger.error("❌ Too many login attempts. Please wait a few minutes and try again.")
            return False
                
        except Exception as e:
            self.logger.error(f"❌ Login error: {e}")
            return False
    
    def post_photo(self, image_path, caption):
        """Post a photo to Instagram feed"""
        try:
            # Verify file exists
            if not Path(image_path).exists():
                self.logger.error(f"❌ Image not found: {image_path}")
                return False
            
            self.logger.info(f"📸 Uploading: {image_path}")
            
            # Add random delay to seem human (5-15 seconds)
            import random
            time.sleep(random.uniform(5, 15))
            
            # Upload the photo
            media = self.client.photo_upload(
                path=image_path,
                caption=caption
            )
            
            self.logger.info(f"✅ Posted successfully!")
            self.logger.info(f"🔗 Post link: https://www.instagram.com/p/{media.code}/")
            
            # Move to posted folder
            self._archive_post(image_path)
            
            return True
            
        except PleaseWaitFewMinutes:
            self.logger.warning("⏳ Rate limited. Waiting 5 minutes...")
            time.sleep(300)  # Wait 5 minutes
            return self.post_photo(image_path, caption)  # Retry
            
        except Exception as e:
            self.logger.error(f"❌ Post failed: {e}")
            return False
    
    def _archive_post(self, image_path):
        """Move posted image to archive folder"""
        posted_dir = os.path.join('data', 'posted')
        os.makedirs(posted_dir, exist_ok=True)
        
        filename = os.path.basename(image_path)
        new_path = os.path.join(posted_dir, filename)
        
        try:
            os.rename(image_path, new_path)
            self.logger.info(f"📦 Archived to: {new_path}")
        except Exception as e:
            self.logger.warning(f"⚠️ Could not archive: {e}")
    
    def test_connection(self):
        """Test if connection is working"""
        try:
            user_id = self.client.user_id
            user_info = self.client.user_info(user_id)
            self.logger.info(f"✅ Connected as @{user_info.username}")
            self.logger.info(f"📊 Followers: {user_info.follower_count}")
            self.logger.info(f"📝 Full name: {user_info.full_name}")
            return True
        except Exception as e:
            self.logger.error(f"❌ Connection test failed: {e}")
            return False
    
    def logout(self):
        """Logout and clear session"""
        try:
            self.client.logout()
            if Path(self.session_file).exists():
                Path(self.session_file).unlink()
            self.logger.info("✅ Logged out and session cleared")
            return True
        except Exception as e:
            self.logger.error(f"❌ Logout error: {e}")
            return False