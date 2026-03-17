"""
Create YouTube Shorts video: stock footage background + text overlay + voiceover.
"""
import os
import requests
import textwrap
from moviepy.editor import (
    VideoFileClip,
    AudioFileClip,
    TextClip,
    CompositeVideoClip,
    concatenate_videoclips,
    ColorClip,
)
import config


def fetch_stock_footage(query: str, num_clips: int = 3) -> list[str]:
    """Download vertical stock footage clips from Pexels."""
    headers = {"Authorization": config.PEXELS_API_KEY}
    params = {
        "query": query,
        "orientation": "portrait",
        "size": "medium",
        "per_page": num_clips * 2,  # fetch extra for fallback
    }
    resp = requests.get(
        "https://api.pexels.com/videos/search", headers=headers, params=params
    )
    resp.raise_for_status()
    videos = resp.json().get("video_files", [])

    # Fallback: extract from top-level videos
    if not videos:
        for v in resp.json().get("videos", []):
            videos.extend(v.get("video_files", []))

    # Prefer HD portrait files
    downloaded = []
    for vid_data in resp.json().get("videos", []):
        if len(downloaded) >= num_clips:
            break
        files = vid_data.get("video_files", [])
        # Pick best portrait file
        best = None
        for f in files:
            w = f.get("width", 0)
            h = f.get("height", 0)
            if h > w and h >= 1080:  # portrait and at least 1080p
                best = f
                break
        if not best and files:
            best = files[0]
        if best:
            url = best["link"]
            path = os.path.join(config.TEMP_DIR, f"stock_{len(downloaded)}.mp4")
            print(f"  Downloading stock clip: {url[:80]}...")
            r = requests.get(url, stream=True)
            with open(path, "wb") as fp:
                for chunk in r.iter_content(chunk_size=8192):
                    fp.write(chunk)
            downloaded.append(path)

    return downloaded


def _create_text_clip(
    text: str, duration: float, fontsize: int = config.FONT_SIZE, position: str = "center"
) -> TextClip:
    """Create a styled text overlay clip."""
    wrapped = textwrap.fill(text, width=22)
    txt_clip = TextClip(
        wrapped,
        fontsize=fontsize,
        color=config.FONT_COLOR,
        stroke_color=config.STROKE_COLOR,
        stroke_width=config.STROKE_WIDTH,
        font="Liberation-Sans-Bold",
        method="caption",
        size=(config.VIDEO_WIDTH - 100, None),
        align="center",
    )
    txt_clip = txt_clip.set_duration(duration).set_position(("center", position))
    return txt_clip


def _build_segment_clip(
    bg_clip: VideoFileClip, text: str, audio_path: str, start_y: str = "center"
) -> CompositeVideoClip:
    """Build a single segment: background + text + audio."""
    audio = AudioFileClip(audio_path)
    duration = audio.duration + 0.5  # small padding

    # Trim or loop background to match audio duration
    if bg_clip.duration < duration:
        bg = bg_clip.loop(duration=duration)
    else:
        bg = bg_clip.subclip(0, duration)

    # Resize background to target dimensions
    bg = bg.resize((config.VIDEO_WIDTH, config.VIDEO_HEIGHT))

    # Add semi-transparent overlay for text readability
    overlay = ColorClip(
        size=(config.VIDEO_WIDTH, config.VIDEO_HEIGHT),
        color=(0, 0, 0),
    ).set_opacity(0.4).set_duration(duration)

    # Create text
    txt = _create_text_clip(text, duration, position=start_y)

    composite = CompositeVideoClip([bg, overlay, txt], size=(config.VIDEO_WIDTH, config.VIDEO_HEIGHT))
    composite = composite.set_audio(audio)
    composite = composite.set_duration(duration)

    return composite


def create_video(script: dict, audio_files: list[str]) -> str:
    """
    Create the full YouTube Short video.
    Returns path to the final video file.
    """
    print("[*] Fetching stock footage...")
    search_terms = ["data technology", "coding computer", "server room"]
    stock_clips_paths = fetch_stock_footage(
        query="technology data server",
        num_clips=3,
    )

    # Fallback: create colored backgrounds if no stock footage
    if not stock_clips_paths:
        print("[WARN] No stock footage found. Using gradient backgrounds.")
        stock_clips_paths = _create_fallback_backgrounds()

    # Load stock clips
    stock_clips = []
    for p in stock_clips_paths:
        try:
            clip = VideoFileClip(p)
            stock_clips.append(clip)
        except Exception as e:
            print(f"[WARN] Could not load {p}: {e}")

    if not stock_clips:
        stock_clips = [_create_color_clip(color) for color in [(20, 30, 60), (10, 40, 30), (40, 20, 50)]]

    # Build segments
    all_texts = [script["hook"]] + script["segments"]
    segments = []

    for i, (text, audio_path) in enumerate(zip(all_texts, audio_files)):
        bg = stock_clips[i % len(stock_clips)]
        y_pos = "center"
        fontsize = config.FONT_SIZE + 10 if i == 0 else config.FONT_SIZE  # larger hook
        segment = _build_segment_clip(bg, text, audio_path, start_y=y_pos)
        segments.append(segment)

    # Concatenate all segments
    print("[*] Compositing final video...")
    final = concatenate_videoclips(segments, method="compose")

    # Pad or trim to hit the target duration (default 55s)
    target = config.VIDEO_DURATION
    if final.duration < target:
        # Extend the last segment's background to fill remaining time
        pad_duration = target - final.duration
        pad = ColorClip(
            size=(config.VIDEO_WIDTH, config.VIDEO_HEIGHT),
            color=(0, 0, 0),
            duration=pad_duration,
        )
        final = concatenate_videoclips([final, pad], method="compose")
    elif final.duration > target:
        final = final.subclip(0, target)

    output_path = os.path.join(config.OUTPUT_DIR, "short.mp4")
    final.write_videofile(
        output_path,
        fps=config.VIDEO_FPS,
        codec="libx264",
        audio_codec="aac",
        preset="fast",
        threads=4,
    )

    # Cleanup
    for clip in stock_clips:
        clip.close()
    final.close()

    print(f"[*] Video saved to {output_path}")
    return output_path


def _create_fallback_backgrounds() -> list[str]:
    """Create simple colored background videos as fallback."""
    paths = []
    colors = [(15, 25, 55), (10, 40, 35), (45, 15, 50)]
    for i, color in enumerate(colors):
        path = os.path.join(config.TEMP_DIR, f"bg_{i}.mp4")
        clip = ColorClip(
            size=(config.VIDEO_WIDTH, config.VIDEO_HEIGHT),
            color=color,
            duration=15,
        )
        clip.write_videofile(path, fps=config.VIDEO_FPS, codec="libx264", logger=None)
        clip.close()
        paths.append(path)
    return paths


def _create_color_clip(color: tuple, duration: float = 15) -> VideoFileClip:
    """Create a simple color background clip."""
    return ColorClip(
        size=(config.VIDEO_WIDTH, config.VIDEO_HEIGHT),
        color=color,
        duration=duration,
    )
