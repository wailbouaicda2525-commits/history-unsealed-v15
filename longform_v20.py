"""
longform_v20.py — V20.5 CINEMA BEAST ADAPTIVE DEEP DOCUMENTARY ENGINE (12–30 MIN • 1920x1080 24fps)
Upgrades over V15:
  1. STRICT STORY-LOCKED REAL MOVING VIDEO CLIPS (Exact Wikipedia/Commons/NASA/Internet Archive
     footage of THAT EXACT EVENT + Groq AI Picture Editor Judge >= 8/10 approving era-matched Pixabay HD B-Roll!)
  2. LIVE 2026 GROQ SHOWRUNNER (qwen/qwen3.8-27b primary + openai/gpt-oss-120b backup — zero 404s!)
  3. FULL TRIPLE BOOK MARKETING FUNNEL ('Unsealed Archives Press'):
       - Mid-Video FULL-SCREEN 11-second Narrated 2-Book Commercial Break right at the halfway mark!
       - Sleek floating 3D Book Promo Banner in Chapters 2 & N-1!
       - Full 2-Book 3D Collector's Finale Outro on the final chapter!
  4. EXACT CLICKABLE YOUTUBE TIMELINE CHAPTERS (00:00 format matched to actual rendered chapter durations!)
  5. VIRAL SPLIT-SCREEN REAL-ARCHIVAL THUMBNAIL (auto-picks real archival human/event photos via face+contrast
     scoring, crimson diagonal slash, massive WHITE+RED impact headline, tilted red archival stamp!)
"""
import os
import re
import gc
import ssl
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
from scriptwriter_v20 import _extract_json, _trim_words
from voice_engine_v15 import synthesize_voice_v15, mix_cinema_audio_v15
from video_scout_v20 import scout_real_videos_v20
from renderer_v20_cinema import (
    render_v20_cinema,
    render_midroll_book_commercial_16x9,
    pick_best_thumb_photos,
    generate_v20_thumbnail,
)
from uploader_v15 import upload_video_to_youtube, send_telegram

SSL_CTX = ssl.create_default_context()
UA = "UnsealedArchivesV20/2.5 (https://youtube.com/@behindthecurtainworld)"

# CHANNEL 2 ('HISTORY UNSEALED') DEDICATED 36-EPISODE US/WORLD BLOCKBUSTER DEEP-DIVE CATALOG
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

OUTLINE_SYSTEM_PROMPT_V20 = """You are the executive showrunner for a flagship Netflix / Warnoctis / LEMMiNO / Johnny Harris style long-form YouTube history documentary channel targeting Tier-1 US audiences.
Given a verified historical topic and its real Wikipedia section map, design a gripping multi-chapter documentary blueprint with the EXACT target chapter count requested.
Each chapter title MUST read like a compelling clickable YouTube chapter on the timeline (e.g. 'The buses on the hill', 'Six seconds in Dallas', 'The secret cable snaps', 'Adenauer in Moscow' — vivid, concrete, chronological!).
Return ONLY valid JSON:
{
  "video_title": "High-CTR US YouTube Documentary Title 48-76 chars (complete words, curiosity gap, authoritative)",
  "thumb_white": "FIRST 2-3 WHITE WORDS OF VIRAL SPLIT-SCREEN THUMBNAIL (ALL CAPS, e.g. 'THE WALL CAME')",
  "thumb_red": "1-2 EXPLOSIVE RED POWER WORDS AT END OF THUMBNAIL (ALL CAPS, e.g. 'OVERNIGHT')",
  "thumb_stamp": "SHORT RED ARCHIVAL STAMP <= 16 chars (ALL CAPS, e.g. 'CIA ARCHIVE' or 'DECLASSIFIED')",
  "thumb_pill": "OPTIONAL YEAR/DATE TRANSITION <= 14 chars (e.g. '1968 -> 1974' or 'OCT 1962')",
  "video_queries_broll": [
    "1-2 concrete visual nouns for Pixabay B-roll matching this EXACT era/setting",
    "1-2 concrete visual nouns for tension/atmosphere",
    "1-2 concrete visual nouns for investigation/command",
    "1-2 concrete visual nouns for climax/aftermath"
  ],
  "tags": ["history documentary", "full documentary", "us history", "6-10 high-RPM SEO tags"],
  "outline": [
    {"chapter_title": "100% UNIQUE Vivid YouTube Chapter Title <= 40 chars (NEVER repeat any chapter title!)", "focus": "1-sentence investigative angle for this chapter"}
  ]
}"""

