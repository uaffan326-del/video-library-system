import internetarchive as ia
import requests
import os
from typing import List, Dict, Optional
from tqdm import tqdm
import time


class ArchiveOrgScraper:
    """Scraper for archive.org video content."""
    
    def __init__(self, download_dir: str = "downloads"):
        self.download_dir = download_dir
        os.makedirs(download_dir, exist_ok=True)
    
    def search_videos(self, query: str, max_results: int = 100, 
                     media_type: str = "movies") -> List[Dict]:
        """
        Search archive.org for videos.
        
        Args:
            query: Search query (e.g., "nature abstract", "city timelapse")
            max_results: Maximum number of results to return
            media_type: Type of media ("movies", "video")
        
        Returns:
            List of video metadata dictionaries
        """
        print(f"Searching archive.org for: {query}")
        
        search_query = f"mediatype:{media_type} AND {query}"
        
        try:
            results = ia.search_items(search_query, fields=['identifier', 'title', 'description'])
            
            video_items = []
            count = 0
            
            for result in results:
                if count >= max_results:
                    break
                
                video_items.append({
                    'identifier': result.get('identifier'),
                    'title': result.get('title'),
                    'description': result.get('description', ''),
                    'url': f"https://archive.org/details/{result.get('identifier')}"
                })
                count += 1
            
            print(f"Found {len(video_items)} videos")
            return video_items
            
        except Exception as e:
            print(f"Error searching archive.org: {e}")
            return []
    
    def get_video_files(self, identifier: str) -> List[Dict]:
        """
        Get available video files for an item.
        
        Args:
            identifier: Archive.org identifier
        
        Returns:
            List of video file information
        """
        try:
            item = ia.get_item(identifier)
            video_files = []
            
            # Look for video files
            video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.ogv']
            
            for file in item.files:
                name = file.get('name', '').lower()
                if any(name.endswith(ext) for ext in video_extensions):
                    # Prefer smaller formats for efficiency
                    format_name = file.get('format', '').lower()
                    
                    video_files.append({
                        'name': file.get('name'),
                        'format': format_name,
                        'size': file.get('size', 0),
                        'url': f"https://archive.org/download/{identifier}/{file.get('name')}"
                    })
            
            # Sort by size (prefer smaller files)
            video_files.sort(key=lambda x: int(x['size']) if x['size'] else float('inf'))
            
            return video_files
            
        except Exception as e:
            print(f"Error getting files for {identifier}: {e}")
            return []
    
    def download_video(self, identifier: str, video_file: Dict, 
                       output_filename: Optional[str] = None) -> Optional[str]:
        """
        Download a video file from archive.org.
        
        Args:
            identifier: Archive.org identifier
            video_file: Video file dictionary from get_video_files
            output_filename: Optional custom filename
        
        Returns:
            Path to downloaded file or None if failed
        """
        try:
            url = video_file['url']
            filename = output_filename or video_file['name']
            filepath = os.path.join(self.download_dir, filename)
            
            # Skip if already downloaded
            if os.path.exists(filepath):
                print(f"Already downloaded: {filename}")
                return filepath
            
            print(f"Downloading: {filename}")
            
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            
            with open(filepath, 'wb') as f:
                with tqdm(total=total_size, unit='B', unit_scale=True) as pbar:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            pbar.update(len(chunk))
            
            print(f"Downloaded successfully: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"Error downloading video: {e}")
            if os.path.exists(filepath):
                os.remove(filepath)
            return None
    
    def download_best_video(self, identifier: str, title: str) -> Optional[Dict]:
        """
        Download the best available video for an item.
        
        Args:
            identifier: Archive.org identifier
            title: Video title (for naming)
        
        Returns:
            Dictionary with video info and filepath
        """
        video_files = self.get_video_files(identifier)
        
        if not video_files:
            print(f"No video files found for {identifier}")
            return None
        
        # Try to download the first suitable file (already sorted by size)
        for video_file in video_files:
            # Skip very large files (>500MB)
            file_size_mb = int(video_file.get('size', 0)) / (1024 * 1024)
            if file_size_mb > 500:
                continue
            
            # Generate clean filename
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_title = safe_title[:50]  # Limit length
            ext = os.path.splitext(video_file['name'])[1]
            output_filename = f"{identifier}_{safe_title}{ext}"
            
            filepath = self.download_video(identifier, video_file, output_filename)
            
            if filepath:
                return {
                    'identifier': identifier,
                    'title': title,
                    'filepath': filepath,
                    'original_url': f"https://archive.org/details/{identifier}",
                    'file_size': video_file.get('size')
                }
        
        return None
    
    def batch_download(self, search_queries: List[str], videos_per_query: int = 10) -> List[Dict]:
        """
        Download videos for multiple search queries.
        
        Args:
            search_queries: List of search terms
            videos_per_query: How many videos to download per query
        
        Returns:
            List of downloaded video information
        """
        downloaded_videos = []
        
        for query in search_queries:
            print(f"\n{'='*60}")
            print(f"Processing query: {query}")
            print(f"{'='*60}\n")
            
            items = self.search_videos(query, max_results=videos_per_query * 2)
            
            downloaded_count = 0
            for item in items:
                if downloaded_count >= videos_per_query:
                    break
                
                video_info = self.download_best_video(
                    item['identifier'], 
                    item.get('title', item['identifier'])
                )
                
                if video_info:
                    video_info['search_query'] = query
                    video_info['description'] = item.get('description', '')
                    downloaded_videos.append(video_info)
                    downloaded_count += 1
                
                # Be nice to archive.org servers
                time.sleep(1)
            
            print(f"\nDownloaded {downloaded_count} videos for query: {query}")
        
        return downloaded_videos


# Predefined search queries based on the use case
DEFAULT_SEARCH_QUERIES = [
    "abstract motion background",
    "nature landscape scenic",
    "city urban timelapse",
    "ocean water waves",
    "sky clouds sunset",
    "particles animation",
    "geometric patterns",
    "fire flames",
    "rain weather",
    "forest trees",
    "space stars galaxy",
    "light bokeh",
    "smoke fog",
    "mountains landscape",
    "flowers garden",
]
