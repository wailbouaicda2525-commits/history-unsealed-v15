"""
retrofit_thumbnails_v21.py — One-Shot V21 Unified Miniature Retrofit for ALL Existing YouTube Videos!
Lists all uploaded videos on the authenticated channel (Long-Form + Shorts), fetches verified real
zero-text archival photography for each video's exact historical subject, renders a crisp 1280x720
V21 miniature using renderer_v20_cinema.generate_v20_thumbnail(), and updates every video's thumbnail
live via YouTube Data API v3 (`thumbnails().set`).
"""
import os
import re
import ssl
import json
import time
import argparse
import urllib.parse
import urllib.request

from renderer_v20_cinema import generate_v20_thumbnail, pick_best_thumb_photos
from uploader_v15 import get_youtube_service, send_telegram

SSL_CTX = ssl.create_default_context()
UA = "UnsealedArchivesPress/2.1 (https://github.com/wailbouaicda2525-commits; archival-documentary)"

# Fact-checked, high-CTR miniature overrides for every existing video across CH1 & CH2
CURATED_VIDEO_SPECS = {
    # ===================== CH1: BEHIND THE CURTAIN =====================
    "slZHuN2oS1M": {
        "wiki": ["Operation Paperclip", "Wernher von Braun"],
        "white": "1,600 NAZIS",
        "red": "FOR NASA",
        "pill": "1945",
        "stamp": "TOP SECRET",
        "teaser": "OPERATION PAPERCLIP EXPOSED",
    },
    "UFASu1GdEXU": {
        "wiki": ["June 1962 Alcatraz escape", "Alcatraz Federal Penitentiary"],
        "white": "THEY ESCAPED",
        "red": "ALCATRAZ",
        "pill": "JUN 1962",
        "stamp": "FBI FILE",
        "teaser": "DID THEY REALLY SURVIVE?",
    },
    "GVDungL64vA": {
        "wiki": ["D. B. Cooper", "Boeing 727"],
        "white": "HE JUMPED",
        "red": "WITH $200K",
        "pill": "NOV 1971",
        "stamp": "UNSOLVED",
        "teaser": "THE ONLY UNSOLVED SKYJACKING",
    },
    "kXm0hXh7UlQ": {
        "wiki": ["1983 Soviet nuclear false alarm incident", "Stanislav Petrov"],
        "white": "ONE MAN",
        "red": "STOPPED WW3",
        "pill": "SEP 1983",
        "stamp": "DECLASSIFIED",
        "teaser": "5 MINUTES TO NUCLEAR WAR",
    },
    "BEd7cVf__bk": {
        "wiki": ["Operation Gold", "Berlin Wall"],
        "white": "CIA TUNNEL",
        "red": "UNDER BERLIN",
        "pill": "1955–56",
        "stamp": "CIA ARCHIVE",
        "teaser": "THE KGB KNEW ALL ALONG",
    },
    "ThjCOZuwY9Q": {
        "wiki": ["Checkpoint Charlie", "Operation Gold"],
        "white": "SECRET SPY",
        "red": "TUNNEL",
        "pill": "1954–56",
        "stamp": "TOP SECRET",
        "teaser": "440,000 TAPPED SOVIET CALLS",
    },
    "38E1tY_YJuE": {
        "wiki": ["GSF Explorer", "Project Azorian"],
        "prefer_lead": True,
        "white": "THE CIA STOLE",
        "red": "A SOVIET SUB",
        "pill": "1974",
        "stamp": "CIA ARCHIVE",
        "teaser": "THE $500M SECRET SALVAGE",
    },
    "DosLi1gUL24": {
        "wiki": ["Soviet submarine K-129 (1960)", "Project Azorian"],
        "white": "THE $500M",
        "red": "FAKE SHIP",
        "pill": "1974",
        "stamp": "DECLASSIFIED",
        "teaser": "HOW THE CIA LIFTED K-129",
    },
    "3Vo8RHfifHc": {
        "wiki": ["Red Square", "Soviet Union"],
        "query": "Moscow street Soviet Union 1970s winter",
        "white": "DAILY LIFE IN",
        "red": "THE USSR",
        "pill": "1950–85",
        "stamp": "ARCHIVE FILE",
        "teaser": "BEHIND THE IRON CURTAIN",
    },
    # ===================== CH2: HISTORY UNSEALED =====================
    "NJxEgi5Fhwo": {
        "wiki": ["Tehran Conference"],
        "white": "THE SECRET",
        "red": "SUMMIT",
        "pill": "NOV 1943",
        "stamp": "UNSEALED",
        "teaser": "ROOSEVELT'S WWII GAMBLE",
    },
    "bU53ZBgVAsg": {
        "wiki": ["Lyndon B. Johnson"],
        "prefer_lead": True,
        "white": "THE SPEECH",
        "red": "THAT SAVED US",
        "pill": "NOV 1963",
        "stamp": "ARCHIVED",
        "teaser": "5 DAYS AFTER DALLAS",
    },
    "X1F3kfpiSR0": {
        "wiki": ["Battle of Ia Drang", "Robert McNamara"],
        "prefer_lead": True,
        "white": "400,000",
        "red": "MORE TROOPS",
        "pill": "NOV 1965",
        "stamp": "DECLASSIFIED",
        "teaser": "THE PENTAGON MEMO EXPOSED",
    },
    "wEZIR5kjd08": {
        "wiki": ["Bell UH-1 Iroquois", "Vietnam War"],
        "query": "UH-1 Huey helicopter Vietnam rescue troops",
        "white": "ONE PILOT",
        "red": "AGAINST ALL",
        "pill": "NOV 1968",
        "stamp": "VERIFIED",
        "teaser": "THE IMPOSSIBLE RESCUE MISSION",
    },
    "kNAYEIgYFxg": {
        "wiki": ["Apollo 11", "Buzz Aldrin"],
        "white": "12 SECONDS",
        "red": "FROM ABORT",
        "pill": "JUL 1969",
        "stamp": "NASA ARCHIVE",
        "teaser": "THE 1202 ALARM ON APOLLO 11",
    },
    "cB4sljOHqo4": {
        "wiki": ["Hull note", "Cordell Hull", "Attack on Pearl Harbor"],
        "white": "THE NOTE THAT",
        "red": "STARTED WAR",
        "pill": "NOV 1941",
        "stamp": "UNSEALED",
        "teaser": "11 DAYS BEFORE PEARL HARBOR",
    },
    "YncrLOYQhDA": {
        "wiki": ["Attack on Pearl Harbor", "USS Arizona"],
        "prefer_lead": True,
        "white": "7:55 AM",
        "red": "PEARL HARBOR",
        "pill": "DEC 1941",
        "stamp": "ARCHIVE FILE",
        "teaser": "MINUTE BY MINUTE DOCUMENTARY",
    },
    "4YLrH9wTdr0": {
        "wiki": ["Iran–Contra affair", "Ronald Reagan", "Oliver North"],
        "white": "WHITE HOUSE",
        "red": "COVER-UP",
        "pill": "NOV 1986",
        "stamp": "UNSEALED",
        "teaser": "INSIDE THE IRAN-CONTRA SCANDAL",
    },
}


