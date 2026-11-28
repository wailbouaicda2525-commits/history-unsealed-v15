#!/usr/bin/env python3
"""
V21 EMPIRE FACEBOOK SOCIAL & TEASER AUTOPILOT — fb_social_autopilot_v21.py
Channel-aware (reads channel_config.json for Behind The Curtain OR History Unsealed):
  - `--mode teaser_doc`:  1080x1350 Cinema Premiere Teaser Poster ~2h BEFORE next Full Documentary!
  - `--mode teaser_reel`: 1080x1350 Classified Countdown Poster ~2h BEFORE peak daily Reel!
  - `--mode carousel`:    4-Slide 1080x1350 Declassified Archival Mini-Dossier Carousel!
  - `--mode text`:        Viral Historical Debate Poll + Next Documentary Sneak Peek!
  - `--mode welcome`:     Official Page Launch Welcome Post + 4-Slide Brand Showcase Carousel!
"""
import argparse
import datetime as dt
import json
import os
import random
import re
import textwrap
from pathlib import Path
import requests
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

from publisher_facebook_v21 import (
    publish_fb_carousel,
    publish_fb_photo_post,
    publish_fb_text_post,
    fb_is_configured,
)

BASE_DIR = Path(__file__).resolve().parent
FONT_BLACK = str(BASE_DIR / "fonts/Montserrat-Black.ttf")
FONT_BOLD = str(BASE_DIR / "fonts/Montserrat-Bold.ttf")
if not Path(FONT_BLACK).exists():
    FONT_BLACK = str(BASE_DIR / "fonts/Montserrat-Var.ttf")
    FONT_BOLD = FONT_BLACK

BTC_TOPICS_FALLBACK = [
    ("Project Azorian", "1974", "PACIFIC OCEAN", "How the CIA built a fake mining ship to steal a sunken Soviet nuclear submarine 3 miles underwater"),
    ("Operation Gold", "1955", "EAST BERLIN", "The secret 1,476-foot CIA tunnel dug straight under the Soviet sector of Berlin — and the mole who betrayed it"),
    ("Stanislav Petrov", "1983", "SERPUKHOV-15, USSR", "The Soviet officer who saw 5 incoming US nuclear missiles on radar and broke protocol to save humanity"),
    ("Numbers stations", "1968", "IRON CURTAIN", "The eerie Cold War shortwave radio voices transmitting coded espionage orders every night"),
    ("Chernobyl liquidators", "1986", "PRIPYAT, USSR", "The three divers who walked into radioactive water beneath Reactor 4 to prevent a second continental explosion"),
    ("Vasili Arkhipov", "1962", "CARIBBEAN SEA", "The lone Soviet submarine officer who refused to authorize a nuclear torpedo during the Cuban Missile Crisis"),
]

HU_TOPICS_FALLBACK = [
    ("Assassination of John F. Kennedy", "1963", "DALLAS, TEXAS", "Inside the 6 seconds in Dallas and the declassified files that reshaped American history"),
    ("Apollo 11", "1969", "HOUSTON, TEXAS", "1202 Program Alarm: How Apollo 11 came 25 seconds from aborting humanity's first Moon landing"),
    ("Cuban Missile Crisis", "1962", "WASHINGTON & HAVANA", "13 days on the brink: the secret backchannel letters that stopped nuclear war"),
    ("Sinking of the Titanic", "1912", "NORTH ATLANTIC", "The fatal chain of ignored ice warnings and missing binoculars on the night of April 14, 1912"),
    ("Isabella Stewart Gardner Museum theft", "1990", "BOSTON, USA", "81 minutes in Boston: how two fake police officers vanished with $500 million in priceless art"),
    ("Dyatlov Pass incident", "1959", "URAL MOUNTAINS", "Inside the eerie 1959 expedition that left nine experienced hikers dead in the frozen Urals"),
]


def _load_cfg() -> dict:
    return json.loads((BASE_DIR / "channel_config.json").read_text(encoding="utf-8"))


