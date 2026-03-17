import os
from dotenv import load_dotenv

load_dotenv()

# --- OpenAI ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# --- Pexels ---
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")

# --- YouTube ---
YOUTUBE_CLIENT_ID = os.getenv("YOUTUBE_CLIENT_ID", "")
YOUTUBE_CLIENT_SECRET = os.getenv("YOUTUBE_CLIENT_SECRET", "")
YOUTUBE_REFRESH_TOKEN = os.getenv("YOUTUBE_REFRESH_TOKEN", "")
YOUTUBE_CATEGORY_ID = os.getenv("VIDEO_CATEGORY_ID", "28")  # 28 = Science & Technology

# --- Video Settings ---
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920  # 9:16 portrait for Shorts
VIDEO_FPS = 30
VIDEO_DURATION = 55  # target duration in seconds (under 60s for Shorts)
FONT_SIZE = 52
FONT_COLOR = "white"
STROKE_COLOR = "black"
STROKE_WIDTH = 3

# --- Paths ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_DIR = os.path.join(BASE_DIR, "tmp")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
OUTPUT_DIR = os.path.join(BASE_DIR, "output_videos")

for d in [TEMP_DIR, ASSETS_DIR, OUTPUT_DIR]:
    os.makedirs(d, exist_ok=True)
