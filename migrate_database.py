"""
Database Migration Script
Adds new columns for extended features to existing database
"""

import sqlite3
import os

def migrate_database(db_path="video_library.db"):
    """Add new columns and tables to existing database."""
    
    print("🔄 Migrating database schema...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if migration is needed
    cursor.execute("PRAGMA table_info(videos)")
    columns = [col[1] for col in cursor.fetchall()]
    
    print(f"\n📊 Current columns: {', '.join(columns)}")
    
    # Add new columns to videos table if they don't exist
    new_columns = [
        ("source", "TEXT"),
        ("motion_level", "TEXT"),
        ("motion_score", "REAL"),
        ("bpm", "REAL"),
        ("tempo_category", "TEXT"),
        ("energy_level", "REAL"),
        ("autoplay_compatible", "BOOLEAN DEFAULT 0"),
        ("is_web_optimized", "BOOLEAN DEFAULT 0"),
        ("video_codec", "TEXT"),
        ("audio_codec", "TEXT"),
        ("category", "TEXT")
    ]
    
    print("\n➕ Adding new columns...")
    for col_name, col_type in new_columns:
        if col_name not in columns:
            try:
                cursor.execute(f"ALTER TABLE videos ADD COLUMN {col_name} {col_type}")
                print(f"  ✅ Added: {col_name}")
            except sqlite3.OperationalError as e:
                print(f"  ⚠️ {col_name}: {e}")
        else:
            print(f"  ⏭️ Skipped: {col_name} (already exists)")
    
    # Create new tables if they don't exist
    print("\n📋 Creating new tables...")
    
    # Key frames table
    try:
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
        print("  ✅ Created: key_frames")
    except sqlite3.OperationalError as e:
        print(f"  ⚠️ key_frames: {e}")
    
    # Use cases table
    try:
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
        print("  ✅ Created: use_cases")
    except sqlite3.OperationalError as e:
        print(f"  ⚠️ use_cases: {e}")
    
    # Categories table
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                parent_category TEXT,
                description TEXT
            )
        ''')
        print("  ✅ Created: categories")
    except sqlite3.OperationalError as e:
        print(f"  ⚠️ categories: {e}")
    
    # Create new indexes
    print("\n🔍 Creating indexes...")
    
    indexes = [
        ("idx_motion_level", "videos(motion_level)"),
        ("idx_bpm", "videos(bpm)"),
        ("idx_category", "videos(category)"),
        ("idx_key_frames_video", "key_frames(video_id)"),
        ("idx_use_cases_video", "use_cases(video_id)")
    ]
    
    for idx_name, idx_def in indexes:
        try:
            cursor.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {idx_def}")
            print(f"  ✅ Created: {idx_name}")
        except sqlite3.OperationalError as e:
            print(f"  ⚠️ {idx_name}: {e}")
    
    conn.commit()
    
    # Verify migration
    cursor.execute("PRAGMA table_info(videos)")
    new_columns = [col[1] for col in cursor.fetchall()]
    
    print(f"\n✅ Migration complete!")
    print(f"📊 Total columns now: {len(new_columns)}")
    
    conn.close()

if __name__ == "__main__":
    migrate_database()
    print("\n🎉 Database is ready for new features!")
