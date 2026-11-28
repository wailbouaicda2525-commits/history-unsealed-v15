"""
scriptwriter_v20.py — V20 CINEMA BEAST Viral US-Audience Documentary Showrunner
Priority Order (2026 Verified Live!):
  1) Free Groq API (GROQ_API_KEY) -> qwen/qwen3.8-27b (primary) & openai/gpt-oss-120b (backup)
  2) Free Google Gemini API (GEMINI_API_KEY)
  3) Zero-Fail High-Retention Documentary Fallback

Outputs gripping narration + custom real-video search queries (Pixabay B-Roll + Internet Archive films)
+ Johnny Harris live-highlighted classified dossier lines!
"""
import os
import re
import ssl
import json
import urllib.request

SSL_CTX = ssl.create_default_context()
UA = "UnsealedArchivesV20/2.0 (https://youtube.com/@behindthecurtainworld)"

SYSTEM_PROMPT_V20 = """You are the lead viral documentary showrunner writing for a high-RPM Tier-1 US YouTube audience (Johnny Harris x LEMMiNO x Fern x Netflix Cold War style).
Given a verified historical event, write an electrifying 42-to-48 second documentary narration (110 to 124 words) strictly grounded in the provided facts, PLUS exact real-video search queries AND high-CTR YouTube Title + Thumbnail + 0-3s Hook synergy.

STRICT VIRAL HOOK RULES (FIRST 8 WORDS DECIDE 80% OF VIEWS!):
1. NEVER start with dead clichés like "On this day", "For decades", "In history", "Welcome", "Did you know", "Today", "A single turning point", or "Have you ever wondered".
2. OPEN INSIDE PEAK TENSION in the VERY FIRST SENTENCE using one of these 5 viral formulas:
   - Countdown/Clock Stake: "Three seconds from nuclear war, one Russian officer refused the firing order."
   - Impossible Secret/Price Tag: "The CIA spent $350 million building a fake ship just to steal a sunken Soviet submarine."
   - Fatal 1-Second Mistake: "A single unlocked door in 1972 brought down the most powerful president on Earth."
   - Buried Evidence Paradox: "For forty years, officials called this photo a hoax — until the vault opened."
   - Shocking Scale/Survival: "At 5:12 AM, one crack beneath San Francisco erased an entire city in seventy-two hours."
3. THUMBNAIL + TITLE CURIOSITY SYNERGY: The thumbnail text (`thumb_white` + `thumb_red`) MUST be 2-4 MASSIVE punchy words total (NEVER repeat the full title!). It must create an instant curiosity gap when paired with the YouTube title!
4. Crisp, cinematic spoken American documentary pacing. Short punchy sentences mixed with dramatic reveals. Plain spoken English ONLY (no emojis, no hashtags, no stage directions, no brackets).
5. Return ONLY valid JSON with these exact keys:
{
  "title": "High-CTR US YouTube title <= 66 chars (curiosity gap, complete words, NO #Shorts)",
  "hook_top": "2-3 WORD GIANT COLD-OPEN HOOK (ALL CAPS, e.g. 'FIVE MINUTES TO WW3')",
  "hook_sub": "SHORT CONTEXT LINE <= 32 chars (ALL CAPS, e.g. 'OCT 27, 1962 • CUBAN BLOCKADE')",
  "hook_teaser": "GRIPPING CURIOSITY OPEN-LOOP LINE <= 40 chars (ALL CAPS, e.g. 'BURIED IN CIA VAULTS FOR 40 YEARS')",
  "newspaper_headline": "DRAMATIC 4-6 WORD VINTAGE NEWSPAPER HEADLINE (ALL CAPS)",
  "thumb_hook": "2-3 GIANT ALL-CAPS THUMBNAIL WORDS (e.g. 'ONE MAN STOPPED WW3')",
  "thumb_white": "1-3 SHORT WHITE WORDS FOR THUMBNAIL <= 16 chars (ALL CAPS, e.g. 'THE CIA STOLE A' or '3 SECONDS TO')",
  "thumb_red": "1-2 EXPLOSIVE POWER WORDS <= 13 chars (ALL CAPS, e.g. 'SOVIET SUB' or 'WW3')",
  "thumb_stamp": "SHORT RED RUBBER STAMP BADGE <= 16 chars (ALL CAPS, e.g. 'CIA ARCHIVE' or 'DECLASSIFIED')",
  "thumb_pill": "SHORT YEAR/ERA TAG <= 14 chars (e.g. '1968 -> 1974' or 'OCT 1962')",
  "narration": "110-124 word gripping factual documentary narration in plain English (must open with a brutal 0-3s hook and finish cleanly under 49 seconds).",
  "polaroid_caption": "Short archival evidence caption <= 42 chars (ALL CAPS)",
  "stamp_line1": "1-2 WORD RED STAMP (ALL CAPS, e.g. 'DECLASSIFIED' or 'TOP SECRET')",
  "stamp_line2": "SHORT SUB-STAMP <= 22 chars (ALL CAPS)",
  "forensic_header": "CLASSIFIED DOSSIER HEADER <= 38 chars (ALL CAPS)",
  "forensic_lines": [
    "LINE 1: Verified date/codename fact <= 42 chars",
    "LINE 2: Verified location/turning point <= 42 chars",
    "LINE 3: Verified shocking aftermath <= 42 chars"
  ],
  "split_left_label": "SHORT LABEL <= 18 chars (ALL CAPS, e.g. 'ARCHIVAL FILM')",
  "split_right_label": "SHORT LABEL <= 18 chars (ALL CAPS, e.g. 'DECLASSIFIED FILE')",
  "climax_stat_label": "SHORT EYEBROW <= 26 chars (ALL CAPS)",
  "climax_stat_big": "BOLD NUMBER OR YEAR <= 18 chars (ALL CAPS)",
  "climax_stat_sub": "IMPACT CONTEXT <= 38 chars (ALL CAPS)",
  "video_queries_broll": [
    "1-2 concrete visual nouns for Pixabay video (NEVER use 'close up', e.g. 'submarine underwater')",
    "1-2 concrete visual nouns for tension (e.g. 'radar military' or 'ocean storm')",
    "1-2 concrete visual nouns for investigation (e.g. 'typewriter document' or 'map compass')",
    "1-2 concrete visual nouns for climax (e.g. 'battleship sea' or 'rocket launch')"
  ],
  "video_queries_archival": [
    "2-3 word historical film query for Internet Archive / NARA (e.g. 'cold war submarine')",
    "2-3 word historical film query (e.g. 'atomic missile navy')"
  ],
  "tags": ["history", "us history", "history documentary", "cold war", "declassified", "3-5 topic tags"]
}"""


