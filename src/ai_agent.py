import os
import pandas as pd
from openai import OpenAI
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv
import json
from pathlib import Path

load_dotenv()

class AIAgent:
    def __init__(self):
        """Initialize AI Agent with OpenAI and Google Sheets"""
        # OpenAI setup
        self.openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Google Sheets setup
        self.sheet_id = os.getenv("GOOGLE_SHEET_ID")
        self.sheets_service = self._setup_google_sheets()
        
        # Track which phone we're posting
        self.current_index = 0
        self.phones = []
        
    def _setup_google_sheets(self):
        """Set up Google Sheets API connection"""
        try:
            # Try to load credentials if they exist
            creds_file = os.getenv("GOOGLE_CREDENTIALS_FILE")
            if creds_file and Path(creds_file).exists():
                creds = service_account.Credentials.from_service_account_file(
                    creds_file,
                    scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
                )
                return build('sheets', 'v4', credentials=creds)
            else:
                # For public sheets - no auth needed
                return build('sheets', 'v4', developerKey=None)
        except Exception as e:
            print(f"⚠️ Google Sheets setup warning: {e}")
            return None
    
    def load_inventory(self):
        """Load phones from Google Sheets"""
        try:
            if self.sheets_service:
                # Try authenticated access
                result = self.sheets_service.spreadsheets().values().get(
                    spreadsheetId=self.sheet_id,
                    range='Sheet1!A2:D'  # A to D columns
                ).execute()
                rows = result.get('values', [])
            else:
                # Public access method - use pandas as fallback
                url = f"https://docs.google.com/spreadsheets/d/{self.sheet_id}/gviz/tq?tqx=out:csv&sheet=Sheet1"
                df = pd.read_csv(url)
                rows = df.values.tolist()
            
            # Convert to list of phone objects
            self.phones = []
            for row in rows:
                if len(row) >= 4:  # Make sure we have all columns
                    phone = {
                        'model': row[0],
                        'storage': row[1],
                        'price': row[2],
                        'condition': row[3] if len(row) > 3 else 'New',
                        'stock': row[4] if len(row) > 4 else 'In Stock'
                    }
                    self.phones.append(phone)
            
            print(f"✅ Loaded {len(self.phones)} phones from Google Sheets")
            return self.phones
            
        except Exception as e:
            print(f"❌ Error loading from Google Sheets: {e}")
            # Fallback sample data
            self.phones = [
                {'model': 'iPhone 13', 'storage': '128GB', 'price': '65000', 'condition': 'New', 'stock': '3'},
                {'model': 'Samsung S23', 'storage': '256GB', 'price': '72000', 'condition': 'New', 'stock': '2'},
                {'model': 'iPhone 12', 'storage': '64GB', 'price': '48000', 'condition': 'Clean', 'stock': '5'}
            ]
            return self.phones
    
    def get_next_phone(self):
        """Get the next phone to post (round-robin)"""
        if not self.phones:
            self.load_inventory()
        
        if not self.phones:
            return None
        
        phone = self.phones[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.phones)
        return phone
    
    def generate_caption(self, phone):
        """Generate Instagram caption using OpenAI"""
        prompt = f"""You are the official AI marketing manager for Link Phones Center in Nairobi. 
Create a high-converting Instagram caption for this phone:

Model: {phone['model']} {phone['storage']}
Price: KES {phone['price']}
Condition: {phone['condition']}
Stock: {phone.get('stock', 'Available')}

Include:
- 3 selling features
- Sense of urgency (limited stock)
- 5 local hashtags (#NairobiPhones, #KenyaTech, etc.)
- WhatsApp call-to-action (use +254700000000)

Make it engaging, professional, and under 200 words."""

        try:
            response = self.openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a social media marketing expert for phone sales in Kenya."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.7
            )
            
            caption = response.choices[0].message.content
            return caption
            
        except Exception as e:
            print(f"❌ OpenAI error: {e}")
            # Fallback caption
            return f"""🔥 {phone['model']} {phone['storage']} - KES {phone['price']} 🔥

Brand New Condition ✅
Same-day delivery in Nairobi 🚚
M-Pesa accepted 💳

📱 WhatsApp: +254700000000

#NairobiPhones #PhoneDealsKE #{phone['model'].replace(' ', '')} #{phone['condition']}Phones #TechKenya"""
    
    def create_post_data(self):
        """Create complete post data (caption + image path)"""
        phone = self.get_next_phone()
        if not phone:
            return None
        
        caption = self.generate_caption(phone)
        
        # For now, we'll use a placeholder image path
        # Later we'll integrate Canva API here
        image_filename = f"{phone['model'].replace(' ', '_')}_{phone['storage']}.jpg".lower()
        image_path = os.path.join('data', 'posts', image_filename)
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.join('data', 'posts'), exist_ok=True)
        
        return {
            'phone': phone,
            'caption': caption,
            'image_path': image_path,
            'scheduled_time': None  # Will be set by scheduler
        }