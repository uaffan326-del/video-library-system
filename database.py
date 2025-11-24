import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional
import os


class VideoDatabase:
    """Manages SQLite database for video clips and their metadata."""
    
    def __init__(self, db_path: str = "video_library.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Main videos table - EXTENDED
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT,
                source_url TEXT NOT NULL,
                source_identifier TEXT,
                file_path TEXT NOT NULL,
                duration REAL,
                width INTEGER,
                height INTEGER,
                file_size INTEGER,
                motion_level TEXT,
                motion_score REAL,
                bpm REAL,
                tempo_category TEXT,
                energy_level REAL,
                autoplay_compatible BOOLEAN DEFAULT 0,
                is_web_optimized BOOLEAN DEFAULT 0,
                video_codec TEXT,
                audio_codec TEXT,
                category TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(file_path)
            )
        ''')
        
        # Tags table for themes, styles, etc.
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id INTEGER NOT NULL,
                tag_type TEXT NOT NULL,
                tag_value TEXT NOT NULL,
                confidence REAL,
                FOREIGN KEY (video_id) REFERENCES videos(id) ON DELETE CASCADE
            )
        ''')
        
        # Colors table for dominant colors
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS colors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id INTEGER NOT NULL,
                color_hex TEXT NOT NULL,
                color_name TEXT,
                percentage REAL,
                FOREIGN KEY (video_id) REFERENCES videos(id) ON DELETE CASCADE
            )
        ''')
        
        # Mood/sentiment table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS moods (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id INTEGER NOT NULL,
                mood_type TEXT NOT NULL,
                intensity REAL,
                description TEXT,
                FOREIGN KEY (video_id) REFERENCES videos(id) ON DELETE CASCADE
            )
        ''')
        
        # AI analysis metadata
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id INTEGER NOT NULL,
                analysis_type TEXT NOT NULL,
                result_json TEXT,
                analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (video_id) REFERENCES videos(id) ON DELETE CASCADE
            )
        ''')
        
        # NEW: Key frames table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS key_frames (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id INTEGER NOT NULL,
                frame_index INTEGER NOT NULL,
                timestamp REAL NOT NULL,
                frame_path TEXT,
                thumbnail_path TEXT,
                is_representative BOOLEAN DEFAULT 0,
                FOREIGN KEY (video_id) REFERENCES videos(id) ON DELETE CASCADE
            )
        ''')
        
        # NEW: Use cases table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS use_cases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id INTEGER NOT NULL,
                use_case TEXT NOT NULL,
                suitability_score REAL,
                description TEXT,
                FOREIGN KEY (video_id) REFERENCES videos(id) ON DELETE CASCADE
            )
        ''')
        
        # NEW: Categories table for auto-categorization
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                parent_category TEXT,
                description TEXT
            )
        ''')
        
        # Create indexes for faster queries
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tags_video ON tags(video_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tags_type ON tags(tag_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tags_value ON tags(tag_value)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_colors_video ON colors(video_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_moods_video ON moods(video_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_motion_level ON videos(motion_level)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_bpm ON videos(bpm)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_category ON videos(category)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_key_frames_video ON key_frames(video_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_use_cases_video ON use_cases(video_id)')
        
        conn.commit()
        conn.close()
    
    def add_video(self, source_url: str, file_path: str, source_identifier: str = None,
                  duration: float = None, width: int = None, height: int = None, 
                  source: str = None, motion_level: str = None, motion_score: float = None,
                  bpm: float = None, tempo_category: str = None, energy_level: float = None,
                  autoplay_compatible: bool = False, is_web_optimized: bool = False,
                  video_codec: str = None, audio_codec: str = None, category: str = None) -> int:
        """Add a video entry to the database with extended fields."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            file_size = os.path.getsize(file_path) if os.path.exists(file_path) else None
            
            cursor.execute('''
                INSERT INTO videos (source, source_url, source_identifier, file_path, duration, 
                                  width, height, file_size, motion_level, motion_score, bpm, 
                                  tempo_category, energy_level, autoplay_compatible, is_web_optimized,
                                  video_codec, audio_codec, category)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (source, source_url, source_identifier, file_path, duration, width, height, 
                  file_size, motion_level, motion_score, bpm, tempo_category, energy_level,
                  autoplay_compatible, is_web_optimized, video_codec, audio_codec, category))
            
            video_id = cursor.lastrowid
            conn.commit()
            return video_id
        except sqlite3.IntegrityError:
            # Video already exists
            cursor.execute('SELECT id FROM videos WHERE file_path = ?', (file_path,))
            return cursor.fetchone()[0]
        finally:
            conn.close()
    
    def add_tags(self, video_id: int, tags: List[Dict[str, any]]):
        """Add tags to a video. Tags format: [{'type': 'theme', 'value': 'nature', 'confidence': 0.9}, ...]"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for tag in tags:
            cursor.execute('''
                INSERT INTO tags (video_id, tag_type, tag_value, confidence)
                VALUES (?, ?, ?, ?)
            ''', (video_id, tag.get('type'), tag.get('value'), tag.get('confidence', 1.0)))
        
        conn.commit()
        conn.close()
    
    def add_colors(self, video_id: int, colors: List[Dict[str, any]]):
        """Add dominant colors. Format: [{'hex': '#FF5733', 'name': 'red', 'percentage': 0.4}, ...]"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for color in colors:
            cursor.execute('''
                INSERT INTO colors (video_id, color_hex, color_name, percentage)
                VALUES (?, ?, ?, ?)
            ''', (video_id, color.get('hex'), color.get('name'), color.get('percentage')))
        
        conn.commit()
        conn.close()
    
    def add_mood(self, video_id: int, mood_type: str, intensity: float = None, description: str = None):
        """Add mood analysis. mood_type: 'positive', 'negative', 'neutral'"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO moods (video_id, mood_type, intensity, description)
            VALUES (?, ?, ?, ?)
        ''', (video_id, mood_type, intensity, description))
        
        conn.commit()
        conn.close()
    
    def add_ai_analysis(self, video_id: int, analysis_type: str, result: dict):
        """Store complete AI analysis results as JSON."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO ai_analysis (video_id, analysis_type, result_json)
            VALUES (?, ?, ?)
        ''', (video_id, analysis_type, json.dumps(result)))
        
        conn.commit()
        conn.close()
    
    def search_videos(self, tags: List[str] = None, mood: str = None, 
                      color: str = None, limit: int = 10) -> List[Dict]:
        """Search videos by tags, mood, or color."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = 'SELECT DISTINCT v.* FROM videos v'
        conditions = []
        params = []
        
        if tags:
            query += ' JOIN tags t ON v.id = t.video_id'
            conditions.append(f't.tag_value IN ({",".join(["?" for _ in tags])})')
            params.extend(tags)
        
        if mood:
            query += ' JOIN moods m ON v.id = m.video_id'
            conditions.append('m.mood_type = ?')
            params.append(mood)
        
        if color:
            query += ' JOIN colors c ON v.id = c.video_id'
            conditions.append('c.color_name = ? OR c.color_hex = ?')
            params.extend([color, color])
        
        if conditions:
            query += ' WHERE ' + ' AND '.join(conditions)
        
        query += f' LIMIT {limit}'
        
        cursor.execute(query, params)
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return results
    
    def get_video_details(self, video_id: int) -> Dict:
        """Get complete details for a video including tags, colors, and mood."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get video info
        cursor.execute('SELECT * FROM videos WHERE id = ?', (video_id,))
        video = dict(cursor.fetchone())
        
        # Get tags
        cursor.execute('SELECT tag_type, tag_value, confidence FROM tags WHERE video_id = ?', (video_id,))
        video['tags'] = [dict(row) for row in cursor.fetchall()]
        
        # Get colors
        cursor.execute('SELECT color_hex, color_name, percentage FROM colors WHERE video_id = ?', (video_id,))
        video['colors'] = [dict(row) for row in cursor.fetchall()]
        
        # Get moods
        cursor.execute('SELECT mood_type, intensity, description FROM moods WHERE video_id = ?', (video_id,))
        video['moods'] = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        return video
    
    def get_stats(self) -> Dict:
        """Get database statistics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {}
        cursor.execute('SELECT COUNT(*) FROM videos')
        stats['total_videos'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(DISTINCT tag_value) FROM tags')
        stats['unique_tags'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(DISTINCT color_name) FROM colors')
        stats['unique_colors'] = cursor.fetchone()[0]
        
        conn.close()
        return stats
    
    def add_key_frame(self, video_id: int, frame_index: int, timestamp: float,
                     frame_path: str = None, thumbnail_path: str = None, 
                     is_representative: bool = False):
        """Add a key frame for a video."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO key_frames (video_id, frame_index, timestamp, frame_path, 
                                   thumbnail_path, is_representative)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (video_id, frame_index, timestamp, frame_path, thumbnail_path, is_representative))
        
        conn.commit()
        conn.close()
    
    def add_use_case(self, video_id: int, use_case: str, suitability_score: float = None,
                    description: str = None):
        """Add a use case recommendation for a video."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO use_cases (video_id, use_case, suitability_score, description)
            VALUES (?, ?, ?, ?)
        ''', (video_id, use_case, suitability_score, description))
        
        conn.commit()
        conn.close()
    
    def add_category(self, name: str, parent_category: str = None, description: str = None):
        """Add a category to the categories table."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO categories (name, parent_category, description)
                VALUES (?, ?, ?)
            ''', (name, parent_category, description))
            conn.commit()
        except sqlite3.IntegrityError:
            pass  # Category already exists
        finally:
            conn.close()
    
    def update_video_category(self, video_id: int, category: str):
        """Update the category for a video."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('UPDATE videos SET category = ? WHERE id = ?', (category, video_id))
        
        conn.commit()
        conn.close()
    
    def search_by_motion(self, motion_level: str, limit: int = 10) -> List[Dict]:
        """Search videos by motion level."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM videos WHERE motion_level = ? LIMIT ?
        ''', (motion_level, limit))
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results
    
    def search_by_tempo(self, min_bpm: float, max_bpm: float, limit: int = 10) -> List[Dict]:
        """Search videos by BPM range."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM videos WHERE bpm BETWEEN ? AND ? ORDER BY bpm LIMIT ?
        ''', (min_bpm, max_bpm, limit))
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results
