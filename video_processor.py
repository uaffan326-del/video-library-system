import cv2
import os
from typing import List, Tuple, Optional
import numpy as np


class VideoClipper:
    """Split videos into short clips suitable for lyric video backgrounds."""
    
    def __init__(self, output_dir: str = "processed_clips", 
                 clip_duration: Tuple[int, int] = (3, 10)):
        """
        Initialize video clipper.
        
        Args:
            output_dir: Directory to save clipped videos
            clip_duration: Tuple of (min_duration, max_duration) in seconds
                         Default (3, 10) for 3-10 second clips
        """
        self.output_dir = output_dir
        self.min_duration = clip_duration[0]
        self.max_duration = clip_duration[1]
        os.makedirs(output_dir, exist_ok=True)
    
    def get_video_info(self, video_path: str) -> dict:
        """Get video metadata."""
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            return None
        
        info = {
            'fps': cap.get(cv2.CAP_PROP_FPS),
            'frame_count': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            'duration': cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(cv2.CAP_PROP_FPS)
        }
        
        cap.release()
        return info
    
    def extract_frame(self, video_path: str, time_seconds: float) -> Optional[np.ndarray]:
        """Extract a single frame at specified time."""
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            return None
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_number = int(time_seconds * fps)
        
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = cap.read()
        
        cap.release()
        
        return frame if ret else None
    
    def extract_multiple_frames(self, video_path: str, num_frames: int = 3) -> List[np.ndarray]:
        """Extract multiple evenly-spaced frames from video."""
        info = self.get_video_info(video_path)
        if not info:
            return []
        
        frames = []
        duration = info['duration']
        
        # Extract frames at evenly spaced intervals
        for i in range(num_frames):
            time = (i + 1) * duration / (num_frames + 1)
            frame = self.extract_frame(video_path, time)
            if frame is not None:
                frames.append(frame)
        
        return frames
    
    def clip_video(self, input_path: str, output_path: str, 
                   start_time: float, duration: float) -> bool:
        """
        Create a clip from a video.
        
        Args:
            input_path: Source video path
            output_path: Output clip path
            start_time: Start time in seconds
            duration: Clip duration in seconds
        
        Returns:
            True if successful, False otherwise
        """
        try:
            cap = cv2.VideoCapture(input_path)
            
            if not cap.isOpened():
                print(f"Error: Could not open video {input_path}")
                return False
            
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # Set up video writer
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            
            # Calculate frame range
            start_frame = int(start_time * fps)
            end_frame = int((start_time + duration) * fps)
            
            # Set starting position
            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
            
            frame_count = 0
            while frame_count < (end_frame - start_frame):
                ret, frame = cap.read()
                if not ret:
                    break
                
                out.write(frame)
                frame_count += 1
            
            cap.release()
            out.release()
            
            return os.path.exists(output_path)
            
        except Exception as e:
            print(f"Error clipping video: {e}")
            return False
    
    def split_into_clips(self, video_path: str, clip_duration: Optional[float] = None) -> List[dict]:
        """
        Split a video into multiple clips.
        
        Args:
            video_path: Path to source video
            clip_duration: Duration of each clip (uses default if None)
        
        Returns:
            List of clip information dictionaries
        """
        if clip_duration is None:
            clip_duration = self.max_duration
        
        info = self.get_video_info(video_path)
        if not info:
            print(f"Could not get info for {video_path}")
            return []
        
        total_duration = info['duration']
        
        # Skip very short videos
        if total_duration < self.min_duration:
            print(f"Video too short ({total_duration:.1f}s): {video_path}")
            return []
        
        clips = []
        base_name = os.path.splitext(os.path.basename(video_path))[0]
        
        # Calculate number of clips
        num_clips = int(total_duration / clip_duration)
        
        # Limit to reasonable number of clips per video
        num_clips = min(num_clips, 10)
        
        if num_clips == 0:
            num_clips = 1
        
        print(f"Splitting {video_path} into {num_clips} clips...")
        
        for i in range(num_clips):
            start_time = i * clip_duration
            
            # Don't exceed video duration
            if start_time + clip_duration > total_duration:
                actual_duration = total_duration - start_time
                if actual_duration < self.min_duration:
                    break
            else:
                actual_duration = clip_duration
            
            output_filename = f"{base_name}_clip_{i+1:03d}.mp4"
            output_path = os.path.join(self.output_dir, output_filename)
            
            # Skip if already exists
            if os.path.exists(output_path):
                print(f"Clip already exists: {output_filename}")
                clips.append({
                    'path': output_path,
                    'start_time': start_time,
                    'duration': actual_duration,
                    'source_video': video_path
                })
                continue
            
            success = self.clip_video(video_path, output_path, start_time, actual_duration)
            
            if success:
                clips.append({
                    'path': output_path,
                    'start_time': start_time,
                    'duration': actual_duration,
                    'source_video': video_path,
                    'width': info['width'],
                    'height': info['height']
                })
                print(f"Created clip: {output_filename}")
            else:
                print(f"Failed to create clip {i+1}")
        
        return clips
    
    def process_batch(self, video_paths: List[str], clip_duration: Optional[float] = None) -> List[dict]:
        """
        Process multiple videos into clips.
        
        Args:
            video_paths: List of video file paths
            clip_duration: Duration for each clip
        
        Returns:
            List of all created clips
        """
        all_clips = []
        
        for video_path in video_paths:
            print(f"\n{'='*60}")
            print(f"Processing: {os.path.basename(video_path)}")
            print(f"{'='*60}\n")
            
            clips = self.split_into_clips(video_path, clip_duration)
            all_clips.extend(clips)
        
        print(f"\n{'='*60}")
        print(f"Total clips created: {len(all_clips)}")
        print(f"{'='*60}\n")
        
        return all_clips
