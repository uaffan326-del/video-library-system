"""
Auto-Categorization System

Automatically assigns categories to videos based on AI tags and metadata.
Creates hierarchical category structure for better organization.
"""

from typing import Dict, List, Optional
from database import VideoDatabase


class AutoCategorizer:
    """Automatically categorize videos based on tags and metadata."""
    
    # Hierarchical category structure
    CATEGORY_HIERARCHY = {
        'Nature': {
            'subcategories': ['Forest', 'Ocean', 'Mountains', 'Sky', 'Desert', 'Wildlife', 'Flowers', 'Weather'],
            'keywords': ['nature', 'natural', 'outdoor', 'landscape', 'scenic', 'wilderness']
        },
        'Urban': {
            'subcategories': ['City', 'Street', 'Architecture', 'Traffic', 'Night City', 'Downtown'],
            'keywords': ['city', 'urban', 'building', 'street', 'downtown', 'metropolitan', 'architecture']
        },
        'Abstract': {
            'subcategories': ['Geometric', 'Particles', 'Fluid', 'Patterns', 'Light Effects', 'Fractals'],
            'keywords': ['abstract', 'geometric', 'pattern', 'particle', 'fluid', 'fractal', 'light']
        },
        'Space': {
            'subcategories': ['Stars', 'Planets', 'Nebula', 'Galaxy', 'Astronaut', 'Satellites'],
            'keywords': ['space', 'star', 'planet', 'galaxy', 'cosmic', 'universe', 'nebula', 'celestial']
        },
        'Water': {
            'subcategories': ['Ocean', 'River', 'Lake', 'Rain', 'Waterfall', 'Underwater'],
            'keywords': ['water', 'ocean', 'sea', 'river', 'lake', 'rain', 'waves', 'underwater']
        },
        'Fire': {
            'subcategories': ['Flames', 'Sparks', 'Explosion', 'Candles', 'Campfire'],
            'keywords': ['fire', 'flame', 'burn', 'spark', 'explosion', 'heat', 'candle']
        },
        'Technology': {
            'subcategories': ['Digital', 'Code', 'Interface', 'Data', 'Glitch', 'Futuristic'],
            'keywords': ['tech', 'digital', 'computer', 'code', 'data', 'interface', 'screen', 'cyber']
        },
        'People': {
            'subcategories': ['Portraits', 'Groups', 'Activities', 'Silhouettes', 'Crowds'],
            'keywords': ['people', 'person', 'human', 'crowd', 'portrait', 'silhouette', 'group']
        },
        'Textures': {
            'subcategories': ['Wood', 'Metal', 'Fabric', 'Stone', 'Paper', 'Glass'],
            'keywords': ['texture', 'material', 'surface', 'wood', 'metal', 'fabric', 'stone']
        },
        'Motion': {
            'subcategories': ['Timelapse', 'Slow Motion', 'Spin', 'Zoom', 'Pan', 'Tracking'],
            'keywords': ['timelapse', 'slow motion', 'movement', 'motion', 'dynamic', 'action']
        }
    }
    
    def __init__(self, db_path: str = "video_library.db"):
        self.db = VideoDatabase(db_path)
        self._initialize_categories()
    
    def _initialize_categories(self):
        """Initialize category hierarchy in database."""
        for main_category, data in self.CATEGORY_HIERARCHY.items():
            # Add main category
            self.db.add_category(main_category, parent_category=None)
            
            # Add subcategories
            for subcategory in data['subcategories']:
                self.db.add_category(subcategory, parent_category=main_category)
    
    def categorize_video(self, video_id: int) -> str:
        """
        Automatically categorize a video based on its tags.
        
        Args:
            video_id: Video ID in database
        
        Returns:
            Assigned category name
        """
        # Get video tags
        video = self.db.get_video_details(video_id)
        
        if not video or not video.get('tags'):
            return 'Uncategorized'
        
        # Extract tag values
        tag_values = [tag['tag_value'].lower() for tag in video['tags']]
        tag_text = ' '.join(tag_values)
        
        # Score each category
        category_scores = {}
        
        for category, data in self.CATEGORY_HIERARCHY.items():
            score = 0
            
            # Check main category keywords
            for keyword in data['keywords']:
                if keyword in tag_text:
                    score += 2
            
            # Check subcategory matches
            for subcategory in data['subcategories']:
                if subcategory.lower() in tag_text:
                    score += 3
                    # Direct match to subcategory
                    category_scores[f"{category} > {subcategory}"] = score + 5
            
            if score > 0:
                category_scores[category] = score
        
        # Select best category
        if category_scores:
            best_category = max(category_scores, key=category_scores.get)
        else:
            best_category = 'Uncategorized'
        
        # Update database
        self.db.update_video_category(video_id, best_category)
        
        return best_category
    
    def categorize_batch(self, video_ids: List[int]) -> Dict[int, str]:
        """Categorize multiple videos at once."""
        results = {}
        
        for video_id in video_ids:
            category = self.categorize_video(video_id)
            results[video_id] = category
            print(f"Video {video_id}: {category}")
        
        return results
    
    def get_category_distribution(self) -> Dict[str, int]:
        """Get count of videos in each category."""
        import sqlite3
        
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT category, COUNT(*) as count
            FROM videos
            WHERE category IS NOT NULL
            GROUP BY category
            ORDER BY count DESC
        ''')
        
        distribution = {row[0]: row[1] for row in cursor.fetchall()}
        conn.close()
        
        return distribution
    
    def suggest_use_cases(self, video_id: int) -> List[Dict]:
        """
        Suggest use cases for a video based on its characteristics.
        
        Returns list of use cases with suitability scores.
        """
        video = self.db.get_video_details(video_id)
        
        if not video:
            return []
        
        use_cases = []
        
        # Get video characteristics
        category = video.get('category', '').lower()
        tags = [tag['tag_value'].lower() for tag in video.get('tags', [])]
        moods = [mood['mood_type'] for mood in video.get('moods', [])]
        motion_level = video.get('motion_level', '')
        energy = video.get('energy_level', 0)
        
        tag_text = ' '.join(tags)
        
        # Define use case rules
        use_case_rules = {
            'Wedding Videos': {
                'keywords': ['romantic', 'love', 'elegant', 'beautiful', 'flower', 'sunset'],
                'moods': ['positive'],
                'motion': ['slow', 'moderate'],
                'categories': ['Nature', 'Flowers', 'Sky']
            },
            'Party/Event Videos': {
                'keywords': ['energetic', 'vibrant', 'colorful', 'lights', 'crowd', 'celebration'],
                'moods': ['positive'],
                'motion': ['fast', 'intense'],
                'energy_min': 60
            },
            'Meditation/Relaxation': {
                'keywords': ['calm', 'peaceful', 'serene', 'nature', 'water', 'forest'],
                'moods': ['neutral'],
                'motion': ['static', 'slow'],
                'energy_max': 30
            },
            'Corporate/Business': {
                'keywords': ['professional', 'modern', 'clean', 'tech', 'office', 'city'],
                'moods': ['neutral', 'positive'],
                'motion': ['slow', 'moderate'],
                'categories': ['Urban', 'Technology']
            },
            'Music Videos (Upbeat)': {
                'keywords': ['energetic', 'dynamic', 'colorful', 'abstract', 'lights'],
                'moods': ['positive'],
                'motion': ['fast', 'intense'],
                'energy_min': 50
            },
            'Music Videos (Emotional)': {
                'keywords': ['dramatic', 'emotional', 'cinematic', 'moody'],
                'moods': ['negative', 'neutral'],
                'motion': ['slow', 'moderate']
            },
            'Sports/Action': {
                'keywords': ['fast', 'action', 'dynamic', 'intense', 'movement'],
                'motion': ['fast', 'intense'],
                'energy_min': 70
            },
            'Nature Documentaries': {
                'keywords': ['nature', 'wildlife', 'landscape', 'scenic', 'natural'],
                'categories': ['Nature', 'Water', 'Mountains', 'Forest'],
                'motion': ['slow', 'moderate']
            },
            'Travel/Tourism': {
                'keywords': ['landscape', 'scenic', 'beautiful', 'exotic', 'destination'],
                'categories': ['Nature', 'Urban', 'Ocean', 'Mountains'],
                'moods': ['positive']
            },
            'Tech/Startup Presentations': {
                'keywords': ['tech', 'digital', 'modern', 'innovative', 'futuristic'],
                'categories': ['Technology', 'Abstract'],
                'motion': ['moderate', 'fast']
            },
            'Horror/Thriller': {
                'keywords': ['dark', 'mysterious', 'eerie', 'fog', 'shadows'],
                'moods': ['negative'],
                'motion': ['slow', 'moderate']
            },
            'Children/Family Content': {
                'keywords': ['bright', 'colorful', 'cheerful', 'playful', 'fun'],
                'moods': ['positive'],
                'categories': ['Nature', 'Abstract']
            }
        }
        
        # Score each use case
        for use_case_name, rules in use_case_rules.items():
            score = 0
            max_score = 0
            
            # Check keywords
            if 'keywords' in rules:
                max_score += len(rules['keywords']) * 2
                for keyword in rules['keywords']:
                    if keyword in tag_text:
                        score += 2
            
            # Check moods
            if 'moods' in rules:
                max_score += 3
                if any(mood in rules['moods'] for mood in moods):
                    score += 3
            
            # Check motion
            if 'motion' in rules and motion_level:
                max_score += 2
                if motion_level in rules['motion']:
                    score += 2
            
            # Check category
            if 'categories' in rules and category:
                max_score += 3
                if any(cat.lower() in category for cat in rules['categories']):
                    score += 3
            
            # Check energy level
            if 'energy_min' in rules:
                max_score += 2
                if energy >= rules['energy_min']:
                    score += 2
            
            if 'energy_max' in rules:
                max_score += 2
                if energy <= rules['energy_max']:
                    score += 2
            
            # Calculate suitability percentage
            if max_score > 0:
                suitability = (score / max_score) * 100
                
                # Only include if reasonably suitable
                if suitability >= 30:
                    use_cases.append({
                        'use_case': use_case_name,
                        'suitability_score': round(suitability, 1),
                        'description': f"Suitable for {use_case_name.lower()}"
                    })
                    
                    # Store in database
                    self.db.add_use_case(video_id, use_case_name, suitability, 
                                        f"Auto-suggested based on tags and metadata")
        
        # Sort by suitability
        use_cases.sort(key=lambda x: x['suitability_score'], reverse=True)
        
        return use_cases


# Example usage
if __name__ == "__main__":
    categorizer = AutoCategorizer()
    
    # Categorize all uncategorized videos
    import sqlite3
    conn = sqlite3.connect("video_library.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM videos WHERE category IS NULL OR category = 'Uncategorized'")
    video_ids = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    if video_ids:
        print(f"Categorizing {len(video_ids)} videos...\n")
        results = categorizer.categorize_batch(video_ids)
        
        print("\n📊 Category Distribution:")
        distribution = categorizer.get_category_distribution()
        for category, count in distribution.items():
            print(f"  {category}: {count} videos")
    else:
        print("No videos to categorize")
