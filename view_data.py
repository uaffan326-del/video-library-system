#!/usr/bin/env python3
"""
Quick script to view backend data
Usage: python view_data.py [option]
Options: stats, videos, tags, colors, moods, all
"""

import sys
import sqlite3
from tabulate import tabulate
import json

def get_connection():
    return sqlite3.connect('video_library.db')

def show_stats():
    """Show database statistics"""
    conn = get_connection()
    cursor = conn.cursor()
    
    print("\n" + "="*60)
    print("📊 DATABASE STATISTICS")
    print("="*60)
    
    # Video count
    cursor.execute('SELECT COUNT(*) FROM videos')
    video_count = cursor.fetchone()[0]
    print(f"\n📹 Total Videos: {video_count}")
    
    # Tag count
    cursor.execute('SELECT COUNT(DISTINCT tag_value) FROM tags')
    tag_count = cursor.fetchone()[0]
    print(f"🏷️  Unique Tags: {tag_count}")
    
    # Color count
    cursor.execute('SELECT COUNT(DISTINCT color_name) FROM colors')
    color_count = cursor.fetchone()[0]
    print(f"🎨 Unique Colors: {color_count}")
    
    # Mood count
    cursor.execute('SELECT COUNT(*) FROM moods')
    mood_count = cursor.fetchone()[0]
    print(f"😊 Total Moods: {mood_count}")
    
    # AI Analysis count
    cursor.execute('SELECT COUNT(*) FROM ai_analysis')
    ai_count = cursor.fetchone()[0]
    print(f"🤖 AI Analyses: {ai_count}")
    
    # Total duration
    cursor.execute('SELECT SUM(duration) FROM videos')
    total_duration = cursor.fetchone()[0] or 0
    print(f"⏱️  Total Duration: {total_duration:.1f} seconds ({total_duration/60:.1f} minutes)")
    
    conn.close()

def show_videos(limit=20):
    """Show all videos with details"""
    conn = get_connection()
    cursor = conn.cursor()
    
    print("\n" + "="*60)
    print(f"📹 VIDEOS (showing first {limit})")
    print("="*60 + "\n")
    
    cursor.execute('''
        SELECT id, file_path, duration, width, height, created_at
        FROM videos
        ORDER BY created_at DESC
        LIMIT ?
    ''', (limit,))
    
    videos = cursor.fetchall()
    headers = ['ID', 'File Path', 'Duration', 'Width', 'Height', 'Created']
    print(tabulate(videos, headers=headers, tablefmt='grid'))
    
    conn.close()

def show_tags(limit=50):
    """Show all tags"""
    conn = get_connection()
    cursor = conn.cursor()
    
    print("\n" + "="*60)
    print(f"🏷️  TAGS (showing first {limit})")
    print("="*60 + "\n")
    
    cursor.execute('''
        SELECT t.tag_value, t.tag_type, COUNT(*) as count
        FROM tags t
        GROUP BY t.tag_value, t.tag_type
        ORDER BY count DESC
        LIMIT ?
    ''', (limit,))
    
    tags = cursor.fetchall()
    headers = ['Tag', 'Type', 'Count']
    print(tabulate(tags, headers=headers, tablefmt='grid'))
    
    conn.close()

def show_colors():
    """Show all colors"""
    conn = get_connection()
    cursor = conn.cursor()
    
    print("\n" + "="*60)
    print("🎨 COLORS")
    print("="*60 + "\n")
    
    cursor.execute('''
        SELECT c.color_name, COUNT(*) as count, 
               GROUP_CONCAT(DISTINCT c.hex_code) as hex_codes
        FROM colors c
        GROUP BY c.color_name
        ORDER BY count DESC
    ''')
    
    colors = cursor.fetchall()
    headers = ['Color', 'Videos', 'Hex Codes']
    print(tabulate(colors, headers=headers, tablefmt='grid'))
    
    conn.close()

def show_moods():
    """Show all moods"""
    conn = get_connection()
    cursor = conn.cursor()
    
    print("\n" + "="*60)
    print("😊 MOODS")
    print("="*60 + "\n")
    
    cursor.execute('''
        SELECT m.mood_type, AVG(m.intensity) as avg_intensity, COUNT(*) as count
        FROM moods m
        GROUP BY m.mood_type
        ORDER BY count DESC
    ''')
    
    moods = cursor.fetchall()
    headers = ['Mood', 'Avg Intensity', 'Count']
    
    # Format intensity
    formatted = [(m[0], f"{m[1]:.1f}/10", m[2]) for m in moods]
    print(tabulate(formatted, headers=headers, tablefmt='grid'))
    
    conn.close()

