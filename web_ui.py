"""
Web UI Server for Video Database Browser

A Flask-based web interface to browse, search, and preview video clips.
"""

from flask import Flask, render_template, jsonify, request, send_file, redirect, url_for, flash
from flask_cors import CORS
from flask_login import login_required, current_user, login_user, logout_user
import os
from database import VideoDatabase
from search import VideoSearcher
import cv2
from pathlib import Path
import threading
import time
from auth import init_auth, authenticate_user

app = Flask(__name__)
CORS(app)

# Initialize authentication
init_auth(app)

# Initialize database and searcher
db = VideoDatabase()
searcher = VideoSearcher()

# Thumbnail directory
THUMBNAIL_DIR = "thumbnails"
os.makedirs(THUMBNAIL_DIR, exist_ok=True)

# Scraping state
scraping_state = {
    'running': False,
    'progress': 0,
    'status': 'idle',
    'current_task': '',
    'videos_processed': 0,
    'clips_created': 0,
    'error': None
}
scraping_thread = None


def generate_thumbnail(video_path: str, output_path: str, time_seconds: float = 1.0):
    """Generate a thumbnail for a video."""
    if os.path.exists(output_path):
        return True
    
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return False
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_number = int(time_seconds * fps)
        
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = cap.read()
        cap.release()
        
        if ret:
            # Resize to thumbnail size
            height, width = frame.shape[:2]
            max_width = 320
            if width > max_width:
                scale = max_width / width
                new_width = int(width * scale)
                new_height = int(height * scale)
                frame = cv2.resize(frame, (new_width, new_height))
            
            cv2.imwrite(output_path, frame)
            return True
        
        return False
    except Exception as e:
        print(f"Error generating thumbnail: {e}")
        return False


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        user = authenticate_user(username, password)
        if user:
            login_user(user, remember=True)
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('index'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """Logout user."""
    logout_user()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('login'))


@app.route('/')
@login_required
def index():
    """Main page."""
    return render_template('index.html')


@app.route('/api/stats')
@login_required
def get_stats():
    """Get database statistics."""
    try:
        stats = searcher.get_stats_summary()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/videos')
@login_required
def get_videos():
    """Get videos with optional filters."""
    try:
        # Get query parameters
        keywords = request.args.get('keywords', '').strip()
        mood = request.args.get('mood', '').strip()
        color = request.args.get('color', '').strip()
        limit = int(request.args.get('limit', 50))
        
        # Parse keywords
        keyword_list = [k.strip() for k in keywords.split(',') if k.strip()] if keywords else None
        
        # Search videos
        if keyword_list or mood or color:
            videos = searcher.search_combined(
                keywords=keyword_list,
                mood=mood if mood else None,
                color=color if color else None,
                limit=limit
            )
        else:
            # Get random videos if no filters
            videos = searcher.get_random_videos(count=limit)
        
        # Add thumbnails and full details
        for video in videos:
            video_details = db.get_video_details(video['id'])
            video.update(video_details)
            
            # Generate thumbnail path
            video_filename = Path(video['file_path']).stem
            thumbnail_path = os.path.join(THUMBNAIL_DIR, f"{video_filename}.jpg")
            
            # Generate thumbnail if it doesn't exist
            if not os.path.exists(thumbnail_path) and os.path.exists(video['file_path']):
                generate_thumbnail(video['file_path'], thumbnail_path)
            
            video['thumbnail'] = f"/api/thumbnail/{video_filename}.jpg" if os.path.exists(thumbnail_path) else None
            video['video_url'] = f"/api/video/{video['id']}"
        
        return jsonify({'videos': videos, 'count': len(videos)})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/video/<int:video_id>')
@login_required
def get_video_file(video_id):
    """Serve video file."""
    try:
        import sqlite3
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT file_path FROM videos WHERE id = ?', (video_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result and os.path.exists(result[0]):
            return send_file(result[0], mimetype='video/mp4')
        else:
            return jsonify({'error': 'Video not found'}), 404
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/thumbnail/<path:filename>')
@login_required
def get_thumbnail(filename):
    """Serve thumbnail image."""
    thumbnail_path = os.path.join(THUMBNAIL_DIR, filename)
    if os.path.exists(thumbnail_path):
        return send_file(thumbnail_path, mimetype='image/jpeg')
    else:
        return jsonify({'error': 'Thumbnail not found'}), 404


