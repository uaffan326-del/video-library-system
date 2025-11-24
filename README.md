# Video Scraping System

A complete automated system for scraping, processing, and cataloging short video clips for use as lyric video backgrounds.

## Features

- **Archive.org Scraping**: Download videos from archive.org using customizable search queries
- **Automatic Video Clipping**: Split videos into 3-5 second segments optimized for lyric videos
- **AI-Powered Tagging**: Uses GPT-4 Vision to analyze and tag videos with:
  - Themes (nature, urban, abstract, etc.)
  - Mood (positive, negative, neutral) with intensity
  - Visual style (cinematic, minimalist, vibrant, etc.)
  - Energy levels (calm, energetic, intense)
  - Dominant colors
  - Descriptive keywords
  - Genre suitability
- **SQLite Database**: Organized storage with fast search capabilities
- **Search System**: Query videos by keywords, mood, color, or combined criteria

## Installation

### Prerequisites

- Python 3.8 or higher
- OpenAI API key (for GPT-4 Vision analysis)

### Setup

1. **Clone or download this project**

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Configure environment variables**:

Create a `.env` file in the project root:
```bash
cp .env.example .env
```

Edit `.env` and add your OpenAI API key:
```
OPENAI_API_KEY=sk-your-actual-api-key-here
```

## Usage

### Quick Start

Run the pipeline with default settings (downloads 6 videos, processes them, and creates database):

```bash
python main.py scrape
```

### Web UI Interface

Launch the web-based video browser:

```bash
python web_ui.py
```

Then open your browser to: **http://localhost:5000**

The web UI provides:
- 🔍 Search videos by keywords, mood, and color
- 🎵 Find videos matching lyric lines
- 📹 Preview videos with thumbnails
- 🏷️ View detailed tags and metadata
- 🎨 See color palettes
- 📊 Database statistics

### Custom Search Queries

Specify your own search queries:

```bash
python main.py scrape "nature landscape" "abstract motion" "urban cityscape"
```

### Process Existing Videos

If you already have videos downloaded, you can process them directly:

```bash
python main.py process path/to/video/folder
```

### Search the Database

After processing videos, use the search module:

```python
from search import VideoSearcher

searcher = VideoSearcher()

# Search by keywords
videos = searcher.search_by_keywords(['nature', 'calm'])

# Search by mood
videos = searcher.search_by_mood('positive', limit=10)

# Search by color
videos = searcher.search_by_color('blue', limit=5)

# Combined search
videos = searcher.search_combined(
    keywords=['abstract'],
    mood='positive',
    color='blue',
    limit=10
)

# Get random videos
videos = searcher.get_random_videos(count=5)
```

Run the search demo:
```bash
python search.py
```

## Project Structure

```
Video Scraping project/
├── main.py              # Main pipeline orchestration
├── scraper.py           # Archive.org video scraping
├── video_processor.py   # Video clipping and frame extraction
├── ai_tagger.py         # GPT-4 Vision analysis and tagging
├── database.py          # SQLite database management
├── search.py            # Video search and retrieval
├── web_ui.py            # Flask web server for UI
├── config.py            # Configuration settings
├── requirements.txt     # Python dependencies
├── .env                 # Configuration (API keys)
├── .gitignore          # Git ignore rules
├── templates/           # HTML templates
│   └── index.html      # Main web interface
├── static/              # CSS and JavaScript
│   ├── style.css       # UI styling
│   └── script.js       # Frontend logic
├── downloads/          # Downloaded source videos (created automatically)
├── processed_clips/    # 3-5 second clips (created automatically)
├── thumbnails/         # Video thumbnails (created automatically)
└── video_library.db    # SQLite database (created automatically)
```

## Database Schema

### Tables

- **videos**: Core video information (path, duration, dimensions, source)
- **tags**: Video tags (theme, style, energy, keywords, genres)
- **colors**: Dominant colors with percentages
- **moods**: Emotional tone and intensity
- **ai_analysis**: Complete AI analysis results in JSON format

### Search Indexes

Optimized indexes on:
- Tag types and values
- Video IDs
- Color information

