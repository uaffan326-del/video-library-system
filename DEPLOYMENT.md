# Deployment Guide - PythonAnywhere (Free)

## 🌐 Deploy to PythonAnywhere (Recommended)

### Step 1: Create Account
1. Go to https://www.pythonanywhere.com/
2. Sign up for free account
3. Confirm email

### Step 2: Upload Your Project
1. Click "Files" tab
2. Upload all project files, or use Git:
   ```bash
   cd ~
   git clone <your-repo-url>
   cd "Video Scraping project"
   ```

### Step 3: Install Dependencies
1. Click "Consoles" → "Bash"
2. Run:
   ```bash
   cd "Video Scraping project"
   pip3 install --user -r requirements.txt
   ```

### Step 4: Configure Web App
1. Click "Web" tab
2. "Add a new web app"
3. Choose "Flask"
4. Python version: 3.9+
5. Point to your `web_ui.py` file

### Step 5: Configure WSGI
Edit the WSGI configuration file:
```python
import sys
path = '/home/YOUR_USERNAME/Video Scraping project'
if path not in sys.path:
    sys.path.append(path)

from web_ui import app as application
```

### Step 6: Add API Key
1. In web app settings, add environment variable:
   - Name: `OPENAI_API_KEY`
   - Value: Your API key

### Step 7: Reload
Click "Reload" button

### Your Live URL:
`https://YOUR_USERNAME.pythonanywhere.com`

---

## 🔥 Option 2: Render.com (Free Tier)

### Step 1: Prepare Files
Create `render.yaml`:
```yaml
services:
  - type: web
    name: video-library
    env: python
    buildCommand: "pip install -r requirements.txt"
    startCommand: "gunicorn web_ui:app"
    envVars:
      - key: OPENAI_API_KEY
        sync: false
```

### Step 2: Add to requirements.txt
Add: `gunicorn==21.2.0`

### Step 3: Deploy
1. Push to GitHub
2. Go to https://render.com
3. "New Web Service"
4. Connect GitHub repo
5. Deploy!

URL: `https://your-app.onrender.com`

---

## ⚡ Option 3: Railway.app (Easy)

### Step 1: Install Railway CLI (Optional)
Or use web interface

### Step 2: Deploy
```bash
npm i -g @railway/cli
railway login
railway init
railway up
```

### Step 3: Add Environment Variables
```bash
railway variables set OPENAI_API_KEY=your_key
```

URL: `https://your-app.railway.app`

---

## 🐳 Option 4: Docker + Any Platform

### Create Dockerfile:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_APP=web_ui.py
ENV PORT=5000

EXPOSE 5000

CMD ["python", "web_ui.py"]
```

Deploy to:
- Heroku
- Google Cloud Run
- AWS ECS
- DigitalOcean App Platform

---

## 💰 Cost Comparison

| Platform | Free Tier | Paid |
|----------|-----------|------|
| PythonAnywhere | ✅ Yes (limited) | $5/mo |
| Render | ✅ Yes (sleeps after 15min) | $7/mo |
| Railway | ✅ $5 free credit | $5/mo |
| Fly.io | ✅ Yes (limited) | Pay as you go |

---

## ⚠️ Important for Live Deployment

### 1. Update web_ui.py for Production
Change:
```python
if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
```

### 2. Add Production Server
Update requirements.txt:
```
gunicorn>=21.2.0
```

### 3. Database Considerations
- SQLite works for small scale
- For production at scale, consider PostgreSQL
- Your current SQLite will work fine initially

### 4. Environment Variables
Never commit `.env` file!
Set on platform:
- `OPENAI_API_KEY`
- `PEXELS_API_KEY` (optional)
- `PIXABAY_API_KEY` (optional)

---

## 🎯 Recommended: PythonAnywhere

**Why?**
- ✅ Easiest for beginners
- ✅ True free tier (always on)
- ✅ SQLite works out of box
- ✅ No credit card needed
- ✅ 3-month free with education email

**Limitations:**
- 512MB disk space (upgrade for more)
- Limited CPU time
- One web app on free tier

Perfect for testing and early users!

---

## Need Help?

Choose your platform and I can provide specific deployment commands!