def _extract_json(raw_text):
    txt = re.sub(r"<think>[\s\S]*?</think>", "", str(raw_text or ""), flags=re.I).strip()
    m = re.search(r"\{[\s\S]*\}", txt)
    if not m:
        raise ValueError("No JSON found in response")
    return json.loads(m.group(0))


def _trim_words(txt, max_c):
    txt = re.sub(r"\s+", " ", str(txt or "")).strip(" ,.;:-")
    if len(txt) <= max_c:
        return txt
    cut = txt[:max_c + 1].rsplit(" ", 1)[0].strip(" ,.;:-")
    return cut if cut else txt[:max_c].strip(" ,.;:-")


def _clean_yt_title(txt, max_c=88):
    """V20.7.2: Guarantees complete, punchy YouTube titles with ZERO mid-word cutoffs or unclosed parentheses."""
    s = re.sub(r"\s+", " ", str(txt or "")).strip(" ,.;:-–—")
    s = re.sub(r"\s*#shorts\b", "", s, flags=re.I).strip(" ,.;:-–—")
    if len(s) > max_c:
        # First try dropping trailing parenthetical suffix if it pushes over limit
        no_par = re.sub(r"\s*\([^)]*\)\s*$", "", s).strip(" ,.;:-–—")
        if 24 <= len(no_par) <= max_c:
            s = no_par
        else:
            s = _trim_words(s, max_c)
    # Never leave an unclosed '(' or '['
    if s.count("(") > s.count(")"):
        s = s.rsplit("(", 1)[0].strip(" ,.;:-–—")
    if s.count("[") > s.count("]"):
        s = s.rsplit("[", 1)[0].strip(" ,.;:-–—")
    # Never end on a dangling function word
    dangling = {"a", "an", "the", "of", "in", "to", "for", "with", "and", "or", "by", "from", "on", "at", "that", "who", "which", "full"}
    parts = s.split()
    while len(parts) > 3 and parts[-1].lower().strip(".,:;-–—") in dangling:
        parts.pop()
    return " ".join(parts).strip(" ,.;:-–—")


