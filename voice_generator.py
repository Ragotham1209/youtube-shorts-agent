"""
Generate voiceover audio using Edge TTS (free, high quality).
"""
import asyncio
import os
import edge_tts
import config


# Natural-sounding English voices
VOICE = "en-US-AndrewMultilingualNeural"  # clear male voice, great for tech
RATE = "+5%"  # slightly faster for Shorts pacing


async def _generate_audio(text: str, output_path: str) -> str:
    """Generate audio file from text using Edge TTS."""
    communicate = edge_tts.Communicate(text, VOICE, rate=RATE)
    await communicate.save(output_path)
    return output_path


def generate_voiceover(script: dict) -> list[str]:
    """
    Generate individual audio files for each segment of the script.
    Returns list of audio file paths.
    """
    audio_files = []

    # Generate hook audio
    hook_path = os.path.join(config.TEMP_DIR, "hook.mp3")
    asyncio.run(_generate_audio(script["hook"], hook_path))
    audio_files.append(hook_path)

    # Generate segment audios
    for i, segment in enumerate(script["segments"]):
        seg_path = os.path.join(config.TEMP_DIR, f"segment_{i}.mp3")
        asyncio.run(_generate_audio(segment, seg_path))
        audio_files.append(seg_path)

    return audio_files


def generate_full_voiceover(script: dict) -> str:
    """
    Generate a single audio file with the full script narration.
    Returns path to the audio file.
    """
    full_text = script["hook"] + ". " + ". ".join(script["segments"])
    output_path = os.path.join(config.TEMP_DIR, "full_voiceover.mp3")
    asyncio.run(_generate_audio(full_text, output_path))
    return output_path