def _get_json(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout, context=SSL_CTX) as r:
        return json.loads(r.read().decode("utf-8"))


def _download_img(url, out_path):
    try:
        # Strip Wikipedia tracking query string if present
        clean_u = url.split("?")[0] if "upload.wikimedia.org" in url else url
        req = urllib.request.Request(clean_u, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=25, context=SSL_CTX) as r:
            data = r.read()
        if len(data) < 10000:
            return None
        with open(out_path, "wb") as f:
            f.write(data)
        return out_path
    except Exception:
        return None


def _is_bad_wiki_img(url):
    """Inspect ONLY the filename (never the domain!) to filter SVGs, flags, logos, diagrams, maps."""
    path = urllib.parse.urlparse(str(url or "")).path.lower()
    fname = path.rsplit("/", 1)[-1]
    bad_ext = (".svg", ".gif", ".ogg", ".webm", ".pdf", ".tif", ".tiff", ".webp")
    if any(fname.endswith(e) for e in bad_ext):
        return True
    bad_kw = (
        "flag_of", "coat_of_arms", "seal_of", "logo", "emblem", "insignia", "patch",
        "map_", "_map", "location", "locator", "signature", "diagram", "chart",
        "icon", "commons-logo", "wikimedia-logo", "stamp_", "coin", "ribbon", "poster",
        "newspaper", "document", "memo", "letter", "page_", "cover",
    )
    return any(b in fname for b in bad_kw)