def show_video_details(video_id):
    """Show detailed info for a specific video"""
    conn = get_connection()
    cursor = conn.cursor()
    
    print("\n" + "="*60)
    print(f"🎬 VIDEO DETAILS - ID: {video_id}")
    print("="*60 + "\n")
    
    # Basic info
    cursor.execute('SELECT * FROM videos WHERE id = ?', (video_id,))
    video = cursor.fetchone()
    
    if not video:
        print(f"❌ Video with ID {video_id} not found")
        conn.close()
        return
    
    print(f"📁 File: {video[2]}")
    print(f"📏 Resolution: {video[3]}x{video[4]}")
    print(f"⏱️  Duration: {video[5]:.1f}s")
    print(f"📅 Created: {video[6]}")
    
    # Tags
    print("\n🏷️  Tags:")
    cursor.execute('''
        SELECT tag_type, tag_value, confidence
        FROM tags
        WHERE video_id = ?
        ORDER BY tag_type, confidence DESC
    ''', (video_id,))
    tags = cursor.fetchall()
    
    if tags:
        print(tabulate(tags, headers=['Type', 'Value', 'Confidence'], tablefmt='simple'))
    else:
        print("  No tags")
    
    # Colors
    print("\n🎨 Colors:")
    cursor.execute('''
        SELECT color_name, hex_code, percentage
        FROM colors
        WHERE video_id = ?
        ORDER BY percentage DESC
    ''', (video_id,))
    colors = cursor.fetchall()
    
    if colors:
        print(tabulate(colors, headers=['Name', 'Hex', 'Percentage'], tablefmt='simple'))
    else:
        print("  No colors")
    
    # Moods
    print("\n😊 Moods:")
    cursor.execute('''
        SELECT mood_type, intensity
        FROM moods
        WHERE video_id = ?
        ORDER BY intensity DESC
    ''', (video_id,))
    moods = cursor.fetchall()
    
    if moods:
        formatted = [(m[0], f"{m[1]:.1f}/10") for m in moods]
        print(tabulate(formatted, headers=['Type', 'Intensity'], tablefmt='simple'))
    else:
        print("  No moods")
    
    # AI Analysis
    print("\n🤖 AI Analysis:")
    cursor.execute('''
        SELECT analysis_json
        FROM ai_analysis
        WHERE video_id = ?
    ''', (video_id,))
    ai_result = cursor.fetchone()
    
    if ai_result and ai_result[0]:
        try:
            analysis = json.loads(ai_result[0])
            print(json.dumps(analysis, indent=2))
        except:
            print(ai_result[0])
    else:
        print("  No AI analysis")
    
    conn.close()

def show_all():
    """Show everything"""
    show_stats()
    show_videos(10)
    show_tags(20)
    show_colors()
    show_moods()

def main():
    if len(sys.argv) < 2:
        print("Usage: python view_data.py [option]")
        print("\nOptions:")
        print("  stats         - Show database statistics")
        print("  videos [n]    - Show videos (default: 20)")
        print("  tags [n]      - Show tags (default: 50)")
        print("  colors        - Show color distribution")
        print("  moods         - Show mood distribution")
        print("  video <id>    - Show details for specific video")
        print("  all           - Show everything")
        print("\nExamples:")
        print("  python view_data.py stats")
        print("  python view_data.py videos 50")
        print("  python view_data.py video 1")
        return
    
    option = sys.argv[1].lower()
    
    try:
        if option == 'stats':
            show_stats()
        elif option == 'videos':
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
            show_videos(limit)
        elif option == 'tags':
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 50
            show_tags(limit)
        elif option == 'colors':
            show_colors()
        elif option == 'moods':
            show_moods()
        elif option == 'video':
            if len(sys.argv) < 3:
                print("❌ Please provide video ID: python view_data.py video <id>")
                return
            video_id = int(sys.argv[2])
            show_video_details(video_id)
        elif option == 'all':
            show_all()
        else:
            print(f"❌ Unknown option: {option}")
            print("Run 'python view_data.py' without arguments for help")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    main()
