"""
longform_v15.py — V15 BEAST ADAPTIVE MASSIVE DEEP SINGLE-TOPIC DOCUMENTARY ENGINE
(12 TO 30 MINUTES NATURAL RUNTIME • 7 TO 15 DEEP CHAPTERS • 1920x1080 24fps • PARALLEL MULTI-CORE RENDER)

Runs automatically EVERY 2 DAYS per channel!
- Dynamically sizes chapter count (7 to 15 chapters -> ~12 to ~30 minutes) based on REAL historical depth
  (zero artificial 15-min cap on massive topics like Apollo 11, Cuban Missile Crisis, Pearl Harbor, Chernobyl;
   zero fluff padding on tighter dossiers!)
- Harvests FULL multi-section Wikipedia article (up to 60,000+ chars of real verified history)
  + 20-32 deduplicated real archival photos across main + linked articles
- Two-stage Free Gemini / Groq Showrunner (1 Master Blueprint + 1 focused call per chapter with cliffhanger
  continuity — prevents JSON truncation on 4,000+ word 28-minute scripts!), plus rich deterministic fallback
- Renders chapters in PARALLEL across CPU cores (3 workers on GitHub Actions 4-vCPU runner -> ~18-24 min
  even for a 28-30 min 1080p film!) with `show_outro=True` ONLY on the final chapter
- Losslessly concatenates into a single 1080p master MP4 with YouTube timestamped chapters
- Auto-generates a custom episode-specific V15 High-CTR 1280x720 Thumbnail
- Uploads directly to YouTube + sends rich Telegram alert!
"""
import os
import re
import gc
import json
import time
import shutil
import argparse
import subprocess
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from concurrent.futures import ProcessPoolExecutor, as_completed

try:
    import imageio_ffmpeg
    FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    FFMPEG = shutil.which("ffmpeg") or "ffmpeg"

from scout_v15 import (
    _get_json, _clean_summary, fetch_extra_page_images, download_clean_images,
    stitch_esri_dark_map, _pick_origin_vector, _haversine_km,
    BTC_SECRET_CATALOG, discover_live_wiki_topic_tuple,
)
from scriptwriter_v15 import _extract_json, _trim_words
from voice_engine_v15 import synthesize_voice_v15, mix_cinema_audio_v15
from renderer_v15_beast import render_v15_beast, generate_v15_thumbnail
from uploader_v15 import upload_video_to_youtube, send_telegram