def _call_groq_v20(prompt, api_key, sys_prompt=SYSTEM_PROMPT_V20, max_tokens=1600):
    """2026 Verified Live Groq Models: qwen/qwen3.8-27b (primary) -> openai/gpt-oss-120b (backup)."""
    url = "https://api.groq.com/openai/v1/chat/completions"
    for model in ("qwen/qwen3.8-27b", "openai/gpt-oss-120b"):
        payload = {
            "model": model,
            "temperature": 0.72,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": f"VERIFIED DOSSIER:\n{prompt}"},
            ],
        }
        if "gpt-oss" in model:
            payload["reasoning_effort"] = "low"
        else:
            payload["response_format"] = {"type": "json_object"}
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
                "User-Agent": UA,
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=35, context=SSL_CTX) as r:
                data = json.loads(r.read().decode("utf-8"))
            txt = data["choices"][0]["message"].get("content", "")
            if not txt:
                raise ValueError("Empty content")
            return _extract_json(txt), f"groq:{model}"
        except Exception as e:
            print(f"[SCRIPT-V20] Groq {model} skipped: {e}")
    return None, None


def _call_gemini_v20(prompt, api_key, sys_prompt=SYSTEM_PROMPT_V20):
    for model in ("gemini-2.5-flash", "gemini-2.0-flash"):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": f"{sys_prompt}\n\nVERIFIED DOSSIER:\n{prompt}"}]}],
            "generationConfig": {"temperature": 0.72, "responseMimeType": "application/json"},
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "User-Agent": UA},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30, context=SSL_CTX) as r:
                data = json.loads(r.read().decode("utf-8"))
            txt = data["candidates"][0]["content"]["parts"][0]["text"]
            return _extract_json(txt), f"gemini:{model}"
        except Exception as e:
            print(f"[SCRIPT-V20] Gemini {model} skipped: {e}")
    return None, None


