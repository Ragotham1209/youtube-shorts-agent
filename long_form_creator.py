"""
Create long-form YouTube videos (10-20 min) with screen-recording style visuals.
Uses moviepy 2.x API only. No moviepy.editor dependency.
"""
import os
import asyncio
import edge_tts
from moviepy import (
    ImageClip,
    AudioFileClip,
    CompositeVideoClip,
    concatenate_videoclips,
    ColorClip,
)
import config
from screen_renderer import render_code_frame, render_terminal_frame, render_title_card

LONG_FORM_VOICE = "en-US-AndrewMultilingualNeural"
LONG_FORM_RATE = "-2%"


async def _generate_section_audio(text: str, output_path: str) -> str:
    """Generate audio for a single section."""
    communicate = edge_tts.Communicate(text, LONG_FORM_VOICE, rate=LONG_FORM_RATE)
    await communicate.save(output_path)
    return output_path


def _make_section_clip(frame_path: str, audio_path: str, pad: float = 1.0):
    """Create a video clip from a frame image and audio."""
    audio = AudioFileClip(audio_path)
    duration = audio.duration + pad

    img_clip = ImageClip(frame_path)
    img_clip = img_clip.with_duration(duration)
    img_clip = img_clip.resized((config.VIDEO_WIDTH, config.VIDEO_HEIGHT))
    img_clip = img_clip.with_audio(audio)

    return img_clip


def create_long_video(tutorial: dict) -> str:
    """Create a long-form video from a tutorial script."""
    sections = tutorial["sections"]
    clips = []

    for i, section in enumerate(sections):
        print(f"  Processing section {i + 1}/{len(sections)}: {section.get('heading', 'Title')}")

        section_type = section["type"]
        if section_type == "title_card":
            frame_path = render_title_card(
                section["heading"],
                section.get("subheading", ""),
            )
        elif section_type == "terminal":
            frame_path = render_terminal_frame(
                section["heading"],
                section["content"],
            )
        elif section_type == "code":
            frame_path = render_code_frame(
                section["heading"],
                section["content"],
                section.get("language", "python"),
            )
        else:
            frame_path = render_title_card(section.get("heading", ""), "")

        narration = section.get("narration", "")
        audio_path = os.path.join(config.TEMP_DIR, f"long_section_{i}.mp3")
        asyncio.run(_generate_section_audio(narration, audio_path))

        pad = 2.0 if section_type == "title_card" else 1.5
        clip = _make_section_clip(frame_path, audio_path, pad=pad)
        clips.append(clip)

        if i < len(sections) - 1:
            transition = ColorClip(
                size=(config.VIDEO_WIDTH, config.VIDEO_HEIGHT),
                color=(0, 0, 0),
                duration=0.3,
            )
            clips.append(transition)

    print("[*] Compositing long-form video...")
    final = concatenate_videoclips(clips, method="compose")

    output_path = os.path.join(config.OUTPUT_DIR, "long_form.mp4")
    final.write_videofile(
        output_path,
        fps=config.VIDEO_FPS,
        codec="libx264",
        audio_codec="aac",
        preset="medium",
        threads=4,
    )

    duration_min = final.duration / 60

    for clip in clips:
        clip.close()
    final.close()

    print(f"[*] Long-form video saved: {output_path} ({duration_min:.1f} minutes)")
    return output_path
