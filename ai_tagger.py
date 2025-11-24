import base64
import os
from typing import List, Dict
import numpy as np
import cv2
from openai import OpenAI
from collections import Counter
import colorsys


class AITagger:
    """AI-powered video analysis and tagging using OpenAI's GPT-4 Vision."""
    
    def __init__(self, api_key: str):
        """
        Initialize AI tagger.
        
        Args:
            api_key: OpenAI API key
        """
        self.client = OpenAI(api_key=api_key)
    
    def encode_frame(self, frame: np.ndarray) -> str:
        """Encode frame to base64 for API."""
        # Resize frame to reduce API costs
        height, width = frame.shape[:2]
        max_dim = 512
        
        if max(height, width) > max_dim:
            scale = max_dim / max(height, width)
            new_width = int(width * scale)
            new_height = int(height * scale)
            frame = cv2.resize(frame, (new_width, new_height))
        
        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Encode to JPEG
        _, buffer = cv2.imencode('.jpg', frame_rgb)
        return base64.b64encode(buffer).decode('utf-8')
    
    def analyze_frame_with_gpt4(self, frame: np.ndarray) -> Dict:
        """
        Analyze a video frame using GPT-4 Vision.
        
        Returns:
            Dictionary with analysis results
        """
        try:
            base64_image = self.encode_frame(frame)
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": """Analyze this video frame for use as a lyric video background. Provide:

1. THEME: Main subject/theme (nature, urban, abstract, space, etc.)
2. MOOD: Emotional tone (positive, negative, neutral) and intensity (1-10)
3. STYLE: Visual style (cinematic, abstract, minimalist, vibrant, dark, etc.)
4. ENERGY: Energy level (calm, moderate, energetic, intense)
5. COLORS: Dominant color palette
6. KEYWORDS: 5-7 descriptive keywords for search/filtering
7. SUITABLE_FOR: Types of song genres or moods this would work well with

