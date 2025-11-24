#!/usr/bin/env python3
"""
Video Scraping System - Main Script

This script orchestrates the complete video scraping, processing, and tagging pipeline:
1. Scrapes videos from archive.org
2. Clips them into 3-5 second segments
3. Uses AI (ChatGPT) to analyze and tag clips
4. Stores everything in a SQLite database
"""

import os
import sys
from dotenv import load_dotenv
from tqdm import tqdm

from scraper import ArchiveOrgScraper, DEFAULT_SEARCH_QUERIES
from video_processor import VideoClipper
from ai_tagger import AITagger
from database import VideoDatabase


class VideoScrapingPipeline:
    """Main pipeline for video scraping and processing."""
    
    def __init__(self, openai_api_key: str, database_path: str = "video_library.db"):
        """Initialize pipeline components."""
        self.scraper = ArchiveOrgScraper(download_dir="downloads")
        self.clipper = VideoClipper(output_dir="processed_clips", clip_duration=(3, 10))
        self.tagger = AITagger(api_key=openai_api_key)
        self.database = VideoDatabase(db_path=database_path)
    
    def run_full_pipeline(self, search_queries: list = None, videos_per_query: int = 5):
        """
        Run the complete pipeline from scraping to database storage.
        
        Args:
            search_queries: List of search terms (uses defaults if None)
            videos_per_query: Number of videos to download per query
        """
        if search_queries is None:
            search_queries = DEFAULT_SEARCH_QUERIES[:5]  # Start with first 5 queries
        
        print("\n" + "="*80)
        print("VIDEO SCRAPING PIPELINE STARTED")
        print("="*80 + "\n")
        
        # Step 1: Download videos
        print("\n[STEP 1/4] Downloading videos from archive.org...")
        print("-" * 80)
        downloaded_videos = self.scraper.batch_download(search_queries, videos_per_query)
        
        if not downloaded_videos:
            print("No videos downloaded. Exiting.")
            return
        
        print(f"\nSuccessfully downloaded {len(downloaded_videos)} videos")
        
        # Step 2: Clip videos
        print("\n[STEP 2/4] Clipping videos into 3-5 second segments...")
        print("-" * 80)
        video_paths = [v['filepath'] for v in downloaded_videos]
        all_clips = self.clipper.process_batch(video_paths)
        
        if not all_clips:
            print("No clips created. Exiting.")
            return
        
        print(f"\nSuccessfully created {len(all_clips)} clips")
        
        # Step 3: Analyze and tag clips
        print("\n[STEP 3/4] Analyzing clips with AI...")
        print("-" * 80)
        
        for i, clip in enumerate(tqdm(all_clips, desc="Analyzing clips")):
            try:
                # Extract frames for analysis
                frames = self.clipper.extract_multiple_frames(clip['path'], num_frames=3)
                
                if not frames:
                    print(f"\nWarning: Could not extract frames from {clip['path']}")
                    continue
                
                # Analyze with AI
                analysis = self.tagger.analyze_video_clip(frames)
                
                if not analysis:
                    print(f"\nWarning: Analysis failed for {clip['path']}")
                    continue
                
                # Find source video info
                source_video = next(
                    (v for v in downloaded_videos if v['filepath'] == clip['source_video']),
                    None
                )
                
                # Step 4: Store in database
                video_id = self.database.add_video(
                    source_url=source_video['original_url'] if source_video else '',
                    file_path=clip['path'],
                    source_identifier=source_video['identifier'] if source_video else '',
                    duration=clip['duration'],
                    width=clip.get('width'),
                    height=clip.get('height')
                )
                
                # Add tags
                tags = []
                
                # Theme tag
                if analysis.get('theme'):
                    tags.append({'type': 'theme', 'value': analysis['theme'], 'confidence': 1.0})
                
                # Style tag
                if analysis.get('style'):
                    tags.append({'type': 'style', 'value': analysis['style'], 'confidence': 1.0})
                
                # Energy tag
                if analysis.get('energy'):
                    tags.append({'type': 'energy', 'value': analysis['energy'], 'confidence': 1.0})
                
                # Keyword tags
                for keyword in analysis.get('keywords', []):
                    tags.append({'type': 'keyword', 'value': keyword, 'confidence': 0.8})
                
                # Suitable for tags
                if analysis.get('suitable_for'):
                    tags.append({'type': 'genre', 'value': analysis['suitable_for'], 'confidence': 0.9})
                
                # Search query tag (from original search)
                if source_video and source_video.get('search_query'):
                    tags.append({'type': 'search_query', 'value': source_video['search_query'], 'confidence': 1.0})
                
                self.database.add_tags(video_id, tags)
                
                # Add colors
                colors = analysis.get('dominant_colors', [])
                self.database.add_colors(video_id, colors)
                
                # Add mood
                mood = analysis.get('mood', 'neutral')
                mood_intensity = analysis.get('mood_intensity', 5)
                self.database.add_mood(video_id, mood, mood_intensity)
                
                # Store complete AI analysis
                self.database.add_ai_analysis(video_id, 'gpt4_vision', analysis)
                
            except Exception as e:
                print(f"\nError processing clip {clip['path']}: {e}")
                continue
        
        # Final summary
        print("\n" + "="*80)
        print("PIPELINE COMPLETED SUCCESSFULLY")
        print("="*80)
        
        stats = self.database.get_stats()
        print(f"\nDatabase Statistics:")
        print(f"  Total videos: {stats['total_videos']}")
        print(f"  Unique tags: {stats['unique_tags']}")
        print(f"  Unique colors: {stats['unique_colors']}")
        print(f"\nDatabase saved to: {self.database.db_path}")
    
    def process_existing_videos(self, video_dir: str):
        """
        Process videos that are already downloaded.
        
        Args:
            video_dir: Directory containing video files
        """
        print(f"\n[Processing existing videos from: {video_dir}]")
        
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm']
        video_files = []
        
        for file in os.listdir(video_dir):
            if any(file.lower().endswith(ext) for ext in video_extensions):
                video_files.append(os.path.join(video_dir, file))
        
        if not video_files:
            print(f"No video files found in {video_dir}")
            return
        
        print(f"Found {len(video_files)} videos")
        
        # Clip videos
        print("\n[Clipping videos...]")
        all_clips = self.clipper.process_batch(video_files)
        
        # Analyze and store
        print("\n[Analyzing clips with AI...]")
        for clip in tqdm(all_clips, desc="Processing"):
            try:
                frames = self.clipper.extract_multiple_frames(clip['path'], num_frames=3)
                if not frames:
                    continue
                
                analysis = self.tagger.analyze_video_clip(frames)
                if not analysis:
                    continue
                
                # Store in database
                video_id = self.database.add_video(
                    source_url="local_file",
                    file_path=clip['path'],
                    duration=clip['duration'],
                    width=clip.get('width'),
                    height=clip.get('height')
                )
                
                # Add metadata (simplified version)
                tags = [{'type': 'theme', 'value': analysis.get('theme', 'unknown'), 'confidence': 1.0}]
                self.database.add_tags(video_id, tags)
                self.database.add_colors(video_id, analysis.get('dominant_colors', []))
                self.database.add_mood(video_id, analysis.get('mood', 'neutral'), analysis.get('mood_intensity', 5))
                self.database.add_ai_analysis(video_id, 'gpt4_vision', analysis)
                
            except Exception as e:
                print(f"\nError: {e}")
                continue
        
        print("\nProcessing complete!")
        stats = self.database.get_stats()
        print(f"Total videos in database: {stats['total_videos']}")