CHAPTER_SYSTEM_PROMPT_V20 = """You are writing ONE deep narrative chapter of a flagship Netflix / LEMMiNO / Johnny Harris style YouTube documentary targeting Tier-1 US audiences.
RULES:
1. STRICTLY factual and grounded in the provided verified historical dossier. Plain spoken English ONLY inside narration (NO brackets, NO stage directions, NO markdown, NO hashtags).
2. Write 255 to 305 spoken words (~1.8 to 2.1 minutes spoken!) with vivid investigative storytelling, exact dates, real names, real numbers, human tension, and a smooth hook into the next chapter.
3. Return ONLY valid JSON matching this EXACT schema:
{
  "chapter_title": "Vivid Clickable YouTube Chapter Title <= 40 chars",
  "hook_top": "2-3 WORD DRAMATIC CHAPTER SLAM (ALL CAPS)",
  "hook_sub": "SHORT CONTEXT LINE <= 36 chars (ALL CAPS)",
  "newspaper_headline": "DRAMATIC 4-6 WORD ARCHIVE HEADLINE (ALL CAPS)",
  "narration": "255-305 word deeply engaging factual chapter narration in plain spoken English.",
  "polaroid_caption": "ARCHIVAL EVIDENCE CAPTION <= 42 chars (ALL CAPS)",
  "stamp_line1": "1-2 WORD RED STAMP (ALL CAPS)",
  "stamp_line2": "SHORT SUB-STAMP <= 22 chars (ALL CAPS)",
  "forensic_header": "CLASSIFIED DOSSIER HEADER <= 38 chars (ALL CAPS)",
  "forensic_lines": [
    "LINE 1: Key verified date/codename <= 42 chars",
    "LINE 2: Key verified turning point <= 42 chars",
    "LINE 3: Key verified aftermath/fact <= 42 chars"
  ],
  "split_left_label": "LABEL A <= 18 chars (ALL CAPS)",
  "split_right_label": "LABEL B <= 18 chars (ALL CAPS)",
  "climax_stat_label": "EYEBROW <= 26 chars (ALL CAPS)",
  "climax_stat_big": "PUNCHY NUMBER/YEAR <= 18 chars (ALL CAPS)",
  "climax_stat_sub": "CONTEXT <= 38 chars (ALL CAPS)"
}"""


def _fetch_full_wiki_sections(wiki_title):
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
    if forced_chapters and forced_chapters >= 3:
        return min(16, forced_chapters)
    total_chars = sum(len(b) for _, b in sections)
    n_sec = len(sections)
    if total_chars >= 45000 and n_sec >= 12:
        return 14  # ~26-29 min epic
    if total_chars >= 32000 and n_sec >= 10:
        return 12  # ~22-25 min epic
    if total_chars >= 22000 and n_sec >= 8:
        return 10  # ~18-21 min deep doc
    if total_chars >= 14000 and n_sec >= 6:
        return 9   # ~16-19 min deep doc
    if total_chars >= 8000:
        return 8   # ~14-16 min focused doc
    return 7       # ~12-14 min focused dossier


def scout_deep_documentary_v20(cfg, topic_override=None, forced_chapters=0, history_path="state/longform_log.json", work_dir="/tmp/v20_longform"):
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
        print(f"[DEEP SCOUT V20] Curated catalog finished ({len(catalog)} episodes); engaging 365-Day Infinite Live Discovery...")
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
    wiki_page_url = p_sum.get("content_urls", {}).get("desktop", {}).get("page", "")
    dossier = {
        "id": doc_id,
        "wiki_title": wiki_title,
        "title": wiki_title,
        "wiki_url": wiki_page_url,
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
        "sources": [wiki_page_url],
    }
    print(f"[V20.5 DEEP SCOUT OK] [{yr_int}] {wiki_title} | {total_chars:,} chars -> {target_chapters} chapters | {len(saved_imgs)} archival photos")
    return dossier


