#!/usr/bin/env python3
"""
V21 EMPIRE FACEBOOK PUBLISHER — publisher_facebook_v21.py
100% Direct Meta Graph API v24.0 Publisher ($0/mo, ZERO Buffer!) for Behind The Curtain & History Unsealed:
  1) Facebook Reels (9:16 Cinema Shorts -> /{page_id}/video_reels 3-phase rupload + V21 cover)
  2) Facebook Watch Long-Form Documentaries (16:9 12-30m MP4 -> chunked graph-video upload + V21 thumb)
  3) Facebook 1080x1350 Suspense Teaser Posters (/{page_id}/photos)
  4) Facebook 4-Slide 1080x1350 Archival Dossier Carousels (/{page_id}/photos + /feed)
  5) Facebook Viral History Debate Text Polls (/{page_id}/feed)
"""
import json
import os
import time
from pathlib import Path
from typing import List, Optional

import requests

GRAPH_VER = "v24.0"
GRAPH_URL = f"https://graph.facebook.com/{GRAPH_VER}"
GRAPH_VIDEO_URL = f"https://graph-video.facebook.com/{GRAPH_VER}"


def _fb_creds() -> tuple[str, str]:
    return os.environ.get("FB_PAGE_ID", "").strip(), os.environ.get("FB_PAGE_ACCESS_TOKEN", "").strip()


def fb_is_configured() -> bool:
    pid, tok = _fb_creds()
    return bool(pid and tok)


def _check_resp(resp: requests.Response, label: str) -> dict:
    try:
        data = resp.json()
    except Exception:
        data = {"raw": resp.text[:400]}
    if resp.status_code >= 400 or "error" in data:
        raise RuntimeError(f"[FB {label} ERROR {resp.status_code}] {data}")
    return data


def upload_fb_reel(mp4_path: str | Path, title: str, description: str, thumb_path: Optional[str | Path] = None) -> Optional[str]:
    pid, tok = _fb_creds()
    if not (pid and tok):
        print("[FB REEL] Skipped (FB_PAGE_ID / FB_PAGE_ACCESS_TOKEN secrets not set yet)", flush=True)
        return None
    mp4_path = Path(mp4_path)
    desc = f"🎬 {title}\n\n{description}"[:2050]

    r1 = requests.post(f"{GRAPH_URL}/{pid}/video_reels", data={"upload_phase": "start", "access_token": tok}, timeout=60)
    d1 = _check_resp(r1, "REEL_START")
    video_id = d1["video_id"]
    upload_url = d1.get("upload_url") or f"https://rupload.facebook.com/video-upload/{GRAPH_VER}/{video_id}"

    fsize = mp4_path.stat().st_size
    with open(mp4_path, "rb") as fh:
        r2 = requests.post(
            upload_url,
            headers={"Authorization": f"OAuth {tok}", "offset": "0", "file_size": str(fsize)},
            data=fh,
            timeout=300,
        )
    _check_resp(r2, "REEL_UPLOAD")

    r3 = requests.post(
        f"{GRAPH_URL}/{pid}/video_reels",
        data={"upload_phase": "finish", "video_id": video_id, "video_state": "PUBLISHED", "description": desc, "access_token": tok},
        timeout=120,
    )
    _check_resp(r3, "REEL_FINISH")
    print(f"[FB REEL LIVE!] video_id={video_id} | page={pid}", flush=True)

    if thumb_path and Path(thumb_path).exists():
        for attempt in range(2):
            try:
                time.sleep(2.5 if attempt == 0 else 4.0)
                with open(thumb_path, "rb") as tfh:
                    rt = requests.post(
                        f"{GRAPH_URL}/{video_id}/thumbnails",
                        data={"is_preferred": "true", "access_token": tok},
                        files={"source": (Path(thumb_path).name, tfh, "image/jpeg")},
                        timeout=90,
                    )
                if rt.status_code < 400 and "error" not in rt.text:
                    print(f"[FB REEL COVER OK!] video_id={video_id}", flush=True)
                    break
            except Exception as e:
                print(f"[FB REEL COVER WARN attempt {attempt+1}]: {e}", flush=True)
    return video_id


