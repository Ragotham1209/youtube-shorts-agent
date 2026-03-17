#!/usr/bin/env python3
"""
YouTube Shorts Agent - Main Orchestrator
Generates and uploads a Data Engineering YouTube Short.
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


def load_history() -> list[str]:
    """Load previously used topic titles."""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    return []


def save_history(history: list[str]):
    """Save topic history."""
    # Keep last 100 topics
    with open(HISTORY_FILE, "w") as f:
        json.dump(history[-100:], f, indent=2)


def cleanup():
    """Remove temporary files."""
    if os.path.exists(config.TEMP_DIR):
        shutil.rmtree(config.TEMP_DIR)
        os.makedirs(config.TEMP_DIR, exist_ok=True)


def main():
    print("=" * 60)
    print(f"  YouTube Shorts Agent - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    dry_run = "--dry-run" in sys.argv
    skip_upload = "--no-upload" in sys.argv

    try:
        # Step 1: Generate script
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

        # Step 2: Generate voiceover
        print("\n[2/4] Generating voiceover...")
        audio_files = generate_voiceover(script)
        print(f"  Generated {len(audio_files)} audio clips.")

        # Step 3: Create video
        print("\n[3/4] Creating video...")
        video_path = create_video(script, audio_files)
        print(f"  Video: {video_path}")

        # Step 4: Upload to YouTube
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

        # Save topic to history
        history.append(script["title"])
        save_history(history)

        print("\n[DONE] Successfully completed!")

    except Exception as e:
        print(f"\n[ERROR] {e}", file=sys.stderr)
        raise
    finally:
        cleanup()


if __name__ == "__main__":
    main()
