# Quick Start Guide

## 1. Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
```

Edit `.env` and add your OpenAI API key:
```
OPENAI_API_KEY=sk-your-actual-key-here
```

## 2. Scrape and Process Videos

```bash
# Run with defaults (3 queries, 2 videos each = ~12 clips)
python main.py scrape

# Or customize
python main.py scrape "ocean waves" "mountain sunset" "city lights"
```

This will:
1. Download videos from archive.org
2. Split them into 3-5 second clips
3. Analyze with GPT-4 Vision
4. Store in SQLite database

## 3. Launch Web UI

```bash
python web_ui.py
```

Open browser: **http://localhost:5000**

## 4. Use Programmatically

```python
from search import VideoSearcher

searcher = VideoSearcher()

# Find video for a lyric
video = searcher.get_video_for_lyric(
    lyric_text="Dancing under the stars",
    mood_hint="positive"
)

print(f"Video path: {video['file_path']}")
```

## Web UI Features

- **Search by keywords**: nature, urban, abstract, etc.
- **Filter by mood**: positive, negative, neutral
- **Filter by color**: blue, red, green, etc.
- **Lyric matching**: Enter a lyric line, get matching video
- **Video preview**: Click any video to watch and see full details
- **Color palettes**: See dominant colors in each video
- **Tags**: View all AI-generated tags

## Tips

### Start Small
```bash
# Test with just 1 video per query
python main.py scrape "nature" --videos-per-query 1
```

### Process Existing Videos
```bash
python main.py process path/to/videos
```

### Check Database
```python
from search import VideoSearcher
searcher = VideoSearcher()
stats = searcher.get_stats_summary()
print(stats)
```

## Cost Estimates

- **GPT-4 Vision**: ~$0.01-0.02 per clip
- **Test run (6 clips)**: ~$0.06-0.12
- **Small library (100 clips)**: ~$1-2
- **Large library (1000 clips)**: ~$10-20

## Troubleshooting

**"OPENAI_API_KEY not found"**
→ Create `.env` file with your API key

**"Could not open video"**
→ Video may be corrupted, try different searches

**Web UI won't start**
→ Check if port 5000 is available
→ Install Flask: `pip install flask flask-cors`

**No videos in database**
→ Run `python main.py scrape` first

## Next Steps

1. **Customize searches**: Edit `scraper.py` → `DEFAULT_SEARCH_QUERIES`
2. **Adjust clip length**: Edit `.env` → `CLIP_DURATION_MIN` and `CLIP_DURATION_MAX`
3. **Integrate with your app**: Use `search.py` functions in your lyric video generator
4. **Scale up**: Process more videos as needed

---

Need help? Check the main README.md for detailed documentation.