## Cost Considerations

### OpenAI API Costs

The system uses GPT-4 Vision (gpt-4o model) to analyze video frames:
- **Approximate cost**: $0.01-0.02 per video clip
- **For 100 clips**: ~$1-2
- **For 1000 clips**: ~$10-20

To reduce costs:
- Process in batches
- Use the `videos_per_query` parameter to limit downloads
- Start with a small test run

### Storage Requirements

- **Source videos**: Varies (10-500 MB each)
- **Processed clips**: ~1-5 MB per clip
- **Database**: Minimal (~1-10 MB for thousands of clips)

Estimate: **5-10 GB** for 1000 processed clips

## Legal Considerations

This system is designed to work with archive.org, which hosts:
- **Public domain content**
- **Creative Commons licensed material**
- **Content with various usage rights**

### Important Notes:

1. **Always verify licenses**: Check the license of each video before commercial use
2. **Archive.org content**: Most suitable content is public domain
3. **Attribution**: Some licenses may require attribution
4. **Commercial use**: Ensure licenses permit your intended use case

### Recommended Sources:

- **Archive.org**: Public domain and CC-licensed content
- **Pexels**: Free stock videos (check their license)
- **Pixabay**: Free media with permissive licenses
- **Unsplash**: High-quality free photos/videos

## Customization

### Clip Duration

Edit `.env` to change clip duration:
```
CLIP_DURATION_MIN=3
CLIP_DURATION_MAX=5
```

### Search Queries

Edit `scraper.py` to customize `DEFAULT_SEARCH_QUERIES`:
```python
DEFAULT_SEARCH_QUERIES = [
    "your custom query",
    "another query",
    # ... more queries
]
```

### AI Analysis Prompt

Modify `ai_tagger.py` - the `analyze_frame_with_gpt4()` method - to customize what information is extracted from videos.

## Troubleshooting

### "OPENAI_API_KEY not found"
- Ensure `.env` file exists in the project root
- Verify your API key is correctly set in `.env`

### "Could not open video"
- Video file may be corrupted
- Try with different videos
- Check if opencv-python is properly installed

### Slow processing
- AI analysis takes time (~5-10 seconds per clip)
- Start with small batches (videos_per_query=2)
- Process during off-peak hours

### High API costs
- Reduce `videos_per_query` parameter
- Process only essential content
- Consider using cached results for testing

## Example Workflow

```python
# 1. Initialize the pipeline
from main import VideoScrapingPipeline
import os

api_key = os.getenv('OPENAI_API_KEY')
pipeline = VideoScrapingPipeline(api_key)

# 2. Run with custom queries
pipeline.run_full_pipeline(
    search_queries=['ocean waves', 'mountain landscape'],
    videos_per_query=3
)

# 3. Search the database
from search import VideoSearcher
searcher = VideoSearcher()

# Find videos for a lyric
video = searcher.get_video_for_lyric(
    lyric_text="Under the stars tonight",
    mood_hint="positive"
)
print(f"Selected video: {video['file_path']}")

# 4. Get statistics
stats = searcher.get_stats_summary()
print(f"Total videos: {stats['total_videos']}")
print(f"Top themes: {stats['top_themes']}")
```

## Future Enhancements

- [ ] Web interface for browsing videos
- [ ] Batch export functionality
- [ ] Integration with video editing tools
- [ ] Advanced NLP for lyric-to-video matching
- [ ] Support for more video sources (Pexels API, etc.)
- [ ] Video quality filtering
- [ ] Duplicate detection
- [ ] Advanced color palette extraction

## Contributing

This is a personal project but open to improvements:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project code is provided as-is for the job posting requirements. Individual videos scraped have their own licenses - always verify before use.

## Support

For issues or questions:
1. Check this README
2. Review the code comments
3. Test with small batches first
4. Verify API key configuration

## Acknowledgments

- Archive.org for providing access to public domain content
- OpenAI for GPT-4 Vision API
- Open source libraries: opencv-python, internetarchive, and others

---

**Created for**: Video background library generation for lyric video SaaS application  
**Date**: November 2025