Format your response as:
THEME: [theme]
MOOD: [mood] (intensity: [1-10])
STYLE: [style]
ENERGY: [energy level]
COLORS: [color1, color2, color3]
KEYWORDS: [keyword1, keyword2, keyword3, keyword4, keyword5]
SUITABLE_FOR: [genre/mood suggestions]"""
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500
            )
            
            content = response.choices[0].message.content
            return self._parse_gpt_response(content)
            
        except Exception as e:
            print(f"Error analyzing frame with GPT-4: {e}")
            return {}
    
    def _parse_gpt_response(self, content: str) -> Dict:
        """Parse GPT-4 response into structured data."""
        result = {
            'theme': '',
            'mood': '',
            'mood_intensity': 5,
            'style': '',
            'energy': '',
            'colors': [],
            'keywords': [],
            'suitable_for': ''
        }
        
        lines = content.strip().split('\n')
        
        for line in lines:
            if ':' not in line:
                continue
            
            key, value = line.split(':', 1)
            key = key.strip().lower()
            value = value.strip()
            
            if key == 'theme':
                result['theme'] = value
            elif key == 'mood':
                # Extract mood and intensity
                if '(intensity:' in value.lower():
                    mood_part = value.split('(')[0].strip()
                    intensity_part = value.split('intensity:')[1].split(')')[0].strip()
                    result['mood'] = mood_part
                    try:
                        result['mood_intensity'] = int(intensity_part)
                    except:
                        result['mood_intensity'] = 5
                else:
                    result['mood'] = value
            elif key == 'style':
                result['style'] = value
            elif key == 'energy':
                result['energy'] = value
            elif key == 'colors':
                colors = [c.strip() for c in value.split(',')]
                result['colors'] = colors
            elif key == 'keywords':
                keywords = [k.strip() for k in value.split(',')]
                result['keywords'] = keywords
            elif key == 'suitable_for':
                result['suitable_for'] = value
        
        return result
    
    def extract_dominant_colors(self, frame: np.ndarray, num_colors: int = 5) -> List[Dict]:
        """
        Extract dominant colors from frame using color quantization.
        
        Returns:
            List of color dictionaries with hex, rgb, and name
        """
        # Resize for faster processing
        small_frame = cv2.resize(frame, (150, 150))
        
        # Reshape to list of pixels
        pixels = small_frame.reshape(-1, 3)
        
        # Convert to float
        pixels = np.float32(pixels)
        
        # K-means clustering
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.2)
        _, labels, centers = cv2.kmeans(pixels, num_colors, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
        
        # Count pixels per cluster
        label_counts = Counter(labels.flatten())
        
        # Get dominant colors
        colors = []
        total_pixels = len(labels)
        
        for i in range(num_colors):
            color_bgr = centers[i].astype(int)
            color_rgb = (int(color_bgr[2]), int(color_bgr[1]), int(color_bgr[0]))
            
            # Calculate percentage
            percentage = label_counts.get(i, 0) / total_pixels
            
            # Convert to hex
            hex_color = "#{:02x}{:02x}{:02x}".format(*color_rgb)
            
            # Get color name
            color_name = self._get_color_name(color_rgb)
            
            colors.append({
                'hex': hex_color,
                'rgb': color_rgb,
                'name': color_name,
                'percentage': round(percentage, 3)
            })
        
        # Sort by percentage
        colors.sort(key=lambda x: x['percentage'], reverse=True)
        
        return colors
    
    def _get_color_name(self, rgb: tuple) -> str:
        """Get approximate color name from RGB values."""
        r, g, b = [x / 255.0 for x in rgb]
        h, s, v = colorsys.rgb_to_hsv(r, g, b)
        
        # Convert hue to degrees
        h = h * 360
        
        # Determine color name based on HSV
        if v < 0.2:
            return "black"
        elif s < 0.1:
            if v > 0.8:
                return "white"
            else:
                return "gray"
        elif h < 15 or h >= 345:
            return "red"
        elif h < 45:
            return "orange"
        elif h < 75:
            return "yellow"
        elif h < 165:
            return "green"
        elif h < 195:
            return "cyan"
        elif h < 255:
            return "blue"
        elif h < 285:
            return "purple"
        else:
            return "pink"
    
    def analyze_video_clip(self, frames: List[np.ndarray]) -> Dict:
        """
        Analyze multiple frames from a video clip.
        
        Args:
            frames: List of video frames (numpy arrays)
        
        Returns:
            Complete analysis dictionary
        """
        if not frames:
            return {}
        
        print(f"Analyzing {len(frames)} frames with AI...")
        
        # Analyze middle frame with GPT-4
        middle_frame = frames[len(frames) // 2]
        gpt_analysis = self.analyze_frame_with_gpt4(middle_frame)
        
        # Extract colors from all frames and aggregate
        all_colors = []
        for frame in frames:
            colors = self.extract_dominant_colors(frame, num_colors=3)
            all_colors.extend(colors)
        
        # Aggregate color information
        color_counter = {}
        for color in all_colors:
            name = color['name']
            if name not in color_counter:
                color_counter[name] = {'count': 0, 'hex': color['hex'], 'percentage': 0}
            color_counter[name]['count'] += 1
            color_counter[name]['percentage'] += color['percentage']
        
        # Get top colors
        top_colors = sorted(
            color_counter.items(),
            key=lambda x: x[1]['count'],
            reverse=True
        )[:5]
        
        final_colors = [
            {
                'name': name,
                'hex': data['hex'],
                'percentage': round(data['percentage'] / len(frames), 3)
            }
            for name, data in top_colors
        ]
        
        # Combine all analysis
        result = {
            'gpt_analysis': gpt_analysis,
            'dominant_colors': final_colors,
            'theme': gpt_analysis.get('theme', ''),
            'mood': gpt_analysis.get('mood', ''),
            'mood_intensity': gpt_analysis.get('mood_intensity', 5),
            'style': gpt_analysis.get('style', ''),
            'energy': gpt_analysis.get('energy', ''),
            'keywords': gpt_analysis.get('keywords', []),
            'suitable_for': gpt_analysis.get('suitable_for', '')
        }
        
        return result
