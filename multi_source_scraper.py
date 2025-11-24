"""
Multi-Source Video Scraper
Supports: Pexels, Pixabay, Videvo, Archive.org

Provides unified interface for scraping videos from multiple legal sources
with pre-download filtering capabilities.
"""

import requests
import os
import time
from typing import List, Dict, Optional
from tqdm import tqdm
import internetarchive as ia


class VideoSource:
    """Base class for video sources."""
    
    def search(self, query: str, max_results: int = 10, filters: Dict = None) -> List[Dict]:
        """Search for videos. Must be implemented by subclasses."""
        raise NotImplementedError
    
    def download(self, video_info: Dict, output_path: str) -> Optional[str]:
        """Download video. Must be implemented by subclasses."""
        raise NotImplementedError


class PexelsSource(VideoSource):
    """Pexels API video source (free stock videos)."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.pexels.com/videos"
        self.headers = {"Authorization": api_key}
    
    def search(self, query: str, max_results: int = 10, filters: Dict = None) -> List[Dict]:
        """
        Search Pexels for videos.
        
        Filters:
            - min_duration: Minimum duration in seconds
            - max_duration: Maximum duration in seconds
            - min_width: Minimum width in pixels
            - min_height: Minimum height in pixels
        """
        filters = filters or {}
        
        videos = []
        page = 1
        per_page = min(max_results, 80)
        
        try:
            while len(videos) < max_results:
                response = requests.get(
                    f"{self.base_url}/search",
                    headers=self.headers,
                    params={
                        "query": query,
                        "per_page": per_page,
                        "page": page
                    }
                )
                
                if response.status_code != 200:
                    print(f"Pexels API error: {response.status_code}")
                    break
                
                data = response.json()
                
                for video in data.get("videos", []):
                    if len(videos) >= max_results:
                        break
                    
                    # Apply filters
                    duration = video.get("duration", 0)
                    if filters.get("min_duration") and duration < filters["min_duration"]:
                        continue
                    if filters.get("max_duration") and duration > filters["max_duration"]:
                        continue
                    
                    # Get best quality file
                    video_files = video.get("video_files", [])
                    if not video_files:
                        continue
                    
                    # Sort by quality (prefer HD)
                    video_files.sort(key=lambda x: x.get("width", 0) * x.get("height", 0), reverse=True)
                    
                    best_file = video_files[0]
                    
                    # Apply resolution filters
                    width = best_file.get("width", 0)
                    height = best_file.get("height", 0)
                    
                    if filters.get("min_width") and width < filters["min_width"]:
                        continue
                    if filters.get("min_height") and height < filters["min_height"]:
                        continue
                    
                    videos.append({
                        "source": "pexels",
                        "id": video.get("id"),
                        "title": f"Pexels Video {video.get('id')}",
                        "description": query,
                        "url": video.get("url"),
                        "download_url": best_file.get("link"),
                        "duration": duration,
                        "width": width,
                        "height": height,
                        "file_type": best_file.get("file_type", "video/mp4"),
                        "license": "Pexels License (Free)",
                        "autoplay_compatible": True  # Pexels videos are web-optimized
                    })
                
                if not data.get("videos") or len(data["videos"]) == 0:
                    break
                
                page += 1
                time.sleep(0.5)  # Rate limiting
            
            return videos
            
        except Exception as e:
            print(f"Error searching Pexels: {e}")
            return []
    
    def download(self, video_info: Dict, output_path: str) -> Optional[str]:
        """Download video from Pexels."""
        try:
            response = requests.get(video_info["download_url"], stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            
            with open(output_path, 'wb') as f, tqdm(
                desc=f"Downloading {video_info['title'][:30]}",
                total=total_size,
                unit='iB',
                unit_scale=True
            ) as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    size = f.write(chunk)
                    pbar.update(size)
            
            return output_path
            
        except Exception as e:
            print(f"Error downloading from Pexels: {e}")
            return None


class PixabaySource(VideoSource):
    """Pixabay API video source (free stock videos)."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://pixabay.com/api/videos/"
    
    def search(self, query: str, max_results: int = 10, filters: Dict = None) -> List[Dict]:
        """Search Pixabay for videos."""
        filters = filters or {}
        
        videos = []
        page = 1
        per_page = min(max_results, 200)
        
        try:
            while len(videos) < max_results:
                response = requests.get(
                    self.base_url,
                    params={
                        "key": self.api_key,
                        "q": query,
                        "per_page": per_page,
                        "page": page,
                        "video_type": "all"
                    }
                )
                
                if response.status_code != 200:
                    print(f"Pixabay API error: {response.status_code}")
                    break
                
                data = response.json()
                
                for video in data.get("hits", []):
                    if len(videos) >= max_results:
                        break
                    
                    duration = video.get("duration", 0)
                    
                    # Apply filters
                    if filters.get("min_duration") and duration < filters["min_duration"]:
                        continue
                    if filters.get("max_duration") and duration > filters["max_duration"]:
                        continue
                    
                    # Get video files
                    video_files = video.get("videos", {})
                    
                    # Prefer HD quality
                    best_quality = None
                    for quality in ["large", "medium", "small", "tiny"]:
                        if quality in video_files:
                            best_quality = video_files[quality]
                            break
                    
                    if not best_quality:
                        continue
                    
                    width = best_quality.get("width", 0)
                    height = best_quality.get("height", 0)
                    
                    # Apply resolution filters
                    if filters.get("min_width") and width < filters["min_width"]:
                        continue
                    if filters.get("min_height") and height < filters["min_height"]:
                        continue
                    
                    videos.append({
                        "source": "pixabay",
                        "id": video.get("id"),
                        "title": f"Pixabay Video {video.get('id')}",
                        "description": video.get("tags", query),
                        "url": video.get("pageURL"),
                        "download_url": best_quality.get("url"),
                        "duration": duration,
                        "width": width,
                        "height": height,
                        "file_type": "video/mp4",
                        "license": "Pixabay License (Free)",
                        "autoplay_compatible": True
                    })
                
                if not data.get("hits") or len(data["hits"]) == 0:
                    break
                
                page += 1
                time.sleep(0.5)
            
            return videos
            
        except Exception as e:
            print(f"Error searching Pixabay: {e}")
            return []
    
    def download(self, video_info: Dict, output_path: str) -> Optional[str]:
        """Download video from Pixabay."""
        try:
            response = requests.get(video_info["download_url"], stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            
            with open(output_path, 'wb') as f, tqdm(
                desc=f"Downloading {video_info['title'][:30]}",
                total=total_size,
                unit='iB',
                unit_scale=True
            ) as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    size = f.write(chunk)
                    pbar.update(size)
            
            return output_path
            
        except Exception as e:
            print(f"Error downloading from Pixabay: {e}")
            return None


class VidevoSource(VideoSource):
    """Videvo scraper (free stock videos) - uses web scraping."""
    
    def search(self, query: str, max_results: int = 10, filters: Dict = None) -> List[Dict]:
        """
        Search Videvo (simplified - returns placeholder).
        Note: Videvo requires web scraping or their API access.
        """
        print("Note: Videvo integration requires additional setup")
        return []
    
    def download(self, video_info: Dict, output_path: str) -> Optional[str]:
        return None


class ArchiveOrgSource(VideoSource):
    """Archive.org video source (existing implementation)."""
    
    def __init__(self, download_dir: str = "downloads"):
        self.download_dir = download_dir
    
    def search(self, query: str, max_results: int = 10, filters: Dict = None) -> List[Dict]:
        """Search archive.org for videos."""
        filters = filters or {}
        
        search_query = f"mediatype:movies AND {query}"
        
        try:
            results = ia.search_items(search_query, fields=['identifier', 'title', 'description'])
            
            videos = []
            count = 0
            
            for result in results:
                if count >= max_results:
                    break
                
                identifier = result.get('identifier')
                
                # Get video files
                try:
                    item = ia.get_item(identifier)
                    video_files = []
                    
                    for file in item.files:
                        name = file.get('name', '').lower()
                        if any(name.endswith(ext) for ext in ['.mp4', '.avi', '.mov', '.mkv']):
                            video_files.append({
                                'name': file.get('name'),
                                'size': file.get('size', 0),
                                'url': f"https://archive.org/download/{identifier}/{file.get('name')}"
                            })
                    
                    if video_files:
                        # Sort by size
                        video_files.sort(key=lambda x: int(x['size']) if x['size'] else float('inf'))
                        best_file = video_files[0]
                        
                        videos.append({
                            'source': 'archive.org',
                            'identifier': identifier,
                            'title': result.get('title'),
                            'description': result.get('description', ''),
                            'url': f"https://archive.org/details/{identifier}",
                            'download_url': best_file['url'],
                            'file_name': best_file['name'],
                            'file_size': best_file['size'],
                            'license': 'Public Domain / Archive.org',
                            'autoplay_compatible': False  # Archive.org videos need inspection
                        })
                        count += 1
                
                except Exception as e:
                    print(f"Error processing {identifier}: {e}")
                    continue
            
            return videos
            
        except Exception as e:
            print(f"Error searching archive.org: {e}")
            return []
    
    def download(self, video_info: Dict, output_path: str) -> Optional[str]:
        """Download video from archive.org."""
        try:
            response = requests.get(video_info["download_url"], stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            
            with open(output_path, 'wb') as f, tqdm(
                desc=f"Downloading {video_info['title'][:30]}",
                total=total_size,
                unit='iB',
                unit_scale=True
            ) as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    size = f.write(chunk)
                    pbar.update(size)
            
            return output_path
            
        except Exception as e:
            print(f"Error downloading from archive.org: {e}")
            return None


class MultiSourceScraper:
    """Unified interface for scraping videos from multiple sources."""
    
    def __init__(self, config: Dict[str, str] = None, download_dir: str = "downloads"):
        """
        Initialize multi-source scraper.
        
        Args:
            config: Dictionary with API keys
                {
                    'pexels_api_key': 'xxx',
                    'pixabay_api_key': 'xxx'
                }
            download_dir: Directory for downloads
        """
        self.download_dir = download_dir
        os.makedirs(download_dir, exist_ok=True)
        
        config = config or {}
        
        # Initialize sources
        self.sources = {}
        
        if config.get('pexels_api_key'):
            self.sources['pexels'] = PexelsSource(config['pexels_api_key'])
        
        if config.get('pixabay_api_key'):
            self.sources['pixabay'] = PixabaySource(config['pixabay_api_key'])
        
        # Archive.org always available (no API key needed)
        self.sources['archive.org'] = ArchiveOrgSource(download_dir)
        
        print(f"Initialized with sources: {', '.join(self.sources.keys())}")
    
    def search_all_sources(self, query: str, max_per_source: int = 5, 
                          filters: Dict = None, sources: List[str] = None) -> List[Dict]:
        """
        Search multiple sources.
        
        Args:
            query: Search query
            max_per_source: Maximum results per source
            filters: Filtering criteria (duration, resolution, etc.)
            sources: List of source names to search (None = all)
        
        Returns:
            List of video results from all sources
        """
        all_videos = []
        
        sources_to_search = sources if sources else list(self.sources.keys())
        
        for source_name in sources_to_search:
            if source_name not in self.sources:
                print(f"Warning: Source '{source_name}' not available")
                continue
            
            print(f"\n🔍 Searching {source_name} for '{query}'...")
            
            try:
                videos = self.sources[source_name].search(query, max_per_source, filters)
                all_videos.extend(videos)
                print(f"  Found {len(videos)} videos")
            except Exception as e:
                print(f"  Error: {e}")
        
        return all_videos
    
    def download_video(self, video_info: Dict) -> Optional[str]:
        """Download a video from any source."""
        source_name = video_info.get('source')
        
        if source_name not in self.sources:
            print(f"Error: Unknown source '{source_name}'")
            return None
        
        # Generate filename
        safe_title = "".join(c for c in video_info.get('title', 'video')[:50] 
                            if c.isalnum() or c in (' ', '-', '_')).strip()
        filename = f"{source_name}_{video_info.get('id', 'unknown')}_{safe_title}.mp4"
        output_path = os.path.join(self.download_dir, filename)
        
        # Skip if already downloaded
        if os.path.exists(output_path):
            print(f"Already downloaded: {filename}")
            return output_path
        
        return self.sources[source_name].download(video_info, output_path)
    
    def batch_download(self, video_list: List[Dict]) -> List[str]:
        """Download multiple videos."""
        downloaded = []
        
        for video in tqdm(video_list, desc="Downloading videos"):
            path = self.download_video(video)
            if path:
                downloaded.append(path)
        
        return downloaded


# Example usage
if __name__ == "__main__":
    # Configure with API keys (optional)
    config = {
        'pexels_api_key': 'YOUR_PEXELS_API_KEY',  # Get from: https://www.pexels.com/api/
        'pixabay_api_key': 'YOUR_PIXABAY_API_KEY'  # Get from: https://pixabay.com/api/docs/
    }
    
    scraper = MultiSourceScraper(config)
    
    # Search with filters
    filters = {
        'min_duration': 5,      # At least 5 seconds
        'max_duration': 60,     # Maximum 60 seconds
        'min_width': 1280,      # At least 720p
        'min_height': 720
    }
    
    # Search all sources
    videos = scraper.search_all_sources(
        query="nature landscape",
        max_per_source=3,
        filters=filters
    )
    
    print(f"\n\n📊 Total videos found: {len(videos)}")
    
    # Download first 3
    if videos:
        print("\n📥 Downloading...")
        downloaded = scraper.batch_download(videos[:3])
        print(f"✅ Downloaded {len(downloaded)} videos")