# CHANNEL 2 ('THE DAILY ARCHIVE') DEDICATED 36-EPISODE US/WORLD BLOCKBUSTER DEEP-DIVE CATALOG
# 100% ZERO OVERLAP with Behind The Curtain's Cold War / Covert Ops catalog!
DAILY_ARCHIVE_LONGFORM_CATALOG = [
    ("Assassination of John F. Kennedy", "1963", "DALLAS, TEXAS", 32.7793, -96.8085, "Inside the 6 Seconds in Dallas That Changed America Forever"),
    ("Attack on Pearl Harbor", "1941", "PEARL HARBOR, HAWAII", 21.365, -157.950, "Minute by Minute: The Morning That Dragged America Into WWII"),
    ("Apollo 11", "1969", "HOUSTON, TEXAS", 29.559, -95.090, "1202 Alarm: How Apollo 11 Nearly Aborted Seconds Before Landing"),
    ("Sinking of the Titanic", "1912", "NORTH ATLANTIC OCEAN", 41.732, -49.947, "The Fatal Chain of Mistakes That Sank the Unsinkable Titanic"),
    ("Normandy landings", "1944", "NORMANDY, FRANCE", 49.370, -0.880, "D-Day Declassified: The Logistics and Deception Behind June 6, 1944"),
    ("Cuban Missile Crisis", "1962", "WASHINGTON & HAVANA", 23.114, -82.367, "13 Days on the Brink: How Close the World Came to Nuclear Extinction"),
    ("Watergate scandal", "1972", "WASHINGTON, D.C.", 38.900, -77.055, "The Midnight Break-In That Brought Down an American President"),
    ("Wall Street crash of 1929", "1929", "NEW YORK CITY, USA", 40.707, -74.011, "Black Tuesday: How Wall Street Collapsed and Triggered the Great Depression"),
    ("Space Shuttle Challenger disaster", "1986", "CAPE CANAVERAL, FLORIDA", 28.573, -80.649, "73 Seconds After Liftoff: The Ignored Warnings Behind Challenger"),
    ("Hindenburg disaster", "1937", "LAKEHURST, NEW JERSEY", 40.033, -74.353, "34 Seconds in New Jersey: What Really Destroyed the Hindenburg"),
    ("Sinking of the RMS Lusitania", "1915", "CELTIC SEA, IRELAND", 51.417, -8.550, "18 Minutes to Sink: The Torpedo That Shifted World War I"),
    ("Operation Eagle Claw", "1980", "DESERT ONE, IRAN", 33.073, 55.892, "Desert One: Inside the Secret U.S. Hostage Rescue Mission Gone Wrong"),
    ("Isabella Stewart Gardner Museum theft", "1990", "BOSTON, MASSACHUSETTS", 42.338, -71.099, "81 Minutes in Boston: The $500 Million Art Heist Never Solved"),
    ("Great Brink's Robbery", "1950", "BOSTON, MASSACHUSETTS", 42.366, -71.055, "The Crime of the Century: Inside the 1950 Boston Armored Vault Heist"),
    ("1906 San Francisco earthquake", "1906", "SAN FRANCISCO, CALIFORNIA", 37.775, -122.419, "5:12 AM: The Earthquake and 3-Day Firestorm That Rebuilt San Francisco"),
    ("Great Chicago Fire", "1871", "CHICAGO, ILLINOIS", 41.878, -87.630, "30 Hours of Fire: How Chicago Burned to the Ground in 1871"),
    ("Hoover Dam", "1931", "BLACK CANYON, NEVADA", 36.016, -114.738, "Taming the Colorado: The Extreme Engineering Behind Hoover Dam"),
    ("Panama Canal", "1914", "PANAMA ISTHMUS", 9.080, -79.680, "Dividing Two Continents: The Impossible Construction of the Panama Canal"),
    ("First transcontinental railroad", "1869", "PROMONTORY SUMMIT, UTAH", 41.618, -112.548, "1,912 Miles of Iron: The Race That Connected America Coast to Coast"),
    ("Dyatlov Pass incident", "1959", "URAL MOUNTAINS, USSR", 61.755, 59.463, "Dead Mountain: Re-Examining the Mysterious 1959 Ural Expedition"),
    ("Tunguska event", "1908", "SIBERIA, RUSSIA", 60.886, 101.894, "80 Million Flattened Trees: The Mystery Blast of 1908"),
    ("Roanoke Colony", "1590", "ROANOKE ISLAND, USA", 35.937, -75.710, "CROATOAN: Inside America's Oldest Unsolved Colonial Mystery"),
    ("Discovery of the tomb of Tutankhamun", "1922", "VALLEY OF THE KINGS, EGYPT", 25.740, 32.601, "Wonderful Things: Inside the 1922 Opening of King Tut's Sealed Tomb"),
    ("Eruption of Mount Vesuvius in 79 AD", "79", "POMPEII, ITALY", 40.750, 14.487, "24 Hours in Pompeii: Reconstructing the Ancient Eruption Hour by Hour"),
    ("1980 eruption of Mount St. Helens", "1980", "SKAMANIA COUNTY, WASHINGTON", 46.191, -122.195, "8:32 AM in Washington: The Morning Mount St. Helens Blew Apart"),
    ("Battle of Gettysburg", "1863", "GETTYSBURG, PENNSYLVANIA", 39.812, -77.225, "Three Days in July: Inside the Turning Point of the American Civil War"),
    ("Golden Gate Bridge", "1937", "SAN FRANCISCO, CALIFORNIA", 37.819, -122.478, "Impossible Steel: How Workers Built the Golden Gate Bridge"),
    ("Wright brothers", "1903", "KITTY HAWK, NORTH CAROLINA", 36.017, -75.667, "12 Seconds in North Carolina: How Two Brothers Solved Human Flight"),
    ("Apollo 8", "1968", "HOUSTON, TEXAS", 29.559, -95.090, "Earthrise 1968: NASA's Most Audacious Gamble to Orbit the Moon"),
    ("Voyager program", "1977", "PASADENA, CALIFORNIA", 34.200, -118.171, "The Grand Tour: How Two 1977 Probes Escaped the Solar System"),
    ("Amelia Earhart", "1937", "HOWLAND ISLAND, PACIFIC", 0.806, -176.618, "Last Transmission: Inside the Search for Amelia Earhart"),
    ("California Gold Rush", "1848", "COLOMA, CALIFORNIA", 38.800, -120.892, "1849: How a Single Flake of Gold Transformed the American West"),
    ("Louisiana Purchase", "1803", "NEW ORLEANS, LOUISIANA", 29.951, -90.071, "Three Cents an Acre: The Secret Diplomacy That Doubled America"),
    ("Spirit of St. Louis", "1927", "LONG ISLAND TO PARIS", 40.727, -73.605, "33.5 Hours Alone: Charles Lindbergh's Impossible Flight Across the Atlantic"),
    ("SS Edmund Fitzgerald", "1975", "LAKE SUPERIOR, USA", 46.998, -85.110, "The Wreck of the Edmund Fitzgerald: Reconstructing the Final Storm"),
    ("ARPANET", "1969", "LOS ANGELES, CALIFORNIA", 34.069, -118.443, "LO: Inside the Cold War Computer Network That Invented the Internet"),
]

OUTLINE_SYSTEM_PROMPT = """You are the executive showrunner for a flagship Netflix / LEMMiNO / Johnny Harris style long-form YouTube documentary channel targeting Tier-1 US audiences.
Given a verified historical topic and its real Wikipedia section map, design a gripping multi-chapter documentary blueprint with the EXACT target chapter count requested.
Return ONLY valid JSON:
{
  "video_title": "High-CTR US YouTube Documentary Title <= 82 chars (curiosity gap, authoritative)",
  "thumb_line1": "1-2 GIANT WORDS (ALL CAPS)",
  "thumb_line2": "1-2 GIANT GOLD WORDS (ALL CAPS)",
  "thumb_line3": "1-2 GIANT WORDS (ALL CAPS)",
  "tags": ["history documentary", "full documentary", "us history", "6-10 high-RPM SEO tags"],
  "outline": [
    {"chapter_title": "Punchy Chapter Title <= 42 chars", "focus": "1-sentence investigative angle for this chapter"}
  ]
}"""

