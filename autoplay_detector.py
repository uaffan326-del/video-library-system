"""
Autoplay Detection Module

Detects if videos are compatible with HTML5 autoplay.
Checks video codecs, container formats, and optimization for web playback.
"""

import cv2
import subprocess
import json
import os
from typing import Dict, Optional


class AutoplayDetector:
    """Detect autoplay compatibility for videos."""
    
    # Web-compatible codecs
    WEB_COMPATIBLE_VIDEO_CODECS = ['h264', 'vp8', 'vp9', 'av1']
    WEB_COMPATIBLE_AUDIO_CODECS = ['aac', 'mp3', 'vorbis', 'opus']
    WEB_COMPATIBLE_CONTAINERS = ['.mp4', '.webm', '.ogv']
    
    def __init__(self):
        self.has_ffprobe = self._check_ffprobe()
    
    def _check_ffprobe(self) -> bool:
        """Check if ffprobe is available."""
        try:
            subprocess.run(['ffprobe', '-version'], 
                          capture_output=True, 
                          check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("Warning: ffprobe not found. Install ffmpeg for detailed codec analysis.")
            return False
    
    def analyze_video(self, video_path: str) -> Dict:
        """
        Analyze video for autoplay compatibility.
        
        Returns:
            {
                'autoplay_compatible': bool,
                'container_format': str,
                'video_codec': str,
                'audio_codec': str,
                'is_web_optimized': bool,
                'moov_atom_position': str,  # 'start' or 'end'
                'file_size_mb': float,
                'duration': float,
                'resolution': tuple,
                'compatibility_issues': list
            }
        """
        if not os.path.exists(video_path):
            return {'autoplay_compatible': False, 'error': 'File not found'}
        
        result = {
            'autoplay_compatible': False,
            'container_format': None,
            'video_codec': None,
            'audio_codec': None,
            'is_web_optimized': False,
            'moov_atom_position': 'unknown',
            'file_size_mb': 0.0,
            'duration': 0.0,
            'resolution': (0, 0),
            'compatibility_issues': []
        }
        
        # Get file info
        file_size = os.path.getsize(video_path) / (1024 * 1024)
        result['file_size_mb'] = round(file_size, 2)
        
        # Get container format
        _, ext = os.path.splitext(video_path)
        result['container_format'] = ext.lower()
        
        # Check container compatibility
        if ext.lower() not in self.WEB_COMPATIBLE_CONTAINERS:
            result['compatibility_issues'].append(f"Container format '{ext}' may not be web-compatible")
        
        # Use OpenCV for basic info
        cap = cv2.VideoCapture(video_path)
        if cap.isOpened():
            result['resolution'] = (
                int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            )
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            if fps > 0:
                result['duration'] = frame_count / fps
            cap.release()
        
        # Use ffprobe for detailed codec information
        if self.has_ffprobe:
            codec_info = self._get_codec_info_ffprobe(video_path)
            if codec_info:
                result.update(codec_info)
        else:
            # Fallback: basic checks
            result.update(self._basic_compatibility_check(video_path))
        
        # Check file size (large files may have buffering issues)
        if file_size > 50:
            result['compatibility_issues'].append(f"Large file size ({file_size:.1f}MB) may cause buffering")
        
        # Determine overall compatibility
        result['autoplay_compatible'] = self._determine_compatibility(result)
        
        return result
    
    def _get_codec_info_ffprobe(self, video_path: str) -> Optional[Dict]:
        """Get detailed codec information using ffprobe."""
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)
            
            info = {}
            
            # Parse streams
            video_codec = None
            audio_codec = None
            
            for stream in data.get('streams', []):
                if stream.get('codec_type') == 'video' and not video_codec:
                    video_codec = stream.get('codec_name', 'unknown').lower()
                elif stream.get('codec_type') == 'audio' and not audio_codec:
                    audio_codec = stream.get('codec_name', 'unknown').lower()
            
            info['video_codec'] = video_codec
            info['audio_codec'] = audio_codec
            
            # Check codec compatibility
            if video_codec and video_codec not in self.WEB_COMPATIBLE_VIDEO_CODECS:
                info['compatibility_issues'] = [f"Video codec '{video_codec}' may not be web-compatible"]
            else:
                info['compatibility_issues'] = []
            
            if audio_codec and audio_codec not in self.WEB_COMPATIBLE_AUDIO_CODECS:
                info['compatibility_issues'].append(f"Audio codec '{audio_codec}' may not be web-compatible")
            
            # Check for web optimization (moov atom at start for MP4)
            format_name = data.get('format', {}).get('format_name', '')
            if 'mp4' in format_name:
                # Check if moov atom is at the start (fast start enabled)
                info['is_web_optimized'] = self._check_mp4_faststart(video_path)
                info['moov_atom_position'] = 'start' if info['is_web_optimized'] else 'end'
            
            return info
            
        except Exception as e:
            print(f"Error getting codec info: {e}")
            return None
    
    def _check_mp4_faststart(self, video_path: str) -> bool:
        """Check if MP4 has moov atom at start (web optimized)."""
        try:
            with open(video_path, 'rb') as f:
                # Read first 8 bytes
                header = f.read(8)
                if len(header) < 8:
                    return False
                
                # Check for 'ftyp' (file type box) at start
                if b'ftyp' in header:
                    # Skip ftyp box and check next
                    f.seek(0)
                    while True:
                        atom_header = f.read(8)
                        if len(atom_header) < 8:
                            break
                        
                        atom_size = int.from_bytes(atom_header[:4], 'big')
                        atom_type = atom_header[4:8]
                        
                        # Found moov at beginning (after ftyp) = optimized
                        if atom_type == b'moov':
                            return True
                        
                        # Found mdat before moov = not optimized
                        if atom_type == b'mdat':
                            return False
                        
                        # Skip to next atom
                        if atom_size <= 8:
                            break
                        f.seek(f.tell() + atom_size - 8)
                        
                        # Don't search too far
                        if f.tell() > 1024 * 1024:  # 1MB
                            break
            
            return False
            
        except Exception as e:
            print(f"Error checking MP4 fast start: {e}")
            return False
    
    def _basic_compatibility_check(self, video_path: str) -> Dict:
        """Basic compatibility check without ffprobe."""
        info = {
            'video_codec': 'unknown',
            'audio_codec': 'unknown',
            'is_web_optimized': False,
            'compatibility_issues': []
        }
        
        # Assume MP4 with h264 is compatible (most common)
        _, ext = os.path.splitext(video_path)
        if ext.lower() == '.mp4':
            info['video_codec'] = 'h264 (assumed)'
            info['audio_codec'] = 'aac (assumed)'
        elif ext.lower() == '.webm':
            info['video_codec'] = 'vp8 (assumed)'
            info['audio_codec'] = 'vorbis (assumed)'
        else:
            info['compatibility_issues'].append('Unknown codec - install ffmpeg for detection')
        
        return info
    
    def _determine_compatibility(self, result: Dict) -> bool:
        """Determine overall autoplay compatibility."""
        # Critical issues
        if result.get('error'):
            return False
        
        # Container must be web-compatible
        if result['container_format'] not in self.WEB_COMPATIBLE_CONTAINERS:
            return False
        
        # Check for critical compatibility issues
        critical_issues = ['may not be web-compatible', 'Unknown codec']
        for issue in result['compatibility_issues']:
            if any(critical in issue for critical in critical_issues):
                # Still might work if it's MP4
                if result['container_format'] == '.mp4':
                    continue
                return False
        
        # If we got here, it's probably compatible
        return True
    
    def optimize_for_web(self, input_path: str, output_path: str) -> bool:
        """
        Optimize video for web playback using ffmpeg.
        - Converts to H.264 + AAC in MP4
        - Enables fast start (moov atom at beginning)
        
        Requires ffmpeg to be installed.
        """
        if not self.has_ffprobe:
            print("Error: ffmpeg not installed")
            return False
        
        try:
            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-c:v', 'libx264',          # H.264 video codec
                '-preset', 'medium',         # Encoding speed/quality
                '-crf', '23',                # Quality (lower = better)
                '-c:a', 'aac',               # AAC audio codec
                '-b:a', '128k',              # Audio bitrate
                '-movflags', '+faststart',   # Enable fast start
                '-y',                        # Overwrite output
                output_path
            ]
            
            print(f"Optimizing video for web playback...")
            subprocess.run(cmd, check=True, capture_output=True)
            print(f"✅ Optimized: {output_path}")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"Error optimizing video: {e}")
            return False