def _deterministic_v20_fallback(ev):
    cname = ev.get("channel_name", "HISTORY UNSEALED")
    is_btc = (ev.get("mode") == "behind_the_curtain")
    summary = re.sub(r"\([^)]*\)", "", ev["summary"]).strip()
    summary = re.sub(r"\s+", " ", summary)
    if not summary.endswith("."):
        summary += "."

    extra_sents = []
    for line in ev.get("extracts", "").split("\n"):
        parts = re.split(r"(?<=[.!?])\s+", line.split(":", 1)[-1].strip())
        for s in parts:
            s = re.sub(r"\([^)]*\)", "", s).strip()
            s = re.sub(r"\s+", " ", s)
            if 48 <= len(s) <= 175 and s[:36].lower() not in summary.lower():
                extra_sents.append(s)
            if len(extra_sents) >= 2:
                break
        if len(extra_sents) >= 2:
            break

    extra_txt = " ".join(extra_sents)
    if is_btc:
        narration = (
            f"In {ev['year']}, one classified mission over {ev['location'].title()} was buried so deep even presidents weren't told the full truth. "
            f"{summary} {extra_txt} "
            f"Satellite coordinates reveal how razor-thin the margin was between quiet survival and global disaster. "
            f"When the vault finally opened, historians realized the official story was only half the picture. "
            f"Subscribe to {cname.title()} for tomorrow's declassified file."
        )
    else:
        narration = (
            f"One split-second decision in {ev['location'].title()} during {ev['year']} changed history forever — and almost nobody remembers how close it came to failing. "
            f"{summary} {extra_txt} "
            f"Textbooks bury this moment in a single quiet paragraph, yet the real archival record is far more intense. "
            f"Subscribe to {cname.title()} for tomorrow's unsealed file."
        )
    words = narration.split()
    if len(words) > 136:
        narration = " ".join(words[:132]).rstrip(",;:") + "."

    short_t = re.sub(r"\([^)]*\)", "", ev.get("title") or ev.get("hook_hint") or ev["summary"][:60]).strip()
    raw_fb_title = f"{ev['year']}: The Untold Truth Behind {short_t}"
    if len(raw_fb_title) > 88:
        raw_fb_title = f"{ev['year']}: {short_t}"
    return {
        "title": _clean_yt_title(raw_fb_title, 88),
        "hook_top": _trim_words(f"DECLASSIFIED {ev['year']}" if is_btc else f"UNTOLD {ev['year']}", 22).upper(),
        "hook_sub": _trim_words(f"{ev['display_date']} • {ev['location']}", 32).upper(),
        "hook_teaser": "BURIED IN CLASSIFIED FILES FOR DECADES" if is_btc else "THE TRUE RECORD TEXTBOOKS LEFT OUT",
        "newspaper_headline": _trim_words(f"{ev['year']}: {short_t}", 36).upper(),
        "thumb_hook": _trim_words(f"SECRET {ev['year']}" if is_btc else f"UNTOLD {ev['year']}", 18).upper(),
        "thumb_white": _trim_words("THEY HID THIS" if is_btc else "HISTORY HID", 16).upper(),
        "thumb_red": str(ev["year"]),
        "thumb_stamp": "CIA ARCHIVE" if is_btc else "UNSEALED",
        "thumb_pill": str(ev["year"]),
        "narration": narration,
        "polaroid_caption": _trim_words(f"ARCHIVE FILE • {short_t}", 40).upper(),
        "stamp_line1": "TOP SECRET" if is_btc else "VERIFIED",
        "stamp_line2": _trim_words(f"DOSSIER {ev['year']}", 20).upper(),
        "forensic_header": _trim_words(f"CASE FILE // {short_t}", 36).upper(),
        "forensic_lines": [
            _trim_words(f"DATE RECORDED: {ev['display_date']}", 42).upper(),
            _trim_words(f"SITE: {ev['location']} ({ev['lat']}N, {ev['lon']}E)", 42).upper(),
            _trim_words("ARCHIVE STATUS: FULL DECLASSIFICATION", 42).upper(),
        ],
        "split_left_label": "ARCHIVAL FILM",
        "split_right_label": "DECLASSIFIED FILE",
        "climax_stat_label": "HISTORICAL TURNING POINT",
        "climax_stat_big": str(ev["year"]),
        "climax_stat_sub": _trim_words(f"{ev['location']} ARCHIVE RECORD", 36).upper(),
        "video_queries_broll": [],
        "video_queries_archival": [],
        "tags": ["history", "us history", "history documentary", "declassified", "secret history", str(ev["year"])],
    }


