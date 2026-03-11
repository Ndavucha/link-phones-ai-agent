from flask import Flask, render_template_string, request, jsonify, redirect, url_for, session
import threading
import logging
import os
import json
from datetime import datetime
from dotenv import load_dotenv
from src.post_manager import PostManager
from src.ai_agent import AIAgent
from src.multi_platform import MultiPlatformPoster

load_dotenv()
app = Flask(__name__)
app.secret_key = os.urandom(24)  # For session management

logging.basicConfig(level=logging.INFO)

# HTML Template for the dashboard
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Link Phones AI Agent - Testing Dashboard</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }
        
        .dashboard {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .card {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        
        .card h2 {
            color: #333;
            margin-bottom: 20px;
            font-size: 1.5em;
            border-bottom: 2px solid #f0f0f0;
            padding-bottom: 10px;
        }
        
        .card h2 i {
            margin-right: 10px;
            color: #667eea;
        }
        
        .form-group {
            margin-bottom: 15px;
        }
        
        label {
            display: block;
            margin-bottom: 5px;
            color: #555;
            font-weight: 500;
        }
        
        input[type="text"],
        input[type="password"],
        input[type="url"],
        select,
        textarea {
            width: 100%;
            padding: 10px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 14px;
            transition: border-color 0.3s;
        }
        
        input:focus,
        select:focus,
        textarea:focus {
            outline: none;
            border-color: #667eea;
        }
        
        textarea {
            min-height: 100px;
            resize: vertical;
        }
        
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 25px;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.3s, box-shadow 0.3s;
            width: 100%;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
        }
        
        .btn-small {
            padding: 8px 15px;
            font-size: 14px;
            width: auto;
        }
        
        .platform-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 10px;
            margin: 15px 0;
        }
        
        .platform-checkbox {
            display: flex;
            align-items: center;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 8px;
            cursor: pointer;
            transition: background 0.3s;
        }
        
        .platform-checkbox:hover {
            background: #e9ecef;
        }
        
        .platform-checkbox input {
            margin-right: 8px;
        }
        
        .result-box {
            margin-top: 20px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }
        
        .result-box.success {
            border-left-color: #28a745;
        }
        
        .result-box.error {
            border-left-color: #dc3545;
        }
        
        .result-box h3 {
            color: #333;
            margin-bottom: 10px;
            font-size: 1.1em;
        }
        
        .result-box pre {
            background: white;
            padding: 10px;
            border-radius: 5px;
            overflow-x: auto;
            font-size: 12px;
            border: 1px solid #e0e0e0;
        }
        
        .status-badge {
            display: inline-block;
            padding: 5px 10px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            margin-left: 10px;
        }
        
        .status-badge.connected {
            background: #d4edda;
            color: #155724;
        }
        
        .status-badge.disconnected {
            background: #f8d7da;
            color: #721c24;
        }
        
        .api-key-input {
            font-family: monospace;
            background: #f8f9fa;
        }
        
        .footer {
            text-align: center;
            color: white;
            margin-top: 30px;
            opacity: 0.8;
        }
        
        .footer a {
            color: white;
            text-decoration: none;
            font-weight: 600;
        }
        
        .footer a:hover {
            text-decoration: underline;
        }
        
        .tabs {
            display: flex;
            margin-bottom: 20px;
            border-bottom: 2px solid #e0e0e0;
        }
        
        .tab {
            padding: 10px 20px;
            cursor: pointer;
            color: #666;
            font-weight: 500;
            transition: all 0.3s;
        }
        
        .tab.active {
            color: #667eea;
            border-bottom: 2px solid #667eea;
            margin-bottom: -2px;
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
        }
        
        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Link Phones AI Agent</h1>
            <p>Test your social media automation with AI-powered content generation</p>
        </div>
        
        <div class="dashboard">
            <!-- Test Configuration Card -->
            <div class="card">
                <h2><i>⚙️</i> 1. Configure Test</h2>
                
                <div class="tabs">
                    <div class="tab active" onclick="switchTab('quick')">Quick Test</div>
                    <div class="tab" onclick="switchTab('custom')">Custom Post</div>
                </div>
                
                <!-- Quick Test Tab -->
                <div id="quick-tab" class="tab-content active">
                    <div class="form-group">
                        <label>Select Platforms to Test:</label>
                        <div class="platform-grid">
                            <label class="platform-checkbox">
                                <input type="checkbox" id="platform-fb" checked> Facebook
                            </label>
                            <label class="platform-checkbox">
                                <input type="checkbox" id="platform-ig"> Instagram
                            </label>
                            <label class="platform-checkbox">
                                <input type="checkbox" id="platform-twitter"> Twitter
                            </label>
                            <label class="platform-checkbox">
                                <input type="checkbox" id="platform-li"> LinkedIn
                            </label>
                        </div>
                    </div>
                    
                    <button class="btn" onclick="quickTest()">🚀 Run Quick Test</button>
                </div>
                
                <!-- Custom Post Tab -->
                <div id="custom-tab" class="tab-content">
                    <div class="form-group">
                        <label>Custom Caption:</label>
                        <textarea id="custom-caption" placeholder="Enter your own caption or leave empty for AI-generated..."></textarea>
                    </div>
                    
                    <div class="form-group">
                        <label>Image URL (optional):</label>
                        <input type="url" id="custom-image" placeholder="https://example.com/image.jpg">
                    </div>
                    
                    <div class="platform-grid">
                        <label class="platform-checkbox">
                            <input type="checkbox" id="custom-fb" checked> Facebook
                        </label>
                        <label class="platform-checkbox">
                            <input type="checkbox" id="custom-ig"> Instagram
                        </label>
                        <label class="platform-checkbox">
                            <input type="checkbox" id="custom-twitter"> Twitter
                        </label>
                    </div>
                    
                    <button class="btn" onclick="customPost()">📤 Post Custom</button>
                </div>
                
                <div id="test-result" class="result-box" style="display: none;"></div>
            </div>
            
            <!-- AI Configuration Card -->
            <div class="card">
                <h2><i>🧠</i> 2. AI Settings</h2>
                
                <div class="form-group">
                    <label>OpenAI API Key:</label>
                    <input type="text" id="openai-key" class="api-key-input" placeholder="sk-..." value="{{ openai_key or '' }}">
                </div>
                
                <div class="form-group">
                    <label>Google Sheet ID (optional):</label>
                    <input type="text" id="sheet-id" placeholder="1djqEYbqC0Sp_Rx7-5dQz5vKNS-U6PGAfL_pRnUWy5zw" value="{{ sheet_id or '' }}">
                </div>
                
                <div class="form-group">
                    <label>Test Phone (if no sheet):</label>
                    <select id="test-phone">
                        <option value="iphone13">iPhone 13 128GB - KES 65,000</option>
                        <option value="samsung23">Samsung S23 256GB - KES 72,000</option>
                        <option value="iphone12">iPhone 12 64GB - KES 48,000</option>
                    </select>
                </div>
                
                <button class="btn" onclick="saveSettings()">💾 Save Settings</button>
                
                <div class="result-box" id="ai-status" style="display: none;"></div>
            </div>
            
            <!-- Platform Connection Card -->
            <div class="card">
                <h2><i>🔌</i> 3. Connect Platforms</h2>
                
                <p style="color: #666; margin-bottom: 20px;">Connect your social accounts to test posting:</p>
                
                <div class="platform-grid" style="grid-template-columns: 1fr;">
                    <div class="platform-checkbox" style="justify-content: space-between;">
                        <span><i>📘</i> Facebook</span>
                        <span class="status-badge connected">Connected</span>
                    </div>
                    
                    <div class="platform-checkbox" style="justify-content: space-between;">
                        <span><i>📷</i> Instagram</span>
                        <span class="status-badge connected">Connected</span>
                    </div>
                    
                    <div class="platform-checkbox" style="justify-content: space-between;">
                        <span><i>🐦</i> Twitter</span>
                        <span class="status-badge disconnected">Not Connected</span>
                        <button class="btn-small" onclick="connectPlatform('twitter')">Connect</button>
                    </div>
                    
                    <div class="platform-checkbox" style="justify-content: space-between;">
                        <span><i>🔗</i> LinkedIn</span>
                        <span class="status-badge disconnected">Not Connected</span>
                        <button class="btn-small" onclick="connectPlatform('linkedin')">Connect</button>
                    </div>
                </div>
                
                <div style="margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 8px;">
                    <p style="color: #666; margin-bottom: 10px;"><strong>🔑 API Key Status:</strong></p>
                    <p style="font-size: 14px;">✅ Ayrshare API: Configured</p>
                    <p style="font-size: 14px;">✅ OpenAI API: {{ 'Configured' if openai_key else '❌ Not Set' }}</p>
                </div>
            </div>
        </div>
        
        <!-- Recent Posts Card -->
        <div class="card" style="grid-column: 1/-1;">
            <h2><i>📊</i> Recent Test Posts</h2>
            
            <div id="recent-posts">
                {% if recent_posts %}
                    {% for post in recent_posts %}
                    <div class="result-box success" style="margin-top: 10px;">
                        <div style="display: flex; justify-content: space-between;">
                            <span><strong>{{ post.time }}</strong> - {{ post.platforms|join(', ') }}</span>
                            <span style="color: #28a745;">✓ Success</span>
                        </div>
                        <pre style="margin-top: 10px;">{{ post.caption[:100] }}...</pre>
                    </div>
                    {% endfor %}
                {% else %}
                    <p style="color: #666; text-align: center;">No test posts yet. Run a test above!</p>
                {% endif %}
            </div>
        </div>
        
        <!-- API Documentation Card -->
        <div class="card" style="grid-column: 1/-1;">
            <h2><i>📚</i> API Endpoints for Testing</h2>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px;">
                <div>
                    <h3>POST /api/test</h3>
                    <p style="color: #666; font-size: 14px;">Run a test post</p>
                    <pre style="background: #f8f9fa; padding: 10px; border-radius: 5px; font-size: 12px;">{
  "platforms": ["facebook"],
  "caption": "optional"
}</pre>
                </div>
                
                <div>
                    <h3>GET /health</h3>
                    <p style="color: #666; font-size: 14px;">Health check</p>
                    <pre style="background: #f8f9fa; padding: 10px; border-radius: 5px;">{
  "status": "healthy"
}</pre>
                </div>
                
                <div>
                    <h3>GET /post-now</h3>
                    <p style="color: #666; font-size: 14px;">Quick test post</p>
                    <p><a href="/post-now" target="_blank">Try it now →</a></p>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>Built with ❤️ for Link Phones | <a href="https://github.com/yourusername/link-phones-ai-agent" target="_blank">GitHub</a></p>
        </div>
    </div>
    
    <script>
        let recentPosts = [];
        
        function switchTab(tab) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            
            if (tab === 'quick') {
                document.querySelectorAll('.tab')[0].classList.add('active');
                document.getElementById('quick-tab').classList.add('active');
            } else {
                document.querySelectorAll('.tab')[1].classList.add('active');
                document.getElementById('custom-tab').classList.add('active');
            }
        }
        
        async function quickTest() {
            const resultBox = document.getElementById('test-result');
            resultBox.style.display = 'block';
            resultBox.className = 'result-box';
            resultBox.innerHTML = '<div class="loading" style="margin-right: 10px;"></div> Testing...';
            
            // Get selected platforms
            const platforms = [];
            if (document.getElementById('platform-fb').checked) platforms.push('facebook');
            if (document.getElementById('platform-ig').checked) platforms.push('instagram');
            if (document.getElementById('platform-twitter').checked) platforms.push('twitter');
            if (document.getElementById('platform-li').checked) platforms.push('linkedin');
            
            if (platforms.length === 0) {
                resultBox.innerHTML = '<h3>❌ Error</h3><p>Select at least one platform</p>';
                resultBox.classList.add('error');
                return;
            }
            
            try {
                const response = await fetch('/api/test', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        platforms: platforms,
                        test_phone: document.getElementById('test-phone').value
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    resultBox.className = 'result-box success';
                    resultBox.innerHTML = `
                        <h3>✅ Test Successful!</h3>
                        <p>Posted to: ${platforms.join(', ')}</p>
                        <pre>${JSON.stringify(data.result, null, 2)}</pre>
                    `;
                    
                    // Add to recent posts
                    const postList = document.getElementById('recent-posts');
                    const newPost = document.createElement('div');
                    newPost.className = 'result-box success';
                    newPost.style.marginTop = '10px';
                    newPost.innerHTML = `
                        <div style="display: flex; justify-content: space-between;">
                            <span><strong>${new Date().toLocaleTimeString()}</strong> - ${platforms.join(', ')}</span>
                            <span style="color: #28a745;">✓ Success</span>
                        </div>
                        <pre style="margin-top: 10px;">${data.caption.substring(0, 100)}...</pre>
                    `;
                    postList.prepend(newPost);
                    
                } else {
                    resultBox.className = 'result-box error';
                    resultBox.innerHTML = `
                        <h3>❌ Test Failed</h3>
                        <p>Error: ${data.error}</p>
                    `;
                }
            } catch (e) {
                resultBox.className = 'result-box error';
                resultBox.innerHTML = `<h3>❌ Error</h3><p>${e.message}</p>`;
            }
        }
        
        async function customPost() {
            const resultBox = document.getElementById('test-result');
            resultBox.style.display = 'block';
            resultBox.className = 'result-box';
            resultBox.innerHTML = '<div class="loading" style="margin-right: 10px;"></div> Posting...';
            
            const platforms = [];
            if (document.getElementById('custom-fb').checked) platforms.push('facebook');
            if (document.getElementById('custom-ig').checked) platforms.push('instagram');
            if (document.getElementById('custom-twitter').checked) platforms.push('twitter');
            
            try {
                const response = await fetch('/api/test', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        platforms: platforms,
                        custom_caption: document.getElementById('custom-caption').value,
                        custom_image: document.getElementById('custom-image').value
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    resultBox.className = 'result-box success';
                    resultBox.innerHTML = `
                        <h3>✅ Posted Successfully!</h3>
                        <pre>${JSON.stringify(data.result, null, 2)}</pre>
                    `;
                } else {
                    resultBox.className = 'result-box error';
                    resultBox.innerHTML = `<h3>❌ Failed</h3><p>${data.error}</p>`;
                }
            } catch (e) {
                resultBox.className = 'result-box error';
                resultBox.innerHTML = `<h3>❌ Error</h3><p>${e.message}</p>`;
            }
        }
        
        async function saveSettings() {
            const status = document.getElementById('ai-status');
            status.style.display = 'block';
            status.innerHTML = '<div class="loading" style="margin-right: 10px;"></div> Saving...';
            
            try {
                const response = await fetch('/api/settings', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        openai_key: document.getElementById('openai-key').value,
                        sheet_id: document.getElementById('sheet-id').value
                    })
                });
                
                const data = await response.json();
                
                status.className = 'result-box success';
                status.innerHTML = '<h3>✅ Settings Saved</h3>';
                
                setTimeout(() => {
                    status.style.display = 'none';
                }, 3000);
                
            } catch (e) {
                status.className = 'result-box error';
                status.innerHTML = `<h3>❌ Error</h3><p>${e.message}</p>`;
            }
        }
        
        function connectPlatform(platform) {
            alert(`Redirecting to ${platform} OAuth... (This would connect your account)`);
            // In production, this would redirect to Ayrshare/Late OAuth
        }
    </script>
