import sys
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