CHAPTER_SYSTEM_PROMPT = """You are writing ONE deep narrative chapter of a flagship Netflix / LEMMiNO / Johnny Harris style YouTube documentary targeting Tier-1 US audiences.
RULES:
1. STRICTLY factual and grounded in the provided verified historical dossier. Plain spoken English ONLY inside narration (NO brackets, NO stage directions, NO markdown, NO hashtags).
2. Write 255 to 305 spoken words (~1.8 to 2.1 minutes spoken!) with vivid investigative pacing, exact dates, real names, real numbers, human tension, and a compelling closing line that hooks viewers into the next chapter.
3. Return ONLY valid JSON matching this EXACT schema:
{
  "chapter_title": "Short Punchy Chapter Title <= 42 chars",
  "newspaper_headline": "DRAMATIC 4-6 WORD ARCHIVE HEADLINE (ALL CAPS)",
  "narration": "255-305 word deeply engaging factual chapter narration in plain spoken English.",
  "polaroid_caption": "ARCHIVAL EVIDENCE CAPTION <= 42 chars (ALL CAPS)",
  "stamp_line1": "1-2 WORD RED STAMP (ALL CAPS)",
  "stamp_line2": "SHORT SUB-STAMP <= 22 chars (ALL CAPS)",
  "forensic_header": "CLASSIFIED DOSSIER HEADER <= 38 chars (ALL CAPS)",
  "forensic_lines": [
    "LINE 1: Key verified date/codename <= 46 chars",
    "LINE 2: Key verified turning point <= 46 chars",
    "LINE 3: Key verified aftermath/fact <= 46 chars"
  ],
  "split_left_label": "LABEL A <= 18 chars (ALL CAPS)",
  "split_right_label": "LABEL B <= 18 chars (ALL CAPS)",
  "climax_stat_label": "EYEBROW <= 26 chars (ALL CAPS)",
  "climax_stat_big": "PUNCHY NUMBER/YEAR <= 18 chars (ALL CAPS)",
  "climax_stat_sub": "CONTEXT <= 38 chars (ALL CAPS)"
}"""


def _fetch_full_wiki_sections(wiki_title):
    """Pulls the FULL structured plain-text Wikipedia article (up to 60,000+ chars) split into clean sections."""
    api = "https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode({
        "action": "query", "titles": wiki_title, "prop": "extracts",
        "explaintext": "1", "format": "json"
    })
    data = _get_json(api, timeout=25)
    full_text = ""
    for p in data.get("query", {}).get("pages", {}).values():
        full_text = p.get("extract") or ""
        break

    skip_heads = {
        "see also", "references", "notes", "bibliography", "further reading",
        "external links", "sources", "citations", "footnotes", "explanatory notes",
        "gallery", "in popular culture", "memorials", "commemoration",
    }
    sections = []
    cur_head = "Introduction"
    cur_lines = []
    for line in full_text.splitlines():
        m = re.match(r"^==+\s*(.+?)\s*==+$", line.strip())
        if m:
            body = re.sub(r"\s+", " ", " ".join(cur_lines)).strip()
            if len(body) > 120 and cur_head.lower() not in skip_heads:
                sections.append((cur_head, body))
            cur_head = m.group(1).strip()
            cur_lines = []
        else:
            if line.strip():
                cur_lines.append(line.strip())
    body = re.sub(r"\s+", " ", " ".join(cur_lines)).strip()
    if len(body) > 120 and cur_head.lower() not in skip_heads:
        sections.append((cur_head, body))
    return sections


def _fetch_linked_titles(wiki_title, limit=10):
    try:
        api = "https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode({
            "action": "query", "titles": wiki_title, "prop": "links",
            "plnamespace": "0", "pllimit": "30", "format": "json"
        })
        data = _get_json(api, timeout=12)
        titles = []
        for p in data.get("query", {}).get("pages", {}).values():
            for lk in p.get("links", []):
                t = lk.get("title", "")
                if t and not any(b in t.lower() for b in ("list of", "isbn", "identifier", "archive", "category", "disambiguation")):
                    titles.append(t)
        return titles[:limit]
    except Exception:
        return []


def compute_adaptive_chapters(sections, forced_chapters=0):
    """
    Naturally scales documentary runtime (12 to 30 minutes) to the topic's REAL historical depth!
      - Massive Epic Dossiers (>=32,000 chars & >=10 sections): 13-15 chapters (~24-30 min)
      - Deep Multi-Act Dossiers (>=16,000 chars & >=7 sections): 10-12 chapters (~18-23 min)
      - Focused Investigative Dossiers (<16,000 chars):          7-9 chapters  (~12-17 min)
    Zero artificial 15-min ceiling AND zero empty padding!
    """
    if forced_chapters and forced_chapters >= 4:
        return min(16, forced_chapters)
    total_chars = sum(len(b) for _, b in sections)
    n_sec = len(sections)
    if total_chars >= 45000 and n_sec >= 12:
        return 15  # ~28-30 min epic
    if total_chars >= 32000 and n_sec >= 10:
        return 13  # ~24-27 min epic
    if total_chars >= 22000 and n_sec >= 8:
        return 11  # ~20-23 min deep doc
    if total_chars >= 14000 and n_sec >= 6:
        return 9   # ~16-19 min deep doc
    if total_chars >= 8000:
        return 8   # ~14-16 min focused doc
    return 7       # ~12-14 min focused dossier