</body>
</html>
'''

# Store recent posts in memory (for demo)
recent_posts = []

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template_string(
        HTML_TEMPLATE,
        openai_key=os.getenv('OPENAI_API_KEY', ''),
        sheet_id=os.getenv('GOOGLE_SHEET_ID', ''),
        recent_posts=recent_posts[-5:]  # Last 5 posts
    )

@app.route('/api/test', methods=['POST'])
def test_post():
    """API endpoint for testing posts"""
    try:
        data = request.json
        platforms = data.get('platforms', ['facebook'])
        custom_caption = data.get('custom_caption')
        custom_image = data.get('custom_image')
        test_phone = data.get('test_phone', 'iphone13')
        
        # Initialize manager
        manager = PostManager()
        
        if custom_caption:
            # Use custom caption
            caption = custom_caption
            phone = {'model': 'Custom', 'storage': '', 'price': '', 'condition': 'New'}
            image_path = 'data/posts/custom.jpg'
            
            # Create placeholder
            manager._create_placeholder_image(phone, image_path)
            
            # Upload image
            image_url = manager._upload_image_to_hosting(image_path)
            
            # Post to platforms
            result = manager.multi_poster.post(
                caption=caption,
                image_url=image_url,
                platforms=platforms
            )
        else:
            # Use AI-generated content
            result = manager.create_and_post_multi(platforms=platforms)
            caption = "AI-generated content"
        
        # Store in recent posts
        recent_posts.append({
            'time': datetime.now().strftime('%H:%M:%S'),
            'platforms': platforms,
            'caption': caption[:100],
            'result': result
        })
        
        return jsonify({
            'success': True,
            'result': result,
            'caption': caption
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/settings', methods=['POST'])
def save_settings():
    """Save user settings (temporarily in session)"""
    try:
        data = request.json
        
        # In production, you'd save these to a database
        # For testing, we'll just acknowledge
        if data.get('openai_key'):
            os.environ['OPENAI_API_KEY'] = data['openai_key']
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/post-now')
def post_now():
    """Quick test endpoint"""
    try:
        manager = PostManager()
        success = manager.create_and_post_multi(platforms=["facebook"])
        return jsonify({"success": success}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy"}), 200

# Background scheduler
def run_scheduler():
    """Run scheduled posts in background"""
    manager = PostManager()
    manager.ai_agent.load_inventory()
    
    import schedule
    import time
    
    schedule.every().day.at("09:00").do(manager.create_and_post_multi)
    schedule.every().day.at("19:00").do(manager.create_and_post_multi)
    
    while True:
        schedule.run_pending()
        time.sleep(60)

# Start scheduler in background thread
if __name__ != '__main__':
    thread = threading.Thread(target=run_scheduler, daemon=True)
    thread.start()
    app.logger.info("✅ Scheduler started")

if __name__ == '__main__':
    thread = threading.Thread(target=run_scheduler, daemon=True)
    thread.start()
    app.run(host='0.0.7', port=5000, debug=True)