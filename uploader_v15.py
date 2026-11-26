"""
uploader_v15.py — Zero-Touch YouTube Data API v3 Uploader + Thumbnail Setter + Telegram Alert
Also supports checking Google Drive '01 — READY TO PUBLISH' queue for flagship Behind The Curtain episodes!
"""
import os
import json
import urllib.request
import urllib.parse


def send_telegram(text):
    tok = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    cid = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    if not tok or not cid:
        return
    try:
        url = f"https://api.telegram.org/bot{tok}/sendMessage"
        data = urllib.parse.urlencode({"chat_id": cid, "text": text, "parse_mode": "HTML"}).encode("utf-8")
        urllib.request.urlopen(urllib.request.Request(url, data=data, method="POST"), timeout=15)
    except Exception as e:
        print(f"[TELEGRAM WARN] {e}")


def get_google_creds(scopes):
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    creds = Credentials(
        token=None,
        refresh_token=os.environ["GOOGLE_REFRESH_TOKEN"].strip(),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["GOOGLE_CLIENT_ID"].strip(),
        client_secret=os.environ["GOOGLE_CLIENT_SECRET"].strip(),
        scopes=scopes,
    )
    creds.refresh(Request())
    return creds


def get_youtube_service():
    from googleapiclient.discovery import build
    creds = get_google_creds([
        "https://www.googleapis.com/auth/youtube.upload",
        "https://www.googleapis.com/auth/youtube.force-ssl",
    ])
    return build("youtube", "v3", credentials=creds, cache_discovery=False)


def upload_video_to_youtube(mp4_path, title, description, tags, privacy="public", thumbnail_path=None):
    from googleapiclient.http import MediaFileUpload
    yt = get_youtube_service()
    body = {
        "snippet": {
            "title": title[:98],
            "description": description[:4900],
            "tags": tags[:20],
            "categoryId": "27",
            "defaultLanguage": "en",
            "defaultAudioLanguage": "en",
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False,
        },
    }
    media = MediaFileUpload(mp4_path, mimetype="video/mp4", chunksize=8 * 1024 * 1024, resumable=True)
    req = yt.videos().insert(part="snippet,status", body=body, media_body=media)
    resp = None
    while resp is None:
        status, resp = req.next_chunk()
        if status:
            print(f"  [YT UPLOAD] {int(status.progress() * 100)}%", flush=True)
    vid_id = resp["id"]
    print(f"[YOUTUBE LIVE!] https://www.youtube.com/watch?v={vid_id} (privacy={privacy})")

    if thumbnail_path and os.path.exists(thumbnail_path):
        try:
            yt.thumbnails().set(
                videoId=vid_id,
                media_body=MediaFileUpload(thumbnail_path, mimetype="image/jpeg"),
            ).execute()
            print("[THUMBNAIL UPLOADED OK!]")
        except Exception as e:
            print(f"[THUMBNAIL SKIPPED — verify channel phone at youtube.com/verify]: {e}")

    return vid_id