def _theme(cfg: dict) -> dict:
    is_btc = (cfg.get("mode") == "behind_the_curtain")
    if is_btc:
        return {
            "is_btc": True,
            "name": "BEHIND THE CURTAIN",
            "primary": (220, 38, 38),
            "accent": (248, 250, 252),
            "gold": (245, 158, 11),
            "tint": (10, 12, 18),
            "badge": "DECLASSIFIED ARCHIVE  •  1945–1991",
            "hashtags": "#BehindTheCurtain #ColdWar #Declassified #SecretHistory #HistoryDocumentary",
        }
    return {
        "is_btc": False,
        "name": "HISTORY UNSEALED",
        "primary": (238, 195, 76),
        "accent": (205, 32, 42),
        "gold": (238, 195, 76),
        "tint": (10, 12, 20),
        "badge": "OFFICIAL DOCUMENTARY ARCHIVE  •  UNSEALED",
        "hashtags": "#HistoryUnsealed #USHistory #UntoldHistory #HistoryDocumentary #OnThisDay",
    }


def _next_upcoming_doc(cfg: dict) -> tuple[str, str, str, str]:
    """Reads state/longform_log.json + exact catalog to identify the NEXT unpublished documentary!"""
    used = set()
    lp = BASE_DIR / "state/longform_log.json"
    if lp.exists():
        try:
            used = {x.get("id", "") for x in json.loads(lp.read_text(encoding="utf-8"))}
        except Exception:
            pass
    try:
        if cfg.get("mode") == "behind_the_curtain":
            from scout_v15 import BTC_SECRET_CATALOG as cat
        else:
            from longform_v20 import DAILY_ARCHIVE_LONGFORM_CATALOG as cat
        for item in cat:
            cid = f"doc:{re.sub(r'[^a-z0-9]+', '_', item[0].lower())}"
            if cid not in used:
                return str(item[0]), str(item[1]), str(item[2]), str(item[5])
    except Exception:
        pass
    pool = BTC_TOPICS_FALLBACK if cfg.get("mode") == "behind_the_curtain" else HU_TOPICS_FALLBACK
    return random.choice(pool)


def _groq_json(prompt: str, max_tokens: int = 1000) -> dict | None:
    api_key = os.environ.get("GROQ_API_KEY", "").strip()
    if not api_key:
        return None
    for model in ("openai/gpt-oss-120b", "qwen/qwen3-32b"):
        payload = {
            "model": model,
            "temperature": 0.88,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": "Output ONLY valid JSON for viral, authoritative US documentary Facebook posts."},
                {"role": "user", "content": prompt},
            ],
        }
        if "gpt-oss" in model:
            payload["reasoning_effort"] = "low"
        else:
            payload["response_format"] = {"type": "json_object"}
        try:
            r = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                json=payload,
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json", "User-Agent": "UnsealedFB/2.1"},
                timeout=45,
            )
            r.raise_for_status()
            txt = r.json()["choices"][0]["message"]["content"]
            txt = re.sub(r"<think>[\s\S]*?</think>", "", txt, flags=re.I).strip()
            m = re.search(r"\{[\s\S]*\}", txt)
            if m:
                return json.loads(m.group(0))
        except Exception as e:
            print(f"[FB-SOCIAL] Groq skip ({model}: {e})", flush=True)
    return None


def _fit_font(dr: ImageDraw.ImageDraw, text: str, path: str, max_w: int, start_sz: int, min_sz: int = 22):
    sz = start_sz
    while sz >= min_sz:
        f = ImageFont.truetype(path, sz)
        if dr.textlength(text, font=f) <= max_w:
            return f
        sz -= 2
    return ImageFont.truetype(path, min_sz)


def _draw_wrapped(dr, text, font, cx, y0, max_chars, fill, lh, stroke_w=0, max_lines=4):
    y = y0
    for ln in textwrap.wrap(text, width=max_chars)[:max_lines]:
        if stroke_w:
            dr.text((cx, y), ln, font=font, fill=fill, stroke_width=stroke_w, stroke_fill=(6, 8, 14, 255), anchor="mm")
        else:
            dr.text((cx, y), ln, font=font, fill=fill, anchor="mm")
        y += lh
    return y


