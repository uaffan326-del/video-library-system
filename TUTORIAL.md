# 🎬 Video Library System - Complete Tutorial

## 📋 Table of Contents
1. [First Time Setup](#first-time-setup)
2. [Starting the System](#starting-the-system)
3. [Scraping Videos](#scraping-videos)
4. [Browsing Videos](#browsing-videos)
5. [Searching & Filtering](#searching--filtering)
6. [Using for Lyric Videos](#using-for-lyric-videos)
7. [Troubleshooting](#troubleshooting)

---

## 🚀 First Time Setup

### Step 1: Install Dependencies
Open PowerShell in the project folder and run:
```powershell
python -m pip install -r requirements.txt
```

### Step 2: Verify API Key
Your OpenAI API key is already configured in `.env` file. You're good to go!

---

## 🎯 Starting the System

### Open the Web Interface
1. Open PowerShell in project folder
2. Run:
   ```powershell
   python web_ui.py
   ```
3. Open browser and go to: **http://localhost:5000**
4. You should see the Video Library Browser interface

**Keep the PowerShell window open** while using the system!

---

## 📥 Scraping Videos

### From Web UI (Recommended)

1. **At the top of the page**, you'll see **"⚙️ Content Scraper"** panel

2. **Enter search queries** (comma-separated):
   ```
   Example: nature landscape, urban city, abstract motion
   ```

3. **Select videos per query**:
   - Start with **2 videos/query** for testing
   - Increase to **5 videos/query** for larger batches

4. **Click "🚀 Start Scraping"**

5. **Watch the progress**:
   - Progress bar shows completion percentage
   - Status updates (Downloading → Clipping → Analyzing)
   - Live clip counter
   - Takes ~2-5 minutes per video

6. **When complete**:
   - Videos automatically appear in the grid below
   - Stats update automatically

### Cost Estimate
- **2 videos/query × 3 queries** = ~6 videos → ~30 clips → **$0.30-0.60**
- **5 videos/query × 5 queries** = ~25 videos → ~125 clips → **$1.25-2.50**

---

## 🔍 Browsing Videos

### View All Videos
- Scroll down to see the video grid
- Each card shows:
  - Thumbnail preview
  - Duration
  - Mood tag
  - Theme keywords

### View Video Details
1. **Click any video card**
2. Modal opens with:
   - Full video player
   - All tags and metadata
   - Color palette
   - Mood analysis
   - Resolution and file info

3. **Click X or outside** to close

---

## 🎨 Searching & Filtering

### Search by Keywords
1. In the search bar, type keywords:
   ```
   Example: nature, forest, calm
   ```
2. Click **"Search"** button
3. Results filter automatically

### Filter by Mood
1. Use **"Mood"** dropdown:
   - Positive (happy, uplifting, energetic)
   - Negative (sad, dark, tense)
   - Neutral (calm, balanced)

2. Combines with keyword search

### Filter by Color
1. Use **"Color"** dropdown
2. Select dominant color:
   - Blue, Green, Red, Orange, etc.
3. Shows videos with that color palette

### Adjust Results Count
- Use **"Results"** dropdown
- 20, 50, or 100 videos at once

### Clear All Filters
- Click **"Clear"** button to reset

---

## 🎵 Using for Lyric Videos

### Find Video for Lyric Line

1. Scroll to **"🎵 Find Video for Lyric"** section

2. **Enter a lyric line**:
   ```
   Example: "dancing under the stars tonight"
   ```

3. **Optional: Select mood**:
   - Choose expected mood of the lyric
   - Or leave as "Auto-detect mood"

4. **Click "Find Match"**

5. **System analyzes**:
   - Extracts keywords (dancing, stars, night)
   - Matches with video tags
   - Returns best fitting video

6. **Result shows** below with full preview

### Programmatic Usage (For Integration)

If you're building a lyric video app, use this Python code:

```python
from search import VideoSearcher

searcher = VideoSearcher()

# Get video for a lyric
video = searcher.get_video_for_lyric(
    lyric_text="dancing under the stars",
    mood_hint="positive"
)

# Video file path
video_path = video['file_path']

# Use in your video editor
print(f"Use video: {video_path}")
```

### Batch Processing Multiple Lyrics

```python
lyrics = [
    {"text": "sunshine in the morning", "mood": "positive"},
    {"text": "lonely nights alone", "mood": "negative"},
    {"text": "walking down the street", "mood": "neutral"}
]

for lyric in lyrics:
    video = searcher.get_video_for_lyric(
        lyric['text'], 
        lyric['mood']
    )
    print(f"Lyric: {lyric['text']}")
    print(f"Video: {video['file_path']}\n")
```

---

## 💡 Tips & Best Practices

### Scraping Strategy

**Start Small**
```
Query: "nature sunset"
Videos: 2
Result: ~10 clips, costs ~$0.10-0.20
```

**Scale Up Gradually**
```
Queries: "nature, urban, abstract, ocean, sky"
Videos per query: 3-5
Result: 75-125 clips, costs ~$0.75-2.50
```

**Build Large Library**
```
Run multiple batches over time
Each session: 5 queries × 5 videos
Total: 10 sessions = ~500 clips
Cost: ~$5-10 total
```

### Search Query Tips

**Good Queries**:
- ✅ `nature landscape scenic`
- ✅ `city urban night lights`
- ✅ `abstract motion colorful`
- ✅ `ocean waves water`
- ✅ `space stars galaxy`

**Avoid**:
- ❌ Too specific: "red car on highway at sunset"
- ❌ Too generic: "video"
- ❌ Complex phrases: "a beautiful day in the park"

### Organizing Your Library

1. **By Theme**:
   - Nature, Urban, Abstract, Space, Water

2. **By Mood**:
   - Positive, Negative, Neutral

3. **By Color**:
   - Blue (ocean, sky)
   - Green (forest, nature)
   - Orange/Red (sunset, fire)

4. **By Energy**:
   - Calm (meditation, peaceful)
   - Energetic (action, dynamic)
   - Intense (dramatic, powerful)

---

## 🔧 Troubleshooting

### Web UI Won't Load
**Problem**: Can't access http://localhost:5000

**Solution**:
1. Check if `web_ui.py` is running in PowerShell
2. Look for message: "Running on http://127.0.0.1:5000"
3. Try: http://127.0.0.1:5000 instead
4. If port 5000 is busy, change in `web_ui.py`:
   ```python
   app.run(debug=True, host='0.0.0.0', port=5001)
   ```

### No Videos Showing
**Problem**: Web UI loads but no videos appear

**Solution**:
1. You need to scrape videos first!
2. Use the scraper panel at the top
3. Or run manually:
   ```powershell
   python main.py scrape
   ```

### Scraping Fails
**Problem**: Error during scraping

**Solutions**:
- **API Key Error**: Check `.env` file has correct OpenAI key
- **Network Error**: Check internet connection
- **Out of Credits**: Add credits to OpenAI account
- **Video Download Fails**: Some archive.org videos may be unavailable, system will skip them

### Videos Won't Play
**Problem**: Click video but it won't play in modal

**Solution**:
- Browser might not support the codec
- Try different browser (Chrome recommended)
- Video file might be corrupted (rare)

### Slow AI Analysis
**Problem**: AI tagging takes forever

**Expected**:
- ~3-5 seconds per clip is normal
- 100 clips = ~5-8 minutes

**To Speed Up**:
- Reduce clips per video (already 3-5 second segments)
- Process in smaller batches
- Can't speed up OpenAI API itself

---

## 📊 Database Statistics

### View Your Library Stats
1. At the top header, you'll see:
   - 📹 Total Videos
   - 🏷️ Unique Tags
   - 🎨 Unique Colors

2. Or run in Python:
   ```python
   from search import VideoSearcher
   searcher = VideoSearcher()
   stats = searcher.get_stats_summary()
   print(stats)
   ```

### Accessing the Database Directly

SQLite database is at: `video_library.db`

View with tools like:
- **DB Browser for SQLite** (free GUI)
- **DBeaver** (database manager)
- Or query with Python:

```python
import sqlite3

conn = sqlite3.connect('video_library.db')
cursor = conn.cursor()

# Get all videos
cursor.execute('SELECT * FROM videos')
videos = cursor.fetchall()

for video in videos:
    print(video)

conn.close()
```

---

## 🎬 Complete Workflow Example

### Build a 500-Clip Library for Lyric Videos

**Day 1: Setup & Test**
```
1. Start web UI: python web_ui.py
2. Open http://localhost:5000
3. Test scrape: 2 videos/query, 3 queries
4. Result: ~15 clips, ~$0.15
5. Verify quality in UI
```

**Day 2-5: Build Library**
```
Each day:
1. Run scraper with 5 queries × 5 videos
2. Let it run (~30-45 minutes)
3. Result per day: ~125 clips
4. Cost per day: ~$1.25-2.50
```

**Day 6: Organize & Test**
```
1. Browse library (500+ clips)
2. Test searches by mood
3. Test lyric matching
4. Fine-tune as needed
```

**Total Cost**: ~$5-10 for 500 clips

---

## 🔌 Integration with Your App

### Basic Integration

```python
# In your lyric video generator
from search import VideoSearcher

class LyricVideoGenerator:
    def __init__(self):
        self.searcher = VideoSearcher()
    
    def generate_video(self, lyrics, audio_path):
        video_clips = []
        
        # For each lyric line
        for line in lyrics:
            # Get matching video
            video = self.searcher.get_video_for_lyric(
                lyric_text=line['text'],
                mood_hint=line.get('mood')
            )
            
            video_clips.append({
                'lyric': line['text'],
                'video_path': video['file_path'],
                'start_time': line['start'],
                'end_time': line['end']
            })
        
        # Combine clips with subtitles
        self.render_final_video(video_clips, audio_path)
```

### Advanced: Random Selection

```python
# Get multiple options for variety
videos = searcher.search_combined(
    keywords=['nature', 'calm'],
    mood='positive',
    limit=10  # Get 10 options
)

# Randomly pick one
import random
selected = random.choice(videos)
```

---

## 📞 Need Help?

### Check These First:
1. ✅ Is `web_ui.py` running?
2. ✅ Is `.env` file configured with API key?
3. ✅ Did you scrape videos first?
4. ✅ Is port 5000 accessible?

### Common Questions:

**Q: How many videos should I scrape?**
A: Start with 50-100 clips, then scale based on needs.

**Q: Can I use my own videos?**
A: Yes! Put them in a folder and run:
```powershell
python main.py process path/to/videos
```

**Q: How do I backup my library?**
A: Copy these folders/files:
- `video_library.db` (database)
- `processed_clips/` (video files)
- `thumbnails/` (optional, can regenerate)

**Q: Can I use different AI models?**
A: Currently uses GPT-4 Vision. To use other models, modify `ai_tagger.py`.

---

## 🎉 You're Ready!

Your video library system is fully set up and ready to use. Start by:

1. ✅ Running `python web_ui.py`
2. ✅ Opening http://localhost:5000
3. ✅ Scraping your first batch of videos
4. ✅ Exploring the interface

Happy video scraping! 🚀
