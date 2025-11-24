"""
Motion Detection and Analysis Module

Analyzes video motion levels using OpenCV optical flow.
Classifies videos as: static, slow, moderate, fast, intense
"""

import cv2
import numpy as np
from typing import Tuple, Dict, List
import os


class MotionDetector:
    """Detect and analyze motion in videos."""
    
    # Motion level thresholds
    MOTION_LEVELS = {
        'static': (0, 0.5),
        'slow': (0.5, 2.0),
        'moderate': (2.0, 5.0),
        'fast': (5.0, 10.0),
        'intense': (10.0, float('inf'))
    }
    
    def __init__(self):
        pass
    
    def analyze_motion(self, video_path: str, sample_frames: int = 30) -> Dict:
        """
        Analyze motion in a video.
        
        Args:
            video_path: Path to video file
            sample_frames: Number of frames to analyze (spread across video)
        
        Returns:
            Dictionary with motion analysis:
            {
                'motion_level': 'slow|moderate|fast|intense',
                'motion_score': float,  # 0-100
                'optical_flow_magnitude': float,
                'motion_areas_percentage': float,
                'camera_motion': bool,
                'object_motion': bool
            }
        """
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            print(f"Error: Could not open video {video_path}")
            return None
        
        # Get video properties
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        if total_frames < 2:
            cap.release()
            return {
                'motion_level': 'static',
                'motion_score': 0.0,
                'optical_flow_magnitude': 0.0,
                'motion_areas_percentage': 0.0,
                'camera_motion': False,
                'object_motion': False
            }
        
        # Sample frames evenly across video
        frame_indices = np.linspace(0, total_frames - 2, min(sample_frames, total_frames - 1), dtype=int)
        
        motion_magnitudes = []
        motion_area_percentages = []
        
        prev_frame = None
        
        for idx in frame_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            
            if not ret:
                continue
            
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Resize for faster processing
            small_gray = cv2.resize(gray, (320, 240))
            
            if prev_frame is not None:
                # Calculate optical flow
                flow = cv2.calcOpticalFlowFarneback(
                    prev_frame, small_gray,
                    None,
                    pyr_scale=0.5,
                    levels=3,
                    winsize=15,
                    iterations=3,
                    poly_n=5,
                    poly_sigma=1.2,
                    flags=0
                )
                
                # Calculate magnitude and angle
                magnitude, angle = cv2.cartToPolar(flow[..., 0], flow[..., 1])
                
                # Average magnitude
                avg_magnitude = np.mean(magnitude)
                motion_magnitudes.append(avg_magnitude)
                
                # Calculate percentage of frame with significant motion
                motion_threshold = 0.5
                motion_mask = magnitude > motion_threshold
                motion_percentage = np.sum(motion_mask) / motion_mask.size * 100
                motion_area_percentages.append(motion_percentage)
            
            prev_frame = small_gray
        
        cap.release()
        
        if not motion_magnitudes:
            return {
                'motion_level': 'static',
                'motion_score': 0.0,
                'optical_flow_magnitude': 0.0,
                'motion_areas_percentage': 0.0,
                'camera_motion': False,
                'object_motion': False
            }
        
        # Calculate statistics
        avg_motion_magnitude = np.mean(motion_magnitudes)
        max_motion_magnitude = np.max(motion_magnitudes)
        avg_motion_area = np.mean(motion_area_percentages)
        
        # Determine motion level
        motion_level = self._classify_motion_level(avg_motion_magnitude)
        
        # Detect camera vs object motion
        # High motion area percentage = likely camera motion
        # Low motion area percentage with high magnitude = likely object motion
        camera_motion = avg_motion_area > 60
        object_motion = avg_motion_area < 40 and avg_motion_magnitude > 1.0
        
        # Motion score (0-100)
        motion_score = min(100, avg_motion_magnitude * 10)
        
        return {
            'motion_level': motion_level,
            'motion_score': round(motion_score, 2),
            'optical_flow_magnitude': round(avg_motion_magnitude, 3),
            'max_motion_magnitude': round(max_motion_magnitude, 3),
            'motion_areas_percentage': round(avg_motion_area, 2),
            'camera_motion': camera_motion,
            'object_motion': object_motion
        }
    
    def _classify_motion_level(self, magnitude: float) -> str:
        """Classify motion level based on optical flow magnitude."""
        for level, (min_val, max_val) in self.MOTION_LEVELS.items():
            if min_val <= magnitude < max_val:
                return level
        return 'intense'
    
    def analyze_batch(self, video_paths: List[str], sample_frames: int = 30) -> Dict[str, Dict]:
        """Analyze motion for multiple videos."""
        results = {}
        
        for video_path in video_paths:
            if not os.path.exists(video_path):
                print(f"Warning: Video not found: {video_path}")
                continue
            
            print(f"Analyzing motion: {os.path.basename(video_path)}")
            
            motion_data = self.analyze_motion(video_path, sample_frames)
            
            if motion_data:
                results[video_path] = motion_data
                print(f"  Motion level: {motion_data['motion_level']} "
                      f"(score: {motion_data['motion_score']})")
        
        return results
    
    def detect_scene_changes(self, video_path: str, threshold: float = 30.0) -> List[int]:
        """
        Detect scene changes in video.
        
        Args:
            video_path: Path to video
            threshold: Threshold for scene change detection (higher = fewer scenes)
        
        Returns:
            List of frame indices where scenes change
        """
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            return []
        
        scene_changes = [0]  # First frame is always a scene
        prev_frame = None
        frame_idx = 0
        
        while True:
            ret, frame = cap.read()
            
            if not ret:
                break
            
            # Resize and convert to grayscale
            small_frame = cv2.resize(frame, (320, 240))
            gray = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)
            
            if prev_frame is not None:
                # Calculate frame difference
                diff = cv2.absdiff(prev_frame, gray)
                mean_diff = np.mean(diff)
                
                # Scene change detected
                if mean_diff > threshold:
                    scene_changes.append(frame_idx)
            
            prev_frame = gray
            frame_idx += 1
        
        cap.release()
        
        return scene_changes
    
    def get_motion_heatmap(self, video_path: str, output_path: str = None) -> np.ndarray:
        """
        Generate a motion heatmap visualization.
        
        Args:
            video_path: Path to video
            output_path: Optional path to save heatmap image
        
        Returns:
            Motion heatmap as numpy array
        """
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            return None
        
        # Read first frame
        ret, first_frame = cap.read()
        if not ret:
            cap.release()
            return None
        
        # Initialize accumulator
        h, w = first_frame.shape[:2]
        motion_accumulator = np.zeros((h, w), dtype=np.float32)
        
        prev_gray = cv2.cvtColor(first_frame, cv2.COLOR_BGR2GRAY)
        frame_count = 0
        
        while True:
            ret, frame = cap.read()
            
            if not ret:
                break
            
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Calculate frame difference
            diff = cv2.absdiff(prev_gray, gray)
            
            # Accumulate motion
            motion_accumulator += diff.astype(np.float32)
            
            prev_gray = gray
            frame_count += 1
            
            # Limit analysis to save time
            if frame_count > 100:
                break
        
        cap.release()
        
        # Normalize
        if frame_count > 0:
            motion_accumulator /= frame_count
        
        # Create heatmap
        motion_normalized = cv2.normalize(motion_accumulator, None, 0, 255, cv2.NORM_MINMAX)
        heatmap = cv2.applyColorMap(motion_normalized.astype(np.uint8), cv2.COLORMAP_JET)
        
        # Overlay on first frame
        overlay = cv2.addWeighted(first_frame, 0.6, heatmap, 0.4, 0)
        
        if output_path:
            cv2.imwrite(output_path, overlay)
        
        return overlay


# Example usage
if __name__ == "__main__":
    detector = MotionDetector()
    
    # Analyze a single video
    video_path = "test_video.mp4"
    
    if os.path.exists(video_path):
        print("Analyzing motion...")
        result = detector.analyze_motion(video_path)
        
        print("\n📊 Motion Analysis Results:")
        print(f"  Motion Level: {result['motion_level']}")
        print(f"  Motion Score: {result['motion_score']}/100")
        print(f"  Optical Flow: {result['optical_flow_magnitude']}")
        print(f"  Motion Area: {result['motion_areas_percentage']}%")
        print(f"  Camera Motion: {result['camera_motion']}")
        print(f"  Object Motion: {result['object_motion']}")
        
        # Detect scene changes
        print("\n🎬 Detecting scene changes...")
        scenes = detector.detect_scene_changes(video_path)
        print(f"  Found {len(scenes)} scenes at frames: {scenes[:10]}...")
        
        # Generate heatmap
        print("\n🗺️ Generating motion heatmap...")
        heatmap = detector.get_motion_heatmap(video_path, "motion_heatmap.jpg")
        if heatmap is not None:
            print("  Saved to: motion_heatmap.jpg")
    else:
        print(f"Video not found: {video_path}")
