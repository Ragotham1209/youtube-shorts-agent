"""
Create YouTube Shorts video: stock footage background + text overlay + voiceover.
Compatible with moviepy 2.x
"""
import os
import requests
import textwrap

try:
    from moviepy.editor import (
        VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip,
        concatenate_videoclips, ColorClip,
    )
    MOVIEPY_V2 = False
except ImportError:
    from moviepy import (
        VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip,
        concatenate_videoclips, ColorClip,
    )
    MOVIEPY_V2 = True

import config


def fetch_stock_footage(query: str, num_clips: int = 3) -> list[str]:
    """Download vertical stock footage clips from Pexels."""
    headers = {"Authorization": config.PEXELS_API_KEY}
    params = {
        "query": query,
        "orientation": "portrait",
        "size": "medium",
        "per_page": num_clips * 2,
    }
    resp = requests.get(
        "https://api.pexels.com/videos/search", headers=headers, params=params
    )
    resp.raise_for_status()

    downloaded = []
    for vid_data in resp.json().get("videos", []):
        if len(downloaded) >= num_clips:
            break
        files = vid_data.get("video_files", [])
        best = None
        for f in files:
            w = f.get("width", 0)
            h = f.get("height", 0)
            if h > w and h >= 1080:
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


# --- Compatibility helpers for moviepy v1 vs v2 ---

def _set_duration(clip, duration):
    if MOVIEPY_V2:
        return clip.with_duration(duration)
    return clip.set_duration(duration)

def _set_position(clip, pos):
    if MOVIEPY_V2:
        return clip.with_position(pos)
    return clip.set_position(pos)

def _set_audio(clip, audio):
    if MOVIEPY_V2:
        return clip.with_audio(audio)
    return clip.set_audio(audio)

def _set_opacity(clip, opacity):
    if MOVIEPY_V2:
        return clip.with_opacity(opacity)
    return clip.set_opacity(opacity)

def _resize(clip, newsize):
    if MOVIEPY_V2:
        return clip.resized(newsize)
    return clip.resize(newsize)

def _subclip(clip, t1, t2):
    if MOVIEPY_V2:
        return clip.subclipped(t1, t2)
    return clip.subclip(t1, t2)

def _loop(clip, duration):
    return clip.loop(duration=duration)


def _create_text_clip(
    text: str, duration: float, fontsize: int = config.FONT_SIZE, position: str = "center"
) -> TextClip:
    """Create a styled text overlay clip."""
    wrapped = textwrap.fill(text, width=22)

    if MOVIEPY_V2:
        txt_clip = TextClip(
            text=wrapped,
            font_size=fontsize,
            color=config.FONT_COLOR,
            stroke_color=config.STROKE_COLOR,
            stroke_width=config.STROKE_WIDTH,
            font="/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            method="caption",
            size=(config.VIDEO_WIDTH - 100, None),
        )
    else:
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

    txt_clip = _set_duration(txt_clip, duration)
    txt_clip = _set_position(txt_clip, ("center", position))
    return txt_clip


def _build_segment_clip(bg_clip, text: str, audio_path: str, start_y: str = "center"):
    """Build a single segment: background + text + audio."""
    audio = AudioFileClip(audio_path)
    duration = audio.duration + 0.5

    # Trim or loop background to match audio duration
    if bg_clip.duration < duration:
        bg = _loop(bg_clip, duration)
    else:
        bg = _subclip(bg_clip, 0, duration)

    bg = _resize(bg, (config.VIDEO_WIDTH, config.VIDEO_HEIGHT))

    # Semi-transparent overlay for text readability
    overlay = ColorClip(
        size=(config.VIDEO_WIDTH, config.VIDEO_HEIGHT),
        color=(0, 0, 0),
    )
    overlay = _set_opacity(overlay, 0.4)
    overlay = _set_duration(overlay, duration)

    txt = _create_text_clip(text, duration, position=start_y)

    composite = CompositeVideoClip(
        [bg, overlay, txt], size=(config.VIDEO_WIDTH, config.VIDEO_HEIGHT)
    )
    composite = _set_audio(composite, audio)
    composite = _set_duration(composite, duration)

    return composite


def create_video(script: dict, audio_files: list[str]) -> str:
    """Create the full YouTube Short video."""
    print("[*] Fetching stock footage...")
    stock_clips_paths = fetch_stock_footage(
        query="technology data server",
        num_clips=3,
    )

    if not stock_clips_paths:
        print("[WARN] No stock footage found. Using gradient backgrounds.")
        stock_clips_paths = _create_fallback_backgrounds()

    stock_clips = []
    for p in stock_clips_paths:
        try:
            clip = VideoFileClip(p)
            stock_clips.append(clip)
        except Exception as e:
            print(f"[WARN] Could not load {p}: {e}")

    if not stock_clips:
        stock_clips = [
            _create_color_clip(color)
            for color in [(20, 30, 60), (10, 40, 30), (40, 20, 50)]
        ]

    all_texts = [script["hook"]] + script["segments"]
    segments = []

    for i, (text, audio_path) in enumerate(zip(all_texts, audio_files)):
        bg = stock_clips[i % len(stock_clips)]
        segment = _build_segment_clip(bg, text, audio_path, start_y="center")
        segments.append(segment)

    print("[*] Compositing final video...")
    final = concatenate_videoclips(segments, method="compose")

    # Pad or trim to hit the target duration (default 55s)
    target = config.VIDEO_DURATION
    if final.duration < target:
        pad_duration = target - final.duration
        pad = ColorClip(
            size=(config.VIDEO_WIDTH, config.VIDEO_HEIGHT),
            color=(0, 0, 0),
            duration=pad_duration,
        )
        final = concatenate_videoclips([final, pad], method="compose")
    elif final.duration > target:
        final = _subclip(final, 0, target)

    output_path = os.path.join(config.OUTPUT_DIR, "short.mp4")
    final.write_videofile(
        output_path,
        fps=config.VIDEO_FPS,
        codec="libx264",
        audio_codec="aac",
        preset="fast",
        threads=4,
    )

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


def _create_color_clip(color: tuple, duration: float = 15):
    """Create a simple color background clip."""
    return ColorClip(
        size=(config.VIDEO_WIDTH, config.VIDEO_HEIGHT),
        color=color,
        duration=duration,
    )