def main():
    """Main entry point."""
    # Load environment variables
    load_dotenv()
    
    openai_api_key = os.getenv('OPENAI_API_KEY')
    
    if not openai_api_key:
        print("ERROR: OPENAI_API_KEY not found in environment variables")
        print("Please create a .env file with your OpenAI API key")
        print("Example: OPENAI_API_KEY=sk-...")
        sys.exit(1)
    
    # Initialize pipeline
    pipeline = VideoScrapingPipeline(openai_api_key)
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "process" and len(sys.argv) > 2:
            # Process existing videos
            video_dir = sys.argv[2]
            pipeline.process_existing_videos(video_dir)
        
        elif command == "scrape":
            # Full pipeline with custom queries
            queries = sys.argv[2:] if len(sys.argv) > 2 else None
            videos_per_query = 3  # Conservative default
            pipeline.run_full_pipeline(queries, videos_per_query)
        
        else:
            print("Usage:")
            print("  python main.py scrape [query1] [query2] ...  - Download and process videos")
            print("  python main.py process <directory>            - Process existing videos")
    
    else:
        # Run with default settings
        print("Running pipeline with default settings...")
        print("To customize, use: python main.py scrape [queries]")
        print()
        
        # Run with a small subset for testing
        pipeline.run_full_pipeline(
            search_queries=DEFAULT_SEARCH_QUERIES[:3],
            videos_per_query=2
        )


if __name__ == "__main__":
    main()
