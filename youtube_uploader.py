"""
Upload videos to YouTube using the YouTube Data API v3.
"""
import os
import json
import httplib2
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
import config

YOUTUBE_UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload"
YOUTUBE_API_SERVICE = "youtube"
YOUTUBE_API_VERSION = "v3"


def _get_credentials() -> Credentials:
    """Build OAuth2 credentials from refresh token."""
    creds = Credentials(
        token=None,
        refresh_token=config.YOUTUBE_REFRESH_TOKEN,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=config.YOUTUBE_CLIENT_ID,
        client_secret=config.YOUTUBE_CLIENT_SECRET,
        scopes=[YOUTUBE_UPLOAD_SCOPE],
    )
    return creds


def upload_video(
    video_path: str,
    title: str,
    description: str,
    tags: list[str],
    category_id: str = config.YOUTUBE_CATEGORY_ID,
) -> str:
    """
    Upload a video to YouTube.
    Returns the video ID of the uploaded video.
    """
    credentials = _get_credentials()
    youtube = build(YOUTUBE_API_SERVICE, YOUTUBE_API_VERSION, credentials=credentials)

    # Append #Shorts to title for YouTube Shorts discovery
    if "#Shorts" not in title:
        title = f"{title} #Shorts"

    # Build description
    full_description = (
        f"{description}\n\n"
        f"#DataEngineering #Shorts #Tech\n"
        f"#{' #'.join(tags[:10])}\n\n"
        "---\n"
        "Daily Data Engineering tips and concepts.\n"
        "Subscribe for more!"
    )

    body = {
        "snippet": {
            "title": title[:100],  # YouTube title limit
            "description": full_description[:5000],
            "tags": tags[:30],
            "categoryId": category_id,
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(
        video_path,
        mimetype="video/mp4",
        resumable=True,
        chunksize=1024 * 1024,  # 1MB chunks
    )

    print(f"[*] Uploading '{title}' to YouTube...")
    request = youtube.videos().insert(
        part=",".join(body.keys()),
        body=body,
        media_body=media,
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"  Upload progress: {int(status.progress() * 100)}%")

    video_id = response["id"]
    print(f"[*] Upload complete! Video ID: {video_id}")
    print(f"    URL: https://youtube.com/shorts/{video_id}")

    return video_id