def write_script_v20(ev):
    """Master V20 Showrunner: Groq 2026 Live -> Gemini -> Zero-Fail Fallback."""
    ev_title = ev.get("title") or ev.get("hook_hint") or ev.get("summary", "")[:80]
    prompt = (
        f"CHANNEL: {ev.get('channel_name', 'HISTORY UNSEALED')}\n"
        f"MODE: {ev.get('mode', 'daily_archive')}\n"
        f"EVENT TITLE: {ev_title}\n"
        f"DATE: {ev.get('date_label', ev['display_date'])} (Year {ev['year']})\n"
        f"LOCATION: {ev['location']} ({ev['lat']}, {ev['lon']})\n"
        f"VERIFIED SUMMARY: {ev['summary']}\n"
        f"ADDITIONAL VERIFIED FACTS:\n{ev.get('extracts', '')[:2600]}"
    )

    out, src = None, None
    groq_key = os.environ.get("GROQ_API_KEY", "").strip()
    gem_key = os.environ.get("GEMINI_API_KEY", "").strip()

    # 1) GROQ FIRST (verified blazing fast 2026 live models!)
    if groq_key:
        out, src = _call_groq_v20(prompt, groq_key)
    # 2) GEMINI SECOND
    if not out and gem_key:
        out, src = _call_gemini_v20(prompt, gem_key)
    # 3) FALLBACK
    if not out:
        out = _deterministic_v20_fallback(ev)
        src = "v20-deterministic-fallback"

    fb = _deterministic_v20_fallback(ev)
    for k, v in fb.items():
        if not out.get(k):
            out[k] = v

    # Sanitize lengths (V20.7.2: allow up to 88 chars so complete titles NEVER drop final nouns before #Shorts!)
    out["title"] = _clean_yt_title(out["title"], 88)
    out["hook_top"] = _trim_words(out["hook_top"], 22).upper()
    out["hook_sub"] = _trim_words(out["hook_sub"], 34).upper()
    out["hook_teaser"] = _trim_words(out.get("hook_teaser") or fb["hook_teaser"], 42).upper()
    out["newspaper_headline"] = _trim_words(out["newspaper_headline"], 42).upper()
    out["thumb_hook"] = _trim_words(out["thumb_hook"], 22).upper()
    if not out.get("thumb_white") or not out.get("thumb_red"):
        parts = out["thumb_hook"].split()
        if len(parts) >= 3:
            out["thumb_white"] = " ".join(parts[:-1])
            out["thumb_red"] = parts[-1]
        else:
            out["thumb_white"] = out["thumb_hook"]
            out["thumb_red"] = str(ev["year"])
    out["thumb_white"] = _trim_words(out["thumb_white"], 18).upper()
    out["thumb_red"] = _trim_words(out["thumb_red"], 14).upper()
    out["thumb_stamp"] = _trim_words(out.get("thumb_stamp") or ("CIA ARCHIVE" if ev.get("mode") == "behind_the_curtain" else "HISTORY UNSEALED"), 16).upper()
    out["thumb_pill"] = _trim_words(out.get("thumb_pill") or str(ev["year"]), 15).upper()
    out["polaroid_caption"] = _trim_words(out["polaroid_caption"], 42).upper()
    out["stamp_line1"] = _trim_words(out["stamp_line1"], 16).upper()
    out["stamp_line2"] = _trim_words(out["stamp_line2"], 22).upper()
    out["forensic_header"] = _trim_words(out["forensic_header"], 38).upper()
    lines = out.get("forensic_lines") or fb["forensic_lines"]
    out["forensic_lines"] = [_trim_words(re.sub(r"^LINE\s*\d+\s*:\s*", "", str(l), flags=re.I), 42).upper() for l in lines[:3]]
    while len(out["forensic_lines"]) < 3:
        out["forensic_lines"].append(fb["forensic_lines"][len(out["forensic_lines"])])
    out["split_left_label"] = _trim_words(out["split_left_label"], 18).upper()
    out["split_right_label"] = _trim_words(out["split_right_label"], 18).upper()
    out["climax_stat_label"] = _trim_words(out["climax_stat_label"], 26).upper()
    out["climax_stat_big"] = _trim_words(out["climax_stat_big"], 18).upper()
    out["climax_stat_sub"] = _trim_words(out["climax_stat_sub"], 38).upper()
    out["narration"] = re.sub(r"\[[^\]]*\]|\([^)]*\)", "", str(out["narration"])).strip()
    out["narration"] = re.sub(r"\s+", " ", out["narration"])
    # Ensure narration fits cleanly inside ~45-49s so the 4.2s 3D Book Collector Outro NEVER gets clipped!
    n_words = out["narration"].split()
    if len(n_words) > 122:
        # Cut cleanly at last sentence boundary <= 122 words
        clipped = " ".join(n_words[:122])
        last_dot = max(clipped.rfind("."), clipped.rfind("!"), clipped.rfind("?"))
        out["narration"] = clipped[:last_dot + 1] if last_dot > 350 else (clipped.rstrip(",;:") + ".")
    out["source"] = src
    print(f"[SCRIPT-V20] Generated via {src} | words={len(out['narration'].split())} | title={out['title']}")
    return out