def fetch_archival_photos_for_video(vid_id, title, spec, work_dir):
    """Fetch 2-5 crisp, zero-text real archival photographs from Wikipedia / Wikimedia Commons."""
    os.makedirs(work_dir, exist_ok=True)
    saved = []
    urls_seen = set()

    def _try_url(u):
        if not u:
            return
        if u.startswith("//"):
            u = "https:" + u
        base_u = u.split("?")[0]
        if base_u in urls_seen or _is_bad_wiki_img(base_u):
            return
        urls_seen.add(base_u)
        out_p = os.path.join(work_dir, f"{vid_id}_img_{len(saved)}.jpg")
        if _download_img(base_u, out_p):
            saved.append(out_p)
            time.sleep(0.15)

    wiki_titles = list(spec.get("wiki") or [])
    if not wiki_titles:
        clean_q = re.sub(r"#shorts|\([^)]*\)", "", title, flags=re.I).strip()
        try:
            sr = _get_json(
                "https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode({
                    "action": "query", "list": "search", "srsearch": clean_q,
                    "srlimit": 2, "format": "json"
                })
            )
            for hit in sr.get("query", {}).get("search", []):
                wiki_titles.append(hit["title"])
        except Exception:
            pass

    for wt in wiki_titles:
        if len(saved) >= 4:
            break
        try:
            enc = urllib.parse.quote(wt.replace(" ", "_"))
            js = _get_json(f"https://en.wikipedia.org/api/rest_v1/page/summary/{enc}")
            for k in ("originalimage", "thumbnail"):
                src = (js.get(k) or {}).get("source")
                if src:
                    _try_url(src)
                    if saved:
                        break
        except Exception:
            pass

        try:
            enc = urllib.parse.quote(wt.replace(" ", "_"))
            ml = _get_json(f"https://en.wikipedia.org/api/rest_v1/page/media-list/{enc}")
            for item in ml.get("items", [])[:14]:
                if len(saved) >= 5:
                    break
                if item.get("type") != "image":
                    continue
                srcset = item.get("srcset") or []
                u = srcset[-1]["src"] if srcset else (item.get("original") or {}).get("source")
                _try_url(u)
        except Exception:
            pass

    if len(saved) < 2 or spec.get("query"):
        q = spec.get("query") or re.sub(r"#shorts|\([^)]*\)", "", title, flags=re.I).strip()
        try:
            cm = _get_json(
                "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode({
                    "action": "query", "generator": "search", "gsrsearch": f"{q} filetype:bitmap",
                    "gsrnamespace": 6, "gsrlimit": 8, "prop": "imageinfo",
                    "iiprop": "url|size|mime", "iiurlwidth": 1280, "format": "json"
                })
            )
            for pg in (cm.get("query", {}).get("pages") or {}).values():
                if len(saved) >= 5:
                    break
                ii = (pg.get("imageinfo") or [{}])[0]
                if ii.get("width", 0) >= 640 and "jpeg" in (ii.get("mime") or "").lower():
                    _try_url(ii.get("thumburl") or ii.get("url"))
        except Exception:
            pass

    return saved


def _auto_spec_from_title(title, is_btc):
    clean = re.sub(r"#shorts|\(19\d\d[^)]*\)|\(20\d\d[^)]*\)", "", title, flags=re.I).strip(" :–—-")
    m_yr = re.search(r"\b(1[5-9]\d{2}|20[0-2]\d)\b", title)
    yr = m_yr.group(1) if m_yr else ("SECRET" if is_btc else "ARCHIVE")
    words = [w for w in re.sub(r"[^A-Za-z0-9$\-'\s]", " ", clean).split() if len(w) > 1]
    if len(words) >= 4:
        w_part = " ".join(words[:2]).upper()
        r_part = " ".join(words[2:4]).upper()
    elif len(words) >= 2:
        w_part = words[0].upper()
        r_part = " ".join(words[1:3]).upper()
    else:
        w_part = "THE UNTOLD"
        r_part = "TRUTH"
    return {
        "wiki": [],
        "white": w_part[:16],
        "red": r_part[:13],
        "pill": yr[:9],
        "stamp": "DECLASSIFIED" if is_btc else "UNSEALED",
        "teaser": "THE DECLASSIFIED ARCHIVE" if is_btc else "FULL ARCHIVAL RECORD",
    }


def list_all_channel_videos(yt):
    ch = yt.channels().list(mine=True, part="contentDetails,snippet").execute()
    items = ch.get("items") or []
    if not items:
        raise RuntimeError("No authenticated YouTube channel found!")
    uploads_pl = items[0]["contentDetails"]["relatedPlaylists"]["uploads"]
    ch_title = items[0]["snippet"]["title"]

    videos = []
    page_tok = None
    while True:
        res = yt.playlistItems().list(
            playlistId=uploads_pl,
            part="snippet,contentDetails",
            maxResults=50,
            pageToken=page_tok,
        ).execute()
        for it in res.get("items", []):
            vid_id = it["contentDetails"]["videoId"]
            title = it["snippet"]["title"]
            videos.append((vid_id, title))
        page_tok = res.get("nextPageToken")
        if not page_tok:
            break
    return ch_title, videos


