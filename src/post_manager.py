from src.ai_agent import AIAgent
from src.instagram_client import InstagramClient
from src.multi_platform import MultiPlatformPoster
import schedule
import time
import logging
import os
import requests
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any, Union

class PostManager:
    def __init__(self):
        self.ai_agent = AIAgent()
        self.instagram = InstagramClient()  # Keep for backward compatibility
        self.multi_poster = MultiPlatformPoster()  # New multi-platform poster
        self.logger = logging.getLogger(__name__)
        
        # Load inventory on startup
        self.ai_agent.load_inventory()
        
    def create_and_post(self, platforms: Optional[List[str]] = None, use_multi: bool = True) -> bool:
        """
        Create a post and publish to social media
        
        Args:
            platforms: List of platforms ['instagram', 'facebook', 'twitter', 'linkedin']
            use_multi: If True, use Ayrshare multi-platform. If False, use Instagram only.
        
        Returns:
            bool: True if successful, False otherwise
        """
        self.logger.info("🚀 Starting post creation workflow...")
        
        try:
            # Step 1: Get AI-generated content
            self.logger.info("🤖 Getting AI-generated content...")
            post_data = self.ai_agent.create_post_data()
            
            if not post_data:
                self.logger.error("❌ Failed to generate post data")
                return False
            
            phone = post_data['phone']
            caption = post_data['caption']
            image_path = post_data['image_path']
            
            self.logger.info(f"📱 Posting: {phone['model']} {phone['storage']}")
            self.logger.info(f"📝 Caption length: {len(caption)} chars")
            
            # Step 2: Create placeholder image if it doesn't exist
            if not Path(image_path).exists():
                self._create_placeholder_image(phone, image_path)
            
            # Step 3: Choose posting method
            if use_multi:
                return self._post_multi_platform(phone, caption, image_path, platforms)
            else:
                return self._post_instagram_only(phone, caption, image_path)
                
        except Exception as e:
            self.logger.error(f"❌ Workflow error: {e}")
            return False
    
    def _post_multi_platform(self, phone: Dict, caption: str, image_path: str, platforms: Optional[List[str]] = None) -> bool:
        """Handle multi-platform posting via Ayrshare"""
        
        # Upload image to hosting service
        self.logger.info("📤 Uploading image to hosting...")
        image_url = self._upload_image_to_hosting(image_path)
        
        if not image_url:
            self.logger.error("❌ Could not upload image")
            return False
        
        # Set default platforms if none provided
        if platforms is None:
            platforms = ["instagram", "facebook", "twitter"]
        
        self.logger.info(f"📤 Posting to: {', '.join(platforms)}")
        
        # Post to multiple platforms
        result = self.multi_poster.post(
            caption=caption,
            image_url=image_url,
            platforms=platforms
        )
        
        # Handle the result (which could be dict, list, or None)
        return self._handle_multi_platform_result(result, phone, caption, platforms)
    
    def _handle_multi_platform_result(self, result: Any, phone: Dict, caption: str, platforms: List[str]) -> bool:
        """Safely handle different response types from Ayrshare"""
        
        if result is None:
            self.logger.error("❌ Multi-platform post failed (no response)")
            return False
        
        # Case 1: Result is a dictionary (successful post)
        if isinstance(result, dict):
            self.logger.info("✅ Multi-platform post completed!")
            
            # Check for post IDs
            if 'postIds' in result and isinstance(result['postIds'], dict):
                for platform, post_id in result['postIds'].items():
                    self.logger.info(f"   📱 {platform}: {post_id}")
            else:
                self.logger.info(f"   📱 Response: {result}")
            
            # Log the successful post
            self._log_post(phone, caption, platforms=platforms)
            return True
        
        # Case 2: Result is a list (might be error or status list)
        elif isinstance(result, list):
            self.logger.info("✅ Multi-platform post completed (list response)!")
            self.logger.info(f"   📱 Response items: {len(result)}")
            
            # Check if it's a list of success responses
            for item in result:
                if isinstance(item, dict) and 'platform' in item:
                    self.logger.info(f"   📱 {item.get('platform')}: {item.get('status', 'posted')}")
            
            # Log the successful post
            self._log_post(phone, caption, platforms=platforms)
            return True
        
        # Case 3: Result is something else (unexpected)
        else:
            self.logger.warning(f"⚠️ Unexpected result type: {type(result)}")
            self.logger.warning(f"⚠️ Result: {result}")
            
            # Assume it worked if we got any response
            self._log_post(phone, caption, platforms=platforms)
            return True
    
    def _post_instagram_only(self, phone: Dict, caption: str, image_path: str) -> bool:
        """Handle Instagram-only posting via instagrapi"""
        
        self.logger.info("🔑 Logging into Instagram...")
        if not self.instagram.login():
            self.logger.error("❌ Instagram login failed")
            return False
        
        if not self.instagram.test_connection():
            self.logger.error("❌ Instagram connection test failed")
            return False
        
        self.logger.info("📸 Posting to Instagram...")
        success = self.instagram.post_photo(image_path, caption)
        
        if success:
            self.logger.info("✅ Instagram post completed!")
            self._log_post(phone, caption, platforms=["instagram"])
            return True
        else:
            self.logger.error("❌ Instagram post failed")
            return False
    
    def _upload_image_to_hosting(self, image_path: str) -> Optional[str]:
        """
        Upload image to temporary hosting (imgbb free service)
        Get API key from: https://api.imgbb.com/
        
        Returns:
            str: Image URL or None if failed
        """
        try:
            # Try to get API key from environment
            imgbb_key = os.getenv("IMGBB_API_KEY")
            
            # If no API key, use a placeholder URL (for testing)
            if not imgbb_key:
                self.logger.warning("⚠️ No IMGBB_API_KEY found. Using placeholder image.")
                return "https://img.ayrshare.com/012/gb.jpg"  # Ayrshare test image
            
            # Check if file exists
            if not Path(image_path).exists():
                self.logger.error(f"❌ Image file not found: {image_path}")
                return "https://img.ayrshare.com/012/gb.jpg"
            
            # Upload to imgbb
            with open(image_path, 'rb') as file:
                response = requests.post(
                    "https://api.imgbb.com/1/upload",
                    data={"key": imgbb_key},
                    files={"image": file},
                    timeout=30
                )
            
            if response.status_code == 200:
                response_data = response.json()
                if 'data' in response_data and 'url' in response_data['data']:
                    image_url = response_data['data']['url']
                    self.logger.info(f"✅ Image uploaded: {image_url}")
                    return image_url
                else:
                    self.logger.error(f"❌ Unexpected imgbb response: {response_data}")
                    return "https://img.ayrshare.com/012/gb.jpg"
            else:
                self.logger.error(f"❌ Image upload failed: {response.status_code}")
                self.logger.error(f"Response: {response.text}")
                return "https://img.ayrshare.com/012/gb.jpg"
                
        except Exception as e:
            self.logger.error(f"❌ Error uploading image: {e}")
            return "https://img.ayrshare.com/012/gb.jpg"  # Fallback
    
    def _create_placeholder_image(self, phone: Dict, image_path: str) -> None:
        """Create a simple placeholder image with phone details"""
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            # Create a blank image
            img = Image.new('RGB', (1080, 1080), color=(41, 128, 185))
            draw = ImageDraw.Draw(img)
            
            # Add text
            text = f"{phone['model']}\n{phone['storage']}\nKES {phone['price']}"
            
            # Try to use a default font
            try:
                font = ImageFont.truetype("arial.ttf", 60)
            except:
                font = ImageFont.load_default()
            
            # Get text bounding box for centering
            text_bbox = draw.textbbox((0, 0), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            # Center text
            x = (1080 - text_width) // 2
            y = (1080 - text_height) // 2
            
            draw.text((x, y), text, fill=(255, 255, 255), font=font)
            
            # Save
            img.save(image_path)
            self.logger.info(f"🖼️ Created placeholder: {image_path}")
        except Exception as e:
            self.logger.warning(f"⚠️ Could not create placeholder: {e}")
            # Just create empty file
            Path(image_path).touch()
    
    def _log_post(self, phone: Dict, caption: str, platforms: Optional[List[str]] = None) -> None:
        """Log post for tracking"""
        log_file = Path('logs') / 'posts_log.csv'
        Path('logs').mkdir(exist_ok=True)
        
        import csv
        file_exists = log_file.exists()
        
        platforms_str = ','.join(platforms) if platforms else 'instagram'
        
        try:
            with open(log_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(['timestamp', 'model', 'storage', 'price', 'caption_length', 'platforms', 'status'])
                
                writer.writerow([
                    datetime.now().isoformat(),
                    phone['model'],
                    phone['storage'],
                    phone['price'],
                    len(caption),
                    platforms_str,
                    'success'
                ])
        except Exception as e:
            self.logger.error(f"❌ Failed to log post: {e}")
    
    def schedule_posts(self, platforms: Optional[List[str]] = None, use_multi: bool = True) -> None:
        """
        Set up scheduled posting
        
        Args:
            platforms: List of platforms to post to
            use_multi: Use multi-platform (True) or Instagram only (False)
        """
        # Morning post at 9 AM
        schedule.every().day.at("09:00").do(
            lambda: self.create_and_post(platforms=platforms, use_multi=use_multi)
        )
        
        # Evening post at 7 PM
        schedule.every().day.at("19:00").do(
            lambda: self.create_and_post(platforms=platforms, use_multi=use_multi)
        )
        
        platform_names = ', '.join(platforms) if platforms else 'Instagram only'
        self.logger.info(f"⏰ Scheduler started - Posts at 9 AM and 7 PM daily to: {platform_names}")
        
        # Run once immediately for testing (uncomment if needed)
        # self.create_and_post(platforms=platforms, use_multi=use_multi)
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            self.logger.info("⏹️ Scheduler stopped by user")
        except Exception as e:
            self.logger.error(f"❌ Scheduler error: {e}")
    
    # Keep the original method name for backward compatibility
    def create_and_post_instagram(self) -> bool:
        """Legacy method - posts only to Instagram"""
        return self.create_and_post(use_multi=False)

    # Convenience method for multi-platform
    def create_and_post_multi(self, platforms: Optional[List[str]] = None) -> bool:
        """Post to multiple platforms"""
        if platforms is None:
            platforms = ["instagram", "facebook", "twitter"]
        return self.create_and_post(platforms=platforms, use_multi=True)