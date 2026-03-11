import os
import requests
import logging
from dotenv import load_dotenv
from typing import List, Optional, Dict, Any, Union

load_dotenv()

class MultiPlatformPoster:
    def __init__(self):
        self.api_key = os.getenv("AYRSHARE_API_KEY")
        self.base_url = "https://api.ayrshare.com/api"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.logger = logging.getLogger(__name__)
    
    def post(self, 
             caption: str, 
             image_url: Optional[str] = None,
             platforms: Optional[List[str]] = None,
             scheduled_time: Optional[str] = None) -> Optional[Union[Dict[str, Any], List[Any]]]:
        """
        Post to multiple social media platforms
        
        Args:
            caption: The post caption/text
            image_url: URL of the image to post (optional)
            platforms: List of platforms ['instagram', 'facebook', 'twitter', 'linkedin', 'pinterest']
            scheduled_time: ISO format time for scheduled post (optional)
        
        Returns:
            Response (dictionary or list) or None if failed
        """
        
        if platforms is None:
            # Default platforms if none specified
            platforms = ["instagram", "facebook", "twitter"]
        
        # Prepare the post data
        data = {
            "post": caption,
            "platforms": platforms
        }
        
        # Add image if provided
        if image_url:
            data["mediaUrls"] = [image_url]
        
        # Add scheduling if provided
        if scheduled_time:
            data["scheduledAt"] = scheduled_time
        
        try:
            self.logger.info(f"📤 Posting to platforms: {', '.join(platforms)}")
            self.logger.info(f"📝 Caption length: {len(caption)} chars")
            
            response = requests.post(
                f"{self.base_url}/post",
                json=data,
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                self.logger.info("✅ Post API call successful!")
                
                # Handle different response types
                if isinstance(result, dict):
                    self._log_dict_response(result)
                elif isinstance(result, list):
                    self._log_list_response(result)
                else:
                    self.logger.info(f"   📱 Response: {result}")
                
                return result
            else:
                self.logger.error(f"❌ Post failed: {response.status_code}")
                self.logger.error(f"Response: {response.text}")
                
                # Try to parse error message
                try:
                    error_data = response.json()
                    if isinstance(error_data, dict):
                        if 'errors' in error_data:
                            for error in error_data['errors']:
                                self.logger.error(f"   • {error.get('platform')}: {error.get('message')}")
                        else:
                            self.logger.error(f"   • Error: {error_data.get('message', str(error_data))}")
                    elif isinstance(error_data, list):
                        for error in error_data:
                            self.logger.error(f"   • {error}")
                except:
                    pass
                    
                return None
                
        except requests.exceptions.Timeout:
            self.logger.error("❌ Request timeout")
            return None
        except requests.exceptions.ConnectionError:
            self.logger.error("❌ Connection error")
            return None
        except Exception as e:
            self.logger.error(f"❌ Error posting: {e}")
            return None
    
    def _log_dict_response(self, result: Dict[str, Any]) -> None:
        """Log dictionary response from API"""
        # Log each platform's result
        if 'postIds' in result and isinstance(result['postIds'], dict):
            for platform, post_id in result['postIds'].items():
                self.logger.info(f"   📱 {platform}: {post_id}")
        elif 'id' in result:
            self.logger.info(f"   📱 Post ID: {result['id']}")
        else:
            # Log important fields if they exist
            important_fields = ['status', 'message', 'id', 'reference']
            logged = False
            for field in important_fields:
                if field in result:
                    self.logger.info(f"   📱 {field}: {result[field]}")
                    logged = True
            if not logged:
                self.logger.info(f"   📱 Response: {result}")
    
    def _log_list_response(self, result: List[Any]) -> None:
        """Log list response from API"""
        self.logger.info(f"   📱 Received list response with {len(result)} items")
        for i, item in enumerate(result):
            if isinstance(item, dict):
                # Try to extract platform info
                platform = item.get('platform', item.get('network', f'item_{i}'))
                status = item.get('status', item.get('success', 'ok'))
                self.logger.info(f"   📱 {platform}: {status}")
                
                # Log post ID if available
                if 'id' in item:
                    self.logger.info(f"      🆔 {item['id']}")
            else:
                self.logger.info(f"   📱 item_{i}: {item}")
    
    def get_platforms(self) -> List[str]:
        """
        Get list of connected platforms from Ayrshare
        
        Returns:
            List of platform names that are connected
        """
        try:
            self.logger.info("🔍 Fetching connected platforms...")
            
            # Note: According to Ayrshare docs, this endpoint might be /user or /social/accounts
            # Let's try multiple endpoints
            endpoints = ["/profile", "/user", "/social/accounts"]
            
            for endpoint in endpoints:
                try:
                    response = requests.get(
                        f"{self.base_url}{endpoint}",
                        headers=self.headers,
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        connected = self._parse_platforms_response(data)
                        if connected:
                            return connected
                except:
                    continue
            
            self.logger.warning("⚠️ Could not fetch platforms from any endpoint")
            return []
                
        except Exception as e:
            self.logger.error(f"❌ Error getting platforms: {e}")
            return []
    
    def _parse_platforms_response(self, data: Any) -> List[str]:
        """Parse platform list from various response formats"""
        connected = []
        
        try:
            if isinstance(data, list):
                # Format: [{ "platform": "facebook", "connected": true }, ...]
                for profile in data:
                    if isinstance(profile, dict):
                        if profile.get('connected'):
                            platform = profile.get('platform')
                            if platform:
                                connected.append(platform)
                                self.logger.info(f"   ✅ {platform}")
            
            elif isinstance(data, dict):
                # Try different common formats
                if 'socialAccounts' in data and isinstance(data['socialAccounts'], list):
                    for account in data['socialAccounts']:
                        if account.get('connected'):
                            platform = account.get('platform')
                            if platform:
                                connected.append(platform)
                                self.logger.info(f"   ✅ {platform}")
                
                elif 'platforms' in data and isinstance(data['platforms'], list):
                    connected = data['platforms']
                    for platform in connected:
                        self.logger.info(f"   ✅ {platform}")
                
                else:
                    # Format: { "facebook": { "connected": true }, ... }
                    for platform, info in data.items():
                        if isinstance(info, dict) and info.get('connected'):
                            connected.append(platform)
                            self.logger.info(f"   ✅ {platform}")
                        elif info is True:  # Simple format: { "facebook": true }
                            connected.append(platform)
                            self.logger.info(f"   ✅ {platform}")
            
            if not connected:
                self.logger.info("   ❌ No platforms connected yet")
                self.logger.info("   👉 Go to https://app.ayrshare.com to connect social accounts")
            
        except Exception as e:
            self.logger.error(f"Error parsing platforms response: {e}")
        
        return connected
    
    def schedule_post(self, caption: str, image_url: Optional[str], 
                      platforms: List[str], post_time: str) -> Optional[Union[Dict[str, Any], List[Any]]]:
        """
        Schedule a post for future
        
        Args:
            caption: The post caption/text
            image_url: URL of the image to post (optional)
            platforms: List of platforms to post to
            post_time: ISO format like "2026-03-12T09:00:00Z"
        
        Returns:
            Response dictionary or None if failed
        """
        self.logger.info(f"⏰ Scheduling post for {post_time}")
        return self.post(caption, image_url, platforms, scheduled_time=post_time)
    
    def get_post_status(self, post_id: str) -> Optional[Dict[str, Any]]:
        """
        Check the status of a specific post
        
        Args:
            post_id: The ID of the post to check
        
        Returns:
            Post status information
        """
        try:
            response = requests.get(
                f"{self.base_url}/post",
                params={"id": post_id},
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"❌ Failed to get post status: {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Error getting post status: {e}")
            return None
    
    def delete_post(self, post_id: str) -> bool:
        """
        Delete a post from all platforms
        
        Args:
            post_id: The ID of the post to delete
        
        Returns:
            True if successful, False otherwise
        """
        try:
            response = requests.delete(
                f"{self.base_url}/post",
                params={"id": post_id},
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                self.logger.info(f"✅ Post {post_id} deleted successfully")
                return True
            else:
                self.logger.error(f"❌ Failed to delete post: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error deleting post: {e}")
            return False