def _call_llm_json_v20(system_prompt, user_prompt, timeout=55):
    """2026 Verified Priority: Groq (qwen/qwen3.8-27b -> openai/gpt-oss-120b) -> Gemini."""
    groq_key = os.environ.get("GROQ_API_KEY", "").strip()
    gem_key = os.environ.get("GEMINI_API_KEY", "").strip()

    if groq_key:
        url = "https://api.groq.com/openai/v1/chat/completions"
        for model in ("qwen/qwen3.8-27b", "openai/gpt-oss-120b"):
            payload = {
                "model": model,
                "temperature": 0.72,
                "max_tokens": 2200,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            }
            if "gpt-oss" in model:
                payload["reasoning_effort"] = "low"
            else:
                payload["response_format"] = {"type": "json_object"}
            req = urllib.request.Request(
                url, data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {groq_key}", "User-Agent": UA},
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=timeout, context=SSL_CTX) as r:
                    data = json.loads(r.read().decode("utf-8"))
                return _extract_json(data["choices"][0]["message"].get("content", "")), f"groq:{model}"
            except Exception as e:
                print(f"[LONGFORM-V20 LLM] Groq {model} skipped: {e}")

    if gem_key:
        for model in ("gemini-2.5-flash", "gemini-2.0-flash"):
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={gem_key}"
            payload = {
                "contents": [{"parts": [{"text": f"{system_prompt}\n\n{user_prompt}"}]}],
                "generationConfig": {"temperature": 0.72, "responseMimeType": "application/json"},
            }
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json", "User-Agent": UA}, method="POST")
            try:
                with urllib.request.urlopen(req, timeout=timeout, context=SSL_CTX) as r:
                    data = json.loads(r.read().decode("utf-8"))
                return _extract_json(data["candidates"][0]["content"]["parts"][0]["text"]), f"gemini:{model}"
            except Exception as e:
                print(f"[LONGFORM-V20 LLM] Gemini {model} skipped: {e}")
    return None, None


def _slice_dossier_into_buckets(dossier, n_ch):
    sec_list = dossier["sections"] or [("Overview", dossier["summary"])]
    flat_sents = []
    for head, body in sec_list:
        clean = re.sub(r"\([^)]*\)|\[\d+\]", "", body)
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


def _clean_doc_title_v20(txt, year=None, max_c=92):
    """V20.7.2: Guarantees complete YouTube documentary titles with ZERO mid-word cutoff or unclosed '('."""
    s = re.sub(r"\s+", " ", str(txt or "")).strip(" ,.;:-–—")
    if len(s) > max_c:
        # Try replacing '(YYYY Full Documentary)' with clean '(YYYY)' first
        s2 = re.sub(r"\s*\((\d{4})\s+Full\s+Documentary\)\s*$", r" (\1)", s, flags=re.I)
        if len(s2) <= max_c:
            s = s2
        else:
            no_par = re.sub(r"\s*\([^)]*\)\s*$", "", s).strip(" ,.;:-–—")
            if 28 <= len(no_par) <= max_c:
                s = no_par
            else:
                s = _trim_words(s, max_c)
    if s.count("(") > s.count(")"):
        s = s.rsplit("(", 1)[0].strip(" ,.;:-–—")
    if s.count("[") > s.count("]"):
        s = s.rsplit("[", 1)[0].strip(" ,.;:-–—")
    dangling = {"a", "an", "the", "of", "in", "to", "for", "with", "and", "or", "by", "from", "on", "at", "that", "who", "which", "full"}
    parts = s.split()
    while len(parts) > 3 and parts[-1].lower().strip(".,:;-–—") in dangling:
        parts.pop()
    out = " ".join(parts).strip(" ,.;:-–—")
    if year and str(year) not in out and len(out) + len(str(year)) + 3 <= max_c:
        out = f"{out} ({year})"
    return out