@app.route('/api/video/<int:video_id>/details')
@login_required
def get_video_details(video_id):
    """Get detailed information about a video."""
    try:
        details = db.get_video_details(video_id)
        return jsonify(details)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/search/lyric', methods=['POST'])
@login_required
def search_by_lyric():
    """Search for video matching a lyric line."""
    try:
        data = request.json
        lyric_text = data.get('lyric', '')
        mood_hint = data.get('mood', None)
        
        if not lyric_text:
            return jsonify({'error': 'Lyric text required'}), 400
        
        video = searcher.get_video_for_lyric(lyric_text, mood_hint)
        
        if video:
            # Add full details
            video_details = db.get_video_details(video['id'])
            video.update(video_details)
            
            # Add thumbnail
            video_filename = Path(video['file_path']).stem
            thumbnail_path = os.path.join(THUMBNAIL_DIR, f"{video_filename}.jpg")
            if not os.path.exists(thumbnail_path) and os.path.exists(video['file_path']):
                generate_thumbnail(video['file_path'], thumbnail_path)
            
            video['thumbnail'] = f"/api/thumbnail/{video_filename}.jpg" if os.path.exists(thumbnail_path) else None
            video['video_url'] = f"/api/video/{video['id']}"
            
            return jsonify({'video': video})
        else:
            return jsonify({'error': 'No matching video found'}), 404
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/tags')
@login_required
def get_all_tags():
    """Get all unique tags for filters."""
    try:
        import sqlite3
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()
        
        # Get themes
        cursor.execute('SELECT DISTINCT tag_value FROM tags WHERE tag_type = "theme" ORDER BY tag_value')
        themes = [row[0] for row in cursor.fetchall()]
        
        # Get styles
        cursor.execute('SELECT DISTINCT tag_value FROM tags WHERE tag_type = "style" ORDER BY tag_value')
        styles = [row[0] for row in cursor.fetchall()]
        
        # Get energy levels
        cursor.execute('SELECT DISTINCT tag_value FROM tags WHERE tag_type = "energy" ORDER BY tag_value')
        energies = [row[0] for row in cursor.fetchall()]
        
        # Get moods
        cursor.execute('SELECT DISTINCT mood_type FROM moods ORDER BY mood_type')
        moods = [row[0] for row in cursor.fetchall()]
        
        # Get colors
        cursor.execute('SELECT DISTINCT color_name FROM colors ORDER BY color_name')
        colors = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            'themes': themes,
            'styles': styles,
            'energies': energies,
            'moods': moods,
            'colors': colors
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Scraping Control Endpoints

