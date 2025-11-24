"""
Video Search and Query Module

Provides functions to search and retrieve videos from the database
based on various criteria (tags, mood, colors, etc.)
"""

from database import VideoDatabase
from typing import List, Dict, Optional
import random


class VideoSearcher:
    """Search and retrieve videos from the database."""
    
    def __init__(self, db_path: str = "video_library.db"):
        self.db = VideoDatabase(db_path)
    
    def search_by_keywords(self, keywords: List[str], limit: int = 10) -> List[Dict]:
        """Search videos by keywords."""
        return self.db.search_videos(tags=keywords, limit=limit)
    
    def search_by_mood(self, mood: str, limit: int = 10) -> List[Dict]:
        """
        Search videos by mood.
        
        Args:
            mood: 'positive', 'negative', or 'neutral'
            limit: Maximum number of results
        """
        return self.db.search_videos(mood=mood, limit=limit)
    
    def search_by_color(self, color: str, limit: int = 10) -> List[Dict]:
        """
        Search videos by dominant color.
        
        Args:
            color: Color name (red, blue, green, etc.) or hex code
            limit: Maximum number of results
        """
        return self.db.search_videos(color=color, limit=limit)
    
    def search_combined(self, keywords: List[str] = None, mood: str = None,
                       color: str = None, limit: int = 10) -> List[Dict]:
        """Search with multiple criteria."""
        return self.db.search_videos(tags=keywords, mood=mood, color=color, limit=limit)
    
    def get_random_videos(self, count: int = 10, filters: Dict = None) -> List[Dict]:
        """
        Get random videos, optionally with filters.
        
        Args:
            count: Number of videos to retrieve
            filters: Optional dict with 'mood', 'tags', 'color'
        """
        if filters:
            results = self.db.search_videos(
                tags=filters.get('tags'),
                mood=filters.get('mood'),
                color=filters.get('color'),
                limit=count * 3  # Get more than needed for random selection
            )
        else:
            # Get all videos (limited)
            import sqlite3
            conn = sqlite3.connect(self.db.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(f'SELECT * FROM videos ORDER BY RANDOM() LIMIT {count}')
            results = [dict(row) for row in cursor.fetchall()]
            conn.close()
        
        if len(results) > count:
            results = random.sample(results, count)
        
        return results
    
    def get_video_for_lyric(self, lyric_text: str, mood_hint: str = None) -> Optional[Dict]:
        """
        Get a suitable video for a specific lyric line.
        
        This is a simple implementation. For production, you'd want more
        sophisticated NLP to extract keywords from lyrics.
        
        Args:
            lyric_text: The lyric line
            mood_hint: Optional mood ('positive', 'negative', 'neutral')
        
        Returns:
            Video info dictionary or None
        """
        # Extract simple keywords (basic implementation)
        keywords = self._extract_keywords_from_lyric(lyric_text)
        
        # Search with keywords and mood
        results = self.search_combined(keywords=keywords, mood=mood_hint, limit=5)
        
        if results:
            return random.choice(results)
        
        # Fallback to mood only
        if mood_hint:
            results = self.search_by_mood(mood_hint, limit=5)
            if results:
                return random.choice(results)
        
        # Final fallback to random
        results = self.get_random_videos(count=1)
        return results[0] if results else None
    
    def _extract_keywords_from_lyric(self, lyric: str) -> List[str]:
        """
        Extract potential keywords from lyric text.
        
        This is a simple implementation. For better results, use NLP libraries
        like spaCy or NLTK to extract nouns, themes, etc.
        """
        # Common theme words that might appear in lyrics
        theme_keywords = {
            'nature': ['tree', 'forest', 'mountain', 'river', 'ocean', 'sea', 'sky', 'sun', 'moon', 'star'],
            'urban': ['city', 'street', 'building', 'car', 'traffic', 'lights'],
            'love': ['heart', 'love', 'kiss', 'embrace'],
            'dark': ['night', 'dark', 'shadow', 'black'],
            'light': ['light', 'bright', 'shine', 'glow'],
            'fire': ['fire', 'flame', 'burn'],
            'water': ['water', 'rain', 'ocean', 'wave', 'river'],
            'space': ['space', 'star', 'galaxy', 'universe', 'cosmos']
        }
        
        lyric_lower = lyric.lower()
        found_keywords = []
        
        for theme, words in theme_keywords.items():
            for word in words:
                if word in lyric_lower:
                    found_keywords.append(theme)
                    break
        
        return found_keywords[:3]  # Limit to 3 keywords
    
    def get_stats_summary(self) -> Dict:
        """Get detailed database statistics."""
        import sqlite3
        
        stats = self.db.get_stats()
        
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        # Most common tags
        cursor.execute('''
            SELECT tag_value, COUNT(*) as count 
            FROM tags 
            WHERE tag_type = 'theme'
            GROUP BY tag_value 
            ORDER BY count DESC 
            LIMIT 10
        ''')
        stats['top_themes'] = [{'theme': row[0], 'count': row[1]} for row in cursor.fetchall()]
        
        # Most common moods
        cursor.execute('''
            SELECT mood_type, COUNT(*) as count 
            FROM moods 
            GROUP BY mood_type 
            ORDER BY count DESC
        ''')
        stats['mood_distribution'] = [{'mood': row[0], 'count': row[1]} for row in cursor.fetchall()]
        
        # Most common colors
        cursor.execute('''
            SELECT color_name, COUNT(*) as count 
            FROM colors 
            GROUP BY color_name 
            ORDER BY count DESC 
            LIMIT 10
        ''')
        stats['top_colors'] = [{'color': row[0], 'count': row[1]} for row in cursor.fetchall()]
        
        conn.close()
        
        return stats


def demo_search():
    """Demo function showing how to use the search system."""
    searcher = VideoSearcher()
    
    print("="*60)
    print("VIDEO DATABASE SEARCH DEMO")
    print("="*60)
    
    # Show stats
    stats = searcher.get_stats_summary()
    print(f"\nTotal videos: {stats['total_videos']}")
    print(f"Unique tags: {stats['unique_tags']}")
    print(f"Unique colors: {stats['unique_colors']}")
    
    if stats.get('top_themes'):
        print("\nTop themes:")
        for theme in stats['top_themes'][:5]:
            print(f"  - {theme['theme']}: {theme['count']} videos")
    
    # Example searches
    print("\n" + "-"*60)
    print("Example: Search by keyword 'nature'")
    results = searcher.search_by_keywords(['nature'], limit=3)
    for video in results:
        print(f"  - {video['file_path']}")
    
    print("\n" + "-"*60)
    print("Example: Search by mood 'positive'")
    results = searcher.search_by_mood('positive', limit=3)
    for video in results:
        print(f"  - {video['file_path']}")
    
    print("\n" + "-"*60)
    print("Example: Get random videos")
    results = searcher.get_random_videos(count=3)
    for video in results:
        print(f"  - {video['file_path']}")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    demo_search()