def _bg_canvas(W: int, H: int, theme: dict, blur: int = 0) -> Image.Image:
    src = BASE_DIR / "assets/fb_bg.jpg"
    if src.exists():
        raw = Image.open(src).convert("RGB")
        rw, rh = raw.size
        tr = W / float(H)
        if rw / float(rh) > tr:
            nw = int(rh * tr)
            raw = raw.crop(((rw - nw) // 2, 0, (rw + nw) // 2, rh)).resize((W, H), Image.LANCZOS)
        else:
            nh = int(rw / tr)
            raw = raw.crop((0, (rh - nh) // 2, rw, (rh + nh) // 2)).resize((W, H), Image.LANCZOS)
        if blur:
            raw = raw.filter(ImageFilter.GaussianBlur(radius=blur))
        raw = ImageEnhance.Contrast(raw).enhance(1.12)
        return Image.alpha_composite(raw.convert("RGBA"), Image.new("RGBA", (W, H), (*theme["tint"], 145)))
    return Image.new("RGBA", (W, H), (*theme["tint"], 255))


def _render_teaser_poster(out_path: Path, theme: dict, is_doc: bool, year: str, loc: str, head1: str, head2: str, cliff: str, cta: str) -> Path:
    W, H = 1080, 1350
    canvas = _bg_canvas(W, H, theme, blur=2)

    # Paste iconic circular brand seal / avatar cleanly in upper-center spotlight (y=216..536)
    av_p = BASE_DIR / "assets/fb_avatar.png"
    if av_p.exists():
        d = 310
        av = Image.open(av_p).convert("RGBA").resize((d, d), Image.LANCZOS)
        m = Image.new("L", (d, d), 0)
        ImageDraw.Draw(m).ellipse([4, 4, d - 5, d - 5], fill=255)
        mx, my = (W - d) // 2, 224
        ring = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        rdr = ImageDraw.Draw(ring)
        rdr.ellipse([mx - 10, my - 10, mx + d + 10, my + d + 10], fill=(*theme["primary"], 245))
        rdr.ellipse([mx - 4, my - 4, mx + d + 4, my + d + 4], fill=(8, 10, 16, 255))
        canvas.alpha_composite(ring)
        canvas.paste(av, (mx, my), m)

    grad = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gdr = ImageDraw.Draw(grad)
    for y in range(520, H):
        a = int(248 * ((y - 520) / float(H - 520)) ** 1.12)
        gdr.line([(0, y), (W, y)], fill=(6, 8, 14, a))
    canvas.alpha_composite(grad)

    dr = ImageDraw.Draw(canvas)
    border = theme["primary"]
    dr.rectangle([16, 16, W - 17, H - 17], outline=(*border, 235), width=7)
    dr.rectangle([30, 30, W - 31, H - 31], outline=(255, 255, 255, 65), width=2)

    # Top Countdown Ribbon
    rib_txt = "FULL DOCUMENTARY PREMIERE  •  IN 2 HOURS!" if is_doc else "NEW DECLASSIFIED REEL  •  DROPPING SOON!"
    rib_bg = (205, 28, 36, 255) if (theme["is_btc"] or not is_doc) else (238, 195, 76, 255)
    rib_fg = (255, 255, 255, 255) if rib_bg[0] == 205 else (10, 14, 22, 255)
    f_r = _fit_font(dr, rib_txt, FONT_BLACK, W - 150, 32, 22)
    rw = min(W - 92, int(dr.textlength(rib_txt, font=f_r)) + 64)
    dr.rounded_rectangle([W // 2 - rw // 2, 54, W // 2 + rw // 2, 124], radius=14, fill=rib_bg, outline=(255, 255, 255, 220), width=3)
    dr.text((W // 2, 89), rib_txt, font=f_r, fill=rib_fg, anchor="mm")

    # File Stamp Pill
    st_txt = f"{theme['name']}  •  FILE {year}  •  {loc[:22]}".upper()
    f_s = _fit_font(dr, st_txt, FONT_BLACK, W - 140, 24, 18)
    sw = min(W - 104, int(dr.textlength(st_txt, font=f_s)) + 48)
    dr.rounded_rectangle([W // 2 - sw // 2, 142, W // 2 + sw // 2, 192], radius=12, fill=(14, 18, 28, 235), outline=(*border, 220), width=2)
    dr.text((W // 2, 167), st_txt, font=f_s, fill=(*border, 255), anchor="mm")

    # Sneak Peek Tag
    snk = "PRE-RELEASE DOSSIER  •  NO SPOILERS"
    f_sn = ImageFont.truetype(FONT_BLACK, 23)
    snw = int(dr.textlength(snk, font=f_sn)) + 44
    dr.rounded_rectangle([W // 2 - snw // 2, 566, W // 2 + snw // 2, 608], radius=18, fill=(12, 16, 26, 235), outline=(255, 255, 255, 175), width=2)
    dr.text((W // 2, 587), snk, font=f_sn, fill=(248, 250, 252, 250), anchor="mm")

    # Giant 2-Line Title
    h1, h2 = head1.upper().strip()[:22], head2.upper().strip()[:22]
    f_h1 = _fit_font(dr, h1, FONT_BLACK, W - 110, 92, 46)
    f_h2 = _fit_font(dr, h2, FONT_BLACK, W - 110, 96, 48)
    dr.text((W // 2, 686), h1, font=f_h1, fill=(255, 255, 255, 255), stroke_width=10, stroke_fill=(6, 8, 14, 255), anchor="mm")
    dr.text((W // 2, 782), h2, font=f_h2, fill=(*border, 255), stroke_width=10, stroke_fill=(6, 8, 14, 255), anchor="mm")

    # Cliffhanger Box
    dr.rounded_rectangle([68, 856, W - 68, 1144], radius=22, fill=(10, 14, 24, 232), outline=(*border, 200), width=3)
    dr.text((W // 2, 894), "DECLASSIFIED PREVIEW", font=ImageFont.truetype(FONT_BLACK, 25), fill=(*border, 255), anchor="mm")
    _draw_wrapped(dr, cliff, ImageFont.truetype(FONT_BOLD, 34), W // 2, 954, 41, (241, 245, 249, 255), 44, stroke_w=2, max_lines=4)

    # Bottom CTA
    c_clean = cta.upper().strip()[:40]
    f_c = _fit_font(dr, c_clean, FONT_BLACK, W - 140, 30, 20)
    cw = min(W - 104, int(dr.textlength(c_clean, font=f_c)) + 64)
    cta_bg = (205, 28, 36, 255)
    dr.rounded_rectangle([W // 2 - cw // 2, 1184, W // 2 + cw // 2, 1266], radius=18, fill=cta_bg, outline=(255, 255, 255, 235), width=3)
    dr.text((W // 2, 1225), c_clean, font=f_c, fill=(255, 255, 255, 255), anchor="mm")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(out_path, quality=93, optimize=True)
    return out_path


def _render_slide(out_path: Path, idx: int, total: int, theme: dict, kicker: str, head: str, body: str, cta: str) -> Path:
    W, H = 1080, 1350
    canvas = _bg_canvas(W, H, theme, blur=3 if idx in (2, 3) else 1)
    if idx in (1, 4) and (BASE_DIR / "assets/fb_avatar.png").exists():
        d = 290
        av = Image.open(BASE_DIR / "assets/fb_avatar.png").convert("RGBA").resize((d, d), Image.LANCZOS)
        m = Image.new("L", (d, d), 0)
        ImageDraw.Draw(m).ellipse([4, 4, d - 5, d - 5], fill=255)
        mx, my = (W - d) // 2, 184
        canvas.paste(av, (mx, my), m)

    grad = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gdr = ImageDraw.Draw(grad)
    for y in range(380, H):
        a = int(242 * ((y - 380) / float(H - 380)) ** 1.2)
        gdr.line([(0, y), (W, y)], fill=(6, 8, 14, a))
    canvas.alpha_composite(grad)

    dr = ImageDraw.Draw(canvas)
    border = theme["primary"]
    dr.rectangle([16, 16, W - 17, H - 17], outline=(*border, 225), width=7)

    f_p = ImageFont.truetype(FONT_BLACK, 27)
    pill = f"{theme['name']}  •  {kicker}".upper()[:36]
    pw = min(W - 220, int(dr.textlength(pill, font=f_p)) + 48)
    dr.rounded_rectangle([54, 52, 54 + pw, 110], radius=12, fill=(*border, 255))
    fg_p = (255, 255, 255, 255) if theme["is_btc"] else (10, 14, 22, 255)
    dr.text((54 + pw // 2, 81), pill, font=f_p, fill=fg_p, anchor="mm")

    dr.rounded_rectangle([W - 156, 52, W - 54, 110], radius=12, fill=(20, 26, 40, 240), outline=(*border, 220), width=2)
    dr.text((W - 105, 81), f"{idx}/{total}", font=f_p, fill=(255, 255, 255, 255), anchor="mm")

    f_h = ImageFont.truetype(FONT_BLACK, 66 if idx == 1 else 58)
    f_b = ImageFont.truetype(FONT_BOLD, 37)
    hy = 580 if idx in (1, 4) else 450
    ny = _draw_wrapped(dr, head.upper(), f_h, W // 2, hy, 18, (255, 255, 255, 255) if idx == 1 else (*border, 255), 78, stroke_w=8, max_lines=3)
    _draw_wrapped(dr, body, f_b, W // 2, ny + 44, 36, (241, 245, 249, 255), 50, stroke_w=2, max_lines=5)

    c_txt = cta.upper()[:38]
    f_c = _fit_font(dr, c_txt, FONT_BLACK, W - 140, 29, 20)
    cw = min(W - 108, int(dr.textlength(c_txt, font=f_c)) + 60)
    dr.rounded_rectangle([W // 2 - cw // 2, H - 140, W // 2 + cw // 2, H - 72], radius=16, fill=(205, 28, 36, 255), outline=(255, 255, 255, 235), width=3)
    dr.text((W // 2, H - 106), c_txt, font=f_c, fill=(255, 255, 255, 255), anchor="mm")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(out_path, quality=93, optimize=True)
    return out_path


def run_teaser(cfg: dict, is_doc: bool, dry_run: bool) -> None:
    th = _theme(cfg)
    topic, year, loc, premise = _next_upcoming_doc(cfg)
    kind = "Full 15-25 Minute Deep Documentary" if is_doc else "Brand-New 60-Second Declassified Archive Reel"
    prompt = f"""Write a gripping, SPOILER-FREE Facebook pre-release teaser for '{th['name']}' announcing our upcoming {kind} dropping in ~2 hours!
Topic: {topic} ({year}, {loc})
Verified Context (DO NOT SPOIL THE FINAL REVEAL!): {premise}
Return ONLY valid JSON:
{{
  "poster_top": "BOLD LINE 1 <=16 CHARS ALL CAPS",
  "poster_bottom": "BOLD LINE 2 <=16 CHARS ALL CAPS",
  "poster_cliffhanger": "2 gripping suspense sentences ending in '?' or '...' <=135 chars",
  "poster_cta": "DO YOU KNOW WHAT HAPPENED? COMMENT!",
  "fb_caption": "Compelling 5-7 line Facebook teaser post announcing this {kind} drops in ~2 hours! Build real historical mystery without spoiling the ending, ask followers if they've heard of this file before, and include {th['hashtags']} #ComingSoon."
}}"""
    data = _groq_json(prompt, max_tokens=850) or {
        "poster_top": topic.upper()[:16],
        "poster_bottom": f"FILE {year}!",
        "poster_cliffhanger": f"{premise[:125]}... Watch the full archive drop in 2 hours!",
        "poster_cta": "COMMENT IF YOU KNOW THIS FILE!",
        "fb_caption": (
            f"🚨 {'FULL DOCUMENTARY PREMIERE' if is_doc else 'NEW DECLASSIFIED REEL'} DROPPING IN ~2 HOURS!\n\n"
            f"📁 FILE: {topic} ({year} • {loc})\n"
            f"{premise}.\n\n"
            f"👇 Have you ever heard the real story buried inside this file? Tell us what you think happened before it goes live!\n"
            f"🔔 Follow {th['name']} & turn on notifications so you don't miss the premiere!\n\n"
            f"{th['hashtags']} #ComingSoon"
        ),
    }
    out = Path(f"/tmp/fb_teaser_{cfg['mode']}_{'doc' if is_doc else 'reel'}.jpg")
    _render_teaser_poster(out, th, is_doc, year, loc, str(data["poster_top"]), str(data["poster_bottom"]), str(data["poster_cliffhanger"]), str(data["poster_cta"]))
    print(f"[FB TEASER] Rendered {out} | {th['name']} | Topic='{topic}' ({year})", flush=True)
    if dry_run:
        print("[DRY-RUN CAPTION]:\n", data["fb_caption"], flush=True)
        return
    publish_fb_photo_post(out, str(data["fb_caption"]).strip())


def run_carousel(cfg: dict, is_welcome: bool, dry_run: bool) -> None:
    th = _theme(cfg)
    topic, year, loc, premise = _next_upcoming_doc(cfg)
    if is_welcome:
        if th["is_btc"]:
            data = {
                "caption": (
                    "🎬 WELCOME TO BEHIND THE CURTAIN — OFFICIAL DECLASSIFIED DOCUMENTARY ARCHIVE!\n\n"
                    "Every single day we unseal real Cold War espionage files, hidden bunkers, and ordinary lives behind the Iron Curtain (1945–1991):\n"
                    "🔴 Daily 60-Second Declassified Reels\n"
                    "🎥 Full 15–30 Minute Cinema Documentaries (Every 2 Days)\n"
                    "📂 Real Archival Files, Spy Maps & Collector's Editions\n\n"
                    "👇 Which Cold War secret should we investigate NEXT? Drop a year or codename in the comments!\n\n"
                    f"{th['hashtags']}"
                ),
                "slides": [
                    ("WELCOME", "BEHIND THE CURTAIN", "Real archives, hidden operations & ordinary lives inside the Cold War (1945–1991).", "SWIPE INSIDE THE VAULT ->"),
                    ("DAILY REELS", "60-SECOND ARCHIVES", "Every day we unpack one forgotten covert mission, bunker, or declassified file.", "SWIPE FOR DOCUMENTARIES ->"),
                    ("FULL DOCS", "DEEP INVESTIGATIONS", "Full 15–30 minute cinematic documentaries with real archival footage & satellite maps.", "SWIPE TO REQUEST A FILE ->"),
                    ("YOUR PICK", "WHAT FILE NEXT?", "Comment a Cold War mystery, spy operation, or year you want us to investigate!", "DROP YOUR TOPIC BELOW!"),
                ],
            }
        else:
            data = {
                "caption": (
                    "🎬 WELCOME TO HISTORY UNSEALED — OFFICIAL HISTORICAL DOCUMENTARY ARCHIVE!\n\n"
                    "Every single day we reopen the turning points, forgotten mysteries, and defining hours of American & World History:\n"
                    "🟡 Daily 60-Second Archival Reels\n"
                    "🎥 Full 15–30 Minute Deep Documentaries (Every 2 Days)\n"
                    "📜 Verified Archives, Real Footage & Collector's Editions\n\n"
                    "👇 Which historical turning point should we unseal NEXT? Drop your request below!\n\n"
                    f"{th['hashtags']}"
                ),
                "slides": [
                    ("WELCOME", "HISTORY UNSEALED", "True turning points, forgotten archives & the untold hours that shaped the modern world.", "SWIPE INSIDE THE ARCHIVE ->"),
                    ("DAILY REELS", "ON THIS DAY & BEYOND", "Fast-paced 60-second historical documentaries backed by real archival footage.", "SWIPE FOR FULL DOCS ->"),
                    ("FULL DOCS", "CINEMA DEEP DIVES", "15–30 minute investigative documentaries covering the moments history almost forgot.", "SWIPE TO PICK NEXT FILE ->"),
                    ("YOUR PICK", "WHAT EVENT NEXT?", "Comment a mystery, year, or turning point in American or World history below!", "COMMENT YOUR REQUEST!"),
                ],
            }
    else:
        prompt = f"""Create a 4-slide viral Facebook archival mini-story carousel for '{th['name']}' about '{topic}' ({year}, {loc}: {premise}).
Return ONLY valid JSON:
{{
  "caption": "Engaging 4-line historical Facebook caption ending with a debate question + {th['hashtags']}",
  "slides": [
    ["FILE {year}", "SHOCK HEADLINE <=26 CHARS", "Gripping opening hook <=110 chars", "SWIPE TO UNSEAL ->"],
    ["THE SECRET", "HIDDEN DETAIL <=26 CHARS", "Key verified turning point <=115 chars", "SWIPE FOR THE TWIST ->"],
    ["THE TWIST", "STUNNING REVEAL <=26 CHARS", "Shocking aftermath or fact <=115 chars", "SWIPE TO DEBATE ->"],
    ["YOUR VERDICT", "WHAT WOULD YOU DO?", "Thought-provoking question forcing comments <=110 chars", "COMMENT YOUR TAKE BELOW!"]
  ]
}}"""
        data = _groq_json(prompt, max_tokens=1100) or {
            "caption": f"📂 DECLASSIFIED ({year}): {premise}\n\nWhat would YOU have done in that room? Share your take below! 👇\n\n{th['hashtags']}",
            "slides": [
                (f"FILE {year}", topic[:24], premise[:110], "SWIPE TO UNSEAL ->"),
                ("THE RECORD", f"{loc[:24]}", f"In {year}, few outside the classified briefing room knew how close history came to breaking.", "SWIPE FOR THE TWIST ->"),
                ("THE AFTERMATH", "BURIED FOR DECADES", "Only decades later did declassified archives reveal what truly unfolded behind closed doors.", "SWIPE TO DEBATE ->"),
                ("YOUR VERDICT", "WOULD YOU SPEAK UP?", "If you held this classified truth, would you expose it or protect national secrecy?", "COMMENT YOUR TAKE BELOW!"),
            ],
        }

    out_dir = Path(f"/tmp/fb_carousel_{cfg['mode']}")
    paths = [_render_slide(out_dir / f"s{i}.jpg", i, 4, th, k, h, b, c) for i, (k, h, b, c) in enumerate(data["slides"][:4], 1)]
    print(f"[FB CAROUSEL] Rendered 4 slides in {out_dir} | {th['name']}", flush=True)
    if dry_run:
        print("[DRY-RUN CAPTION]:\n", data["caption"], flush=True)
        return
    publish_fb_carousel(paths, str(data["caption"]).strip())


def run_text(cfg: dict, dry_run: bool) -> None:
    th = _theme(cfg)
    topic, year, loc, premise = _next_upcoming_doc(cfg)
    prompt = f"""Write ONE viral, concise Facebook historical discussion post (85-125 words) for '{th['name']}'.
Ask a gripping 'WHAT WOULD YOU HAVE DONE?' question grounded in real history, give 3 choices (A, B, C), AND end with a 1-line '👀 UPCOMING DOCUMENTARY SNEAK PEEK' hinting at '{topic} ({year})' without spoiling it!
Include {th['hashtags']}. Return ONLY valid JSON: {{"message": "..."}}"""
    res = _groq_json(prompt, max_tokens=500)
    msg = str(res["message"]).strip() if (res and res.get("message")) else (
        f"⚖️ HISTORICAL DILEMMA — WHAT WOULD YOU HAVE DONE?\n\n"
        f"You're the duty officer on shift in {year}. Classified intelligence lands on your desk that could change millions of lives — but your orders say: STAY SILENT.\n\n"
        f"🅰️ Follow orders and protect secrecy\n"
        f"🅱️ Break protocol and warn the world\n"
        f"🇨 Demand an emergency review before acting\n\n"
        f"Drop A, B, or C below — let's debate! 👇\n\n"
        f"👀 UPCOMING DOCUMENTARY SNEAK PEEK: Next we unseal '{topic} ({year})' — stay tuned! 🔔\n\n"
        f"{th['hashtags']}"
    )
    if dry_run:
        print("[DRY-RUN TEXT]:\n", msg, flush=True)
        return
    publish_fb_text_post(msg)


def main():
    cfg = _load_cfg()
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["teaser_doc", "teaser_reel", "carousel", "text", "welcome"], default="teaser_doc")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if not args.dry_run and not fb_is_configured():
        print("[FB SOCIAL] FB_PAGE_ID / FB_PAGE_ACCESS_TOKEN not configured yet — exiting cleanly.", flush=True)
        return
    if args.mode == "teaser_doc":
        run_teaser(cfg, is_doc=True, dry_run=args.dry_run)
    elif args.mode == "teaser_reel":
        run_teaser(cfg, is_doc=False, dry_run=args.dry_run)
    elif args.mode == "welcome":
        run_carousel(cfg, is_welcome=True, dry_run=args.dry_run)
    elif args.mode == "text":
        run_text(cfg, dry_run=args.dry_run)
    else:
        run_carousel(cfg, is_welcome=False, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