def main():
    cfg = json.load(open("channel_config.json", encoding="utf-8"))
    brand = cfg["channel_name"]
    is_btc = (cfg["mode"] == "behind_the_curtain")

    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="Render miniatures locally without calling YouTube API")
    ap.add_argument("--only-curated", action="store_true", help="Dry-run test curated videos for this channel")
    ap.add_argument("--work-dir", default="/tmp/v21_retrofit")
    args = ap.parse_args()

    os.makedirs(args.work_dir, exist_ok=True)
    dry = args.dry_run or (os.environ.get("DRY_RUN", "false").lower() == "true")

    if dry and args.only_curated:
        ch1_ids = ["slZHuN2oS1M", "UFASu1GdEXU", "GVDungL64vA", "kXm0hXh7UlQ", "BEd7cVf__bk", "ThjCOZuwY9Q", "38E1tY_YJuE", "DosLi1gUL24", "3Vo8RHfifHc"]
        ch2_ids = ["NJxEgi5Fhwo", "bU53ZBgVAsg", "X1F3kfpiSR0", "wEZIR5kjd08", "kNAYEIgYFxg", "cB4sljOHqo4", "YncrLOYQhDA", "4YLrH9wTdr0"]
        vids = [(vid, CURATED_VIDEO_SPECS[vid]["teaser"]) for vid in (ch1_ids if is_btc else ch2_ids)]
        yt = None
    else:
        yt = get_youtube_service()
        ch_title, vids = list_all_channel_videos(yt)
        print(f"=== V21 MINIATURE RETROFIT: {brand} ({ch_title}) — {len(vids)} videos found ===")

    MediaFileUpload = None
    if not dry:
        from googleapiclient.http import MediaFileUpload

    ok_count, skip_count, err_count = 0, 0, 0
    for idx, (vid_id, title) in enumerate(vids, 1):
        spec = CURATED_VIDEO_SPECS.get(vid_id) or _auto_spec_from_title(title, is_btc)
        photos = fetch_archival_photos_for_video(vid_id, title, spec, args.work_dir)
        if not photos:
            print(f"  ⚠️ [{idx}/{len(vids)}] No clean archival photo found for {vid_id} ({title[:40]}), skipping.")
            skip_count += 1
            continue
        if spec.get("prefer_lead") and photos:
            hero = photos[0]
            second = photos[1] if len(photos) > 1 else hero
        else:
            hero, second = pick_best_thumb_photos(photos)
        out_jpg = os.path.join(args.work_dir, f"thumb_{vid_id}.jpg")
        generate_v20_thumbnail(
            hero, second, brand,
            spec["white"], spec["red"], spec["stamp"], out_jpg,
            center_pill=spec["pill"], teaser=spec["teaser"],
        )

        if dry:
            print(f"  [{idx}/{len(vids)}] DRY-RUN OK: {vid_id} -> {spec['white']} / {spec['red']} ({len(photos)} photos, best={os.path.basename(hero)})")
            ok_count += 1
            continue

        try:
            yt.thumbnails().set(
                videoId=vid_id,
                media_body=MediaFileUpload(out_jpg, mimetype="image/jpeg"),
            ).execute()
            print(f"  ✅ [{idx}/{len(vids)}] UPDATED LIVE: {vid_id} | {title[:55]}")
            ok_count += 1
            time.sleep(0.8)
        except Exception as e:
            emsg = str(e)
            if "forbidden" in emsg.lower() or "403" in emsg or "shorts" in emsg.lower():
                print(f"  ⚠️ [{idx}/{len(vids)}] SKIPPED (YT Shorts/Verify restriction): {vid_id} -> {emsg[:120]}")
                skip_count += 1
            else:
                print(f"  ❌ [{idx}/{len(vids)}] ERROR: {vid_id} -> {emsg[:140]}")
                err_count += 1

    print(f"\n=== RETROFIT SUMMARY ({brand}) === Updated={ok_count} | Skipped={skip_count} | Errors={err_count}")
    if not dry:
        send_telegram(
            f"🎨🔥 <b>{brand} — V21 MINIATURE RETROFIT COMPLETE!</b>\n"
            f"✅ Updated Live: <b>{ok_count}</b> / {len(vids)} videos\n"
            f"⚠️ Skipped: {skip_count} | ❌ Errors: {err_count}"
        )


if __name__ == "__main__":
    main()
