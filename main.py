#!/usr/bin/env python3
"""
YouTube Agent - Main Orchestrator
Supports both Shorts (daily) and Long-form (weekly) video generation.

Usage:
    python main.py                  # Generate & upload a Short
    python main.py --long-form      # Generate & upload a long-form video
    python main.py --dry-run        # Generate script only, no video
    python main.py --no-upload      # Generate video but skip upload
"""
import os
import sys
import json
import shutil
from datetime import datetime

import config
from content_generator import generate_script
from voice_generator import generate_voiceover
from video_creator import create_video
from youtube_uploader import upload_video

HISTORY_FILE = os.path.join(config.BASE_DIR, "topic_history.json")
LONG_HISTORY_FILE = os.path.join(config.BASE_DIR, "long_topic_history.json")


def load_history(path: str = HISTORY_FILE) -> list[str]:
    """Load previously used topic titles."""
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return []


def save_history(history: list[str], path: str = HISTORY_FILE):
    """Save topic history."""
    with open(path, "w") as f:
        json.dump(history[-100:], f, indent=2)


def cleanup():
    """Remove temporary files."""
    if os.path.exists(config.TEMP_DIR):
        shutil.rmtree(config.TEMP_DIR)
        os.makedirs(config.TEMP_DIR, exist_ok=True)


def run_short(dry_run: bool, skip_upload: bool):
    """Generate and upload a YouTube Short."""
    print("\n[1/4] Generating script...")
    history = load_history()
    script = generate_script(used_topics=history)
    print(f"  Title: {script['title']}")
    print(f"  Hook: {script['hook']}")
    for i, seg in enumerate(script["segments"], 1):
        print(f"  [{i}] {seg}")

    if dry_run:
        print("\n[DRY RUN] Script generated. Exiting.")
        return

    print("\n[2/4] Generating voiceover...")
    audio_files = generate_voiceover(script)
    print(f"  Generated {len(audio_files)} audio clips.")

    print("\n[3/4] Creating video...")
    video_path = create_video(script, audio_files)
    print(f"  Video: {video_path}")

    if skip_upload:
        print("\n[4/4] Skipping upload (--no-upload flag).")
    else:
        print("\n[4/4] Uploading to YouTube...")
        if not config.YOUTUBE_REFRESH_TOKEN:
            print("  [ERROR] No YouTube credentials configured. Skipping upload.")
            print("  Run get_youtube_token.py to set up authentication.")
        else:
            description = (
                f"{script['hook']}\n\n"
                + "\n".join(f"• {s}" for s in script["segments"])
            )
            video_id = upload_video(
                video_path=video_path,
                title=script["title"],
                description=description,
                tags=script.get("tags", ["dataengineering"]),
            )
            print(f"  Published: https://youtube.com/shorts/{video_id}")

    history.append(script["title"])
    save_history(history)


def run_long_form(dry_run: bool, skip_upload: bool):
    """Generate and upload a long-form YouTube video."""
    from long_form_content import generate_tutorial
    from long_form_creator import create_long_video

    print("\n[1/4] Generating tutorial script...")
    history = load_history(LONG_HISTORY_FILE)
    tutorial = generate_tutorial(used_topics=history)
    print(f"  Title: {tutorial['title']}")
    print(f"  Description: {tutorial.get('description', '')}")
    print(f"  Sections: {len(tutorial['sections'])}")
    for i, sec in enumerate(tutorial["sections"], 1):
        print(f"  [{i}] {sec['type']}: {sec.get('heading', 'N/A')}")

    if dry_run:
        print("\n[DRY RUN] Tutorial script generated. Exiting.")
        return

    print("\n[2/4] Rendering frames & generating voiceover...")
    # (handled inside create_long_video)

    print("\n[3/4] Creating long-form video...")
    video_path = create_long_video(tutorial)
    print(f"  Video: {video_path}")

    if skip_upload:
        print("\n[4/4] Skipping upload (--no-upload flag).")
    else:
        print("\n[4/4] Uploading to YouTube...")
        if not config.YOUTUBE_REFRESH_TOKEN:
            print("  [ERROR] No YouTube credentials configured. Skipping upload.")
            print("  Run get_youtube_token.py to set up authentication.")
        else:
            description = (
                f"{tutorial.get('description', tutorial['title'])}\n\n"
                "Chapters:\n"
                + "\n".join(
                    f"• {sec.get('heading', 'Section')}"
                    for sec in tutorial["sections"]
                    if sec["type"] != "title_card"
                )
                + "\n\n#DataEngineering #Tutorial #Python"
            )
            video_id = upload_video(
                video_path=video_path,
                title=tutorial["title"],
                description=description,
                tags=tutorial.get("tags", ["dataengineering", "tutorial"]),
            )
            print(f"  Published: https://youtube.com/watch?v={video_id}")

    history.append(tutorial["title"])
    save_history(history, LONG_HISTORY_FILE)


def main():
    long_form = "--long-form" in sys.argv
    mode = "Long-Form Tutorial" if long_form else "YouTube Short"

    print("=" * 60)
    print(f"  YouTube Agent [{mode}] - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    dry_run = "--dry-run" in sys.argv
    skip_upload = "--no-upload" in sys.argv

    try:
        if long_form:
            run_long_form(dry_run, skip_upload)
        else:
            run_short(dry_run, skip_upload)

        print("\n[DONE] Successfully completed!")

    except Exception as e:
        print(f"\n[ERROR] {e}", file=sys.stderr)
        raise
    finally:
        cleanup()


if __name__ == "__main__":
    main()