def _dedupe_chapter_titles_v20(chapters):
    """V20.7.2: Guarantees 100% UNIQUE clickable YouTube Chapter labels (ZERO repeated headings like 'Construction' x3!)."""
    phase_suffixes = [
        "The Breakthrough",
        "Inside the Operation",
        "Rising Tension",
        "The Turning Point",
        "Hidden Complications",
        "Point of No Return",
        "The Fallout",
        "Declassified Aftermath",
    ]
    dangling = {"a", "an", "the", "of", "in", "to", "for", "with", "and", "or", "by", "from", "on", "at"}

    def _clean_prefix(txt, lim):
        p = _trim_words(txt, lim).split()
        while len(p) > 1 and p[-1].lower().strip(".,:;-–—") in dangling:
            p.pop()
        return " ".join(p)

    seen = {}
    used_norm = set()
    for idx, ch in enumerate(chapters):
        base = re.sub(r"\s+", " ", str(ch.get("chapter_title") or f"Chapter {idx + 1}")).strip(" ,.;:-–—")
        norm = base.lower()
        if norm not in used_norm:
            used_norm.add(norm)
            seen[norm] = 1
            ch["chapter_title"] = _trim_words(base, 42)
            continue

        seen[norm] = seen.get(norm, 1) + 1
        occ = seen[norm]
        narr = str(ch.get("narration") or "")
        yr_m = re.search(r"\b(1[5-9]\d{2}|20[0-2]\d)\b", narr)
        cand = ""
        if yr_m and yr_m.group(1) not in base:
            cand = f"{_clean_prefix(base, 22)}: {yr_m.group(1)} Escalation"
        if not cand or cand.lower() in used_norm:
            suf = phase_suffixes[(occ - 2 + idx) % len(phase_suffixes)]
            cand = f"{_clean_prefix(base, 18)}: {suf}"
        if cand.lower() in used_norm:
            cand = f"{_clean_prefix(base, 26)} — Part {occ}"
        ch["chapter_title"] = _trim_words(cand, 42)
        used_norm.add(ch["chapter_title"].lower())
    return chapters


def _fallback_adaptive_script_v20(dossier):
    n_ch = dossier["target_chapters"]
    buckets = _slice_dossier_into_buckets(dossier, n_ch)
    arc_names = [
        "The Opening Mystery", "Hidden Origins", "The Secret Blueprint", "Escalation",
        "Behind Closed Doors", "Critical Countdown", "Point of No Return", "The Turning Point",
        "Inside The Crisis", "Hidden Revelations", "The Investigation", "Unanswered Questions",
        "Fallout & Cover-Up", "Declassified Legacy",
    ]
    chapters = []
    for i, slice_i in enumerate(buckets):
        ch_head = slice_i[0][0] if slice_i[0][0] != "Introduction" else arc_names[i % len(arc_names)]
        ch_title = _trim_words(ch_head, 36)
        raw_txt = " ".join(s for _, s in slice_i)
        words = raw_txt.split()
        if len(words) > 285:
            raw_txt = " ".join(words[:280]).rsplit(".", 1)[0] + "."
        if i == 0:
            narr = f"{dossier['hook_hint']}. {raw_txt}"
        elif i == n_ch - 1:
            narr = f"{raw_txt} Subscribe to {dossier['channel_name'].title()} and unlock the full illustrated collector's edition using the link below."
        else:
            narr = f"{raw_txt}"

        num_m = re.search(r"(\$[\d,]+(?:\s*(?:million|billion))?|\b\d{1,3}(?:,\d{3})+\b|\b\d+\s*(?:miles|feet|hours|days|years|men|bombs|minutes)\b)", raw_txt, re.I)
        stat_b = num_m.group(1).upper()[:18] if num_m else str(dossier["year"])
        chapters.append({
            "chapter_title": ch_title,
            "hook_top": _trim_words(ch_title, 22).upper(),
            "hook_sub": f"CHAPTER {i+1:02d} • {dossier['year']} • {dossier['location'][:16]}",
            "newspaper_headline": _trim_words(f"{ch_title}: {dossier['wiki_title']}", 42).upper(),
            "narration": narr,
            "polaroid_caption": f"CHAPTER {i+1:02d} • {dossier['wiki_title'][:26].upper()}",
            "stamp_line1": "DECLASSIFIED" if i % 2 == 0 else "TOP SECRET",
            "stamp_line2": f"CHAPTER {i+1:02d} • {dossier['year']}",
            "forensic_header": f"DOSSIER PART {i+1:02d} • {ch_title[:20].upper()}",
            "forensic_lines": [
                f"CHAPTER {i+1:02d}: {ch_title[:30].upper()}",
                f"LOCATION: {dossier['location'][:30]}",
                f"FACT: {_trim_words(slice_i[0][1], 40).upper()}",
            ],
            "split_left_label": f"ARCHIVE FILE {i+1}A",
            "split_right_label": f"EVIDENCE {i+1}B",
            "climax_stat_label": f"CHAPTER {i+1:02d} • {dossier['year']}",
            "climax_stat_big": stat_b,
            "climax_stat_sub": f"SECTOR: {dossier['location'][:26]}",
        })

    chapters = _dedupe_chapter_titles_v20(chapters)
    wt = dossier["wiki_title"].upper().split()
    raw_doc_t = f"{dossier['hook_hint']} ({dossier['year']} Full Documentary)"
    if len(raw_doc_t) > 92:
        raw_doc_t = f"{dossier['hook_hint']} ({dossier['year']})"
    return {
        "video_title": _clean_doc_title_v20(raw_doc_t, year=dossier["year"], max_c=92),
        "thumb_white": _trim_words(" ".join(wt[:-1]) if len(wt) > 1 else "THE SECRET OF", 18).upper(),
        "thumb_red": _trim_words(wt[-1] if wt else str(dossier["year"]), 14).upper(),
        "thumb_stamp": "CIA ARCHIVE" if dossier["mode"] == "behind_the_curtain" else "HISTORY UNSEALED",
        "thumb_pill": str(dossier["year"]),
        "video_queries_broll": [],
        "tags": ["history documentary", "full documentary", "us history", "cold war", "declassified", dossier["wiki_title"].lower(), str(dossier["year"])],
        "chapters": chapters,
    }


