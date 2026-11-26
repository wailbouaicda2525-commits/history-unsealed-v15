"""
scriptwriter_v15.py — V15 BEAST Viral US-Audience Documentary Scriptwriter
1) Free Google Gemini API (GEMINI_API_KEY)
2) Free Groq API (GROQ_API_KEY)
3) Upgraded Zero-Fail High-Retention American/BBC Documentary Writer (offline fallback)
"""
import os
import re
import json
import urllib.request

SYSTEM_PROMPT = """You are the lead documentary showrunner writing for a high-RPM Tier-1 US YouTube audience (Johnny Harris x LEMMiNO x MagnatesMedia x Netflix Cold War style).
Given a verified historical event, write an electrifying 46-to-53 second documentary narration (118 to 136 words) strictly grounded in the provided facts.

RULES:
1. FIRST 3 SECONDS MUST BE A BRUTAL SCROLL-STOPPING HOOK (no 'Welcome back', no 'Did you know', no fluff). Start right inside the tension, date, or shocking twist!
2. Crisp, cinematic spoken American documentary pacing. Short sentences mixed with dramatic reveals. Plain words ONLY (no emojis, no hashtags, no stage directions, no brackets).
3. Return ONLY valid JSON with these exact keys:
{
  "title": "High-CTR US YouTube title <= 66 chars (curiosity gap, complete words, NO #Shorts)",
  "newspaper_headline": "DRAMATIC 4-6 WORD VINTAGE NEWSPAPER HEADLINE (ALL CAPS)",
  "thumb_hook": "2-3 GIANT ALL-CAPS THUMBNAIL WORDS (e.g. 'VANISHED MID-AIR' or '5 MINUTES TO WW3')",
  "narration": "118-136 word gripping factual documentary narration in plain English.",
  "polaroid_caption": "Short archival evidence caption <= 42 chars (ALL CAPS)",
  "stamp_line1": "1-2 WORD RED STAMP (ALL CAPS, e.g. 'UNSOLVED' or 'TOP SECRET')",
  "stamp_line2": "SHORT SUB-STAMP <= 22 chars (ALL CAPS)",
  "forensic_header": "CLASSIFIED DOSSIER HEADER <= 38 chars (ALL CAPS)",
  "forensic_lines": [
    "LINE 1: Verified date/codename fact <= 42 chars",
    "LINE 2: Verified location/turning point <= 42 chars",
    "LINE 3: Verified shocking aftermath <= 42 chars"
  ],
  "split_left_label": "SHORT LABEL <= 18 chars (ALL CAPS, e.g. 'OFFICIAL RECORD')",
  "split_right_label": "SHORT LABEL <= 18 chars (ALL CAPS, e.g. 'DECLASSIFIED')",
  "climax_stat_label": "SHORT EYEBROW <= 26 chars (ALL CAPS)",
  "climax_stat_big": "BOLD NUMBER OR YEAR <= 18 chars (ALL CAPS)",
  "climax_stat_sub": "IMPACT CONTEXT <= 38 chars (ALL CAPS)",
  "tags": ["history", "us history", "history documentary", "cold war", "declassified", "3-5 topic tags"]
}"""


def _extract_json(raw_text):
    m = re.search(r"\{[\s\S]*\}", raw_text)
    if not m:
        raise ValueError("No JSON found")
    return json.loads(m.group(0))


def _trim_words(txt, max_c):
    txt = re.sub(r"\s+", " ", str(txt or "")).strip(" ,.;:-")
    if len(txt) <= max_c:
        return txt
    cut = txt[:max_c + 1].rsplit(" ", 1)[0].strip(" ,.;:-")
    return cut if cut else txt[:max_c].strip(" ,.;:-")


def _call_gemini(prompt, api_key):
    for model in ("gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": f"{SYSTEM_PROMPT}\n\nVERIFIED DOSSIER:\n{prompt}"}]}],
            "generationConfig": {"temperature": 0.72, "responseMimeType": "application/json"},
        }
        req = urllib.request.Request(
            url, data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}, method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.loads(r.read().decode("utf-8"))
            txt = data["candidates"][0]["content"]["parts"][0]["text"]
            return _extract_json(txt), f"gemini:{model}"
        except Exception as e:
            print(f"[SCRIPT] Gemini {model} skipped: {e}")
    return None, None


def _call_groq(prompt, api_key):
    url = "https://api.groq.com/openai/v1/chat/completions"
    payload = {
        "model": "llama-3.3-70b-versatile",
        "temperature": 0.72,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"VERIFIED DOSSIER:\n{prompt}"},
        ],
    }
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read().decode("utf-8"))
        txt = data["choices"][0]["message"]["content"]
        return _extract_json(txt), "groq:llama-3.3-70b"
    except Exception as e:
        print(f"[SCRIPT] Groq skipped: {e}")
    return None, None