def scout_deep_documentary(cfg, topic_override=None, forced_chapters=0, history_path="state/longform_log.json", work_dir="/tmp/v15_longform"):
    os.makedirs(work_dir, exist_ok=True)
    used_ids = set()
    if os.path.exists(history_path):
        try:
            used_ids = {item["id"] for item in json.load(open(history_path))}
        except Exception:
            pass

    catalog = BTC_SECRET_CATALOG if cfg["mode"] == "behind_the_curtain" else DAILY_ARCHIVE_LONGFORM_CATALOG
    chosen = None
    if topic_override:
        for item in catalog:
            if topic_override.lower() in item[0].lower():
                chosen = item
                break
    if chosen is None:
        for item in catalog:
            cid = f"doc:{re.sub(r'[^a-z0-9]+', '_', item[0].lower())}"
            if cid not in used_ids:
                chosen = item
                break
    if chosen is None:
        # 365-Day Infinite Live Wikipedia Discovery for Deep Documentaries (requires >=12,000-char rich articles!)
        print(f"[DEEP SCOUT] Curated catalog finished ({len(catalog)} episodes); engaging 365-Day Infinite Live Discovery...")
        live_t = discover_live_wiki_topic_tuple(cfg["mode"], used_ids, min_summary_chars=320, require_deep=True, id_prefix="doc")
        if live_t:
            chosen = live_t
    if chosen is None:
        chosen = catalog[0]

    wiki_title, year_str, loc_label, lat, lon, hook_hint = chosen
    doc_id = f"doc:{re.sub(r'[^a-z0-9]+', '_', wiki_title.lower())}"
    yr_m = re.search(r"\d+", str(year_str))
    yr_int = int(yr_m.group(0)) if yr_m else 1969

    api_sum = "https://en.wikipedia.org/api/rest_v1/page/summary/" + urllib.parse.quote(wiki_title.replace(" ", "_"))
    p_sum = _get_json(api_sum, timeout=15)
    summary_text = _clean_summary(p_sum.get("extract") or hook_hint)
    coords = p_sum.get("coordinates") or {}
    if "lat" in coords and "lon" in coords:
        lat, lon = float(coords["lat"]), float(coords["lon"])
    sections = _fetch_full_wiki_sections(wiki_title)
    target_chapters = compute_adaptive_chapters(sections, forced_chapters=forced_chapters)
    est_min_lo = int(round(target_chapters * 1.75))
    est_min_hi = int(round(target_chapters * 2.05))

    # Harvest 20-32 DISTINCT real archival photos across main article + linked articles for 12-30 min visual variety!
    img_urls = []
    seen_keys = set()
    def _add_u(u):
        if not u or u.lower().endswith((".svg", ".gif")):
            return
        base = re.sub(r"^\d+px-", "", u.split("?")[0].split("/")[-1].lower())
        if base not in seen_keys:
            seen_keys.add(base)
            img_urls.append(u)

    src0 = (p_sum.get("originalimage") or {}).get("source") or (p_sum.get("thumbnail") or {}).get("source")
    _add_u(src0)
    search_titles = [wiki_title] + _fetch_linked_titles(wiki_title, limit=8)
    for u in fetch_extra_page_images(search_titles[:3], max_imgs=18):
        _add_u(u)
    if len(img_urls) < 28 and len(search_titles) > 3:
        for u in fetch_extra_page_images(search_titles[3:7], max_imgs=18):
            _add_u(u)

    imgs_dir = os.path.join(work_dir, "images")
    if os.path.exists(imgs_dir):
        for fn in os.listdir(imgs_dir):
            os.remove(os.path.join(imgs_dir, fn))
    target_imgs = min(32, max(18, target_chapters * 2 + 4))
    saved_imgs = download_clean_images(img_urls, imgs_dir, target_count=target_imgs)
    if len(saved_imgs) < 4:
        raise RuntimeError(f"Insufficient archival photos for deep documentary '{wiki_title}'")

    olat, olon, oname = _pick_origin_vector(lat, lon)
    dist_km = _haversine_km(olat, olon, lat, lon)
    macro_png, mpx, mpy, mmw, mmh = stitch_esri_dark_map(lat, lon, os.path.join(work_dir, "map_macro.png"), zoom=4, cols=6, rows=5)
    local_png, lpx, lpy, lmw, lmh = stitch_esri_dark_map(lat, lon, os.path.join(work_dir, "map_local.png"), zoom=8, cols=6, rows=6)

    now = datetime.now(timezone.utc)
    total_chars = sum(len(b) for _, b in sections)
    dossier = {
        "id": doc_id,
        "wiki_title": wiki_title,
        "channel_name": cfg["channel_name"],
        "mode": cfg["mode"],
        "date_label": f"FULL DOCUMENTARY • {yr_int}",
        "display_date": str(yr_int),
        "month": now.month,
        "day": now.day,
        "month_name": now.strftime("%B"),
        "year": yr_int,
        "hook_hint": hook_hint,
        "summary": summary_text,
        "sections": sections,
        "target_chapters": target_chapters,
        "total_dossier_chars": total_chars,
        "location": loc_label.upper()[:30],
        "lat": round(lat, 4),
        "lon": round(lon, 4),
        "origin_name": oname,
        "dist_km": dist_km,
        "images": saved_imgs,
        "map_macro": {"path": macro_png, "px": mpx, "py": mpy, "w": mmw, "h": mmh},
        "map_local": {"path": local_png, "px": lpx, "py": lpy, "w": lmw, "h": lmh},
        "sources": [p_sum.get("content_urls", {}).get("desktop", {}).get("page", "")],
    }
    print(
        f"[ADAPTIVE DEEP SCOUT OK] [{yr_int}] {wiki_title} | dossier={total_chars:,} chars, {len(sections)} secs "
        f"-> {target_chapters} chapters (~{est_min_lo}-{est_min_hi} min) | imgs={len(saved_imgs)} | loc={loc_label}"
    )
    return dossier