def build_longform_script_v20(dossier):
    n_ch = dossier["target_chapters"]
    fb = _fallback_adaptive_script_v20(dossier)
    if not (os.environ.get("GROQ_API_KEY", "").strip() or os.environ.get("GEMINI_API_KEY", "").strip()):
        fb["provider"] = "v20-deterministic-fallback"
        return fb

    sec_index = "\n".join(f"- {h}: {b[:220]}" for h, b in dossier["sections"][:18])
    outline_prompt = (
        f"CHANNEL: {dossier['channel_name']}\n"
        f"SUBJECT: {dossier['wiki_title']} ({dossier['year']})\n"
        f"LOCATION: {dossier['location']}\n"
        f"HOOK ANGLE: {dossier['hook_hint']}\n"
        f"EXACT CHAPTER COUNT REQUIRED: {n_ch}\n\n"
        f"VERIFIED WIKIPEDIA SECTION MAP:\n{sec_index}"
    )
    bp, prov = _call_llm_json_v20(OUTLINE_SYSTEM_PROMPT_V20, outline_prompt, timeout=50)
    if not bp or not isinstance(bp.get("outline"), list) or len(bp["outline"]) < max(3, n_ch - 2):
        fb["provider"] = "v20-deterministic-fallback"
        return fb

    outline = bp["outline"][:n_ch]
    while len(outline) < n_ch:
        outline.append({"chapter_title": fb["chapters"][len(outline)]["chapter_title"], "focus": "Verified turning point and aftermath."})

    buckets = _slice_dossier_into_buckets(dossier, n_ch)
    final_chapters = []
    prev_closing = ""
    for i in range(n_ch):
        slice_txt = " ".join(f"[{h}] {s}" for h, s in buckets[i])[:4200]
        ch_plan = outline[i]
        ch_prompt = (
            f"DOCUMENTARY TITLE: {bp.get('video_title', fb['video_title'])}\n"
            f"CHANNEL: {dossier['channel_name']} | SUBJECT: {dossier['wiki_title']} ({dossier['year']})\n"
            f"CHAPTER {i+1} OF {n_ch}: {ch_plan.get('chapter_title', fb['chapters'][i]['chapter_title'])}\n"
            f"ANGLE: {ch_plan.get('focus', '')}\n"
            f"{'OPENING CHAPTER: Start immediately with an unforgettable cold-open hook!' if i == 0 else ''}"
            f"{'FINAL CHAPTER: Deliver an unforgettable conclusion & mention our official illustrated book in the description.' if i == n_ch - 1 else 'End with a smooth investigative hook into the next chapter.'}\n"
            f"{('PREVIOUS CHAPTER ENDED WITH: ' + prev_closing) if prev_closing else ''}\n\n"
            f"VERIFIED ARCHIVAL FACTS FOR THIS CHAPTER:\n{slice_txt}"
        )
        ch_res, ch_prov = _call_llm_json_v20(CHAPTER_SYSTEM_PROMPT_V20, ch_prompt, timeout=50)
        fb_ch = fb["chapters"][i]
        if ch_res and isinstance(ch_res, dict) and len(str(ch_res.get("narration", "")).split()) >= 110:
            for ck, cv in fb_ch.items():
                if not ch_res.get(ck):
                    ch_res[ck] = cv
            ch_res["narration"] = re.sub(r"[\[\]\*#_`]", "", str(ch_res["narration"])).strip()
            ch_res["chapter_title"] = _trim_words(ch_res["chapter_title"], 40)
            final_chapters.append(ch_res)
            prov = ch_prov or prov
        else:
            final_chapters.append(fb_ch)
        prev_closing = final_chapters[-1]["narration"][-220:]
        time.sleep(0.9)

    final_chapters = _dedupe_chapter_titles_v20(final_chapters)
    res = {
        "video_title": _clean_doc_title_v20(bp.get("video_title") or fb["video_title"], year=dossier["year"], max_c=92),
        "thumb_white": _trim_words(bp.get("thumb_white") or fb["thumb_white"], 20).upper(),
        "thumb_red": _trim_words(bp.get("thumb_red") or fb["thumb_red"], 14).upper(),
        "thumb_stamp": _trim_words(bp.get("thumb_stamp") or fb["thumb_stamp"], 16).upper(),
        "thumb_pill": _trim_words(bp.get("thumb_pill") or fb["thumb_pill"], 15).upper(),
        "video_queries_broll": bp.get("video_queries_broll") or [],
        "tags": bp.get("tags") or fb["tags"],
        "chapters": final_chapters,
        "provider": prov or "v20-hybrid",
    }
    tot_w = sum(len(c["narration"].split()) for c in res["chapters"])
    print(f"[V20.5 LONGFORM SCRIPT OK via {res['provider']}] '{res['video_title']}' | {n_ch} chapters | {tot_w} words (~{tot_w/150:.1f} min)")
    return res


