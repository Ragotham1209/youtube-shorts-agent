# YouTube Shorts Agent - Data Engineering

Autonomous agent that creates and publishes Data Engineering YouTube Shorts daily.

## Architecture

```
┌─────────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Content Generator│────▶│ Voice (Edge  │────▶│ Video Creator │────▶│ YouTube      │
│ (OpenAI / Local) │     │   TTS)       │     │ (FFmpeg)      │     │ Uploader     │
└─────────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
        │                                           │
        │ Script JSON                               │ Stock footage (Pexels)
        │ - title                                   │ Text overlays
        │ - hook                                    │ Audio merge
        │ - 5 segments                              │
        │ - tags                                    │
```

## Setup (One-Time)

### 1. Get API Keys

| Service | Purpose | Cost | Link |
|---------|---------|------|------|
| Pexels | Stock footage | Free | https://www.pexels.com/api/ |
| OpenAI | Script generation | ~$0.01/video | https://platform.openai.com/api-keys |
| Google/YouTube | Video upload | Free | See below |

### 2. Set Up YouTube API Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (e.g., "YouTube Shorts Agent")
3. Enable the **YouTube Data API v3**:
   - Navigate to APIs & Services → Library
   - Search "YouTube Data API v3" → Enable
4. Create OAuth 2.0 credentials:
   - Go to APIs & Services → Credentials
   - Click "Create Credentials" → "OAuth client ID"
   - Application type: **Desktop app**
   - Name it (e.g., "Shorts Agent")
   - Download the client ID and secret
5. Configure OAuth consent screen:
   - Go to APIs & Services → OAuth consent screen
   - User type: External (or Internal if using Workspace)
   - Fill in app name, email
   - Add scope: `youtube.upload`
   - Add your Google account as a test user

### 3. Get YouTube Refresh Token

Run the token helper script on your local machine:

```bash
pip install google-auth-oauthlib
python get_youtube_token.py
```

This opens a browser window. Sign in with your YouTube channel's Google account and authorize. The script prints your refresh token.

### 4. Configure GitHub Repository

1. Push this code to a GitHub repository
2. Go to Settings → Secrets and variables → Actions
3. Add these repository secrets:

| Secret Name | Value |
|-------------|-------|
| `OPENAI_API_KEY` | Your OpenAI API key |
| `PEXELS_API_KEY` | Your Pexels API key |
| `YOUTUBE_CLIENT_ID` | OAuth client ID from step 2 |
| `YOUTUBE_CLIENT_SECRET` | OAuth client secret from step 2 |
| `YOUTUBE_REFRESH_TOKEN` | Refresh token from step 3 |

### 5. Set Your Timezone

Edit `.github/workflows/daily_short.yml` and update the cron schedule to match 8:00 PM in your timezone:

| Timezone | Cron Expression |
|----------|----------------|
| US Eastern (EST/EDT) | `0 1 * * *` (1 AM UTC = 8 PM EST) |
| US Pacific (PST/PDT) | `0 4 * * *` (4 AM UTC = 8 PM PST) |
| India (IST) | `30 14 * * *` (2:30 PM UTC = 8 PM IST) |
| UK (GMT/BST) | `0 20 * * *` (8 PM UTC = 8 PM GMT) |
| Central Europe (CET) | `0 19 * * *` (7 PM UTC = 8 PM CET) |

### 6. Enable GitHub Actions

- Go to the Actions tab in your repository
- Enable workflows
- The agent will run automatically on schedule
- You can also trigger it manually via "Run workflow"

## Local Testing

```bash
# Install dependencies
pip install -r requirements.txt
sudo apt install ffmpeg  # or: brew install ffmpeg (macOS)

# Copy and fill in environment variables
cp .env.example .env
# Edit .env with your API keys

# Generate script only (no video/upload)
python main.py --dry-run

# Generate video but skip upload
python main.py --no-upload

# Full run (generate + upload)
python main.py
```

## File Structure

```
├── main.py                 # Orchestrator
├── content_generator.py    # Script generation (OpenAI + fallbacks)
├── voice_generator.py      # Edge TTS voiceover
├── video_creator.py        # Stock footage + text overlay compositing
├── youtube_uploader.py     # YouTube Data API upload
├── get_youtube_token.py    # One-time OAuth token helper
├── config.py               # Configuration and env vars
├── requirements.txt        # Python dependencies
├── topic_history.json      # Tracks used topics (auto-generated)
├── .env.example            # Environment variable template
└── .github/workflows/
    └── daily_short.yml     # GitHub Actions cron workflow
```

## How It Works

1. **Script Generation**: Uses OpenAI GPT-4o-mini to generate a unique Data Engineering topic with a hook and 5 key points. Falls back to 10 built-in topics if OpenAI is unavailable.

2. **Voiceover**: Edge TTS generates natural-sounding speech for each segment (free, no API key needed).

3. **Video Creation**: Downloads portrait stock footage from Pexels, overlays text with a dark gradient for readability, syncs audio, and composites into a 9:16 vertical video under 60 seconds.

4. **Upload**: Publishes to YouTube via the Data API v3 with `#Shorts` tag, proper metadata, and relevant hashtags.

5. **History Tracking**: `topic_history.json` prevents topic repetition across runs.

## Cost Estimate

| Component | Cost per Video | Monthly (30 videos) |
|-----------|---------------|---------------------|
| Edge TTS | Free | Free |
| Pexels API | Free | Free |
| OpenAI GPT-4o-mini | ~$0.01 | ~$0.30 |
| GitHub Actions | Free (2000 min/month) | Free |
| **Total** | **~$0.01** | **~$0.30** |