def _call_llm_json(system_prompt, user_prompt, timeout=60):
    gem_key = os.environ.get("GEMINI_API_KEY", "").strip()
    groq_key = os.environ.get("GROQ_API_KEY", "").strip()
    if gem_key:
        for model in ("gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"):
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={gem_key}"
            payload = {
                "contents": [{"parts": [{"text": f"{system_prompt}\n\n{user_prompt}"}]}],
                "generationConfig": {"temperature": 0.72, "responseMimeType": "application/json"},
            }
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")
            try:
                with urllib.request.urlopen(req, timeout=timeout) as r:
                    data = json.loads(r.read().decode("utf-8"))
                return _extract_json(data["candidates"][0]["content"]["parts"][0]["text"]), f"gemini:{model}"
            except Exception as e:
                print(f"[LONGFORM LLM] Gemini {model} skipped: {e}")
    if groq_key:
        url = "https://api.groq.com/openai/v1/chat/completions"
        payload = {
            "model": "llama-3.3-70b-versatile",
            "temperature": 0.72,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json", "Authorization": f"Bearer {groq_key}"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = json.loads(r.read().decode("utf-8"))
            return _extract_json(data["choices"][0]["message"]["content"]), "groq:llama-3.3-70b"
        except Exception as e:
            print(f"[LONGFORM LLM] Groq skipped: {e}")
    return None, None


def _slice_dossier_into_buckets(dossier, n_ch):
    """Distributes all verified Wikipedia sentences evenly across N chapters in chronological/article order."""
    sec_list = dossier["sections"] or [("Overview", dossier["summary"])]
    flat_sents = []
    for head, body in sec_list:
        clean = re.sub(r"\([^)]*\)", "", body)
        clean = re.sub(r"\[\d+\]", "", clean)
        clean = re.sub(r"\s+", " ", clean).strip()
        sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", clean) if 32 <= len(s.strip()) <= 280]
        for s in sents:
            flat_sents.append((head, s))
    if not flat_sents:
        flat_sents = [("Overview", dossier["summary"])]

    buckets = []
    tot = len(flat_sents)
    for i in range(n_ch):
        a = int(i * tot / n_ch)
        b = int((i + 1) * tot / n_ch) if i < n_ch - 1 else tot
        chunk = flat_sents[a:b] or flat_sents[max(0, a - 4):min(tot, a + 4)] or flat_sents[:6]
        buckets.append(chunk)
    return buckets


def _fallback_adaptive_script(dossier):
    """Zero-fail adaptive N-chapter deep documentary builder directly from the verified Wikipedia dossier."""
    n_ch = dossier["target_chapters"]
    buckets = _slice_dossier_into_buckets(dossier, n_ch)
    arc_names = [
        "The Opening Mystery", "Hidden Origins", "The Secret Blueprint", "Escalation",
        "Behind Closed Doors", "Critical Countdown", "Point of No Return", "The Turning Point",
        "Inside The Crisis", "Hidden Revelations", "The Investigation", "Unanswered Questions",
        "Fallout & Cover-Up", "The Shocking Truth", "Declassified Legacy",
    ]
    chapters = []
    for i, slice_i in enumerate(buckets):
        ch_head = slice_i[0][0] if slice_i[0][0] != "Introduction" else arc_names[i % len(arc_names)]
        ch_title = _trim_words(ch_head, 36)
        raw_txt = " ".join(s for _, s in slice_i)
        words = raw_txt.split()
        if len(words) > 290:
            raw_txt = " ".join(words[:282]).rsplit(".", 1)[0] + "."
        if i == 0:
            narr = f"Chapter One: {ch_title}. {dossier['hook_hint']}. {raw_txt}"
        elif i == n_ch - 1:
            narr = f"Final Chapter: {ch_title}. {raw_txt} Subscribe to {dossier['channel_name'].title()} for our next full declassified documentary."
        else:
            narr = f"Chapter {i + 1}: {ch_title}. {raw_txt}"

        num_m = re.search(r"(\$[\d,]+(?:\s*(?:million|billion))?|\b\d{1,3}(?:,\d{3})+\b|\b\d+\s*(?:miles|feet|hours|days|years|men|bombs|minutes)\b)", raw_txt, re.I)
        stat_b = num_m.group(1).upper()[:18] if num_m else str(dossier["year"])
        chapters.append({
            "chapter_title": ch_title,
            "newspaper_headline": _trim_words(f"{ch_title}: {dossier['wiki_title']}", 44).upper(),
            "narration": narr,
            "polaroid_caption": f"CHAPTER {i+1:02d} • {dossier['wiki_title'][:26].upper()}",
            "stamp_line1": "DECLASSIFIED" if i % 2 == 0 else "TOP SECRET",
            "stamp_line2": f"CHAPTER {i+1:02d} • {dossier['year']}",
            "forensic_header": f"DOSSIER PART {i+1:02d} • {ch_title[:20].upper()}",
            "forensic_lines": [
                f"CHAPTER {i+1:02d}: {ch_title[:30].upper()}",
                f"LOCATION: {dossier['location'][:30]}",
                f"FACT: {_trim_words(slice_i[0][1], 42).upper()}",
            ],
            "split_left_label": f"ARCHIVE FILE {i+1}A",
            "split_right_label": f"EVIDENCE {i+1}B",
            "climax_stat_label": f"CHAPTER {i+1:02d} • {dossier['year']}",
            "climax_stat_big": stat_b,
            "climax_stat_sub": f"SECTOR: {dossier['location'][:26]}",
        })

    words_t = dossier["wiki_title"].upper().split()
    t1 = " ".join(words_t[:2])[:14] or "DECLASSIFIED"
    t2 = " ".join(words_t[2:4])[:14] or str(dossier["year"])
    t3 = "EXPOSED"
    return {
        "video_title": _trim_words(f"{dossier['hook_hint']} ({dossier['year']} Full Documentary)", 86),
        "thumb_line1": t1,
        "thumb_line2": t2,
        "thumb_line3": t3,
        "tags": ["history documentary", "full documentary", "us history", "cold war", "declassified", dossier["wiki_title"].lower(), str(dossier["year"])],
        "chapters": chapters,
    }


def build_longform_script(dossier):
    """
    Two-stage Showrunner pipeline so even a 15-chapter, 4,300-word (30-minute!) script
    is written cleanly chapter-by-chapter with ZERO LLM JSON truncation!
    """
    n_ch = dossier["target_chapters"]
    fb = _fallback_adaptive_script(dossier)
    has_key = bool(os.environ.get("GEMINI_API_KEY", "").strip() or os.environ.get("GROQ_API_KEY", "").strip())
    if not has_key:
        fb["provider"] = "v15-adaptive-deterministic-fallback"
        tot_w = sum(len(c["narration"].split()) for c in fb["chapters"])
        print(f"[LONGFORM SCRIPT OK via {fb['provider']}] '{fb['video_title']}' | {n_ch} chapters | {tot_w} words")
        return fb

    # Stage 1: Master Blueprint Outline (1 call)
    sec_index = "\n".join(f"- {h}: {b[:220]}" for h, b in dossier["sections"][:18])
    outline_prompt = (
        f"CHANNEL: {dossier['channel_name']}\n"
        f"SUBJECT: {dossier['wiki_title']} ({dossier['year']})\n"
        f"LOCATION: {dossier['location']}\n"
        f"HOOK ANGLE: {dossier['hook_hint']}\n"
        f"EXACT CHAPTER COUNT REQUIRED: {n_ch}\n\n"
        f"VERIFIED WIKIPEDIA SECTION MAP:\n{sec_index}"
    )
    bp, prov = _call_llm_json(OUTLINE_SYSTEM_PROMPT, outline_prompt, timeout=50)
    if not bp or not isinstance(bp.get("outline"), list) or len(bp["outline"]) < max(5, n_ch - 2):
        fb["provider"] = "v15-adaptive-deterministic-fallback"
        tot_w = sum(len(c["narration"].split()) for c in fb["chapters"])
        print(f"[LONGFORM SCRIPT FALLBACK] '{fb['video_title']}' | {n_ch} chapters | {tot_w} words")
        return fb

    outline = bp["outline"][:n_ch]
    while len(outline) < n_ch:
        outline.append({"chapter_title": fb["chapters"][len(outline)]["chapter_title"], "focus": "Key verified events and aftermath."})

    # Stage 2: Write each chapter deeply with its real archival source slice + previous cliffhanger!
    buckets = _slice_dossier_into_buckets(dossier, n_ch)
    final_chapters = []
    prev_closing = ""
    for i in range(n_ch):
        slice_txt = " ".join(f"[{h}] {s}" for h, s in buckets[i])[:4200]
        ch_plan = outline[i]
        is_first = (i == 0)
        is_last = (i == n_ch - 1)
        ch_prompt = (
            f"DOCUMENTARY TITLE: {bp.get('video_title', fb['video_title'])}\n"
            f"CHANNEL: {dossier['channel_name']} | SUBJECT: {dossier['wiki_title']} ({dossier['year']})\n"
            f"CHAPTER {i+1} OF {n_ch}: {ch_plan.get('chapter_title', fb['chapters'][i]['chapter_title'])}\n"
            f"ANGLE: {ch_plan.get('focus', '')}\n"
            f"{'OPENING CHAPTER: Start with a cinematic cold-open hook!' if is_first else ''}"
            f"{'FINAL CHAPTER: Deliver an unforgettable historical conclusion & subtle subscribe sign-off.' if is_last else 'End with a smooth investigative hook leading into the next chapter.'}\n"
            f"{('PREVIOUS CHAPTER ENDED WITH: ' + prev_closing) if prev_closing else ''}\n\n"
            f"VERIFIED ARCHIVAL FACTS FOR THIS CHAPTER:\n{slice_txt}"
        )
        ch_res, ch_prov = _call_llm_json(CHAPTER_SYSTEM_PROMPT, ch_prompt, timeout=50)
        fb_ch = fb["chapters"][i]
        if ch_res and isinstance(ch_res, dict) and len(str(ch_res.get("narration", "")).split()) >= 120:
            for ck, cv in fb_ch.items():
                if not ch_res.get(ck):
                    ch_res[ck] = cv
            ch_res["narration"] = re.sub(r"[\[\]\*#_`]", "", str(ch_res["narration"])).strip()
            final_chapters.append(ch_res)
            prov = ch_prov or prov
        else:
            final_chapters.append(fb_ch)
        prev_closing = final_chapters[-1]["narration"][-220:]
        time.sleep(1.8)  # Gentle free-tier rate pacing

    res = {
        "video_title": bp.get("video_title") or fb["video_title"],
        "thumb_line1": bp.get("thumb_line1") or fb["thumb_line1"],
        "thumb_line2": bp.get("thumb_line2") or fb["thumb_line2"],
        "thumb_line3": bp.get("thumb_line3") or fb["thumb_line3"],
        "tags": bp.get("tags") or fb["tags"],
        "chapters": final_chapters,
        "provider": prov or "v15-adaptive-hybrid",
    }
    tot_w = sum(len(c["narration"].split()) for c in res["chapters"])
    print(f"[ADAPTIVE LONGFORM SCRIPT OK via {res['provider']}] '{res['video_title']}' | {n_ch} chapters | {tot_w} words (~{tot_w/150:.1f} min)")
    return res


def fmt_ts(sec):
    return f"{int(sec // 60):02d}:{int(sec % 60):02d}"


def _render_single_chapter_job(job):
    """Top-level worker function for parallel multi-core chapter rendering on GitHub Actions 4-vCPU runners."""
    idx, total_ch, ch, ch_ev, cfg, cdir = job
    os.makedirs(cdir, exist_ok=True)
    is_final = (idx == total_ch - 1)

    voice_mp3 = os.path.join(cdir, "voice.mp3")
    audio_m4a = os.path.join(cdir, "audio.m4a")
    ch_mp4 = os.path.join(cdir, f"ch{idx+1:02d}_1080p.mp4")

    v_dur, words = synthesize_voice_v15(
        ch["narration"], voice_mp3,
        voice=cfg["voice"], rate=cfg.get("voice_rate", "+2%"), pitch=cfg.get("voice_pitch", "-2Hz"),
    )
    speech_off = 0.45
    tot_d = round(speech_off + v_dur + (3.2 if is_final else 1.4), 2)
    b = [0.0, 0.20, 0.42, 0.62, 0.81, 1.0]
    sfx_plan = [
        (0.32, "braaam", 0.40, 0.50),
        (tot_d * 0.072, "dive", 0.28, 0.50),
        (tot_d * 0.115, "radar", 0.18, 0.45),
        (tot_d * b[1] - 0.16, "whip", 0.22, 0.62),
        (tot_d * (b[1] + 0.068), "shutter", 0.34, 0.50),
        (tot_d * (b[1] + 0.082), "paper_rip", 0.28, 0.40),
        (tot_d * (b[1] + 0.145), "stamp", 0.38, 0.58),
        (tot_d * b[2] - 0.16, "whip", 0.22, 0.38),
        (tot_d * b[3] - 0.12, "laser", 0.32, 0.50),
        (tot_d * (b[3] + 0.068), "glitch", 0.28, 0.50),
    ]
    if is_final:
        sfx_plan.append((tot_d - 3.0, "drop", 0.46, 0.50))

    env30, spec30 = mix_cinema_audio_v15(voice_mp3, tot_d, speech_off, audio_m4a, seed=ch_ev["year"] + idx * 17, sfx_plan=sfx_plan)
    actual_d = render_v15_beast(
        ch_ev, ch, v_dur, words, audio_m4a, env30, spec30,
        ch_mp4, vertical=False, show_outro=is_final,
    )
    # Clean chapter scratch audio immediately to keep workspace disk lean on 25-30 min renders!
    for tmpf in (voice_mp3, audio_m4a):
        try:
            if os.path.exists(tmpf):
                os.remove(tmpf)
        except Exception:
            pass
    gc.collect()
    return idx, ch_mp4, actual_d, ch["chapter_title"]


def main():
    cfg = json.load(open("channel_config.json"))
    ap = argparse.ArgumentParser()
    ap.add_argument("--topic", default="", help="Optional specific topic override")
    ap.add_argument("--chapters", type=int, default=0, help="0 = auto-adaptive (7-15 chapters -> 12-30 min)")
    ap.add_argument("--workers", type=int, default=0, help="0 = auto parallel workers based on CPU cores")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--work-dir", default="/tmp/v15_longform_work")
    args = ap.parse_args()

    dry = args.dry_run or (os.environ.get("DRY_RUN", "false").lower() == "true")
    privacy = os.environ.get("PRIVACY_STATUS", "public").strip() or "public"
    forced_ch = args.chapters or int(os.environ.get("TARGET_CHAPTERS", "0") or "0")
    workers = args.workers if args.workers > 0 else min(3, max(1, (os.cpu_count() or 2) - 1))
    os.makedirs(args.work_dir, exist_ok=True)

    print(f"=== {cfg['channel_name']} [V15 BEAST ADAPTIVE DOCUMENTARY — 12-30 MIN 16:9 1080p] (workers={workers}, dry_run={dry}) ===")
    dossier = scout_deep_documentary(cfg, topic_override=args.topic or None, forced_chapters=forced_ch, work_dir=args.work_dir)
    doc_script = build_longform_script(dossier)

    all_imgs = dossier["images"]
    n_imgs = len(all_imgs)
    total_ch = len(doc_script["chapters"])

    jobs = []
    for idx, ch in enumerate(doc_script["chapters"]):
        cdir = os.path.join(args.work_dir, f"ch_{idx+1:02d}")
        ch_imgs = [all_imgs[(idx * 2 + k) % n_imgs] for k in range(4)]
        ch_ev = dict(dossier)
        ch_ev["images"] = ch_imgs
        ch_ev["display_date"] = f"CH {idx+1:02d} • {ch['chapter_title'][:20].upper()}"
        jobs.append((idx, total_ch, ch, ch_ev, cfg, cdir))

    results = {}
    if workers > 1 and total_ch > 1:
        print(f"[PARALLEL RENDER] Dispatching {total_ch} chapters across {workers} worker processes...")
        with ProcessPoolExecutor(max_workers=workers) as ex:
            futs = [ex.submit(_render_single_chapter_job, j) for j in jobs]
            for fut in as_completed(futs):
                idx, ch_mp4, actual_d, ch_title = fut.result()
                results[idx] = (ch_mp4, actual_d, ch_title)
                print(f"  [CHAPTER DONE] {idx+1:02d}/{total_ch:02d} '{ch_title}' -> {actual_d:.1f}s")
    else:
        for j in jobs:
            idx, ch_mp4, actual_d, ch_title = _render_single_chapter_job(j)
            results[idx] = (ch_mp4, actual_d, ch_title)
            print(f"  [CHAPTER DONE] {idx+1:02d}/{total_ch:02d} '{ch_title}' -> {actual_d:.1f}s")

    chapter_mp4s, chapter_lines = [], []
    cursor_t = 0.0
    for idx in range(total_ch):
        ch_mp4, actual_d, ch_title = results[idx]
        chapter_mp4s.append(ch_mp4)
        chapter_lines.append(f"{fmt_ts(cursor_t)} Chapter {idx+1}: {ch_title}")
        cursor_t += actual_d

    concat_txt = os.path.join(args.work_dir, "concat.txt")
    with open(concat_txt, "w") as f:
        for p in chapter_mp4s:
            f.write(f"file '{p}'\n")
    master_mp4 = os.path.join(args.work_dir, "v15_beast_master_1080p.mp4")
    subprocess.run([FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", concat_txt, "-c", "copy", "-movflags", "+faststart", master_mp4], check=True)

    thumb_jpg = os.path.join(args.work_dir, "v15_thumb_1280x720.jpg")
    generate_v15_thumbnail(
        all_imgs[0], dossier["map_local"]["path"], cfg["channel_name"],
        doc_script["thumb_line1"][:16], doc_script["thumb_line2"][:16], doc_script["thumb_line3"][:16],
        f"FULL DOC • {dossier['year']}", thumb_jpg,
    )

    yt_title = doc_script["video_title"][:98]
    sources_txt = "\n".join(s for s in dossier.get("sources", []) if s)
    yt_desc = (
        f"{yt_title}\n\n"
        f"{dossier['summary']}\n\n"
        f"CHAPTERS:\n" + "\n".join(chapter_lines) + "\n\n"
        f"{cfg['description_footer']}\n\n"
        f"Verified Archival Sources:\n{sources_txt}\n"
        f"Map cartography © Esri World Dark Gray Base.\n\n"
        f"{cfg.get('weekly_hashtags', '#HistoryDocumentary #ColdWar #USHistory #Declassified')} #{dossier['year']}"
    )

    if not dry:
        vid_id = upload_video_to_youtube(master_mp4, yt_title, yt_desc, doc_script["tags"], privacy=privacy, thumbnail_path=thumb_jpg)
        os.makedirs("state", exist_ok=True)
        lf_p = "state/longform_log.json"
        hist = json.load(open(lf_p)) if os.path.exists(lf_p) else []
        hist.append({
            "id": dossier["id"], "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "title": yt_title, "chapters": total_ch, "duration": fmt_ts(cursor_t), "video_id": vid_id,
        })
        json.dump(hist[-3000:], open(lf_p, "w"), indent=2)

        send_telegram(
            f"🏆 <b>{cfg['channel_name']} [V15 BEAST] — Massive 16:9 Documentary LIVE!</b>\n\n"
            f"🎬 <b>{yt_title}</b>\n"
            f"⏱️ Duration: {fmt_ts(cursor_t)} ({total_ch} Deep Adaptive Chapters + V15 Auto Thumb)\n"
            f"🤖 AI: {doc_script['provider']}\n"
            f"▶️ https://www.youtube.com/watch?v={vid_id}\n"
            f"🔒 Privacy: <code>{privacy}</code>"
        )
    else:
        print(f"[DEEP LONGFORM DRY RUN OK] {master_mp4} ({fmt_ts(cursor_t)}, {total_ch} chapters) | Thumb: {thumb_jpg}")


if __name__ == "__main__":
    main()
