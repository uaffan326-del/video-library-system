"""
Audio Tempo Detection Module

Analyzes audio to detect BPM (beats per minute) for tempo-based video matching.
Uses librosa for audio analysis.
"""

import librosa
import numpy as np
import os
from typing import Dict, Optional, Tuple


class TempoDetector:
    """Detect tempo/BPM in video audio tracks."""
    
    # Tempo categories
    TEMPO_CATEGORIES = {
        'very_slow': (0, 60),
        'slow': (60, 90),
        'moderate': (90, 120),
        'fast': (120, 150),
        'very_fast': (150, 200),
        'extremely_fast': (200, 300)
    }
    
    def __init__(self):
        pass
    
    def analyze_tempo(self, video_or_audio_path: str) -> Dict:
        """
        Analyze tempo/BPM of video or audio file.
        
        Args:
            video_or_audio_path: Path to video or audio file
        
        Returns:
            {
                'bpm': float,
                'tempo_category': str,
                'tempo_confidence': float,
                'beat_times': list,  # Timestamps of detected beats
                'has_rhythm': bool,
                'energy_level': float,  # 0-100
                'spectral_centroid': float,
                'tempo_stability': float  # How stable the tempo is
            }
        """
        try:
            print(f"Analyzing tempo: {os.path.basename(video_or_audio_path)}")
            
            # Load audio
            y, sr = librosa.load(video_or_audio_path, sr=22050, duration=60)  # Analyze first 60 seconds
            
            if len(y) == 0:
                return self._empty_result()
            
            # Detect tempo
            tempo, beats = librosa.beat.beat_track(y=y, sr=sr, units='time')
            
            # Convert to float if it's an array
            if isinstance(tempo, np.ndarray):
                bpm = float(tempo[0]) if len(tempo) > 0 else 0.0
            else:
                bpm = float(tempo)
            
            # Get tempo category
            tempo_category = self._categorize_tempo(bpm)
            
            # Calculate tempo confidence and stability
            if len(beats) > 1:
                # Calculate beat intervals
                beat_intervals = np.diff(beats)
                tempo_stability = 1.0 - (np.std(beat_intervals) / np.mean(beat_intervals) if np.mean(beat_intervals) > 0 else 1.0)
                tempo_stability = max(0.0, min(1.0, tempo_stability))
                
                # More beats = higher confidence
                tempo_confidence = min(1.0, len(beats) / 100.0)
            else:
                tempo_stability = 0.0
                tempo_confidence = 0.0
            
            # Check if there's a rhythm
            has_rhythm = len(beats) > 4 and tempo_stability > 0.3
            
            # Calculate energy level (RMS energy)
            rms = librosa.feature.rms(y=y)[0]
            energy_level = float(np.mean(rms) * 100)
            energy_level = min(100.0, energy_level)
            
            # Calculate spectral centroid (brightness)
            spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            avg_spectral_centroid = float(np.mean(spectral_centroid))
            
            return {
                'bpm': round(bpm, 2),
                'tempo_category': tempo_category,
                'tempo_confidence': round(tempo_confidence, 3),
                'beat_times': beats.tolist()[:100],  # Limit to first 100 beats
                'num_beats': len(beats),
                'has_rhythm': has_rhythm,
                'energy_level': round(energy_level, 2),
                'spectral_centroid': round(avg_spectral_centroid, 2),
                'tempo_stability': round(tempo_stability, 3)
            }
            
        except Exception as e:
            print(f"Error analyzing tempo: {e}")
            return self._empty_result()
    
    def _empty_result(self) -> Dict:
        """Return empty result for videos without audio or errors."""
        return {
            'bpm': 0.0,
            'tempo_category': 'none',
            'tempo_confidence': 0.0,
            'beat_times': [],
            'num_beats': 0,
            'has_rhythm': False,
            'energy_level': 0.0,
            'spectral_centroid': 0.0,
            'tempo_stability': 0.0
        }
    
    def _categorize_tempo(self, bpm: float) -> str:
        """Categorize tempo based on BPM."""
        for category, (min_bpm, max_bpm) in self.TEMPO_CATEGORIES.items():
            if min_bpm <= bpm < max_bpm:
                return category
        
        if bpm == 0:
            return 'none'
        return 'extremely_fast'
    
    def match_tempo_to_mood(self, bpm: float, energy: float) -> str:
        """
        Suggest mood based on tempo and energy.
        
        Useful for matching videos to lyrics.
        """
        if bpm == 0:
            return 'ambient'
        
        if bpm < 60:
            return 'calm' if energy < 30 else 'dramatic'
        elif bpm < 90:
            return 'relaxed' if energy < 50 else 'groovy'
        elif bpm < 120:
            return 'upbeat' if energy > 50 else 'moderate'
        elif bpm < 150:
            return 'energetic' if energy > 60 else 'driving'
        else:
            return 'intense' if energy > 70 else 'fast'
    
    def find_best_clips_for_bpm(self, target_bpm: float, video_list: list, 
                                tolerance: float = 10.0) -> list:
        """
        Find videos matching a target BPM.
        
        Args:
            target_bpm: Target BPM to match
            video_list: List of video dicts with 'bpm' field
            tolerance: BPM tolerance range
        
        Returns:
            Filtered list sorted by BPM closeness
        """
        matches = []
        
        for video in video_list:
            video_bpm = video.get('bpm', 0)
            
            if video_bpm == 0:
                continue
            
            bpm_diff = abs(video_bpm - target_bpm)
            
            if bpm_diff <= tolerance:
                matches.append({
                    **video,
                    'bpm_difference': bpm_diff
                })
        
        # Sort by closest match
        matches.sort(key=lambda x: x['bpm_difference'])
        
        return matches
    
    def detect_audio_features(self, video_or_audio_path: str) -> Dict:
        """
        Detect comprehensive audio features.
        
        Returns genre suggestions, mood, instruments, etc.
        """
        try:
            # Load audio
            y, sr = librosa.load(video_or_audio_path, sr=22050, duration=30)
            
            if len(y) == 0:
                return {}
            
            # Spectral features
            spectral_centroid = np.mean(librosa.feature.spectral_centroid(y=y, sr=sr))
            spectral_rolloff = np.mean(librosa.feature.spectral_rolloff(y=y, sr=sr))
            zero_crossing_rate = np.mean(librosa.feature.zero_crossing_rate(y))
            
            # MFCC (timbre)
            mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
            mfcc_mean = np.mean(mfccs, axis=1)
            
            # Chroma features (harmony)
            chroma = librosa.feature.chroma_stft(y=y, sr=sr)
            chroma_mean = np.mean(chroma, axis=1)
            
            # RMS energy
            rms = np.mean(librosa.feature.rms(y=y))
            
            return {
                'spectral_centroid': float(spectral_centroid),
                'spectral_rolloff': float(spectral_rolloff),
                'zero_crossing_rate': float(zero_crossing_rate),
                'rms_energy': float(rms),
                'mfcc_features': mfcc_mean.tolist(),
                'chroma_features': chroma_mean.tolist(),
                'brightness': 'bright' if spectral_centroid > 3000 else 'dark',
                'percussiveness': 'percussive' if zero_crossing_rate > 0.1 else 'smooth'
            }
            
        except Exception as e:
            print(f"Error detecting audio features: {e}")
            return {}


