"""
One-time script to obtain a YouTube OAuth2 refresh token.
Run this locally (not in CI) to authorize your Google account.

Usage:
    pip install google-auth-oauthlib
    python get_youtube_token.py
"""
import json
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def main():
    print("=" * 60)
    print("  YouTube OAuth2 Token Generator")
    print("=" * 60)

    client_id = input("\nEnter your OAuth Client ID: ").strip()
    client_secret = input("Enter your OAuth Client Secret: ").strip()

    client_config = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"],
        }
    }

    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
    credentials = flow.run_local_server(port=8080, prompt="consent")

    print("\n" + "=" * 60)
    print("  SUCCESS! Save these values as GitHub Actions secrets:")
    print("=" * 60)
    print(f"\n  YOUTUBE_CLIENT_ID     = {client_id}")
    print(f"  YOUTUBE_CLIENT_SECRET = {client_secret}")
    print(f"  YOUTUBE_REFRESH_TOKEN = {credentials.refresh_token}")
    print()


if __name__ == "__main__":
    main()
