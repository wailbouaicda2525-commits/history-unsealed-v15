#!/usr/bin/env python3
"""
Retroactively repairs ALL already-published YouTube Shorts on this channel that have a
custom 1280x720 thumbnail (`maxres`) but are missing `shortsAspectRatio` (`sardefault.jpg`)
because YouTube had not finished processing when `thumbnails().set` originally fired.
"""
import io, os, re, time, requests
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

def build_yt():
    cid = os.environ.get("YOUTUBE_CLIENT_ID") or os.environ.get("YT_CLIENT_ID")
    csec = os.environ.get("YOUTUBE_CLIENT_SECRET") or os.environ.get("YT_CLIENT_SECRET")
    rtok = os.environ.get("YOUTUBE_REFRESH_TOKEN") or os.environ.get("YT_REFRESH_TOKEN")
    creds = Credentials(token=None, refresh_token=rtok, token_uri="https://oauth2.googleapis.com/token", client_id=cid, client_secret=csec)
    creds.refresh(Request())
    return build("youtube", "v3", credentials=creds, cache_discovery=False)

def dur_secs(iso):
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso or "")
    if not m: return 9999
    return int(m.group(1) or 0)*3600 + int(m.group(2) or 0)*60 + int(m.group(3) or 0)

def main():
    yt = build_yt()
    ch = yt.channels().list(part="contentDetails,snippet", mine=True).execute()["items"][0]
    cname = ch["snippet"]["title"]
    uploads_pl = ch["contentDetails"]["relatedPlaylists"]["uploads"]
    print(f"=== AUDITING SHORTS MINIATURES ON: {cname} ===", flush=True)

    vids = []
    pl = yt.playlistItems().list(part="contentDetails", playlistId=uploads_pl, maxResults=35).execute()
    vids = [it["contentDetails"]["videoId"] for it in pl.get("items", [])]
    if not vids:
        print("No videos found.")
        return

    details = yt.videos().list(part="snippet,contentDetails", id=",".join(vids)).execute().get("items", [])
    fixed = 0
    already_ok = 0
    for v in details:
        vid = v["id"]
        dsec = dur_secs(v["contentDetails"].get("duration"))
        title = v["snippet"].get("title", "")[:55]
        thumbs = v["snippet"].get("thumbnails", {})
        if dsec > 185:
            continue  # Long-form video, not a Short
        if "shortsAspectRatio" in thumbs:
            already_ok += 1
            print(f"  [OK] {vid} ({dsec}s) | ALREADY HAS sardefault.jpg | {title}", flush=True)
            continue
        # Missing shortsAspectRatio! Re-upload its OWN maxres/high custom miniature right now!
        src_url = (thumbs.get("maxres") or thumbs.get("standard") or thumbs.get("high") or {}).get("url")
        if not src_url:
            print(f"  [SKIP] {vid} no source thumb URL", flush=True)
            continue
        img_bytes = requests.get(src_url, timeout=20).content
        media = MediaIoBaseUpload(io.BytesIO(img_bytes), mimetype="image/jpeg", resumable=False)
        yt.thumbnails().set(videoId=vid, media_body=media).execute()
        time.sleep(3)
        chk = yt.videos().list(part="snippet", id=vid).execute()["items"][0]["snippet"]["thumbnails"]
        has_sar = "shortsAspectRatio" in chk
        print(f"  [FIXED LIVE!] {vid} ({dsec}s) | shortsAspectRatio={has_sar} | {title}", flush=True)
        fixed += 1
        time.sleep(1.5)
    print(f"=== DONE ({cname}): ALREADY_OK={already_ok} | FIXED_LIVE={fixed} ===", flush=True)

if __name__ == "__main__":
    main()