# Example usage
if __name__ == "__main__":
    detector = AutoplayDetector()
    
    video_path = "test_video.mp4"
    
    if os.path.exists(video_path):
        print("Analyzing video for autoplay compatibility...\n")
        
        result = detector.analyze_video(video_path)
        
        print("📊 Autoplay Compatibility Analysis:")
        print(f"  ✓ Compatible: {result['autoplay_compatible']}")
        print(f"  Container: {result['container_format']}")
        print(f"  Video Codec: {result['video_codec']}")
        print(f"  Audio Codec: {result['audio_codec']}")
        print(f"  Web Optimized: {result['is_web_optimized']}")
        print(f"  File Size: {result['file_size_mb']} MB")
        print(f"  Duration: {result['duration']:.1f}s")
        print(f"  Resolution: {result['resolution'][0]}x{result['resolution'][1]}")
        
        if result['compatibility_issues']:
            print(f"\n⚠️ Issues:")
            for issue in result['compatibility_issues']:
                print(f"    - {issue}")
        
        # Optimize if needed
        if not result['is_web_optimized'] and result['container_format'] == '.mp4':
            print("\n🔧 Video can be optimized for web playback")
            # optimize = detector.optimize_for_web(video_path, "optimized_" + video_path)
    else:
        print(f"Video not found: {video_path}")