def run_scraping_pipeline(queries, videos_per_query):
    """Run scraping pipeline in background thread."""
    global scraping_state
    
    try:
        from scraper import ArchiveOrgScraper
        from video_processor import VideoClipper
        from ai_tagger import AITagger
        from dotenv import load_dotenv
        
        load_dotenv()
        api_key = os.getenv('OPENAI_API_KEY')
        
        scraping_state['running'] = True
        scraping_state['status'] = 'initializing'
        scraping_state['progress'] = 0
        scraping_state['error'] = None
        
        scraper = ArchiveOrgScraper(download_dir="downloads")
        clipper = VideoClipper(output_dir="processed_clips", clip_duration=(3, 5))
        tagger = AITagger(api_key=api_key)
        
        # Download videos
        scraping_state['status'] = 'downloading'
        scraping_state['current_task'] = f'Downloading videos for {len(queries)} queries'
        downloaded_videos = scraper.batch_download(queries, videos_per_query)
        scraping_state['videos_processed'] = len(downloaded_videos)
        scraping_state['progress'] = 25
        
        if not downloaded_videos:
            scraping_state['error'] = 'No videos downloaded'
            scraping_state['running'] = False
            return
        
        # Clip videos
        scraping_state['status'] = 'clipping'
        scraping_state['current_task'] = f'Clipping {len(downloaded_videos)} videos'
        video_paths = [v['filepath'] for v in downloaded_videos]
        all_clips = clipper.process_batch(video_paths)
        scraping_state['clips_created'] = len(all_clips)
        scraping_state['progress'] = 50
        
        if not all_clips:
            scraping_state['error'] = 'No clips created'
            scraping_state['running'] = False
            return
        
        # Analyze and store
        scraping_state['status'] = 'analyzing'
        total_clips = len(all_clips)
        
        for i, clip in enumerate(all_clips):
            if not scraping_state['running']:  # Check for cancellation
                break
                
            scraping_state['current_task'] = f'Analyzing clip {i+1}/{total_clips}'
            scraping_state['progress'] = 50 + int((i / total_clips) * 50)
            
            try:
                frames = clipper.extract_multiple_frames(clip['path'], num_frames=3)
                if not frames:
                    continue
                
                analysis = tagger.analyze_video_clip(frames)
                if not analysis:
                    continue
                
                source_video = next(
                    (v for v in downloaded_videos if v['filepath'] == clip['source_video']),
                    None
                )
                
                video_id = db.add_video(
                    source_url=source_video['original_url'] if source_video else '',
                    file_path=clip['path'],
                    source_identifier=source_video['identifier'] if source_video else '',
                    duration=clip['duration'],
                    width=clip.get('width'),
                    height=clip.get('height')
                )
                
                # Add tags
                tags = []
                if analysis.get('theme'):
                    tags.append({'type': 'theme', 'value': analysis['theme'], 'confidence': 1.0})
                if analysis.get('style'):
                    tags.append({'type': 'style', 'value': analysis['style'], 'confidence': 1.0})
                if analysis.get('energy'):
                    tags.append({'type': 'energy', 'value': analysis['energy'], 'confidence': 1.0})
                for keyword in analysis.get('keywords', []):
                    tags.append({'type': 'keyword', 'value': keyword, 'confidence': 0.8})
                if analysis.get('suitable_for'):
                    tags.append({'type': 'genre', 'value': analysis['suitable_for'], 'confidence': 0.9})
                if source_video and source_video.get('search_query'):
                    tags.append({'type': 'search_query', 'value': source_video['search_query'], 'confidence': 1.0})
                
                db.add_tags(video_id, tags)
                db.add_colors(video_id, analysis.get('dominant_colors', []))
                db.add_mood(video_id, analysis.get('mood', 'neutral'), analysis.get('mood_intensity', 5))
                db.add_ai_analysis(video_id, 'gpt4_vision', analysis)
                
            except Exception as e:
                print(f"Error processing clip: {e}")
                continue
        
        scraping_state['status'] = 'completed'
        scraping_state['progress'] = 100
        scraping_state['current_task'] = f'Completed! Processed {scraping_state["clips_created"]} clips'
        scraping_state['running'] = False
        
    except Exception as e:
        scraping_state['error'] = str(e)
        scraping_state['status'] = 'error'
        scraping_state['running'] = False
        print(f"Scraping error: {e}")


@app.route('/api/scraping/start', methods=['POST'])
@login_required
def start_scraping():
    """Start the scraping pipeline."""
    global scraping_state, scraping_thread
    
    if scraping_state['running']:
        return jsonify({'error': 'Scraping already in progress'}), 400
    
    try:
        data = request.json or {}
        queries = data.get('queries', ['abstract motion background', 'nature landscape scenic', 'city urban timelapse'])
        videos_per_query = data.get('videos_per_query', 2)
        
        # Reset state
        scraping_state = {
            'running': True,
            'progress': 0,
            'status': 'starting',
            'current_task': 'Initializing...',
            'videos_processed': 0,
            'clips_created': 0,
            'error': None
        }
        
        # Start scraping in background thread
        scraping_thread = threading.Thread(
            target=run_scraping_pipeline,
            args=(queries, videos_per_query),
            daemon=True
        )
        scraping_thread.start()
        
        return jsonify({'message': 'Scraping started', 'state': scraping_state})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/scraping/stop', methods=['POST'])
@login_required
def stop_scraping():
    """Stop the scraping pipeline."""
    global scraping_state
    
    if not scraping_state['running']:
        return jsonify({'error': 'No scraping in progress'}), 400
    
    scraping_state['running'] = False
    scraping_state['status'] = 'stopped'
    scraping_state['current_task'] = 'Stopped by user'
    
    return jsonify({'message': 'Scraping stopped', 'state': scraping_state})


@app.route('/api/scraping/status')
@login_required
def get_scraping_status():
    """Get current scraping status."""
    return jsonify(scraping_state)


if __name__ == '__main__':
    print("="*60)
    print("Video Database Browser")
    print("="*60)
    print(f"\nStarting web server...")
    print(f"Open your browser and go to: http://localhost:5000")
    print(f"\nPress Ctrl+C to stop the server")
    print("="*60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
