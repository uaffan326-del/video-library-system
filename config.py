# Configuration file for project settings
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Configuration settings for the video scraping system."""
    
    # API Keys
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    
    # Database
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'video_library.db')
    
    # Directories
    DOWNLOAD_DIR = 'downloads'
    PROCESSED_CLIPS_DIR = 'processed_clips'
    
    # Video Processing
    CLIP_DURATION_MIN = int(os.getenv('CLIP_DURATION_MIN', '3'))
    CLIP_DURATION_MAX = int(os.getenv('CLIP_DURATION_MAX', '10'))
    
    # Scraping
    MAX_VIDEOS_PER_SEARCH = int(os.getenv('MAX_VIDEOS_PER_SEARCH', '100'))
    
    # AI Analysis
    FRAME_EXTRACT_INTERVAL = float(os.getenv('FRAME_EXTRACT_INTERVAL', '1.0'))
    NUM_FRAMES_FOR_ANALYSIS = 3
    
    # OpenAI Model
    OPENAI_MODEL = 'gpt-4o'
    
    # File size limits (in MB)
    MAX_DOWNLOAD_SIZE_MB = 500
    
    @classmethod
    def validate(cls):
        """Validate configuration."""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY must be set in .env file")
        return True
    
    @classmethod
    def print_config(cls):
        """Print current configuration (hiding sensitive data)."""
        print("Current Configuration:")
        print(f"  Database: {cls.DATABASE_PATH}")
        print(f"  Download directory: {cls.DOWNLOAD_DIR}")
        print(f"  Processed clips directory: {cls.PROCESSED_CLIPS_DIR}")
        print(f"  Clip duration: {cls.CLIP_DURATION_MIN}-{cls.CLIP_DURATION_MAX} seconds")
        print(f"  OpenAI model: {cls.OPENAI_MODEL}")
        print(f"  API Key configured: {'Yes' if cls.OPENAI_API_KEY else 'No'}")