def fmt_ts(sec):
    return f"{int(sec // 60):02d}:{int(sec % 60):02d}"


def _render_chapter_v20_job(job):
    """Parallel multi-core V20.5 Cinema Chapter Worker (real moving videos + Johnny Harris dossiers!)."""
    idx, total_ch, ch, ch_ev, ch_videos, cfg, cdir = job
    os.makedirs(cdir, exist_ok=True)
    is_final = (idx == total_ch - 1)
    # Show sleek non-intrusive floating mid-chapter Book Banner on Chapter 2 & Penultimate Chapter!
    show_banner = (idx == 1) or (idx == max(2, total_ch - 2) and not is_final)

    voice_mp3 = os.path.join(cdir, "voice.mp3")
    audio_m4a = os.path.join(cdir, "audio.m4a")
    ch_mp4 = os.path.join(cdir, f"ch{idx+1:02d}_v20_1080p.mp4")

    v_dur, words = synthesize_voice_v15(
        ch["narration"], voice_mp3,
        voice=cfg["voice"], rate=cfg.get("voice_rate", "+2%"), pitch=cfg.get("voice_pitch", "-2Hz"),
    )
    speech_off = 0.45
    outro_len = 4.2 if is_final else 0.0
    raw_d = speech_off + v_dur + (outro_len + 0.35 if is_final else 1.2)
    # Snap strictly to exact 24fps frame boundary so audio & video match to 0.000ms across 14 chapters!
    tot_d = round(round(raw_d * 24) / 24.0, 4)
    b = [0.0, 0.22, 0.44, 0.64, 0.82, 1.0]
    sfx_plan = [
        (0.28, "braaam", 0.38, 0.50),
        (tot_d * 0.09, "dive", 0.28, 0.50),
        (tot_d * 0.14, "radar", 0.18, 0.45),
        (tot_d * b[1] - 0.14, "whip", 0.22, 0.62),
        (tot_d * (b[1] + 0.09), "shutter", 0.34, 0.50),
        (tot_d * (b[1] + 0.14), "stamp", 0.38, 0.58),
        (tot_d * b[2] - 0.14, "whip", 0.22, 0.38),
        (tot_d * b[3] - 0.12, "laser", 0.30, 0.50),
    ]
    if is_final:
        sfx_plan.append((tot_d - outro_len - 0.2, "drop", 0.44, 0.50))

    env30, spec30 = mix_cinema_audio_v15(voice_mp3, tot_d, speech_off, audio_m4a, seed=ch_ev["year"] + idx * 19, sfx_plan=sfx_plan)
    actual_d = render_v20_cinema(
        ch_ev, ch, v_dur, words, audio_m4a, env30, spec30,
        ch_mp4, video_clips=ch_videos, vertical=False,
        show_outro=is_final, show_midroll_ad=show_banner,
    )
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
    ap.add_argument("--chapters", type=int, default=0, help="0 = auto-adaptive (7-14 chapters -> 12-30 min)")
    ap.add_argument("--workers", type=int, default=0, help="0 = auto parallel workers")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--work-dir", default="/tmp/v20_longform_work")
    args = ap.parse_args()

    dry = args.dry_run or (os.environ.get("DRY_RUN", "false").lower() == "true")
    privacy = os.environ.get("PRIVACY_STATUS", "public").strip() or "public"
    forced_ch = args.chapters or int(os.environ.get("TARGET_CHAPTERS", "0") or "0")
    workers = args.workers if args.workers > 0 else min(3, max(1, (os.cpu_count() or 2) - 1))
    os.makedirs(args.work_dir, exist_ok=True)

    print(f"=== {cfg['channel_name']} [V20.5 CINEMA BEAST ADAPTIVE DOCUMENTARY — 16:9 1080p] (workers={workers}, dry_run={dry}) ===")
    dossier = scout_deep_documentary_v20(cfg, topic_override=args.topic or None, forced_chapters=forced_ch, work_dir=args.work_dir)
    doc_script = build_longform_script_v20(dossier)

    # 🔥 SCOUT STRICTLY STORY-LOCKED REAL MOVING 16:9 VIDEO CLIPS (Groq Editor Verified!)
    vdir = os.path.join(args.work_dir, "real_videos_16x9")
    real_videos = scout_real_videos_v20(dossier, doc_script, vdir, vertical=False, target_clips=7, dur_sec=9.0)

    all_imgs = dossier["images"]
    n_imgs = len(all_imgs)
    total_ch = len(doc_script["chapters"])

    jobs = []
    for idx, ch in enumerate(doc_script["chapters"]):
        cdir = os.path.join(args.work_dir, f"ch_{idx+1:02d}")
        ch_imgs = [all_imgs[(idx * 2 + k) % n_imgs] for k in range(4)]
        ch_ev = dict(dossier)
        ch_ev["images"] = ch_imgs
        ch_ev["display_date"] = f"CH {idx+1:02d} • {ch['chapter_title'][:22].upper()}"
        # Rotate real verified videos across chapters so every chapter stays fresh!
        if real_videos:
            ch_vids = [real_videos[(idx + k) % len(real_videos)] for k in range(min(4, len(real_videos)))]
        else:
            ch_vids = []
        jobs.append((idx, total_ch, ch, ch_ev, ch_vids, cfg, cdir))

    results = {}
    if workers > 1 and total_ch > 1:
        print(f"[PARALLEL V20.5 RENDER] Dispatching {total_ch} chapters across {workers} CPU workers...")
        with ProcessPoolExecutor(max_workers=workers) as ex:
            futs = [ex.submit(_render_chapter_v20_job, j) for j in jobs]
            for fut in as_completed(futs):
                idx, ch_mp4, actual_d, ch_title = fut.result()
                results[idx] = (ch_mp4, actual_d, ch_title)
                print(f"  [CHAPTER DONE] {idx+1:02d}/{total_ch:02d} '{ch_title}' -> {actual_d:.1f}s")
    else:
        for j in jobs:
            idx, ch_mp4, actual_d, ch_title = _render_chapter_v20_job(j)
            results[idx] = (ch_mp4, actual_d, ch_title)
            print(f"  [CHAPTER DONE] {idx+1:02d}/{total_ch:02d} '{ch_title}' -> {actual_d:.1f}s")

    # 🔥 BUILD FULL-SCREEN NARRATED MID-ROLL 2-BOOK COMMERCIAL BREAK (inserted right at halfway mark!)
    mid_idx = max(1, total_ch // 2)
    ad_dir = os.path.join(args.work_dir, "midroll_book_ad")
    os.makedirs(ad_dir, exist_ok=True)
    is_btc = (cfg["mode"] == "behind_the_curtain")
    ad_voice_txt = (
        "Enjoying this declassified investigation? Go deeper with our official collector's books, "
        "The Declassified Vault and History Unsealed. One hundred seventy-four full-color illustrated pages "
        "covering fifty hidden operations and historical turning points. "
        "Save thirty-three percent on the two-book collector's bundle using the link in the description below. "
        "Now, back to the investigation."
    ) if is_btc else (
        "Enjoying this deep historical investigation? Own the full collector's archive with our two official illustrated books, "
        "History Unsealed and The Declassified Vault. One hundred seventy-four full-color pages packed with fifty archival stories. "
        "Save thirty-three percent with the two-book collector's bundle using the link in the description below. "
        "Now, let's return to the story."
    )
    ad_mp3 = os.path.join(ad_dir, "ad_voice.mp3")
    ad_mp4 = os.path.join(ad_dir, "midroll_2book_commercial.mp4")
    ad_vdur, _ = synthesize_voice_v15(ad_voice_txt, ad_mp3, voice=cfg["voice"], rate="+4%", pitch="-1Hz")
    render_midroll_book_commercial_16x9(cfg["mode"], cfg["channel_name"].upper(), ad_mp3, ad_vdur, ad_mp4, ad_dir)
    ad_actual_d = int(round(max(8.5, ad_vdur + 1.2) * 24)) / 24.0

    # 🔥 ASSEMBLE MASTER MP4 + EXACT CLICKABLE YOUTUBE TIMELINE CHAPTERS (00:00 FORMAT!)
    chapter_mp4s, chapter_lines = [], []
    cursor_t = 0.0
    for idx in range(total_ch):
        if idx == mid_idx:
            chapter_mp4s.append(ad_mp4)
            chapter_lines.append(f"{fmt_ts(cursor_t)} Official Illustrated Collector's Books (Save 33%)")
            cursor_t += ad_actual_d
        ch_mp4, actual_d, ch_title = results[idx]
        chapter_mp4s.append(ch_mp4)
        chapter_lines.append(f"{fmt_ts(cursor_t)} {ch_title}")
        cursor_t += actual_d

    concat_txt = os.path.join(args.work_dir, "concat.txt")
    with open(concat_txt, "w") as f:
        for p in chapter_mp4s:
            f.write(f"file '{os.path.abspath(p)}'\n")
    master_mp4 = os.path.join(args.work_dir, "v20_cinema_master_1080p.mp4")
    # Stream-copy video (fast, lossless) + re-mux ONE seamless PTS-locked AAC audio stream (ZERO cumulative sync drift!)
    subprocess.run([
        FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", concat_txt,
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-ac", "2",
        "-af", "aresample=async=1:first_pts=0",
        "-movflags", "+faststart", master_mp4,
    ], check=True)

    # 🔥 GENERATE VIRAL SPLIT-SCREEN REAL-ARCHIVAL THUMBNAIL (auto-selects real archival people/photos!)
    t_left, t_right = pick_best_thumb_photos(all_imgs)
    thumb_jpg = os.path.join(args.work_dir, "v20_viral_thumb_1280x720.jpg")
    generate_v20_thumbnail(
        t_left, t_right, cfg["channel_name"],
        doc_script["thumb_white"], doc_script["thumb_red"],
        doc_script["thumb_stamp"], thumb_jpg,
        center_pill=doc_script.get("thumb_pill"),
    )

    yt_title = doc_script["video_title"][:98]
    sources_txt = "\n".join(s for s in dossier.get("sources", []) if s)
    yt_desc = (
        f"{yt_title}\n\n"
        f"{dossier['summary']}\n\n"
        f"CHAPTERS:\n" + "\n".join(chapter_lines) + "\n\n"
        f"{cfg['description_footer']}\n\n"
        f"Verified Archival Sources:\n{sources_txt}\n"
        f"Map cartography © Esri World Imagery Satellite.\n\n"
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
            f"🎬🔥 <b>{cfg['channel_name']} [V20.5 CINEMA BEAST] — 16:9 Documentary LIVE!</b>\n\n"
            f"🏆 <b>{yt_title}</b>\n"
            f"⏱️ Duration: {fmt_ts(cursor_t)} ({total_ch} YouTube Chapters + Mid-Roll 2-Book Ad + Viral Split Thumb)\n"
            f"🎞️ Real Videos: {len(real_videos)} Story-Locked Clips | AI: {doc_script['provider']}\n"
            f"▶️ https://www.youtube.com/watch?v={vid_id}\n"
            f"🔒 Privacy: <code>{privacy}</code>"
        )
    else:
        print(f"[V20.5 LONGFORM DRY RUN OK] {master_mp4} ({fmt_ts(cursor_t)}, {total_ch} chapters) | Thumb: {thumb_jpg}")
        print("YOUTUBE CHAPTERS:\n" + "\n".join(chapter_lines))


if __name__ == "__main__":
    main()
