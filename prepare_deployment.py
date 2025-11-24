"""
PythonAnywhere Deployment Automation Helper

This script prepares everything for PythonAnywhere deployment.
"""

import os
import zipfile
from pathlib import Path

print("="*60)
print("🚀 PythonAnywhere Deployment Helper")
print("="*60)

# Files to include in deployment
DEPLOY_FILES = [
    'web_ui.py', 'auth.py', 'database.py', 'search.py', 'config.py',
    'ai_tagger.py', 'scraper.py', 'video_processor.py', 'requirements.txt',
    'multi_source_scraper.py', 'motion_detector.py', 'tempo_detector.py',
    'autoplay_detector.py', 'auto_categorizer.py', 'export_module.py',
    'templates/login.html', 'templates/index.html',
    'static/style.css', 'static/script.js'
]

# Create deployment package
print("\n📦 Creating deployment package...")
zip_path = "pythonanywhere_deployment.zip"

with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for file in DEPLOY_FILES:
        if os.path.exists(file):
            zipf.write(file)
            print(f"  ✅ Added: {file}")
        else:
            print(f"  ⚠️  Missing: {file}")

print(f"\n✅ Deployment package created: {zip_path}")
print(f"📊 File size: {os.path.getsize(zip_path) / 1024:.2f} KB")

# Create WSGI configuration
wsgi_content = """import sys
import os

# Add your project directory to the sys.path
path = '/home/YOUR_USERNAME/video-library-system'
if path not in sys.path:
    sys.path.append(path)

# Set environment variables
os.environ['OPENAI_API_KEY'] = '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'
os.environ['ADMIN_USERNAME'] = 'admin'
os.environ['ADMIN_PASSWORD'] = 'VideoLib2025!Secure'
os.environ['SECRET_KEY'] = 'pythonanywhere_secret_key_min_32_chars_2025'
os.environ['FLASK_ENV'] = 'production'

# Import Flask app
from web_ui import app as application
"""

with open('pythonanywhere_wsgi.py', 'w') as f:
    f.write(wsgi_content)

print(f"\n✅ WSGI config created: pythonanywhere_wsgi.py")

# Create step-by-step instructions
instructions = """
╔══════════════════════════════════════════════════════════════╗
║          🚀 PYTHONANYWHERE DEPLOYMENT - 5 STEPS              ║
╚══════════════════════════════════════════════════════════════╝

📋 STEP 1: Create Account (2 minutes)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Go to: https://www.pythonanywhere.com/registration/register/beginner/
2. Fill in:
   - Username: [choose yours]
   - Email: [your email]
   - Password: [your password]
3. Click "Register"
4. Check email and verify
✅ No credit card needed!


📋 STEP 2: Upload Files (3 minutes)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OPTION A - Use Git (Recommended):
1. Click "Consoles" tab → "Bash"
2. Run these commands:
   git clone https://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@github.com/uaffan326-del/video-library-system.git
   cd video-library-system

OPTION B - Upload Zip:
1. Click "Files" tab
2. Upload "pythonanywhere_deployment.zip"
3. Click to extract


📋 STEP 3: Install Dependencies (2 minutes)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. In Bash console, run:
   cd video-library-system
   pip3 install --user -r requirements.txt
2. Wait 2-3 minutes for installation


📋 STEP 4: Create Web App (3 minutes)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Click "Web" tab
2. Click "Add a new web app"
3. Choose "Manual configuration"
4. Select "Python 3.10"
5. Click "Next"


📋 STEP 5: Configure WSGI (3 minutes)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. On Web tab, find "Code" section
2. Click "WSGI configuration file" link
3. DELETE everything in the file
4. COPY content from "pythonanywhere_wsgi.py" 
5. REPLACE "YOUR_USERNAME" with your actual username
6. Click "Save"
7. Go back to Web tab
8. Click green "Reload" button


🎉 DONE! Your URL:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
https://YOUR_USERNAME.pythonanywhere.com

Login with:
👤 Username: admin
🔒 Password: VideoLib2025!Secure


⏱️  Total Time: 13 minutes
💰 Total Cost: $0.00 (FREE FOREVER!)
🔒 Your code: Protected on private GitHub
"""

with open('PYTHONANYWHERE_INSTRUCTIONS.txt', 'w') as f:
    f.write(instructions)

print("\n" + instructions)
print("\n" + "="*60)
print("✅ All files ready for deployment!")
print("="*60)
print("\n📄 Files created:")
print("  1. pythonanywhere_deployment.zip")
print("  2. pythonanywhere_wsgi.py")
print("  3. PYTHONANYWHERE_INSTRUCTIONS.txt")
print("\n👉 Open PYTHONANYWHERE_INSTRUCTIONS.txt for step-by-step guide!")
print("="*60)