def upload_fb_long_video(mp4_path: str | Path, title: str, description: str, thumb_path: Optional[str | Path] = None) -> Optional[str]:
    pid, tok = _fb_creds()
    if not (pid and tok):
        print("[FB LONG VIDEO] Skipped (FB_PAGE_ID / FB_PAGE_ACCESS_TOKEN secrets not set yet)", flush=True)
        return None
    mp4_path = Path(mp4_path)
    fsize = mp4_path.stat().st_size
    endpoint = f"{GRAPH_VIDEO_URL}/{pid}/videos"

    r1 = requests.post(endpoint, data={"upload_phase": "start", "file_size": str(fsize), "access_token": tok}, timeout=60)
    d1 = _check_resp(r1, "VIDEO_START")
    session_id = d1["upload_session_id"]
    video_id = d1["video_id"]
    start_off = int(d1.get("start_offset", 0))
    end_off = int(d1.get("end_offset", fsize))

    with open(mp4_path, "rb") as fh:
        while start_off < fsize:
            fh.seek(start_off)
            chunk = fh.read(max(1, end_off - start_off))
            r2 = requests.post(
                endpoint,
                data={"upload_phase": "transfer", "upload_session_id": session_id, "start_offset": str(start_off), "access_token": tok},
                files={"video_file_chunk": ("chunk.mp4", chunk, "application/octet-stream")},
                timeout=300,
            )
            d2 = _check_resp(r2, "VIDEO_TRANSFER")
            start_off = int(d2.get("start_offset", fsize))
            end_off = int(d2.get("end_offset", fsize))
            print(f"  [FB DOC UPLOAD] {min(100, int(start_off * 100 / max(1, fsize)))}%", flush=True)

    r3 = requests.post(
        endpoint,
        data={
            "upload_phase": "finish",
            "upload_session_id": session_id,
            "title": title[:100],
            "description": description[:4500],
            "published": "true",
            "access_token": tok,
        },
        timeout=120,
    )
    _check_resp(r3, "VIDEO_FINISH")
    print(f"[FB LONG DOC LIVE!] video_id={video_id} | '{title[:70]}'", flush=True)

    if thumb_path and Path(thumb_path).exists():
        for attempt in range(2):
            try:
                time.sleep(3.5 if attempt == 0 else 5.0)
                with open(thumb_path, "rb") as tfh:
                    rt = requests.post(
                        f"{GRAPH_URL}/{video_id}/thumbnails",
                        data={"is_preferred": "true", "access_token": tok},
                        files={"source": (Path(thumb_path).name, tfh, "image/jpeg")},
                        timeout=90,
                    )
                if rt.status_code < 400 and "error" not in rt.text:
                    print(f"[FB DOC THUMB OK!] video_id={video_id}", flush=True)
                    break
            except Exception as e:
                print(f"[FB DOC THUMB WARN attempt {attempt+1}]: {e}", flush=True)
    return video_id


def publish_fb_photo_post(image_path: str | Path, caption: str) -> Optional[str]:
    pid, tok = _fb_creds()
    if not (pid and tok):
        print("[FB PHOTO] Skipped (FB_PAGE_ID / FB_PAGE_ACCESS_TOKEN secrets not set yet)", flush=True)
        return None
    with open(image_path, "rb") as fh:
        r = requests.post(
            f"{GRAPH_URL}/{pid}/photos",
            data={"caption": caption[:4500], "published": "true", "access_token": tok},
            files={"source": (Path(image_path).name, fh, "image/jpeg")},
            timeout=90,
        )
    d = _check_resp(r, "PHOTO_POST")
    post_id = d.get("post_id") or d.get("id", "")
    print(f"[FB PHOTO POST LIVE!] post_id={post_id}", flush=True)
    return post_id


def publish_fb_carousel(image_paths: List[str | Path], caption: str) -> Optional[str]:
    pid, tok = _fb_creds()
    if not (pid and tok):
        print("[FB CAROUSEL] Skipped (FB_PAGE_ID / FB_PAGE_ACCESS_TOKEN secrets not set yet)", flush=True)
        return None
    media_ids = []
    for p in image_paths:
        with open(p, "rb") as fh:
            r = requests.post(
                f"{GRAPH_URL}/{pid}/photos",
                data={"published": "false", "access_token": tok},
                files={"source": (Path(p).name, fh, "image/jpeg")},
                timeout=90,
            )
        media_ids.append(_check_resp(r, "CAROUSEL_PHOTO")["id"])
    payload = {"message": caption[:4500], "access_token": tok}
    for i, mid in enumerate(media_ids):
        payload[f"attached_media[{i}]"] = json.dumps({"media_fbid": mid})
    d_feed = _check_resp(requests.post(f"{GRAPH_URL}/{pid}/feed", data=payload, timeout=90), "CAROUSEL_FEED")
    print(f"[FB CAROUSEL LIVE!] post_id={d_feed.get('id', '')} ({len(media_ids)} slides)", flush=True)
    return d_feed.get("id", "")


def publish_fb_text_post(message: str) -> Optional[str]:
    pid, tok = _fb_creds()
    if not (pid and tok):
        print("[FB TEXT] Skipped (FB_PAGE_ID / FB_PAGE_ACCESS_TOKEN secrets not set yet)", flush=True)
        return None
    d = _check_resp(requests.post(f"{GRAPH_URL}/{pid}/feed", data={"message": message[:4500], "access_token": tok}, timeout=60), "TEXT_POST")
    print(f"[FB TEXT POST LIVE!] post_id={d.get('id', '')}", flush=True)
    return d.get("id", "")
