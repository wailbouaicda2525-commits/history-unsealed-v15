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
    refresh_token = (os.environ.get("YOUTUBE_REFRESH_TOKEN") or os.environ.get("GOOGLE_REFRESH_TOKEN") or "").strip()
    client_id = (os.environ.get("YOUTUBE_CLIENT_ID") or os.environ.get("GOOGLE_CLIENT_ID") or "").strip()
    client_secret = (os.environ.get("YOUTUBE_CLIENT_SECRET") or os.environ.get("GOOGLE_CLIENT_SECRET") or "").strip()
    if not (refresh_token and client_id and client_secret):
        raise RuntimeError("Missing YouTube OAuth secrets! Set YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, YOUTUBE_REFRESH_TOKEN.")
    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
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
        is_sh = ("#shorts" in (title or "").lower()) or ("#shorts" in (description or "").lower()) or ("short" in str(video_path).lower())
        _set_thumbnail_with_shorts_guarantee(yt, vid_id, thumbnail_path, is_short=is_sh)

    return vid_id


def _set_thumbnail_with_shorts_guarantee(yt, vid_id: str, thumbnail_path: str, is_short: bool = False) -> bool:
    """
    Waits until YouTube finishes video processing (`processingStatus == 'succeeded'`)
    BEFORE calling `thumbnails().set`, and for Shorts explicitly verifies that YouTube
    generated `shortsAspectRatio` (`sardefault.jpg`, the exact image shown on `/shorts`!).
    Retries automatically if YouTube's Shorts pipeline hasn't registered `sardefault.jpg` yet.
    """
    import time as _t
    from googleapiclient.http import MediaFileUpload as _MFU

    # 1) Wait for processingStatus == 'succeeded' (prevents YouTube dropping shortsAspectRatio!)
    print(f"  [YT THUMB] Waiting for YouTube processing on {vid_id}...", flush=True)
    for poll in range(22):  # up to ~176s
        try:
            info = yt.videos().list(part="processingDetails,contentDetails", id=vid_id).execute()
            items = info.get("items", [])
            if items:
                pstat = items[0].get("processingDetails", {}).get("processingStatus", "")
                if pstat == "succeeded":
                    print(f"  [YT THUMB] Processing succeeded on poll #{poll+1} — settling 8s for Shorts pipeline...", flush=True)
                    _t.sleep(8)
                    break
                if pstat in ("failed", "terminated"):
                    print(f"  [YT THUMB] Processing status={pstat}", flush=True)
                    break
        except Exception as pe:
            print(f"  [YT THUMB] Poll warning: {pe}", flush=True)
        _t.sleep(8)

    # 2) Upload thumbnail & verify `shortsAspectRatio` (sardefault.jpg) for Shorts!
    ok = False
    max_attempts = 4 if is_short else 2
    for attempt in range(1, max_attempts + 1):
        try:
            yt.thumbnails().set(
                videoId=vid_id,
                media_body=_MFU(str(thumbnail_path), mimetype="image/jpeg"),
            ).execute()
            ok = True
            if not is_short:
                print(f"  [YT THUMB OK!] Set custom 16:9 thumbnail on {vid_id}", flush=True)
                return True
            _t.sleep(5)
            chk = yt.videos().list(part="snippet", id=vid_id).execute()
            thumbs = (chk.get("items") or [{}])[0].get("snippet", {}).get("thumbnails", {})
            if "shortsAspectRatio" in thumbs:
                print(f"  [YT SHORTS MINIATURE VERIFIED OK!] shortsAspectRatio (sardefault.jpg) LIVE on {vid_id} (attempt {attempt})", flush=True)
                return True
            print(f"  [YT SHORTS MINIATURE] attempt {attempt}/{max_attempts}: sardefault.jpg not ready yet — retrying in 20s...", flush=True)
            _t.sleep(20)
        except Exception as e:
            print(f"  [YT THUMB] Attempt {attempt} warning: {e}", flush=True)
            _t.sleep(10)
    return ok
