"""
Export Module

Export video library data in various formats for lyric video software integration.
Supports: JSON, CSV, XML
"""

import json
import csv
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional
from database import VideoDatabase
import os


class VideoLibraryExporter:
    """Export video library in multiple formats."""
    
    def __init__(self, db_path: str = "video_library.db"):
        self.db = VideoDatabase(db_path)
    
    def export_to_json(self, output_path: str, filters: Dict = None, 
                       include_full_details: bool = True) -> bool:
        """
        Export video library to JSON format.
        
        Args:
            output_path: Path to output JSON file
            filters: Optional filters (tags, mood, color, etc.)
            include_full_details: Include all metadata (tags, colors, moods)
        
        Returns:
            True if successful
        """
        try:
            # Get videos
            videos = self._get_filtered_videos(filters)
            
            # Build export data
            export_data = {
                'metadata': {
                    'total_videos': len(videos),
                    'export_format': 'json',
                    'version': '1.0'
                },
                'videos': []
            }
            
            for video in videos:
                video_data = self._prepare_video_data(video, include_full_details)
                export_data['videos'].append(video_data)
            
            # Write to file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Exported {len(videos)} videos to {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ Export error: {e}")
            return False
    
    def export_to_csv(self, output_path: str, filters: Dict = None) -> bool:
        """
        Export video library to CSV format.
        
        CSV columns: id, file_path, duration, category, motion_level, bpm, 
                    tempo_category, mood, theme, keywords, use_cases
        """
        try:
            videos = self._get_filtered_videos(filters)
            
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Header
                writer.writerow([
                    'id', 'file_path', 'source', 'duration', 'width', 'height',
                    'category', 'motion_level', 'motion_score', 'bpm', 'tempo_category',
                    'energy_level', 'autoplay_compatible', 'mood', 'theme', 'style',
                    'keywords', 'dominant_colors', 'use_cases', 'suitable_for'
                ])
                
                # Data rows
                for video in videos:
                    video_details = self.db.get_video_details(video['id'])
                    
                    # Extract tag data
                    tags = video_details.get('tags', [])
                    theme = self._get_tag_value(tags, 'theme')
                    style = self._get_tag_value(tags, 'style')
                    keywords = self._get_tag_values(tags, 'keyword')
                    
                    # Extract mood
                    moods = video_details.get('moods', [])
                    mood = moods[0]['mood_type'] if moods else ''
                    
                    # Extract colors
                    colors = video_details.get('colors', [])
                    color_names = [c['color_name'] for c in colors[:3]]
                    
                    # Get AI analysis for SUITABLE_FOR
                    suitable_for = self._get_suitable_for(video['id'])
                    
                    # Get use cases
                    use_cases = self._get_use_cases(video['id'])
                    
                    writer.writerow([
                        video['id'],
                        video.get('file_path', ''),
                        video.get('source', ''),
                        video.get('duration', 0),
                        video.get('width', 0),
                        video.get('height', 0),
                        video.get('category', ''),
                        video.get('motion_level', ''),
                        video.get('motion_score', 0),
                        video.get('bpm', 0),
                        video.get('tempo_category', ''),
                        video.get('energy_level', 0),
                        video.get('autoplay_compatible', False),
                        mood,
                        theme,
                        style,
                        ', '.join(keywords),
                        ', '.join(color_names),
                        ', '.join(use_cases),
                        suitable_for
                    ])
            
            print(f"✅ Exported {len(videos)} videos to {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ Export error: {e}")
            return False
    
    def export_to_xml(self, output_path: str, filters: Dict = None) -> bool:
        """Export video library to XML format."""
        try:
            videos = self._get_filtered_videos(filters)
            
            # Create XML structure
            root = ET.Element('video_library')
            root.set('total_videos', str(len(videos)))
            root.set('version', '1.0')
            
            for video in videos:
                video_data = self._prepare_video_data(video, include_full_details=True)
                video_elem = self._dict_to_xml(video_data, 'video')
                root.append(video_elem)
            
            # Write to file
            tree = ET.ElementTree(root)
            ET.indent(tree, space='  ')
            tree.write(output_path, encoding='utf-8', xml_declaration=True)
            
            print(f"✅ Exported {len(videos)} videos to {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ Export error: {e}")
            return False
    
    def export_for_lyric_software(self, output_path: str, 
                                  lyric_text: str = None,
                                  bpm_range: tuple = None) -> bool:
        """
        Export simplified format specifically for lyric video software.
        
        Includes only essential fields for automation.
        """
        try:
            filters = {}
            
            # Apply BPM filter if provided
            if bpm_range:
                # This would need custom query - simplified for now
                pass
            
            videos = self._get_filtered_videos(filters)
            
            export_data = []
            
            for video in videos:
                video_details = self.db.get_video_details(video['id'])
                
                # Simplified format
                simple_data = {
                    'video_id': video['id'],
                    'file_path': video.get('file_path', ''),
                    'duration': video.get('duration', 0),
                    'bpm': video.get('bpm', 0),
                    'tempo': video.get('tempo_category', ''),
                    'motion_level': video.get('motion_level', ''),
                    'energy': video.get('energy_level', 0),
                    'mood': self._get_primary_mood(video_details),
                    'theme': self._get_tag_value(video_details.get('tags', []), 'theme'),
                    'keywords': self._get_tag_values(video_details.get('tags', []), 'keyword'),
                    'colors': [c['color_name'] for c in video_details.get('colors', [])[:3]],
                    'recommended_uses': self._get_use_cases(video['id'])
                }
                
                export_data.append(simple_data)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2)
            
            print(f"✅ Exported {len(export_data)} videos for lyric software")
            return True
            
        except Exception as e:
            print(f"❌ Export error: {e}")
            return False
    
    def _get_filtered_videos(self, filters: Dict = None) -> List[Dict]:
        """Get videos with optional filters."""
        import sqlite3
        
        conn = sqlite3.connect(self.db.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if not filters:
            cursor.execute('SELECT * FROM videos')
        else:
            # Build query with filters
            query = 'SELECT * FROM videos WHERE 1=1'
            params = []
            
            if 'category' in filters:
                query += ' AND category = ?'
                params.append(filters['category'])
            
            if 'motion_level' in filters:
                query += ' AND motion_level = ?'
                params.append(filters['motion_level'])
            
            if 'min_bpm' in filters:
                query += ' AND bpm >= ?'
                params.append(filters['min_bpm'])
            
            if 'max_bpm' in filters:
                query += ' AND bpm <= ?'
                params.append(filters['max_bpm'])
            
            cursor.execute(query, params)
        
        videos = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return videos
    
    def _prepare_video_data(self, video: Dict, include_full_details: bool) -> Dict:
        """Prepare video data for export."""
        data = {
            'id': video['id'],
            'file_path': video.get('file_path'),
            'source': video.get('source'),
            'duration': video.get('duration'),
            'resolution': {
                'width': video.get('width'),
                'height': video.get('height')
            },
            'category': video.get('category'),
            'motion': {
                'level': video.get('motion_level'),
                'score': video.get('motion_score')
            },
            'audio': {
                'bpm': video.get('bpm'),
                'tempo_category': video.get('tempo_category'),
                'energy_level': video.get('energy_level')
            },
            'web_compatibility': {
                'autoplay_compatible': video.get('autoplay_compatible'),
                'is_optimized': video.get('is_web_optimized'),
                'video_codec': video.get('video_codec'),
                'audio_codec': video.get('audio_codec')
            }
        }
        
        if include_full_details:
            details = self.db.get_video_details(video['id'])
            data['tags'] = details.get('tags', [])
            data['colors'] = details.get('colors', [])
            data['moods'] = details.get('moods', [])
            data['use_cases'] = self._get_use_cases(video['id'])
        
        return data
    
    def _get_tag_value(self, tags: List[Dict], tag_type: str) -> str:
        """Get first tag value of specified type."""
        for tag in tags:
            if tag.get('tag_type') == tag_type:
                return tag.get('tag_value', '')
        return ''
    
    def _get_tag_values(self, tags: List[Dict], tag_type: str) -> List[str]:
        """Get all tag values of specified type."""
        return [tag['tag_value'] for tag in tags if tag.get('tag_type') == tag_type]
    
    def _get_primary_mood(self, video_details: Dict) -> str:
        """Get primary mood from video details."""
        moods = video_details.get('moods', [])
        if moods:
            # Sort by intensity and return highest
            moods.sort(key=lambda x: x.get('intensity', 0), reverse=True)
            return moods[0]['mood_type']
        return ''
    
    def _get_use_cases(self, video_id: int) -> List[str]:
        """Get use cases for a video."""
        import sqlite3
        
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT use_case FROM use_cases 
            WHERE video_id = ? 
            ORDER BY suitability_score DESC
        ''', (video_id,))
        
        use_cases = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        return use_cases
    
    def _get_suitable_for(self, video_id: int) -> str:
        """Get SUITABLE_FOR from AI analysis."""
        import sqlite3
        
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT result_json FROM ai_analysis 
            WHERE video_id = ? AND analysis_type = 'gpt4_vision'
        ''', (video_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0]:
            try:
                analysis = json.loads(result[0])
                return analysis.get('suitable_for', '')
            except:
                pass
        
        return ''
    
    def _dict_to_xml(self, data: Dict, root_name: str) -> ET.Element:
        """Convert dictionary to XML element."""
        root = ET.Element(root_name)
        
        for key, value in data.items():
            if isinstance(value, dict):
                child = self._dict_to_xml(value, key)
                root.append(child)
            elif isinstance(value, list):
                list_elem = ET.SubElement(root, key)
                for item in value:
                    if isinstance(item, dict):
                        item_elem = self._dict_to_xml(item, 'item')
                        list_elem.append(item_elem)
                    else:
                        item_elem = ET.SubElement(list_elem, 'item')
                        item_elem.text = str(item)
            else:
                child = ET.SubElement(root, key)
                child.text = str(value) if value is not None else ''
        
        return root


# Example usage
if __name__ == "__main__":
    exporter = VideoLibraryExporter()
    
    print("📦 Video Library Exporter\n")
    
    # Export to JSON
    print("1. Exporting to JSON...")
    exporter.export_to_json('video_library_export.json')
    
    # Export to CSV
    print("\n2. Exporting to CSV...")
    exporter.export_to_csv('video_library_export.csv')
    
    # Export to XML
    print("\n3. Exporting to XML...")
    exporter.export_to_xml('video_library_export.xml')
    
    # Export for lyric software
    print("\n4. Exporting for lyric video software...")
    exporter.export_for_lyric_software('lyric_video_library.json')
    
    print("\n✅ All exports complete!")