# Example usage
if __name__ == "__main__":
    detector = TempoDetector()
    
    # Test with a video
    video_path = "test_video.mp4"
    
    if os.path.exists(video_path):
        print("🎵 Analyzing tempo...\n")
        
        result = detector.analyze_tempo(video_path)
        
        print("📊 Tempo Analysis Results:")
        print(f"  BPM: {result['bpm']}")
        print(f"  Category: {result['tempo_category']}")
        print(f"  Confidence: {result['tempo_confidence']:.1%}")
        print(f"  Beats: {result['num_beats']}")
        print(f"  Has Rhythm: {result['has_rhythm']}")
        print(f"  Energy: {result['energy_level']}/100")
        print(f"  Stability: {result['tempo_stability']:.1%}")
        
        # Suggest mood
        mood = detector.match_tempo_to_mood(result['bpm'], result['energy_level'])
        print(f"\n💭 Suggested Mood: {mood}")
        
        # Audio features
        print("\n🎼 Analyzing audio features...")
        features = detector.detect_audio_features(video_path)
        
        if features:
            print(f"  Brightness: {features.get('brightness', 'unknown')}")
            print(f"  Style: {features.get('percussiveness', 'unknown')}")
            print(f"  Spectral Centroid: {features.get('spectral_centroid', 0):.0f} Hz")
    else:
        print(f"Video not found: {video_path}")