def _deterministic_v15_fallback(ev):
    """High-retention deterministic American documentary writer when no LLM key is set."""
    cname = ev.get("channel_name", "THE DAILY ARCHIVE")
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

    if is_btc:
        hook_title = _trim_words(ev.get("hook_hint") or summary, 64)
        narration = (
            f"In {ev['year']}, a classified operation unfolded that almost nobody was ever meant to hear about. "
            f"{summary} "
            + (" ".join(extra_sents[:2]) + " " if extra_sents else "")
            + f"For decades, intelligence files kept the full scale of what happened near {ev['location'].title()} locked behind closed doors. "
            f"Subscribe to {cname.title()} for the next declassified file."
        )
        stamp1 = "TOP SECRET"
        header = f"DECLASSIFIED DOSSIER • {ev['year']}"
    else:
        date_sp = f"{ev['month_name']} {ev['day']}, {ev['year']}"
        hook_title = _trim_words(f"{date_sp}: {summary}", 64)
        narration = (
            f"{date_sp}. In a single afternoon, history changed forever. "
            f"{summary} "
            + (" ".join(extra_sents[:2]) + " " if extra_sents else "")
            + f"Investigators, witnesses, and historians still study what unfolded at {ev['location'].title()} decades later. "
            f"Follow {cname.title()} for tomorrow's unbelievable true story."
        )
        stamp1 = "DECLASSIFIED"
        header = f"ARCHIVE DOSSIER • {ev['date_label']}"

    words = narration.split()
    if len(words) > 134:
        cut = " ".join(words[:126])
        if "." in cut:
            cut = cut.rsplit(".", 1)[0] + "."
        narration = cut + f" Follow {cname.title()} for the next true story."

    # Extract a crisp punchy headline + any notable number in text for the V15 climax stat!
    num_m = re.search(r"(\$[\d,]+(?:\s*(?:million|billion))?|\b\d{1,3}(?:,\d{3})+\b|\b\d+\s*(?:miles|feet|hours|days|years|men|people|bombs|minutes)\b)", summary + " " + " ".join(extra_sents), re.I)
    stat_big = num_m.group(1).upper()[:18] if num_m else str(ev["year"])

    news_hl = _trim_words(ev.get("hook_hint") or summary, 44).upper()
    return {
        "title": hook_title,
        "newspaper_headline": news_hl,
        "thumb_hook": f"SECRET OF {ev['year']}",
        "narration": narration,
        "polaroid_caption": f"FILE #{ev['year']}-{ev['month']:02d}{ev['day']:02d} • {ev['location'][:18]}",
        "stamp_line1": stamp1,
        "stamp_line2": ev["display_date"][:22],
        "forensic_header": header[:38],
        "forensic_lines": [
            f"DATE: {ev['display_date'][:32]}",
            f"SECTOR: {ev['location'][:30]}",
            f"RECORD: {_trim_words(summary, 42).upper()}",
        ],
        "split_left_label": "ARCHIVAL PLATE A",
        "split_right_label": "DECLASSIFIED PLATE B",
        "climax_stat_label": f"VERIFIED RECORD • {ev['year']}",
        "climax_stat_big": stat_big,
        "climax_stat_sub": f"LOCATION: {ev['location'][:26]}",
        "tags": [
            "history", "us history", "history documentary", "cold war",
            "declassified", "secret history", "on this day", str(ev["year"])
        ],
    }


def write_script_v15(ev):
    prompt = (
        f"CHANNEL BRAND: {ev.get('channel_name', 'THE DAILY ARCHIVE')}\n"
        f"DATE: {ev['date_label']}\n"
        f"LOCATION: {ev['location']} ({ev['lat']}, {ev['lon']})\n"
        f"HEADLINE: {ev.get('hook_hint', ev['summary'])}\n"
        f"SUMMARY: {ev['summary']}\n"
        f"VERIFIED WIKIPEDIA FACTS:\n{ev['extracts'][:2400]}"
    )

    result, provider = None, "fallback"
    gem_key = os.environ.get("GEMINI_API_KEY", "").strip()
    groq_key = os.environ.get("GROQ_API_KEY", "").strip()

    if gem_key:
        result, provider = _call_gemini(prompt, gem_key)
    if result is None and groq_key:
        result, provider = _call_groq(prompt, groq_key)
    if result is None:
        result = _deterministic_v15_fallback(ev)
        provider = "v15-deterministic-fallback"

    fb = _deterministic_v15_fallback(ev)
    for k, v in fb.items():
        if k not in result or not result[k]:
            result[k] = v
    result["narration"] = re.sub(r"[\[\]\*#_`]", "", str(result["narration"])).strip()
    result["title"] = _trim_words(result["title"], 68)
    result["provider"] = provider
    print(f"[SCRIPT V15 OK via {provider}] Title: {result['title']} | Words: {len(result['narration'].split())}")
    return result
