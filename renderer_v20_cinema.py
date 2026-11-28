"""
renderer_v20_cinema.py — V20 CINEMA BEAST REAL-VIDEO DOCUMENTARY COMPOSITOR
Supports 9:16 Shorts (1080x1920 @ 30fps) AND 16:9 Longform Documentaries (1920x1080 @ 24fps).

V20 QUANTUM UPGRADES OVER V15:
  1. REAL MOVING VIDEO BACKGROUNDS in every act (Pixabay HD/4K + Internet Archive NARA/Prelinger + Wikimedia + NASA)
  2. 3-SECOND EXPLOSIVE REAL-VIDEO COLD OPEN HOOK (zero static card wait!)
  3. 3D Earth Globe Orbital Drop -> Dark Esri Tactical Map + Live Radar Sweep + Animated Bezier Vector Arc
  4. Authentic 16mm Archival Film Indicator + Real Moving Video Behind Torn Newspaper / Polaroid Detective Board
  5. Johnny Harris / Vox Live-Sweeping Highlighted TOP SECRET Dossier + 1.75x Glass Magnifying Lens over Moving Video
  6. DUAL REAL-VIDEO SPLIT-SCREEN + Barrel-Curved CRT Real-Video Surveillance Monitor + 16-Band Live FFT Spectrum
  7. BUILT-IN 3D HARDCOVER BOOK COLLECTOR'S PROMO OUTRO ('Unsealed Archives Press' — auto-sells Whop books!)
"""
import os
import math
import shutil
import textwrap
import subprocess
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter

try:
    import imageio_ffmpeg
    FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    FFMPEG = shutil.which("ffmpeg") or "ffmpeg"

from video_scout_v20 import VideoPlateV20

FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
ASSET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
FONT_SANS = os.path.join(FONT_DIR, "SpaceGrotesk.ttf")
FONT_SERIF = os.path.join(FONT_DIR, "Newsreader.ttf")
FONT_MONO = os.path.join(FONT_DIR, "JetBrainsMono-Bold.ttf")
for _fp in (FONT_SANS, FONT_SERIF, FONT_MONO):
    if not os.path.exists(_fp):
        FONT_SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        FONT_SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
        FONT_MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"


def load_font(path, size, wght=None):
    f = ImageFont.truetype(path, size)
    if wght is not None:
        try:
            f.set_variation_by_axes([wght])
        except Exception:
            pass
    return f


def ease_io(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def ease_out(t):
    t = max(0.0, min(1.0, t))
    return 1.0 - (1.0 - t) ** 3


def ease_back(t, s=1.45):
    t = max(0.0, min(1.0, t)) - 1.0
    return 1.0 + (s + 1.0) * (t ** 3) + s * (t ** 2)


def cover_plate(path, tw, th, sat=0.80, con=1.18, br=0.86):
    im = Image.open(path).convert("RGB")
    iw, ih = im.size
    sc = max(tw / float(iw), th / float(ih))
    nw, nh = int(round(iw * sc)), int(round(ih * sc))
    im = im.resize((nw, nh), Image.LANCZOS)
    x0, y0 = (nw - tw) // 2, (nh - th) // 2
    im = im.crop((x0, y0, x0 + tw, y0 + th))
    im = ImageEnhance.Color(im).enhance(sat)
    im = ImageEnhance.Contrast(im).enhance(con)
    im = ImageEnhance.Brightness(im).enhance(br)
    return cv2.cvtColor(np.asarray(im), cv2.COLOR_RGB2BGR)


def comp_rgba(dst_bgr, ov_rgba, cx, cy, alpha=1.0):
    oh, ow = ov_rgba.shape[:2]
    dh, dw = dst_bgr.shape[:2]
    x0, y0 = int(round(cx - ow / 2.0)), int(round(cy - oh / 2.0))
    sx0, sy0 = max(0, -x0), max(0, -y0)
    dx0, dy0 = max(0, x0), max(0, y0)
    w = min(ow - sx0, dw - dx0)
    h = min(oh - sy0, dh - dy0)
    if w <= 0 or h <= 0:
        return dst_bgr
    patch = ov_rgba[sy0:sy0 + h, sx0:sx0 + w]
    a = (patch[:, :, 3:4].astype(np.float32) / 255.0) * float(alpha)
    fg = patch[:, :, [2, 1, 0]].astype(np.float32)
    bg = dst_bgr[dy0:dy0 + h, dx0:dx0 + w].astype(np.float32)
    dst_bgr[dy0:dy0 + h, dx0:dx0 + w] = np.clip(fg * a + bg * (1.0 - a), 0, 255).astype(np.uint8)
    return dst_bgr


def comp_pil(dst_bgr, pil_im, cx, cy, scale=1.0, angle=0.0, alpha=1.0, shadow=False):
    if alpha <= 0.01 or scale <= 0.02:
        return dst_bgr
    im = pil_im
    if abs(scale - 1.0) > 0.005:
        im = im.resize((max(2, int(im.width * scale)), max(2, int(im.height * scale))), Image.BILINEAR)
    if abs(angle) > 0.1:
        im = im.rotate(angle, expand=True, resample=Image.BICUBIC)
    arr = np.asarray(im)
    if shadow:
        sh = np.zeros_like(arr)
        sh[:, :, 3] = (arr[:, :, 3].astype(np.float32) * 0.56).astype(np.uint8)
        dst_bgr = comp_rgba(dst_bgr, sh, cx + 12, cy + 18, alpha=alpha)
    return comp_rgba(dst_bgr, arr, cx, cy, alpha=alpha)


def add_anamorphic_flare(frame, y_pos, x_center, intensity=0.45, color_bgr=(60, 185, 255)):
    if intensity <= 0.02:
        return frame
    H, W = frame.shape[:2]
    y0 = max(0, int(y_pos) - 24)
    y1 = min(H, int(y_pos) + 25)
    if y1 <= y0:
        return frame
    xs = np.arange(W, dtype=np.float32)
    ys = np.arange(y0, y1, dtype=np.float32)
    dx = np.exp(-((xs - x_center) / (W * 0.30)) ** 2)[None, :]
    dy = np.exp(-((ys - y_pos) / 7.5) ** 2)[:, None]
    streak = (dy * dx)[:, :, None] * intensity
    band = frame[y0:y1, :, :].astype(np.float32)
    col = np.array(color_bgr, dtype=np.float32)[None, None, :]
    frame[y0:y1, :, :] = np.clip(band + streak * col * 1.45, 0, 255).astype(np.uint8)
    return frame


def sample_25d_beast(plate, W, H, p, style=0, flare_phase=None):
    p = max(0.0, min(1.0, p))
    e = ease_io(p)
    ph, pw = plate.shape[:2]
    if style == 0:
        z, pan_x, pan_y = 1.0 + 0.14 * e, (e - 0.5) * 0.055, (0.5 - e) * 0.03
    elif style == 1:
        z, pan_x, pan_y = 1.15 - 0.11 * e, (0.5 - e) * 0.055, (e - 0.5) * 0.035
    else:
        z, pan_x, pan_y = 1.04 + 0.12 * e, math.sin(e * math.pi) * 0.045, (0.5 - e) * 0.035
    cw, ch = int(pw / z), int(ph / z)
    cx = int(pw * (0.5 + pan_x))
    cy = int(ph * (0.5 + pan_y))
    x0 = max(0, min(pw - cw, cx - cw // 2))
    y0 = max(0, min(ph - ch, cy - ch // 2))
    fr = cv2.resize(plate[y0:y0 + ch, x0:x0 + cw], (W, H), interpolation=cv2.INTER_LINEAR)
    if flare_phase is not None and 0.05 < flare_phase < 0.95:
        fl_i = math.sin(flare_phase * math.pi) * 0.42
        fr = add_anamorphic_flare(fr, int(H * 0.24), int(W * flare_phase), intensity=fl_i, color_bgr=(75, 195, 255))
    return fr


def draw_archival_film_overlay(frame, label="ARCHIVAL FILM // PUBLIC DOMAIN", vertical=True):
    """Authentic 16mm film border accent + sleek translucent archival provenance tag."""
    H, W = frame.shape[:2]
    # Subtle 16mm sprocket edge pips on left/right margins (very tasteful!)
    if not vertical:
        for yy in range(95, H - 95, 92):
            cv2.rectangle(frame, (12, yy), (26, yy + 32), (14, 14, 18), -1)
            cv2.rectangle(frame, (W - 26, yy), (W - 12, yy + 32), (14, 14, 18), -1)
    # Sleek archival provenance badge
    bw = 425
    bx = W - bw - 56 if not vertical else 52
    by = 76 if not vertical else 150
    ov = frame[by:by + 38, bx:bx + bw].copy()
    if ov.size > 0:
        dark = np.full_like(ov, (10, 12, 18))
        frame[by:by + 38, bx:bx + bw] = cv2.addWeighted(ov, 0.25, dark, 0.75, 0)
        cv2.rectangle(frame, (bx, by), (bx + bw, by + 38), (58, 178, 232), 1)
        cv2.circle(frame, (bx + 18, by + 19), 5, (48, 42, 238), -1, cv2.LINE_AA)
        cv2.putText(frame, label[:30], (bx + 32, by + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (238, 224, 172), 1, cv2.LINE_AA)
    return frame


def build_torn_newspaper(headline, date_label, location, width=840):
    h = 285
    im = Image.new("RGBA", (width, h), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    rng = np.random.default_rng(abs(hash(headline)) % (2 ** 31))
    top_pts = [(x, int(10 + rng.integers(-5, 6))) for x in range(12, width - 10, 22)]
    bot_pts = [(x, int(h - 12 + rng.integers(-6, 6))) for x in range(width - 12, 10, -22)]
    poly = [(12, 12)] + top_pts + [(width - 12, 12), (width - 12, h - 12)] + bot_pts + [(12, h - 12)]
    dr.polygon(poly, fill=(236, 227, 206, 255), outline=(170, 158, 134, 255))
    dr.line([(36, 56), (width - 36, 56)], fill=(38, 34, 28, 225), width=3)
    dr.line([(36, 63), (width - 36, 63)], fill=(38, 34, 28, 185), width=1)
    f_mast = load_font(FONT_MONO, 19)
    f_head = load_font(FONT_SERIF, 44, 800)
    f_sub = load_font(FONT_MONO, 18)
    dr.text((width // 2, 34), f"ARCHIVAL PRESS CHRONICLE  •  {date_label.upper()}  •  SPECIAL EDITION", fill=(54, 48, 40, 235), font=f_mast, anchor="mm")
    lines = textwrap.wrap(headline.upper(), width=26)[:2]
    y0 = 115 if len(lines) == 2 else 146
    for i, ln in enumerate(lines):
        dr.text((width // 2, y0 + i * 56), ln, fill=(22, 20, 18, 255), font=f_head, anchor="mm")
    dr.line([(36, h - 52), (width - 36, h - 52)], fill=(38, 34, 28, 185), width=2)
    dr.text((width // 2, h - 32), f"DATELINE: {location[:34].upper()}   |   VERIFIED HISTORICAL RECORD", fill=(92, 82, 68, 230), font=f_sub, anchor="mm")
    return im


def build_3d_book_mockup(cover_path, spine_title="THE DECLASSIFIED VAULT", book_h=470):
    """Build a razor-sharp 3D hardcover book PNG from our actual Book 1 or Book 2 cover!"""
    if not os.path.exists(cover_path):
        return None
    cov = Image.open(cover_path).convert("RGB")
    bw = int(book_h * (cov.width / float(cov.height)))
    cov = cov.resize((bw, book_h), Image.LANCZOS)
    spine_w = max(30, int(bw * 0.13))
    pages_w = max(14, int(bw * 0.055))
    cw = spine_w + bw + pages_w + 48
    ch = book_h + 48
    canvas = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    dr = ImageDraw.Draw(canvas)

    ox, oy = 24, 24
    # Drop shadow
    sh = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([ox + 10, oy + 14, ox + spine_w + bw + pages_w + 6, oy + book_h + 12], radius=8, fill=(0, 0, 0, 175))
    sh = sh.filter(ImageFilter.GaussianBlur(10))
    canvas = Image.alpha_composite(canvas, sh)
    dr = ImageDraw.Draw(canvas)

    # Spine (deep charcoal-navy + gold accent rules)
    dr.rectangle([ox, oy + 6, ox + spine_w, oy + book_h - 4], fill=(16, 20, 30, 255), outline=(218, 178, 82, 235), width=2)
    dr.rectangle([ox + spine_w - 5, oy + 6, ox + spine_w, oy + book_h - 4], fill=(8, 10, 16, 255))
    # Gilded page edges on right
    dr.rectangle([ox + spine_w + bw - 2, oy + 10, ox + spine_w + bw + pages_w, oy + book_h - 10], fill=(238, 228, 204, 255), outline=(170, 154, 124, 255), width=1)
    for px in range(ox + spine_w + bw + 2, ox + spine_w + bw + pages_w - 1, 3):
        dr.line([(px, oy + 12), (px, oy + book_h - 12)], fill=(198, 186, 158, 210), width=1)
    # Front cover pasted cleanly
    canvas.paste(cov.convert("RGBA"), (ox + spine_w, oy))
    # Crisp gold rim & specular book crease highlight
    dr.rectangle([ox + spine_w, oy, ox + spine_w + bw, oy + book_h], outline=(228, 188, 92, 215), width=2)
    dr.line([(ox + spine_w + 10, oy + 2), (ox + spine_w + 10, oy + book_h - 2)], fill=(255, 255, 255, 70), width=3)
    return canvas


def draw_pushpin(frame, x, y):
    cv2.circle(frame, (x + 4, y + 6), 11, (6, 6, 10), -1, cv2.LINE_AA)
    cv2.circle(frame, (x, y), 11, (26, 22, 198), -1, cv2.LINE_AA)
    cv2.circle(frame, (x - 3, y - 3), 4, (130, 130, 255), -1, cv2.LINE_AA)


def apply_magnifying_lens(frame, cx, cy, radius=135, zoom=1.75):
    H, W = frame.shape[:2]
    cx, cy = int(cx), int(cy)
    x0, y0 = max(0, cx - radius), max(0, cy - radius)
    x1, y1 = min(W, cx + radius), min(H, cy + radius)
    if x1 - x0 < 24 or y1 - y0 < 24:
        return frame
    roi = frame[y0:y1, x0:x1]
    rh, rw = roi.shape[:2]
    ys, xs = np.mgrid[0:rh, 0:rw].astype(np.float32)
    dx = (xs + x0 - cx) / float(radius)
    dy = (ys + y0 - cy) / float(radius)
    r2 = dx * dx + dy * dy
    mask = r2 <= 1.0
    factor = (1.0 / zoom) * (1.0 + 0.14 * r2)
    mx = np.clip(cx + dx * radius * factor - x0, 0, rw - 1).astype(np.float32)
    my = np.clip(cy + dy * radius * factor - y0, 0, rh - 1).astype(np.float32)
    zoomed = cv2.remap(roi, mx, my, cv2.INTER_LINEAR)
    glare = np.exp(-(((dx + 0.36) ** 2 + (dy + 0.38) ** 2) / 0.11)) * mask
    zoomed = np.clip(zoomed.astype(np.float32) + glare[:, :, None] * 62.0, 0, 255).astype(np.uint8)
    out_roi = np.where(mask[:, :, None], zoomed, roi)
    frame[y0:y1, x0:x1] = out_roi
    cv2.circle(frame, (cx + 4, cy + 6), radius + 5, (8, 8, 12), 7, cv2.LINE_AA)
    cv2.circle(frame, (cx, cy), radius + 2, (58, 178, 228), 6, cv2.LINE_AA)
    cv2.circle(frame, (cx, cy), radius - 3, (230, 240, 252), 2, cv2.LINE_AA)
    hx1, hy1 = int(cx + radius * 0.72), int(cy + radius * 0.72)
    hx2, hy2 = int(cx + radius * 1.48), int(cy + radius * 1.48)
    cv2.line(frame, (hx1 + 4, hy1 + 6), (hx2 + 4, hy2 + 6), (8, 8, 12), 18, cv2.LINE_AA)
    cv2.line(frame, (hx1, hy1), (hx2, hy2), (38, 44, 58), 16, cv2.LINE_AA)
    cv2.line(frame, (hx1, hy1), (hx2, hy2), (76, 186, 232), 4, cv2.LINE_AA)
    return frame


def build_subtitle_cues(words, speech_off, vertical=True):
    max_words = 3 if vertical else 5
    cues = []
    buf = []
    for w in words:
        s0 = w.get("s", w.get("t0", 0.0)) + speech_off
        e0 = w.get("e", w.get("t1", s0 + 0.25)) + speech_off
        wt = str(w.get("w", "")).upper()
        buf.append({"w": wt, "t0": s0, "t1": e0})
        end_p = bool(wt) and wt[-1] in ".!?,"
        if len(buf) >= max_words or end_p:
            cues.append({"t0": buf[0]["t0"], "t1": buf[-1]["t1"] + 0.08, "words": list(buf)})
            buf = []
    if buf:
        cues.append({"t0": buf[0]["t0"], "t1": buf[-1]["t1"] + 0.08, "words": list(buf)})
    # Clamp cue end times strictly before the next cue starts so captions never lag into the next phrase!
    for idx_c in range(len(cues) - 1):
        if cues[idx_c]["t1"] >= cues[idx_c + 1]["t0"]:
            cues[idx_c]["t1"] = max(cues[idx_c]["t0"] + 0.05, cues[idx_c + 1]["t0"] - 0.01)
    return cues


class SubCacheV20:
    def __init__(self, cues, vertical=True):
        self.cues = cues
        self.vertical = vertical
        self.f = load_font(FONT_SANS, 62 if vertical else 50, 800)
        self.cache = {}

    def get(self, t):
        ci = -1
        for i, c in enumerate(self.cues):
            if c["t0"] <= t <= c["t1"]:
                ci = i
                break
        if ci < 0:
            return None
        cue = self.cues[ci]
        ai = 0
        for j, w in enumerate(cue["words"]):
            if t >= w["t0"] - 0.02:
                ai = j
        key = (ci, ai)
        if key in self.cache:
            return self.cache[key]

        max_w = 960 if self.vertical else 1480
        gap = 20 if self.vertical else 18
        # Auto-fit font size so long words NEVER clip horizontally!
        f_use = self.f
        f_sz = 58 if self.vertical else 48
        tmp = Image.new("RGBA", (max_w, 160), (0, 0, 0, 0))
        dr_t = ImageDraw.Draw(tmp)
        while f_sz >= 34:
            f_use = load_font(FONT_SANS, f_sz, 800)
            widths = [int(dr_t.textlength(w["w"], font=f_use)) for w in cue["words"]]
            tot_w = sum(widths) + gap * (len(widths) - 1)
            if tot_w <= max_w - 76:
                break
            f_sz -= 4
            gap = max(12, gap - 2)
        pad_x = 32
        bw = min(max_w - 8, tot_w + pad_x * 2)
        bh = 104 if self.vertical else 88
        im = Image.new("RGBA", (bw + 16, bh + 16), (0, 0, 0, 0))
        dr = ImageDraw.Draw(im)
        dr.rounded_rectangle([8, 8, bw + 8, bh + 8], radius=16, fill=(8, 10, 16, 224), outline=(248, 206, 72, 195), width=2)
        x = (bw + 16 - tot_w) // 2
        y = (bh + 16) // 2
        pill_h = int(f_sz * 0.64)
        for j, w in enumerate(cue["words"]):
            ww = widths[j]
            if j == ai:
                dr.rounded_rectangle([x - 10, y - pill_h, x + ww + 10, y + pill_h], radius=10, fill=(248, 202, 54, 248))
                dr.text((x, y), w["w"], fill=(12, 12, 16, 255), font=f_use, anchor="lm")
            else:
                dr.text((x + 2, y + 3), w["w"], fill=(0, 0, 0, 210), font=f_use, anchor="lm")
                dr.text((x, y), w["w"], fill=(252, 250, 245, 255), font=f_use, anchor="lm")
            x += ww + gap
        arr = np.asarray(im)
        self.cache[key] = arr
        return arr


def render_v20_cinema(ev, script, voice_dur, words, audio_m4a, env30, spec30, out_mp4,
                      video_clips=None, vertical=True, qa_out=None, show_outro=True, show_midroll_ad=True):
    """
    V20 CINEMA BEAST RENDERER — Real Moving Video Footage + Johnny Harris Highlights + 3D Book Promo Outro!
    """
    W, H = (1080, 1920) if vertical else (1920, 1080)
    FPS = 30 if vertical else 24
    speech_off = 0.45
    outro_len = 4.2 if show_outro else 0.0
    raw_d = speech_off + voice_dur + (outro_len + 0.35 if show_outro else 1.2)
    if vertical:
        raw_d = min(59.0, raw_d)
    n_frames = int(round(raw_d * FPS))
    total_dur = n_frames / float(FPS)
    brand = ev.get("channel_name", "BEHIND THE CURTAIN").upper()
    is_btc = (ev.get("mode") == "behind_the_curtain")
    rng = np.random.default_rng(ev["year"] * 37 + ev["day"] + len(brand))

    # 1) Pre-build Vignette, Fine 35mm Grain, Volumetric Embers, CRT Barrel LUT
    Yg, Xg = np.ogrid[:H, :W]
    Rn = np.sqrt(((Xg - W / 2.0) / (W * 0.58)) ** 2 + ((Yg - H / 2.0) / (H * 0.58)) ** 2)
    VIG = np.clip(1.0 - 0.50 * (np.clip(Rn - 0.36, 0, 1.5) ** 1.85), 0.28, 1.0)[:, :, None].astype(np.float32)

    g_pos, g_neg = [], []
    for _ in range(6):
        g = rng.normal(0, 2.8, (H // 2, W // 2)).astype(np.float32)
        g_pos.append(cv2.cvtColor(cv2.resize(np.clip(g, 0, 10).astype(np.uint8), (W, H), interpolation=cv2.INTER_NEAREST), cv2.COLOR_GRAY2BGR))
        g_neg.append(cv2.cvtColor(cv2.resize(np.clip(-g, 0, 10).astype(np.uint8), (W, H), interpolation=cv2.INTER_NEAREST), cv2.COLOR_GRAY2BGR))

    n_emb = 58
    e_x = rng.uniform(0, W, n_emb); e_y = rng.uniform(0, H, n_emb)
    e_vx = rng.uniform(-24, 34, n_emb); e_vy = rng.uniform(-95, -28, n_emb)
    e_r = rng.integers(2, 6, n_emb)
    e_warm = rng.random(n_emb) > 0.35

    yc_n, xc_n = np.mgrid[0:H, 0:W].astype(np.float32)
    nx = (xc_n - W / 2.0) / (W / 2.0)
    ny = (yc_n - H / 2.0) / (H / 2.0)
    r2 = nx * nx + ny * ny
    k_crt = 0.085
    crt_mx = ((nx * (1.0 + k_crt * r2)) * (W / 2.0) + W / 2.0).astype(np.float32)
    crt_my = ((ny * (1.0 + k_crt * r2)) * (H / 2.0) + H / 2.0).astype(np.float32)

    # 2) Load REAL VIDEO CLIPS (VideoPlateV20) + Archival Photo Fallbacks + Esri Maps
    vplates = []
    vmeta = []
    for vc in (video_clips or []):
        vp = VideoPlateV20(vc["path"], W, H)
        if vp.n >= 24:
            vplates.append(vp)
            vmeta.append(vc)
    print(f"[V20-RENDER] Loaded {len(vplates)} REAL MOVING VIDEO PLATES into compositor!")

    pw, ph = (1280, 2240) if vertical else (2240, 1260)
    plates = [cover_plate(p, pw, ph) for p in ev["images"]]
    while len(plates) < 4:
        plates.append(plates[len(plates) % len(ev["images"])])

    def get_real_video_or_photo(slot_idx, fi, p_loc, darken=1.0, micro_zoom=0.05):
        """Return REAL MOVING VIDEO frame when available, else seamless 2.5D photo fallback."""
        if vplates:
            vi = slot_idx % len(vplates)
            fr = vplates[vi].get_frame(fi + vi * 23, micro_zoom=micro_zoom, p=p_loc)
            if darken < 0.99:
                fr = np.clip(fr.astype(np.float32) * darken, 0, 255).astype(np.uint8)
            return fr, vmeta[vi]
        fr = sample_25d_beast(plates[slot_idx % len(plates)], W, H, p_loc, style=slot_idx % 3)
        if darken < 0.99:
            fr = np.clip(fr.astype(np.float32) * darken, 0, 255).astype(np.uint8)
        return fr, {"source": "photo", "is_archival": False, "tag": ""}

    # Prefer EXACT-STORY real archival video (e.g. from Wikipedia article / NARA exact match / NASA exact match)
    arch_slot = next((i for i, m in enumerate(vmeta) if m.get("exact_story")), None)
    has_exact_archival_video = (arch_slot is not None)
    broll_slots = [i for i, m in enumerate(vmeta) if not m.get("exact_story")]
    b0 = broll_slots[0] if len(broll_slots) > 0 else (0 if vplates else 0)
    b1 = broll_slots[1] if len(broll_slots) > 1 else (b0 if len(broll_slots) > 0 else 0)
    b2 = broll_slots[2] if len(broll_slots) > 2 else (b1 if len(broll_slots) > 1 else b0)

    map_mac = cv2.imread(ev["map_macro"]["path"])
    map_loc = cv2.imread(ev["map_local"]["path"])
    # Ultra-subtle translucent satellite telemetry grid (keeps real Esri Satellite terrain crisp!)
    _grid_ov = map_loc.copy()
    for gx in range(0, map_loc.shape[1], 128):
        cv2.line(_grid_ov, (gx, 0), (gx, map_loc.shape[0]), (145, 195, 215), 1)
    for gy in range(0, map_loc.shape[0], 128):
        cv2.line(_grid_ov, (0, gy), (map_loc.shape[1], gy), (145, 195, 215), 1)
    map_loc = cv2.addWeighted(map_loc, 0.86, _grid_ov, 0.14, 0)

    # 3) 3D Earth Globe LUT
    globe_r = int(min(W, H) * 0.39)
    dx_g, dy_g = (xc_n - W / 2.0) / globe_r, (yc_n - H / 2.0) / globe_r
    rr_g = dx_g * dx_g + dy_g * dy_g
    g_mask = rr_g <= 1.0
    dz_g = np.sqrt(np.clip(1.0 - rr_g, 0.0, 1.0))
    g_shade = np.clip(0.34 + 0.78 * np.clip(dz_g * 0.85 - dx_g * 0.36 - dy_g * 0.25, 0, 1), 0.16, 1.12).astype(np.float32)
    g_rim = (np.clip(1.0 - dz_g, 0, 1) ** 2.9) * g_mask
    g_halo = np.exp(-np.maximum(0.0, np.sqrt(rr_g) - 1.0) * 14.0) * (~g_mask) * (rr_g < 1.38)
    star_bg = np.full((H, W, 3), (4, 6, 12), dtype=np.uint8)
    for _ in range(260):
        c_st = int(rng.integers(165, 245))
        cv2.circle(star_bg, (int(rng.integers(0, W)), int(rng.integers(0, H))), int(rng.integers(1, 3)), (c_st, c_st, min(255, c_st + 18)), -1)
    mh_m, mw_m = map_mac.shape[:2]
    lon_g = np.arcsin(np.clip(dx_g / np.maximum(0.01, np.sqrt(np.clip(1.0 - dy_g * dy_g, 0.001, 1.0))), -1, 1))
    lat_g = np.arcsin(np.clip(dy_g, -1, 1))
    g_mx = (ev["map_macro"]["px"] + lon_g * (mw_m / (2.0 * math.pi))).astype(np.float32)
    g_my = np.clip(ev["map_macro"]["py"] + lat_g * (mh_m / math.pi) * 0.85, 2.0, mh_m - 3.0).astype(np.float32)

    # 4) Fonts & Pre-Built V20 Cinema Assets
    f_huge = load_font(FONT_SANS, 160 if vertical else 184, 800)
    f_big  = load_font(FONT_SANS, 88 if vertical else 102, 800)
    f_hook = load_font(FONT_SANS, 74 if vertical else 86, 800)
    f_h2   = load_font(FONT_SANS, 46 if vertical else 48, 800)
    f_h3   = load_font(FONT_SANS, 34 if vertical else 36, 800)
    f_m24  = load_font(FONT_MONO, 25 if vertical else 23)
    f_m20  = load_font(FONT_MONO, 20 if vertical else 19)
    f_m18  = load_font(FONT_MONO, 18 if vertical else 17)

    news_card = build_torn_newspaper(script["newspaper_headline"], ev["display_date"], ev["location"], width=900 if vertical else 820)

    pol_w, pol_h = (740, 660) if vertical else (740, 580)
    pol_card = Image.new("RGBA", (pol_w, pol_h), (0, 0, 0, 0))
    pdr = ImageDraw.Draw(pol_card)
    pdr.rounded_rectangle([10, 10, pol_w - 10, pol_h - 10], radius=8, fill=(240, 234, 222, 255), outline=(182, 174, 158, 255), width=2)
    im0_bgr = cover_plate(ev["images"][0], pol_w - 68, pol_h - 196, sat=0.84, con=1.22, br=0.95)
    pol_card.paste(Image.fromarray(cv2.cvtColor(im0_bgr, cv2.COLOR_BGR2RGB)), (34, 34))
    pdr.text((38, pol_h - 134), script["polaroid_caption"][:42], fill=(32, 30, 26, 248), font=f_m20)
    pdr.text((38, pol_h - 94), f"GPS: {ev['lat']}°N, {ev['lon']}°E  •  {ev['location'][:22]}", fill=(104, 94, 82, 242), font=f_m18)
    pdr.rectangle([pol_w // 2 - 70, 2, pol_w // 2 + 70, 26], fill=(212, 198, 168, 195))

    st_w, st_h = 430, 126
    stamp = Image.new("RGBA", (st_w, st_h), (0, 0, 0, 0))
    sdr = ImageDraw.Draw(stamp)
    scol = (224, 28, 34, 246)
    sdr.rectangle([6, 6, st_w - 6, st_h - 6], outline=scol, width=7)
    sdr.rectangle([16, 16, st_w - 16, st_h - 16], outline=scol, width=2)
    sdr.text((st_w // 2, 46), script["stamp_line1"][:18], fill=scol, font=f_h3, anchor="mm")
    sdr.text((st_w // 2, 92), script["stamp_line2"][:22], fill=scol, font=f_m20, anchor="mm")
    stamp = stamp.rotate(10, expand=True, resample=Image.BICUBIC)

    dos_cx0 = 72 if vertical else 280
    dos_cx1 = W - 72 if vertical else W - 280
    dos_ph = 340 if vertical else 245
    dos_img_bgr = cover_plate(ev["images"][1 % len(ev["images"])], dos_cx1 - dos_cx0 - 84, dos_ph, sat=0.58, con=1.24, br=0.92)
    dos_inset_pil = Image.fromarray(cv2.cvtColor(dos_img_bgr, cv2.COLOR_BGR2RGB))

    # Climax Glassmorphic Stat Card
    sc_w, sc_h = (880, 320) if vertical else (1040, 310)
    stat_card = Image.new("RGBA", (sc_w, sc_h), (0, 0, 0, 0))
    stdr = ImageDraw.Draw(stat_card)
    stdr.rounded_rectangle([8, 8, sc_w - 8, sc_h - 8], radius=16, fill=(10, 12, 18, 224), outline=(248, 206, 72, 235), width=3)
    stdr.rectangle([8, 8, 22, sc_h - 8], fill=(228, 34, 42, 255))
    stdr.text((sc_w // 2, 66), script["climax_stat_label"][:28], fill=(248, 206, 72, 255), font=f_m24, anchor="mm")
    stdr.text((sc_w // 2, 168), script["climax_stat_big"][:18], fill=(254, 252, 248, 255), font=f_big, anchor="mm")
    stdr.text((sc_w // 2, 260), script["climax_stat_sub"][:38], fill=(195, 202, 215, 255), font=f_m20, anchor="mm")

    # 🔥 BUILT-IN DUAL 3D BOOK MARKETING FUNNEL ('Unsealed Archives Press'):
    #    1) MID-VIDEO SLEEK SLIDE-IN 3D BOOK PROMO BAR (peak curiosity window!)
    #    2) FULL END-SCREEN 2-BOOK COLLECTOR'S OUTRO (flagship + bundle companion book!)
    book_cov_main = os.path.join(ASSET_DIR, "book1_cover.png" if is_btc else "book2_cover.png")
    book_cov_comp = os.path.join(ASSET_DIR, "book2_cover.png" if is_btc else "book1_cover.png")
    book_title_str = "THE DECLASSIFIED VAULT" if is_btc else "HISTORY UNSEALED"
    book_sub_str = "25 SECRET COLD WAR, CIA & KGB FILES" if is_btc else "25 HIDDEN TURNING POINTS IN HISTORY"
    book_3d_main = build_3d_book_mockup(book_cov_main, spine_title=book_title_str, book_h=430 if vertical else 420)
    book_3d_comp = build_3d_book_mockup(book_cov_comp, spine_title="COLLECTOR EDITION", book_h=350 if vertical else 345)
    book_3d_mini = build_3d_book_mockup(book_cov_main, spine_title=book_title_str, book_h=142 if vertical else 132)

    # 1) SLEEK MID-VIDEO PROMO BANNER (slides cleanly under top HUD — zero overlap with subtitles or Shorts bottom UI!)
    mw_a, mh_a = (950, 178) if vertical else (760, 166)
    midroll_ad = Image.new("RGBA", (mw_a, mh_a), (0, 0, 0, 0))
    mdr = ImageDraw.Draw(midroll_ad)
    mdr.rounded_rectangle([6, 6, mw_a - 6, mh_a - 6], radius=16, fill=(10, 14, 24, 238), outline=(238, 194, 78, 248), width=3)
    mdr.rectangle([6, 6, 18, mh_a - 6], fill=(226, 32, 40, 255))
    if book_3d_mini is not None:
        midroll_ad.alpha_composite(book_3d_mini, (26, (mh_a - book_3d_mini.height) // 2))
    tx_m = 202 if vertical else 188
    mdr.rounded_rectangle([tx_m, 22, tx_m + 410, 52], radius=6, fill=(198, 26, 34, 255))
    mdr.text((tx_m + 205, 37), "OFFICIAL BOOK  •  SAVE 33% BUNDLE", fill=(255, 252, 248, 255), font=load_font(FONT_MONO, 16, 700), anchor="mm")
    mdr.text((tx_m, 82), book_title_str, fill=(248, 208, 86, 255), font=load_font(FONT_SANS, 34 if vertical else 30, 800), anchor="lm")
    mdr.text((tx_m, 122), "87 FULL-COLOR PAGES  •  LINK IN DESCRIPTION", fill=(232, 236, 244, 250), font=load_font(FONT_MONO, 18 if vertical else 16, 700), anchor="lm")
    mdr.text((tx_m, 152), "UNSEALED ARCHIVES PRESS  •  INSTANT HD PDF", fill=(166, 178, 198, 230), font=load_font(FONT_MONO, 15, 700), anchor="lm")

    # 2) FULL END-SCREEN 2-BOOK COLLECTOR'S OUTRO
    cw_o, ch_o = (940, 1080) if vertical else (1520, 680)
    outro = Image.new("RGBA", (cw_o, ch_o), (0, 0, 0, 0))
    odr = ImageDraw.Draw(outro)
    odr.rounded_rectangle([10, 10, cw_o - 10, ch_o - 10], radius=22, fill=(9, 13, 22, 242), outline=(228, 184, 76, 245), width=4)
    odr.rounded_rectangle([24, 24, cw_o - 24, ch_o - 24], radius=16, outline=(228, 184, 76, 85), width=2)

    if vertical:
        odr.rounded_rectangle([cw_o // 2 - 330, 56, cw_o // 2 + 330, 108], radius=8, fill=(198, 26, 34, 255))
        odr.text((cw_o // 2, 82), "OFFICIAL ILLUSTRATED COLLECTOR'S BOOKS", fill=(255, 252, 248, 255), font=f_m20, anchor="mm")
        if book_3d_comp is not None:
            comp_rot = book_3d_comp.rotate(-8, expand=True, resample=Image.BICUBIC)
            outro.alpha_composite(comp_rot, (cw_o // 2 + 26, 178))
        if book_3d_main is not None:
            bx_b = (cw_o - book_3d_main.width) // 2 - 75
            outro.alpha_composite(book_3d_main, (bx_b, 126))
        odr.text((cw_o // 2, 628), book_title_str, fill=(248, 208, 86, 255), font=load_font(FONT_SANS, 54, 800), anchor="mm")
        odr.text((cw_o // 2, 686), book_sub_str, fill=(224, 226, 232, 250), font=f_m20, anchor="mm")
        odr.text((cw_o // 2, 738), "87 FULL-COLOR PAGES  •  INSTANT HD PDF", fill=(178, 190, 212, 245), font=f_m20, anchor="mm")
        odr.rounded_rectangle([90, 794, cw_o - 90, 888], radius=14, fill=(226, 32, 40, 255), outline=(248, 208, 86, 255), width=3)
        odr.text((cw_o // 2, 841), "GET THE BOOK — LINK IN DESCRIPTION", fill=(255, 252, 248, 255), font=load_font(FONT_SANS, 29, 800), anchor="mm")
        odr.text((cw_o // 2, 944), "SAVE 33% WITH THE 2-BOOK COLLECTOR'S BUNDLE", fill=(248, 208, 86, 255), font=f_m20, anchor="mm")
        odr.text((cw_o // 2, 1004), f"UNSEALED ARCHIVES PRESS  •  {brand}", fill=(166, 174, 192, 235), font=f_m18, anchor="mm")
    else:
        if book_3d_comp is not None:
            comp_rot = book_3d_comp.rotate(-8, expand=True, resample=Image.BICUBIC)
            outro.alpha_composite(comp_rot, (240, (ch_o - comp_rot.height) // 2 + 24))
        if book_3d_main is not None:
            outro.alpha_composite(book_3d_main, (64, (ch_o - book_3d_main.height) // 2))
        rx = 590
        odr.rounded_rectangle([rx, 86, rx + 580, 136], radius=8, fill=(198, 26, 34, 255))
        odr.text((rx + 290, 111), "OFFICIAL ILLUSTRATED COLLECTOR'S BOOKS", fill=(255, 252, 248, 255), font=f_m20, anchor="mm")
        odr.text((rx, 196), book_title_str, fill=(248, 208, 86, 255), font=load_font(FONT_SANS, 58, 800), anchor="lm")
        odr.text((rx, 268), book_sub_str, fill=(235, 238, 244, 255), font=f_h3, anchor="lm")
        odr.text((rx, 328), "87 FULL-COLOR PAGES  •  25 ARCHIVAL PLATES  •  INSTANT HD PDF", fill=(182, 192, 212, 245), font=f_m20, anchor="lm")
        odr.rounded_rectangle([rx, 392, rx + 820, 482], radius=14, fill=(226, 32, 40, 255), outline=(248, 208, 86, 255), width=3)
        odr.text((rx + 410, 437), "GET YOUR COPY — LINK IN DESCRIPTION BELOW", fill=(255, 252, 248, 255), font=load_font(FONT_SANS, 32, 800), anchor="mm")
        odr.text((rx, 536), "SAVE 33% WITH THE 2-BOOK COLLECTOR'S BUNDLE (174 PAGES)", fill=(248, 208, 86, 255), font=f_m20, anchor="lm")
        odr.text((rx, 594), f"UNSEALED ARCHIVES PRESS  •  SUBSCRIBE TO {brand}", fill=(166, 174, 192, 235), font=f_m18, anchor="lm")

    # 🔥 V21 VIRAL COLD-OPEN HOOK CARD (Pre-built once -> instant Frame-0 clarity + zero per-frame PIL lag!)
    hook_card_v21 = _build_v21_hook_overlay(W, H, ev, script, is_btc, vertical=vertical)

    cues = build_subtitle_cues(words, speech_off, vertical=vertical)
    sub_cache = SubCacheV20(cues, vertical=vertical)
    bounds = [0.0, 0.22, 0.44, 0.64, 0.82, 1.0]
    tr_s = 0.30
    hex_rows = [f"0x{rng.integers(0x1000, 0xFFFF):04X} // {rng.integers(100, 999)}.{rng.integers(10, 99)} MHz" for _ in range(36)]

    def render_scene(si, p, t, fi):
        if si == 0:
            # ACT 0 (V21 VIRAL HOOK):
            #  0..45% -> INSTANT FRAME-0 VIRAL VISUAL HOOK + MOVING B-ROLL + IMPACT SLAM + FLARE SWEEP!
            #  45..70% -> 3D Earth Globe Orbital Drop
            #  70..100% -> Dark Esri Tactical Map + Live Radar + Animated Glowing Mission Vector Arc!
            if p < 0.45:
                q = p / 0.45
                fr, meta = get_real_video_or_photo(b0, fi, q, darken=0.72, micro_zoom=0.07)
                if meta.get("is_archival"):
                    fr = draw_archival_film_overlay(fr, vertical=vertical)
                # Frame-0 (t < 0.08s) is 100% CRISP & VISIBLE (alpha=1.0, scale=1.0) so YouTube Shorts
                # auto-frame picker ALWAYS captures a viral cover miniature! Then smooth punch-in & exit!
                if t < 0.08:
                    pa = 1.0
                    sc_k = 1.0
                else:
                    exit_fade = ease_out(min(1.0, (1.0 - q) / 0.16))
                    pa = exit_fade
                    # Subtle kinetic breathing zoom during hook hold
                    punch = 0.055 * math.sin(min(1.0, (t - 0.08) / 0.24) * math.pi)
                    sc_k = 1.0 + punch + 0.025 * q
                if 0.08 <= t < 0.34:
                    dt = t - 0.08; amp = 14.0 * math.exp(-dt / 0.07)
                    fr = cv2.warpAffine(fr, np.float32([[1, 0, amp * math.sin(dt * 120)], [0, 1, amp * math.cos(dt * 95)]]), (W, H))
                cy_hook = H * (0.435 if vertical else 0.495)
                fr = comp_pil(fr, hook_card_v21, W / 2.0, cy_hook, scale=sc_k, alpha=pa)
                # Animated crimson/gold progress sweep bar right beneath the hook card
                if pa > 0.15:
                    bw_bar = int((W * (0.64 if vertical else 0.46)) * min(1.0, max(0.18, q * 1.15)))
                    by_bar = int(cy_hook + hook_card_v21.height * 0.50 - 22)
                    bar_col = (44, 42, 238) if is_btc else (62, 204, 250)
                    cv2.rectangle(fr, (W // 2 - bw_bar // 2, by_bar), (W // 2 + bw_bar // 2, by_bar + 7), bar_col, -1)
                if 0.12 < q < 0.72:
                    fl_p = (q - 0.12) / 0.60
                    fl_col = (52, 82, 255) if is_btc else (58, 198, 255)
                    fr = add_anamorphic_flare(fr, int(H * (0.43 if vertical else 0.48)), int(W * fl_p), intensity=0.52 * math.sin(math.pi * fl_p), color_bgr=fl_col)
                return fr
            elif p < 0.70:
                # 3D REAL SATELLITE EARTH ORBITAL DROP (vivid Esri Satellite Globe + blue atmospheric Fresnel glow!)
                q = (p - 0.45) / 0.25
                rot_x = (1.0 - ease_io(q)) * 175.0
                tex = cv2.remap(map_mac, g_mx - rot_x, g_my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
                sun_shade = np.clip(g_shade * 1.18 + 0.10, 0.0, 1.18)
                shaded = np.clip(tex.astype(np.float32) * sun_shade[:, :, None], 0, 255).astype(np.uint8)
                rim = np.zeros_like(shaded)
                rim[:, :, 0] = np.clip(g_rim * 255 + g_halo * 225, 0, 255).astype(np.uint8)
                rim[:, :, 1] = np.clip(g_rim * 185 + g_halo * 145, 0, 255).astype(np.uint8)
                rim[:, :, 2] = np.clip(g_rim * 72 + g_halo * 42, 0, 255).astype(np.uint8)
                fr = np.where(g_mask[:, :, None], cv2.add(shaded, rim), cv2.add(star_bg, rim))
                cv2.circle(fr, (W // 2, H // 2), globe_r + 32, (95, 165, 225), 1, cv2.LINE_AA)
                z = 1.0 + 1.85 * (ease_io(max(0.0, (q - 0.28) / 0.72)) ** 1.85)
                fr = cv2.warpAffine(fr, cv2.getRotationMatrix2D((W / 2.0, H / 2.0), 0, z), (W, H))
                # Pulsing crimson + gold orbital target lock descending onto GPS epicenter
                cv2.circle(fr, (W // 2, H // 2), int(20 + (q * 115) % 52), (48, 42, 255), 3, cv2.LINE_AA)
                cv2.circle(fr, (W // 2, H // 2), int(12 + ((q * 115 + 24) % 52)), (56, 212, 255), 2, cv2.LINE_AA)
                cv2.circle(fr, (W // 2, H // 2), 9, (68, 68, 255), -1, cv2.LINE_AA)
                cv2.circle(fr, (W // 2, H // 2), 4, (255, 255, 255), -1, cv2.LINE_AA)
                if q > 0.85:
                    fl = int(205 * ((q - 0.85) / 0.15))
                    fr = cv2.add(fr, np.full((H, W, 3), fl, dtype=np.uint8))
                return fr
            else:
                # 3D-TILTED REAL ESRI SATELLITE TACTICAL MAP + NEON ZONE BLOOM + ANIMATED VECTOR ROUTE!
                q = (p - 0.70) / 0.30
                mp = map_loc.copy()
                tx, ty = int(ev["map_local"]["px"]), int(ev["map_local"]["py"])
                # Soft glowing crimson-amber tactical halo over real satellite epicenter
                halo_ov = np.zeros_like(mp)
                cv2.circle(halo_ov, (tx, ty), 165, (38, 44, 245), -1, cv2.LINE_AA)
                cv2.circle(halo_ov, (tx, ty), 75, (42, 165, 255), -1, cv2.LINE_AA)
                halo_ov = cv2.GaussianBlur(halo_ov, (0, 0), sigmaX=42, sigmaY=42)
                cv2.addWeighted(mp, 1.0, halo_ov, 0.55, 0, dst=mp)
                # Live rotating radar sweep
                sweep_ov = np.zeros_like(mp)
                ang0 = (t * 155.0) % 360.0
                cv2.ellipse(sweep_ov, (tx, ty), (245, 245), 0, ang0 - 52, ang0, (44, 34, 235), -1, cv2.LINE_AA)
                cv2.addWeighted(mp, 1.0, sweep_ov, 0.38, 0, dst=mp)
                ang_r = math.radians(ang0)
                cv2.line(mp, (tx, ty), (int(tx + 245 * math.cos(ang_r)), int(ty + 245 * math.sin(ang_r))), (95, 110, 255), 3, cv2.LINE_AA)
                for rk in range(3):
                    rr = int(22 + ((q * 215 + rk * 70) % 215))
                    cv2.circle(mp, (tx, ty), rr, (62, 62, 255), 3, cv2.LINE_AA)
                # Animated glowing dashed + solid mission vector route over satellite terrain
                ox, oy = tx - 380, ty + 290
                cx_b, cy_b = tx - 210, ty - 140
                n_arc = max(4, int(44 * ease_out(min(1.0, q / 0.70))))
                arc_pts = []
                for k in range(n_arc):
                    u = k / 43.0
                    arc_pts.append([int((1 - u) ** 2 * ox + 2 * (1 - u) * u * cx_b + u ** 2 * tx),
                                    int((1 - u) ** 2 * oy + 2 * (1 - u) * u * cy_b + u ** 2 * ty)])
                if len(arc_pts) >= 2:
                    ap = np.array(arc_pts, dtype=np.int32)
                    cv2.polylines(mp, [ap], False, (36, 30, 195), 14, cv2.LINE_AA)
                    cv2.polylines(mp, [ap], False, (52, 212, 255), 5, cv2.LINE_AA)
                    for k in range(0, len(arc_pts) - 1, 3):
                        cv2.line(mp, tuple(arc_pts[k]), tuple(arc_pts[min(len(arc_pts) - 1, k + 1)]), (255, 255, 255), 3, cv2.LINE_AA)
                    cv2.circle(mp, tuple(arc_pts[-1]), 13, (48, 224, 255), -1, cv2.LINE_AA)
                    cv2.circle(mp, tuple(arc_pts[-1]), 6, (255, 255, 255), -1, cv2.LINE_AA)
                cv2.circle(mp, (tx, ty), 17, (44, 44, 255), -1, cv2.LINE_AA)
                cv2.circle(mp, (tx, ty), 7, (255, 255, 255), -1, cv2.LINE_AA)
                hw = (440 if vertical else 640) - int(155 * ease_io(q))
                hh = int(hw * (H / float(W)))
                tilt = int(hw * 0.24)
                src = np.float32([[tx - hw - tilt, ty - hh], [tx + hw + tilt, ty - hh], [tx + hw - tilt * 0.25, ty + hh], [tx - hw + tilt * 0.25, ty + hh]])
                Hm = cv2.getPerspectiveTransform(src, np.float32([[0, 0], [W, 0], [W, H], [0, H]]))
                fr = cv2.warpPerspective(mp, Hm, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
                if q < 0.16:
                    fr = cv2.add(fr, np.full((H, W, 3), int(170 * (1.0 - q / 0.16)), dtype=np.uint8))
                ui = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dr = ImageDraw.Draw(ui)
                bw_c = 880 if vertical else 660
                bx_c = (W - bw_c) // 2 if vertical else 68
                by_c = 205 if vertical else 104
                dr.rounded_rectangle([bx_c, by_c, bx_c + bw_c, by_c + 162], radius=12, fill=(8, 12, 22, 224), outline=(0, 212, 255, 235), width=3)
                dr.rectangle([bx_c, by_c, bx_c + 12, by_c + 162], fill=(228, 36, 44, 255))
                dr.text((bx_c + 34, by_c + 36), f"SAT RECON: {ev.get('origin_name', 'HQ')} -> TARGET  •  {ev.get('dist_km', 2400):,} KM", fill=(255, 214, 48, 255), font=f_m18, anchor="lm")
                dr.text((bx_c + 34, by_c + 86), ev["location"][:25], fill=(254, 250, 244, 255), font=f_h2, anchor="lm")
                dr.text((bx_c + 34, by_c + 134), f"LAT {ev['lat']:+.4f}   |   LON {ev['lon']:+.4f}   |   LIVE SATELLITE", fill=(140, 215, 248, 245), font=f_m18, anchor="lm")
                return comp_rgba(fr, np.asarray(ui), W / 2.0, H / 2.0)

        elif si == 1:
            # ACT 1:
            #  0..44% -> IF exact-story archival film exists, play REAL ARCHIVAL FOOTAGE OF THIS EXACT EVENT!
            #            Otherwise, display REAL VERIFIED ARCHIVAL PHOTO OF THIS EXACT EVENT (zero fake archival clips!)
            #  44..100% -> MOVING DARKENED VIDEO + Torn Newspaper + Polaroid + Red String + Crimson Stamp!
            if p < 0.44:
                q = p / 0.44
                if has_exact_archival_video:
                    fr, _ = get_real_video_or_photo(arch_slot, fi, q, darken=0.95, micro_zoom=0.05)
                    fr = draw_archival_film_overlay(fr, label="DECLASSIFIED FILM // REAL FOOTAGE", vertical=vertical)
                else:
                    fr = sample_25d_beast(plates[0], W, H, q, style=0, flare_phase=q)
                    fr = draw_archival_film_overlay(fr, label="VERIFIED ARCHIVAL PHOTOGRAPH", vertical=vertical)
                if 0.10 < q < 0.85:
                    fr = add_anamorphic_flare(fr, int(H * 0.24), int(W * q), intensity=0.34 * math.sin(q * math.pi), color_bgr=(75, 195, 255))
                return fr
            q = (p - 0.44) / 0.56
            # LIVE MOVING DARKENED VIDEO BACKGROUND (never a dead static desk!)
            fr, _ = get_real_video_or_photo(b1, fi, q, darken=0.28, micro_zoom=0.03)
            shx, shy = 0.0, 0.0
            if 0.34 <= q < 0.46:
                sdt = (q - 0.34) * 5.8; amp = 22.0 * math.exp(-sdt / 0.08)
                shx, shy = amp * math.sin(sdt * 115), amp * math.cos(sdt * 95)

            pn = ease_back(q / 0.24, s=1.2)
            ny_pos = (380 if vertical else 245) - (1.0 - min(1.03, pn)) * 180
            nx_pos = (W / 2.0) if vertical else (W * 0.30)
            fr = comp_pil(fr, news_card, nx_pos + shx, ny_pos + shy, scale=1.0, angle=-2.2, shadow=True)

            pp = ease_back(max(0.0, (q - 0.08) / 0.24), s=1.22)
            py_pos = (960 if vertical else 585)
            px_pos = (W / 2.0 + 18) if vertical else (W * 0.68)
            fr = comp_pil(fr, pol_card, px_pos + shx, py_pos + shy, scale=1.55 - 0.55 * min(1.04, pp), angle=3.0, shadow=True)

            if q > 0.18:
                p_str = ease_out((q - 0.18) / 0.16)
                pin1 = (int(nx_pos + shx + (190 if vertical else 240)), int(ny_pos + shy + 68))
                pin2 = (int(px_pos + shx - (165 if vertical else 260)), int(py_pos + shy - (255 if vertical else 190)))
                cur_end = (int(pin1[0] + (pin2[0] - pin1[0]) * p_str), int(pin1[1] + (pin2[1] - pin1[1]) * p_str))
                cv2.line(fr, (pin1[0] + 5, pin1[1] + 8), (cur_end[0] + 5, cur_end[1] + 8), (8, 8, 12), 6, cv2.LINE_AA)
                cv2.line(fr, pin1, cur_end, (34, 30, 238), 5, cv2.LINE_AA)
                draw_pushpin(fr, *pin1)
                if p_str > 0.92:
                    draw_pushpin(fr, *pin2)

            if q >= 0.34:
                pst = ease_out((q - 0.34) / 0.08)
                fr = comp_pil(fr, stamp, px_pos + (145 if vertical else 175) + shx, py_pos - (150 if vertical else 120) + shy, scale=2.25 - 1.25 * pst, alpha=min(1.0, pst * 1.6))

            if q < 0.10:
                fr = cv2.add(fr, np.full((H, W, 3), int(225 * ((1.0 - q / 0.10) ** 1.6)), dtype=np.uint8))
            return fr

        elif si == 2:
            # ACT 2: JOHNNY HARRIS LIVE-HIGHLIGHTED TOP SECRET DOSSIER OVER REAL MOVING VIDEO + 1.75x GLASS LENS!
            fr, _ = get_real_video_or_photo(b2, fi, p, darken=0.30, micro_zoom=0.04)
            ui = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dr = ImageDraw.Draw(ui)
            cx0, cx1 = dos_cx0, dos_cx1
            cy0 = 260 if vertical else 125
            cy1 = 1320 if vertical else 875
            dr.rounded_rectangle([cx0, cy0, cx1, cy1], radius=12, fill=(238, 232, 216, 248), outline=(172, 162, 142, 255), width=3)
            dr.text((cx0 + 42, cy0 + 54), script["forensic_header"][:38], fill=(196, 26, 34, 255), font=f_m24)
            dr.line([(cx0 + 42, cy0 + 98), (cx1 - 42, cy0 + 98)], fill=(42, 38, 34, 195), width=3)
            ui.paste(dos_inset_pil, (cx0 + 42, cy0 + 122))

            base_y = cy0 + dos_ph + 165
            step_y = 148 if vertical else 108
            cols_h = [(248, 206, 72, 200), (248, 206, 72, 200), (242, 118, 108, 210)]
            for idx, line in enumerate(script["forensic_lines"][:3]):
                th = 0.08 + idx * 0.22
                ly = base_y + idx * step_y
                wrapped = textwrap.fill(str(line), width=34 if vertical else 58)
                bb = dr.multiline_textbbox((cx0 + 48, ly), wrapped, font=f_m24)
                box_h = max(34, bb[3] - bb[1])
                box_w = min(cx1 - cx0 - 92, max(220, (bb[2] - bb[0]) + 28))
                if p >= th:
                    hp = ease_out((p - th) / 0.14)
                    hw = int(box_w * hp)
                    dr.rounded_rectangle([cx0 + 38, ly - 8, cx0 + 38 + hw, ly + box_h + 12], radius=4, fill=cols_h[idx % 3])
                dr.text((cx0 + 48, ly), wrapped, fill=(18, 18, 16, 255), font=f_m24)
            fr = comp_rgba(fr, np.asarray(ui), W / 2.0, H / 2.0)

            lp = ease_io(min(1.0, p / 0.92))
            mx = (cx0 + 185) + (cx1 - cx0 - 370) * lp
            my = (cy0 + 122 + dos_ph * 0.50) + math.sin(lp * math.pi * 2.0) * 38.0
            return apply_magnifying_lens(fr, mx, my, radius=118 if vertical else 105, zoom=1.75)

        elif si == 3:
            # ACT 3:
            #  0..46% -> DUAL REAL-VIDEO SPLIT-SCREEN (Two real moving videos playing simultaneously!)
            #  46..100% -> BARREL-CURVED CRT REAL-VIDEO INTERCEPT + 16-BAND LIVE FFT SPECTRUM!
            if p < 0.46:
                q = p / 0.46
                if has_exact_archival_video:
                    vA, _ = get_real_video_or_photo(arch_slot, fi, q, darken=0.92, micro_zoom=0.04)
                else:
                    vA = sample_25d_beast(plates[2 % len(plates)], W, H, q, style=1)
                vB, _ = get_real_video_or_photo(b1, fi + 31, q, darken=0.92, micro_zoom=0.04)
                fr = np.zeros((H, W, 3), dtype=np.uint8)
                if vertical:
                    mid = H // 2
                    fr[:mid] = cv2.resize(vA, (W, mid), interpolation=cv2.INTER_LINEAR)
                    fr[mid:] = cv2.resize(vB, (W, H - mid), interpolation=cv2.INTER_LINEAR)
                    lw = int(W * ease_out(min(1.0, q / 0.42)))
                    cv2.line(fr, (0, mid), (lw, mid), (40, 34, 240), 10, cv2.LINE_AA)
                    cv2.line(fr, (0, mid), (lw, mid), (195, 210, 255), 3, cv2.LINE_AA)
                    lbl_l = script["split_left_label"][:20]
                    lbl_r = script["split_right_label"][:20]
                    (tw1, _), _ = cv2.getTextSize(lbl_l, cv2.FONT_HERSHEY_SIMPLEX, 0.80, 2)
                    (tw2, _), _ = cv2.getTextSize(lbl_r, cv2.FONT_HERSHEY_SIMPLEX, 0.80, 2)
                    cv2.rectangle(fr, (46, 200), (46 + tw1 + 44, 256), (10, 12, 18), -1)
                    cv2.rectangle(fr, (46, 200), (46 + tw1 + 44, 256), (225, 36, 44), 2)
                    cv2.putText(fr, lbl_l, (68, 237), cv2.FONT_HERSHEY_SIMPLEX, 0.80, (248, 206, 72), 2, cv2.LINE_AA)
                    rx0 = W - 46 - (tw2 + 44)
                    cv2.rectangle(fr, (rx0, mid + 34), (W - 46, mid + 90), (10, 12, 18), -1)
                    cv2.rectangle(fr, (rx0, mid + 34), (W - 46, mid + 90), (225, 36, 44), 2)
                    cv2.putText(fr, lbl_r, (rx0 + 22, mid + 71), cv2.FONT_HERSHEY_SIMPLEX, 0.80, (248, 248, 250), 2, cv2.LINE_AA)
                else:
                    mid = W // 2
                    fr[:, :mid] = cv2.resize(vA, (mid, H), interpolation=cv2.INTER_LINEAR)
                    fr[:, mid:] = cv2.resize(vB, (W - mid, H), interpolation=cv2.INTER_LINEAR)
                    lh = int(H * ease_out(min(1.0, q / 0.42)))
                    cv2.line(fr, (mid, 0), (mid, lh), (40, 34, 240), 10, cv2.LINE_AA)
                    cv2.line(fr, (mid, 0), (mid, lh), (195, 210, 255), 3, cv2.LINE_AA)
                    cv2.rectangle(fr, (68, 108), (430, 162), (10, 12, 18), -1)
                    cv2.putText(fr, script["split_left_label"][:18], (88, 145), cv2.FONT_HERSHEY_SIMPLEX, 0.82, (248, 206, 72), 2, cv2.LINE_AA)
                    cv2.rectangle(fr, (mid + 34, 108), (mid + 410, 162), (10, 12, 18), -1)
                    cv2.putText(fr, script["split_right_label"][:18], (mid + 54, 145), cv2.FONT_HERSHEY_SIMPLEX, 0.82, (248, 248, 250), 2, cv2.LINE_AA)
                return fr

            q = (p - 0.46) / 0.54
            fr, _ = get_real_video_or_photo(b2, fi, q, darken=0.88, micro_zoom=0.05)
            fr[:, :, 1] = np.clip(fr[:, :, 1].astype(np.int16) + 22, 0, 255).astype(np.uint8)
            fr[::3, :, :] = (fr[::3, :, :].astype(np.float32) * 0.64).astype(np.uint8)
            by = int((t * 420) % (H - 80))
            fr[by:by + 16, :] = np.roll(fr[by:by + 16, :], 26, axis=1)
            b, g, r = cv2.split(fr)
            fr = cv2.merge([np.roll(b, -5, axis=1), g, np.roll(r, 5, axis=1)])
            fr = cv2.remap(fr, crt_mx, crt_my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(6, 10, 8))

            top_y = 215 if vertical else 120
            if int(t * 4) % 2 == 0:
                cv2.circle(fr, (86, top_y), 11, (40, 34, 242), -1, cv2.LINE_AA)
            cv2.putText(fr, f"REC  LIVE INTERCEPT // {ev['year']}", (112, top_y + 8), cv2.FONT_HERSHEY_SIMPLEX, 0.84, (226, 250, 232), 2, cv2.LINE_AA)

            hx_x = W - 360 if vertical else W - 380
            scroll_i = int(t * 5)
            for row_i in range(6):
                cv2.putText(fr, hex_rows[(scroll_i + row_i) % len(hex_rows)], (hx_x, top_y + 42 + row_i * 28), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (92, 225, 130), 1, cv2.LINE_AA)

            oy0 = 1190 if vertical else 720
            oy1 = oy0 + 165
            cv2.rectangle(fr, (64, oy0), (W - 64, oy1), (8, 20, 12), -1)
            cv2.rectangle(fr, (64, oy0), (W - 64, oy1), (78, 228, 126), 2)
            idx30 = min(len(env30) - 1, int(t * 30))
            amp = float(env30[idx30])
            bands = spec30[min(len(spec30) - 1, idx30)]
            mid_x = W // 2
            bar_step = (mid_x - 104) / 16.0
            for bk in range(16):
                bh = int(14 + bands[bk] * 114)
                bx0 = int(84 + bk * bar_step)
                bx1 = int(bx0 + max(6, bar_step * 0.68))
                col_b = (85, 245, 120) if bands[bk] < 0.65 else ((65, 212, 250) if bands[bk] < 0.85 else (62, 62, 250))
                cv2.rectangle(fr, (bx0, oy1 - 14 - bh), (bx1, oy1 - 14), col_b, -1)
            cv2.putText(fr, "FFT SPECTRUM // 16-CH", (84, oy0 + 26), cv2.FONT_HERSHEY_SIMPLEX, 0.54, (130, 242, 160), 1, cv2.LINE_AA)
            cv2.line(fr, (mid_x, oy0 + 12), (mid_x, oy1 - 12), (50, 145, 80), 1)
            n_pts = 48 if vertical else 72
            ox_s = mid_x + 22
            dx_w = (W - 84 - ox_s) / float(n_pts - 1)
            pts = [[int(ox_s + k * dx_w), int((oy0 + oy1) / 2 + math.sin(k * 0.48 + t * 26) * math.cos(k * 0.16 - t * 9) * (10 + 52 * amp))] for k in range(n_pts)]
            cv2.polylines(fr, [np.array(pts, dtype=np.int32)], False, (100, 255, 138), 3, cv2.LINE_AA)
            cv2.putText(fr, "VOICE INTERCEPT WAVE", (ox_s, oy0 + 26), cv2.FONT_HERSHEY_SIMPLEX, 0.54, (130, 242, 160), 1, cv2.LINE_AA)
            return fr

        else:
            # ACT 4: REAL DRAMATIC CINEMA VIDEO + VOLUMETRIC EMBERS + STAT CARD -> 🔥 3D BOOK COLLECTOR'S PROMO OUTRO!
            fr, _ = get_real_video_or_photo(len(vplates) - 1 if vplates else 0, fi, p, darken=0.82, micro_zoom=0.06)
            for k in range(n_emb):
                px = int((e_x[k] + e_vx[k] * t + 22 * math.sin(t * 1.5 + k)) % W)
                py = int((e_y[k] + e_vy[k] * t) % H)
                col_e = (65, 175, 255) if e_warm[k] else (140, 215, 250)
                cv2.circle(fr, (px, py), int(e_r[k]), col_e, -1, cv2.LINE_AA)

            t_rem = total_dur - t
            if (not show_outro) or (t_rem > outro_len):
                sp_sc = ease_back(min(1.0, p / 0.25), s=1.35)
                fade_tail = ease_out(min(1.0, (t_rem - outro_len) / 0.35)) if show_outro else ease_out(min(1.0, t_rem / 0.55))
                sa = ease_out(min(1.0, p / 0.18)) * fade_tail
                return comp_pil(fr, stat_card, W / 2.0, H * (0.44 if vertical else 0.46), scale=0.82 + 0.18 * sp_sc, alpha=sa, shadow=True)
            else:
                ot = outro_len - t_rem
                oa = ease_out(ot / 0.38)
                fr = (fr.astype(np.float32) * (1.0 - 0.72 * oa)).astype(np.uint8)
                bob_y = math.sin(ot * 2.4) * 6.0
                fr = comp_pil(fr, outro, W / 2.0, H / 2.0 + bob_y, scale=1.08 - 0.08 * oa, alpha=oa, shadow=True)
                if ot < 0.16:
                    fr = cv2.add(fr, np.full((H, W, 3), int(145 * (1.0 - ot / 0.16)), dtype=np.uint8))
                return fr

    err_log = open(out_mp4 + ".ff.log", "wb")
    vproc = subprocess.Popen([
        FFMPEG, "-y",
        "-f", "rawvideo", "-vcodec", "rawvideo", "-pix_fmt", "bgr24",
        "-s", f"{W}x{H}", "-r", str(FPS), "-i", "pipe:0",
        "-i", audio_m4a,
        "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "libx264", "-preset", "superfast", "-crf", "21", "-maxrate", "8M", "-bufsize", "12M",
        "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", "-shortest", out_mp4
    ], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=err_log)

    qa_snaps = {}
    qa_targets = [int(n_frames * f) for f in (0.04, 0.19, 0.28, 0.39, 0.54, 0.68, 0.80, 0.96)]

    for fi in range(n_frames):
        t = fi / float(FPS)
        pf = t / total_dur
        si = 0
        for j in range(5):
            if pf >= bounds[j]:
                si = j
        s0, s1 = bounds[si] * total_dur, bounds[si + 1] * total_dur
        p_loc = max(0.0, min(1.0, (t - s0) / max(0.1, s1 - s0)))

        if si < 4 and (s1 - t) < tr_s:
            tp = ease_io(1.0 - (s1 - t) / tr_s)
            fA = render_scene(si, p_loc, t, fi)
            fB = render_scene(si + 1, 0.0, s1, fi)
            sh = int(round(W * tp))
            frame = np.empty((H, W, 3), dtype=np.uint8)
            if sh < W:
                frame[:, :W - sh] = fA[:, sh:]
            if sh > 0:
                frame[:, W - sh:] = fB[:, :sh]
            bk = int(1 + 54 * math.sin(math.pi * tp))
            if bk >= 5:
                frame = cv2.blur(frame, (bk | 1, 1))
        else:
            frame = render_scene(si, p_loc, t, fi)

        frame = np.clip(frame.astype(np.float32) * VIG, 0, 255).astype(np.uint8)
        frame = cv2.add(frame, g_pos[fi % 6])
        frame = cv2.subtract(frame, g_neg[fi % 6])

        if vertical:
            cv2.rectangle(frame, (0, 0), (W, 134), (7, 9, 14), -1)
            cv2.line(frame, (52, 114), (W - 52, 114), (42, 46, 58), 5, cv2.LINE_AA)
            cv2.line(frame, (52, 114), (int(52 + (W - 104) * pf), 114), (42, 34, 238), 6, cv2.LINE_AA)
            cv2.putText(frame, f"{brand}  |  {ev['display_date']}", (52, 82), cv2.FONT_HERSHEY_SIMPLEX, 0.84, (240, 238, 232), 2, cv2.LINE_AA)
        else:
            frame[:52, :] = 8; frame[H - 52:, :] = 8
            cv2.line(frame, (72, 26), (980, 26), (46, 48, 56), 3, cv2.LINE_AA)
            cv2.line(frame, (72, 26), (int(72 + 908 * pf), 26), (42, 36, 238), 4, cv2.LINE_AA)
            cv2.putText(frame, f"{brand}  |  {ev['display_date']} — {ev['location'][:26]}", (1008, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (206, 208, 218), 1, cv2.LINE_AA)

        # 🔥 MID-VIDEO SLEEK 3D BOOK AD BANNER (peak curiosity window ~48%..60% — zero subtitle collision!)
        if show_midroll_ad and (0.48 <= pf <= 0.61):
            t_in = (pf - 0.48) * total_dur
            t_out = (0.61 - pf) * total_dur
            ad_in = ease_out(min(1.0, t_in / 0.42))
            ad_out = ease_out(min(1.0, t_out / 0.38))
            ad_a = ad_in * ad_out
            if vertical:
                # Slides gracefully right below top HUD bar (100% clear of bottom YouTube Shorts UI & subtitles!)
                ad_x = W / 2.0 + (1.0 - ad_in) * 160.0 - (1.0 - ad_out) * 160.0
                ad_y = 248.0
            else:
                ad_x = W - 418.0 + (1.0 - ad_in) * 240.0 + (1.0 - ad_out) * 240.0
                ad_y = 152.0
            frame = comp_pil(frame, midroll_ad, ad_x, ad_y, scale=0.96 + 0.04 * ad_in, alpha=ad_a, shadow=True)

        if (not show_outro) or ((total_dur - t) > outro_len):
            sub = sub_cache.get(t)
            if sub is not None:
                sub_y = 1435 if vertical else H - 108
                frame = comp_rgba(frame, sub, W / 2.0, sub_y)

        # Frame-0..3s stays 100% BRIGHT from t=0.00s (no black flash on Shorts autoplay/frame picker!)
        if (total_dur - t) < 0.55:
            frame = (frame.astype(np.float32) * max(0.0, (total_dur - t) / 0.55)).astype(np.uint8)

        if qa_out and fi in qa_targets:
            qa_snaps[fi] = frame.copy()

        vproc.stdin.write(frame.tobytes())

    vproc.stdin.close()
    ret = vproc.wait()
    err_log.close()
    for vp in vplates:
        vp.close()
    if ret != 0:
        raise RuntimeError(open(out_mp4 + ".ff.log", "rb").read().decode("utf-8", errors="ignore")[-800:])
    os.remove(out_mp4 + ".ff.log")

    if qa_out and qa_snaps:
        cols, rows = 4, 2
        tw, th = (270, 480) if vertical else (480, 270)
        grid = Image.new("RGB", (cols * tw, rows * th), (10, 10, 14))
        dr = ImageDraw.Draw(grid)
        for k, fi_k in enumerate(qa_targets):
            if fi_k in qa_snaps:
                r, c = divmod(k, cols)
                im = Image.fromarray(cv2.cvtColor(qa_snaps[fi_k], cv2.COLOR_BGR2RGB)).resize((tw - 4, th - 4), Image.LANCZOS)
                grid.paste(im, (c * tw + 2, r * th + 2))
                dr.rectangle([c * tw + 6, (r + 1) * th - 28, c * tw + 90, (r + 1) * th - 6], fill=(0, 0, 0))
                dr.text((c * tw + 12, (r + 1) * th - 24), f"t={fi_k/FPS:04.1f}s", fill=(255, 224, 90))
        grid.save(qa_out, "JPEG", quality=90)

    print(f"[V20 CINEMA RENDER OK] {out_mp4} ({total_dur:.1f}s, {W}x{H} {FPS}fps, {os.path.getsize(out_mp4)/1e6:.2f} MB)")
    return total_dur


def _smart_subject_crop(img_path, tw, th, is_right=False):
    """Load real archival photo, upscale/enhance contrast & detail, and auto-center on faces/subjects!"""
    im = cv2.imread(img_path)
    if im is None:
        return np.full((th, tw, 3), (22, 24, 30), dtype=np.uint8)
    ih, iw = im.shape[:2]
    # Detect face/head region if present so real archival people are NEVER cropped at the forehead!
    cx_norm, cy_norm = 0.5, 0.38
    try:
        gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
        casc_p = os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml")
        if os.path.exists(casc_p):
            faces = cv2.CascadeClassifier(casc_p).detectMultiScale(gray, 1.12, 4, minSize=(40, 40))
            if len(faces) > 0:
                # Pick largest prominent face
                fx, fy, fw, fh = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)[0]
                cx_norm = (fx + fw * 0.5) / float(iw)
                cy_norm = (fy + fh * 0.42) / float(ih)
    except Exception:
        pass

    sc = max(tw / float(iw), th / float(ih)) * 1.06
    nw, nh = max(tw, int(round(iw * sc))), max(th, int(round(ih * sc)))
    rs = cv2.resize(im, (nw, nh), interpolation=cv2.INTER_LANCZOS4)

    # Center crop around subject (shifted slightly to avoid being sliced by center diagonal!)
    target_x = int(cx_norm * nw - tw * (0.56 if is_right else 0.44))
    target_y = int(cy_norm * nh - th * 0.46)
    x0 = max(0, min(nw - tw, target_x))
    y0 = max(0, min(nh - th, target_y))
    crop = rs[y0:y0 + th, x0:x0 + tw]

    # Dramatic documentary contrast + CLAHE micro-detail pop + subtle warm/cool colorization contrast!
    lab = cv2.cvtColor(crop, cv2.COLOR_BGR2LAB)
    l_ch, a_ch, b_ch = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.2, tileGridSize=(8, 8))
    l_ch = clahe.apply(l_ch)
    crop = cv2.cvtColor(cv2.merge([l_ch, a_ch, b_ch]), cv2.COLOR_LAB2BGR)

    # Check if B&W archival photo -> apply subtle rich filmic split-tone so Left & Right pop dramatically!
    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV).astype(np.float32)
    is_bw = float(hsv[:, :, 1].mean()) < 18.0
    if is_bw:
        g = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY).astype(np.float32)
        if not is_right:
            # Left side: gritty cool slate-steel wartime tone
            b = np.clip(g * 1.06 + 8, 0, 255)
            gr = np.clip(g * 1.00 + 2, 0, 255)
            r = np.clip(g * 0.94, 0, 255)
        else:
            # Right side: warm dramatic archival sepia-amber tone
            b = np.clip(g * 0.84, 0, 255)
            gr = np.clip(g * 0.99 + 4, 0, 255)
            r = np.clip(g * 1.14 + 8, 0, 255)
        crop = cv2.merge([b, gr, r]).astype(np.uint8)
    else:
        hsv[:, :, 1] = np.clip(hsv[:, :, 1] * (1.18 if is_right else 0.96), 0, 255)
        crop = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

    # Crisp unsharp mask
    blur = cv2.GaussianBlur(crop, (0, 0), 1.4)
    crop = cv2.addWeighted(crop, 1.32, blur, -0.32, 0)
    return crop


def pick_best_thumb_photos(img_paths):
    """
    Score all archival images in ev['images'] to pick the 2 MOST PHOTOGRAPHIC, HUMAN-CENTERED
    REAL ARCHIVAL PHOTOS for the viral split-screen thumbnail (rejecting white text scans,
    blueprints, and blank maps!).
    """
    if not img_paths:
        return None, None
    scored = []
    casc_p = os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml")
    face_det = cv2.CascadeClassifier(casc_p) if os.path.exists(casc_p) else None

    for p in img_paths:
        if not p or not os.path.exists(p):
            continue
        im = cv2.imread(p)
        if im is None:
            continue
        h, w = im.shape[:2]
        gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
        # Reject white paper scans / maps / diagrams
        white_ratio = float(np.mean(gray > 225))
        near_bw_ratio = float(np.mean((gray > 235) | (gray < 20)))
        std_luma = float(np.std(gray))
        score = std_luma * 0.65
        if white_ratio > 0.28:
            score -= 85.0 * white_ratio
        if near_bw_ratio > 0.45:
            score -= 45.0
        # Resolution & landscape preference
        if w >= 700:
            score += 12.0
        # BIG BONUS for REAL ARCHIVAL PEOPLE / FACES!
        has_face = False
        if face_det is not None:
            try:
                small = cv2.resize(gray, (min(w, 640), int(h * min(w, 640) / max(1, w))))
                faces = face_det.detectMultiScale(small, 1.12, 4, minSize=(32, 32))
                if len(faces) > 0:
                    has_face = True
                    score += 55.0 + min(30.0, len(faces) * 10.0)
            except Exception:
                pass
        scored.append((score, has_face, p))

    if not scored:
        return img_paths[0], img_paths[-1]
    scored.sort(key=lambda x: x[0], reverse=True)
    best_left = scored[0][2]
    # Prefer contrasting second real photo
    best_right = scored[1][2] if len(scored) > 1 else best_left
    return best_left, best_right


def _strip_white_borders(im):
    """Auto-trim bright white museum / Bundesarchiv bottom/side caption borders cleanly."""
    ih, iw = im.shape[:2]
    cut_b = ih
    for yy in range(ih - 1, max(1, int(ih * 0.84)), -1):
        if float(im[yy].mean()) > 232.0:
            cut_b = yy
        else:
            break
    if cut_b < ih - 4:
        im = im[:max(100, cut_b - 4), :]
        ih, iw = im.shape[:2]
    cut_t = 0
    for yy in range(0, min(ih - 1, int(ih * 0.10))):
        if float(im[yy].mean()) > 238.0:
            cut_t = yy + 1
        else:
            break
    if cut_t > 4:
        im = im[cut_t + 2:, :]
    return im


def _detect_primary_subject(im):
    """Return (cx_norm, cy_norm, has_face) using Haar frontal face detection."""
    ih, iw = im.shape[:2]
    cx_norm, cy_norm, has_face = 0.50, (0.30 if ih > iw else 0.40), False
    try:
        gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
        casc_p = os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml")
        if os.path.exists(casc_p):
            faces = cv2.CascadeClassifier(casc_p).detectMultiScale(gray, 1.12, 4, minSize=(36, 36))
            if len(faces) > 0:
                fx, fy, fw, fh = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)[0]
                cx_norm = (fx + fw * 0.50) / float(iw)
                cy_norm = (fy + fh * 0.42) / float(ih)
                has_face = True
    except Exception:
        pass
    return cx_norm, cy_norm, has_face


def _draw_soft_shadow_text(im_rgba, pos, text, font, fill, anchor="la", shadow_alpha=215, offset=(0, 6), blur_r=9):
    """Render ultra-clean Netflix-grade soft multi-pass drop shadow text (zero muddy cartoon borders!)."""
    layer = Image.new("RGBA", im_rgba.size, (0, 0, 0, 0))
    ldr = ImageDraw.Draw(layer)
    ox, oy = offset
    ldr.text((pos[0] + ox, pos[1] + oy), text, font=font, fill=(0, 0, 0, shadow_alpha), anchor=anchor)
    layer = layer.filter(ImageFilter.GaussianBlur(radius=blur_r))
    im_rgba.alpha_composite(layer)
    dr = ImageDraw.Draw(im_rgba)
    dr.text((pos[0] + 2, pos[1] + 3), text, font=font, fill=(0, 0, 0, 175), anchor=anchor)
    dr.text(pos, text, font=font, fill=fill, anchor=anchor)


def _draw_rubber_stamp_badge(text, color_rgba=(255, 72, 76, 252), angle=11.0):
    """Crisp angled archival rubber stamp (CIA / DECLASSIFIED / UNSEALED) legible on both dark & light photos."""
    txt = str(text or "DECLASSIFIED").strip().upper()[:16]
    f_st = load_font(FONT_MONO, 25, 700)
    tmp = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    tw = int(tmp.textlength(txt, font=f_st))
    sw, sh = tw + 48, 58
    st = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
    sdr = ImageDraw.Draw(st)
    bg_fill = (12, 10, 14, 218)
    sdr.rounded_rectangle([2, 2, sw - 3, sh - 3], radius=8, fill=bg_fill, outline=color_rgba, width=4)
    sdr.rounded_rectangle([8, 8, sw - 9, sh - 9], radius=5, outline=(color_rgba[0], color_rgba[1], color_rgba[2], 165), width=1)
    sdr.text((sw // 2, sh // 2), txt, font=f_st, fill=color_rgba, anchor="mm")
    return st.rotate(angle, expand=True, resample=Image.BICUBIC)


def _build_v21_hook_overlay(W, H, ev, script, is_btc, vertical=True):
    """
    🔥 V21 VIRAL COLD-OPEN HOOK OVERLAY (Frame-0 100% Crisp Miniature + 0-3s Scroll-Stopper)!
    - 9:16 SHORTS: Real archival hero evidence frame + branded top pill + giant 2-tone viral power
      headline + shocking curiosity teaser strip, locked cleanly inside YouTube Shorts' safe zone!
    - 16:9 LONG-FORM: Sleek cinema documentary title-hook opener matching the viral miniature!
    """
    raw_w = script.get("thumb_white") or script.get("hook_top") or ev.get("location", "SECRET FILE")
    raw_r = script.get("thumb_red") or str(ev.get("year", ""))
    l1, l2, l3 = _split_headline_lines(raw_w, raw_r)
    yr_pill = str(script.get("thumb_pill") or ev.get("year") or "").replace("->", "–").strip().upper()[:16]
    teaser = str(script.get("hook_teaser") or script.get("hook_sub") or ev.get("display_date") or "").strip().upper()[:42]
    stamp_txt = str(script.get("thumb_stamp") or ("DECLASSIFIED" if is_btc else "UNSEALED")).strip().upper()[:16]

    accent_rgb = (228, 32, 38) if is_btc else (246, 198, 62)
    accent_text = (255, 252, 248, 255) if is_btc else (14, 16, 22, 255)
    eyebrow_txt = (f"DECLASSIFIED  •  {yr_pill}" if is_btc else f"HISTORY UNSEALED  •  {yr_pill}")[:32]

    if vertical:
        cw, ch = 876, 980
        card = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        dr = ImageDraw.Draw(card)

        # Frosted obsidian dossier shell with channel accent border (100% inside Shorts safe zone!)
        border_col = (228, 36, 42, 225) if is_btc else (244, 196, 68, 225)
        dr.rounded_rectangle([14, 14, cw - 14, ch - 14], radius=24, fill=(9, 11, 17, 212), outline=border_col, width=3)
        dr.rounded_rectangle([26, 26, cw - 26, ch - 26], radius=18, outline=(255, 255, 255, 42), width=1)

        # 1) Top Branded Eyebrow Pill
        f_eye = load_font(FONT_MONO, 23, 700)
        ew = int(dr.textlength(eyebrow_txt, font=f_eye)) + 48
        ex0 = (cw - ew) // 2
        if is_btc:
            dr.rounded_rectangle([ex0, 40, ex0 + ew, 84], radius=8, fill=(218, 28, 34, 255))
            dr.text((cw // 2, 62), eyebrow_txt, font=f_eye, fill=(255, 252, 248, 255), anchor="mm")
        else:
            dr.rounded_rectangle([ex0, 40, ex0 + ew, 84], radius=8, fill=(18, 22, 34, 248), outline=(246, 198, 62, 245), width=2)
            dr.text((cw // 2, 62), eyebrow_txt, font=f_eye, fill=(248, 206, 74, 255), anchor="mm")

        # 2) Framed Real Archival Hero Evidence Window (instant visual proof at t=0.00s!)
        pw, ph = 752, 372
        px0, py0 = (cw - pw) // 2, 108
        best_img = None
        if ev.get("images"):
            best_img, _ = pick_best_thumb_photos(ev["images"])
        if best_img and os.path.exists(best_img):
            im_bgr = _smart_subject_crop(best_img, pw, ph, is_right=not is_btc)
            ev_pil = Image.fromarray(cv2.cvtColor(im_bgr, cv2.COLOR_BGR2RGB)).convert("RGBA")
        else:
            ev_pil = Image.new("RGBA", (pw, ph), (24, 28, 38, 255))
        # Rounded mask + subtle inner bottom gradient for evidence polish
        mask = Image.new("L", (pw, ph), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, pw - 1, ph - 1], radius=16, fill=255)
        card.paste(ev_pil, (px0, py0), mask)
        dr = ImageDraw.Draw(card)
        dr.rounded_rectangle([px0, py0, px0 + pw, py0 + ph], radius=16, outline=(255, 255, 255, 115), width=2)
        # Tactical corner brackets around archival proof photo
        b_col = (238, 42, 46, 255) if is_btc else (248, 204, 70, 255)
        cl = 26
        for (bx, by, sx, sy) in [
            (px0 - 6, py0 - 6, 1, 1),
            (px0 + pw + 6, py0 - 6, -1, 1),
            (px0 - 6, py0 + ph + 6, 1, -1),
            (px0 + pw + 6, py0 + ph + 6, -1, -1),
        ]:
            dr.line([(bx, by), (bx + sx * cl, by)], fill=b_col, width=4)
            dr.line([(bx, by), (bx, by + sy * cl)], fill=b_col, width=4)

        # Tilted archival rubber stamp tucked cleanly on top-right edge of photo
        st_im = _draw_rubber_stamp_badge(stamp_txt, color_rgba=(238, 44, 48, 240) if is_btc else (248, 204, 72, 242), angle=-9.0)
        card.alpha_composite(st_im, (px0 + pw - st_im.width + 14, py0 - 16))
        dr = ImageDraw.Draw(card)

        # 3) Massive Two-Tone Viral Power Headline (below photo!)
        white_lines = [s for s in (l1, l2) if s]
        y_cur = py0 + ph + (28 if len(white_lines) >= 2 else 54)
        for wl in white_lines:
            fsz = 102
            f_use = load_font(FONT_SANS, fsz, 800)
            while fsz >= 52 and dr.textlength(wl, font=f_use) > cw - 96:
                fsz -= 4
                f_use = load_font(FONT_SANS, fsz, 800)
            _draw_soft_shadow_text(card, (cw // 2, y_cur + fsz // 2), wl, f_use, (254, 252, 248, 255), anchor="mm", blur_r=8)
            y_cur += int(fsz * 1.05)

        # Blazing Power Climax Ribbon Block
        hl_txt = l3 or yr_pill or "DECLASSIFIED"
        fsz_h = 90
        f_hl = load_font(FONT_SANS, fsz_h, 800)
        while fsz_h >= 48 and dr.textlength(hl_txt, font=f_hl) > cw - 140:
            fsz_h -= 4
            f_hl = load_font(FONT_SANS, fsz_h, 800)
        rw = int(dr.textlength(hl_txt, font=f_hl)) + 58
        rh = int(fsz_h * 1.26)
        ry = min(ch - 146 - rh, y_cur + 14)
        dr = ImageDraw.Draw(card)
        dr.rounded_rectangle([(cw - rw) // 2, ry, (cw + rw) // 2, ry + rh], radius=12, fill=(*accent_rgb, 255))
        if is_btc:
            dr.line([(cw - rw) // 2 + 12, ry + 3, (cw + rw) // 2 - 12, ry + 3], fill=(255, 212, 92, 220), width=3)
        dr.text((cw // 2, ry + rh // 2), hl_txt, font=f_hl, fill=accent_text, anchor="mm")

        # 4) Curiosity Open-Loop Teaser Strip
        f_ts = load_font(FONT_MONO, 25, 700)
        tw_t = int(dr.textlength(teaser, font=f_ts))
        while tw_t > cw - 110 and len(teaser) > 16:
            teaser = teaser[:-1]
            tw_t = int(dr.textlength(teaser, font=f_ts))
        ty_bar = ch - 76
        dr.rounded_rectangle([cw // 2 - tw_t // 2 - 30, ty_bar - 24, cw // 2 + tw_t // 2 + 30, ty_bar + 24], radius=8, fill=(18, 22, 32, 236), outline=(255, 255, 255, 78), width=1)
        dr.text((cw // 2, ty_bar), teaser, font=f_ts, fill=(248, 212, 92, 255), anchor="mm")
        return card

    else:
        # 16:9 LONG-FORM CINEMA COLD-OPEN HOOK CARD
        cw, ch = 1480, 540
        card = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        dr = ImageDraw.Draw(card)
        border_col = (228, 36, 42, 225) if is_btc else (244, 196, 68, 225)
        dr.rounded_rectangle([14, 14, cw - 14, ch - 14], radius=22, fill=(8, 10, 16, 212), outline=border_col, width=3)
        # Eyebrow Pill
        f_eye = load_font(FONT_MONO, 26, 700)
        ew = int(dr.textlength(eyebrow_txt, font=f_eye)) + 56
        if is_btc:
            dr.rounded_rectangle([(cw - ew) // 2, 42, (cw + ew) // 2, 90], radius=8, fill=(218, 28, 34, 255))
            dr.text((cw // 2, 66), eyebrow_txt, font=f_eye, fill=(255, 252, 248, 255), anchor="mm")
        else:
            dr.rounded_rectangle([(cw - ew) // 2, 42, (cw + ew) // 2, 90], radius=8, fill=(18, 22, 34, 248), outline=(246, 198, 62, 245), width=2)
            dr.text((cw // 2, 66), eyebrow_txt, font=f_eye, fill=(248, 206, 74, 255), anchor="mm")

        white_lines = [s for s in (l1, l2) if s]
        one_white = " ".join(white_lines)
        f_w = load_font(FONT_SANS, 102, 800)
        fsz_w = 102
        while fsz_w >= 54 and dr.textlength(one_white, font=f_w) > cw - 130:
            fsz_w -= 4
            f_w = load_font(FONT_SANS, fsz_w, 800)
        _draw_soft_shadow_text(card, (cw // 2, 184), one_white, f_w, (254, 252, 248, 255), anchor="mm", blur_r=9)

        hl_txt = l3 or yr_pill or "DECLASSIFIED"
        fsz_h = 92
        f_hl = load_font(FONT_SANS, fsz_h, 800)
        while fsz_h >= 48 and dr.textlength(hl_txt, font=f_hl) > cw - 200:
            fsz_h -= 4
            f_hl = load_font(FONT_SANS, fsz_h, 800)
        rw = int(dr.textlength(hl_txt, font=f_hl)) + 66
        rh = int(fsz_h * 1.28)
        ry = 264
        dr = ImageDraw.Draw(card)
        dr.rounded_rectangle([(cw - rw) // 2, ry, (cw + rw) // 2, ry + rh], radius=12, fill=(*accent_rgb, 255))
        dr.text((cw // 2, ry + rh // 2), hl_txt, font=f_hl, fill=accent_text, anchor="mm")

        f_ts = load_font(FONT_MONO, 27, 700)
        tw_t = int(dr.textlength(teaser, font=f_ts))
        ty_b = ch - 76
        dr.rounded_rectangle([cw // 2 - tw_t // 2 - 34, ty_b - 24, cw // 2 + tw_t // 2 + 34, ty_b + 24], radius=8, fill=(18, 22, 32, 235), outline=(255, 255, 255, 76), width=1)
        dr.text((cw // 2, ty_b), teaser, font=f_ts, fill=(248, 212, 92, 255), anchor="mm")
        return card


def _frame_subject_right(img_path, W, H, base_bgr=(14, 16, 22)):
    """
    🔥 V21 STUDIO COMPOSITING (ZERO BORDER_REPLICATE HORIZONTAL STREAKS!):
    Auto-strips museum caption borders, detects faces/subjects, places the crisp archival subject
    cleanly on the right 66% of the frame, and smoothly feathers its left boundary into a rich
    studio backdrop so the left typography zone is 100% silky-clean and high-contrast!
    """
    canvas = np.zeros((H, W, 3), dtype=np.uint8)
    canvas[:, :] = base_bgr
    if not img_path or not os.path.exists(img_path):
        return canvas

    im = cv2.imread(img_path)
    if im is None:
        return canvas
    im = _strip_white_borders(im)
    ih, iw = im.shape[:2]
    cx_norm, cy_norm, has_face = _detect_primary_subject(im)

    # Enhance micro-detail & crisp sharpness BEFORE compositing
    lab = cv2.cvtColor(im, cv2.COLOR_BGR2LAB)
    l_ch, a_ch, b_ch = cv2.split(lab)
    l_ch = cv2.createCLAHE(clipLimit=2.2, tileGridSize=(8, 8)).apply(l_ch)
    im = cv2.cvtColor(cv2.merge([l_ch, a_ch, b_ch]), cv2.COLOR_LAB2BGR)
    blur = cv2.GaussianBlur(im, (0, 0), 1.2)
    im = cv2.addWeighted(im, 1.30, blur, -0.30, 0)

    # Target visible hero box on the right ~68% (x = 410..1280 -> width 870px)
    # Never stretch or replicate edge pixels! Scale proportionally to fill H cleanly.
    min_w = int(W * 0.64)
    sc_h = (H / float(ih)) * (1.06 if ih > iw else 1.04)
    nw = int(round(iw * sc_h))
    nh = int(round(ih * sc_h))
    if nw < min_w:
        sc_w = min_w / float(iw)
        nw = min_w
        nh = max(H, int(round(ih * sc_w)))
    rs = cv2.resize(im, (nw, nh), interpolation=cv2.INTER_LANCZOS4)

    # Vertical crop centered on face (or upper-middle focal zone)
    y0 = max(0, min(nh - H, int(cy_norm * nh - H * (0.38 if has_face else 0.44))))

    # Horizontal crop: keep primary subject near x ~ 70% of final 1280px canvas
    slot_w = min(W, max(min_w, int(W * 0.74)))
    if nw >= slot_w:
        # Place face/subject cleanly around 58% inside the right slot (which maps to ~70% of full W)
        subj_target = int(slot_w * 0.56)
        x0 = max(0, min(nw - slot_w, int(cx_norm * nw - subj_target)))
        patch = rs[y0:y0 + H, x0:x0 + slot_w]
    else:
        patch = rs[y0:y0 + H, :nw]
        slot_w = nw

    px0 = W - slot_w
    # Silky-smooth cosine S-curve left feather into studio backdrop (ZERO seams, ZERO stripes!)
    feath = min(290, max(160, int(slot_w * 0.34)))
    u = np.linspace(0.0, 1.0, feath, dtype=np.float32)
    smooth = (0.5 - 0.5 * np.cos(np.pi * u)) ** 1.15
    alpha = np.ones((H, slot_w, 1), dtype=np.float32)
    alpha[:, :feath, 0] = smooth[None, :]

    # Add ultra-subtle blurred atmospheric bleed from the photo itself behind the left backdrop
    atm = cv2.GaussianBlur(cv2.resize(im, (W, H), interpolation=cv2.INTER_AREA), (95, 95), 0)
    bg_studio = np.clip(atm.astype(np.float32) * 0.22 + np.array(base_bgr, dtype=np.float32)[None, None, :] * 0.78, 0, 255)
    roi = bg_studio[:, px0:W]
    bg_studio[:, px0:W] = patch.astype(np.float32) * alpha + roi * (1.0 - alpha)
    return np.clip(bg_studio, 0, 255).astype(np.uint8)


def _split_headline_lines(w_txt, r_txt):
    """Split headline cleanly by balanced character length into (top_line_1, top_line_2, highlight_line_3)."""
    w_words = [w for w in str(w_txt or "").strip().upper().split() if w]
    r_str = str(r_txt or "").strip().upper()
    if not w_words and not r_str:
        return "THE SECRET", "ARCHIVE", "DECLASSIFIED"
    if len(w_words) <= 2:
        l1 = " ".join(w_words)
        l2 = ""
    else:
        best_i = 1
        best_diff = 10**9
        for i in range(1, len(w_words)):
            a = " ".join(w_words[:i])
            b = " ".join(w_words[i:])
            diff = abs(len(a) - len(b)) - (0.5 if len(a) >= len(b) else 0.0)
            if diff < best_diff:
                best_diff = diff
                best_i = i
        l1 = " ".join(w_words[:best_i])
        l2 = " ".join(w_words[best_i:])
    return l1, l2, r_str


def generate_v20_thumbnail(hero_img_path, second_img_path, brand, headline_white, headline_red, stamp_badge, out_jpg,
                           center_pill=None, teaser=None):
    """
    🔥 V21 ULTRA-CTR VIRAL DOCUMENTARY MINIATURE ENGINE (1280x720)!
    100% original, high-contrast mobile-first (160px legible!) bespoke brand identities:
      - BEHIND THE CURTAIN -> V21 'DECLASSIFIED SPY BRIEFING' (Cold War steel-platinum + crimson-amber
          rim glow + blazing vermilion power highlight + tilted TOP SECRET stamp + bottom curiosity strip)
      - HISTORY UNSEALED   -> V21 'CINEMATIC ARCHIVAL EPIC' (Hollywood teal-and-gold grade + warm radial
          spotlight + midnight-gold pill + radiant imperial-gold power highlight + archival year crest)
    Bottom-right 210x85 zone is ALWAYS kept clear for YouTube's duration badge!
    """
    W, H = 1280, 720
    is_btc = ("BEHIND" in str(brand or "").upper()) or ("CURTAIN" in str(brand or "").upper())
    l1, l2, l3 = _split_headline_lines(headline_white, headline_red)
    yr_tag = str(center_pill or stamp_badge or "").replace("->", "–").strip().upper()[:16] or "ARCHIVE"
    st_lbl = str(stamp_badge or ("CIA ARCHIVE" if is_btc else "UNSEALED")).strip().upper()[:16]
    ts_lbl = str(teaser or ("THE DECLASSIFIED ARCHIVE" if is_btc else "FULL ARCHIVAL DOCUMENTARY")).strip().upper()[:34]

    ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)

    if is_btc:
        # =====================================================================
        # CHANNEL 1: BEHIND THE CURTAIN — V21 'DECLASSIFIED SPY BRIEFING'
        # =====================================================================
        bg = _frame_subject_right(hero_img_path, W, H, base_bgr=(12, 13, 18))

        # High-contrast Cold War Steel-Platinum + Warm Tungsten Highlights split-tone!
        g = cv2.cvtColor(bg, cv2.COLOR_BGR2GRAY).astype(np.float32)
        g_norm = np.clip(g / 255.0, 0.0, 1.0)
        g_s = np.clip(((g_norm - 0.45) * 1.28 + 0.46), 0.0, 1.0) * 255.0
        # Cool steel shadows + warm silver-tungsten highlights (beats flat dead gray on mobile!)
        hi_w = np.clip((g_s - 120.0) / 135.0, 0.0, 1.0)
        sh_w = 1.0 - hi_w
        b_ch = np.clip(g_s * (1.06 * sh_w + 0.90 * hi_w) + 6 * sh_w, 0, 255)
        g_ch = np.clip(g_s * (1.00 * sh_w + 0.98 * hi_w) + 2 * sh_w, 0, 255)
        r_ch = np.clip(g_s * (0.93 * sh_w + 1.10 * hi_w), 0, 255)
        graded = cv2.merge([b_ch, g_ch, r_ch]).astype(np.float32)

        # Deep obsidian left sweep + crisp subject spotlight on right + crimson-amber rim backlight!
        left_dark = np.clip(1.0 - (xs / 790.0), 0.0, 1.0) ** 1.25
        bot_dark = np.clip((ys - 500.0) / 220.0, 0.0, 1.0) ** 1.5
        shade = np.clip(1.0 - 0.90 * left_dark - 0.45 * bot_dark, 0.08, 1.0)
        canvas = graded * shade[:, :, None]

        # Dramatic Crimson-Amber Intelligence Backlight behind subject & left power zone
        rim_d = np.exp(-(((xs - 660.0) / 310.0) ** 2 + ((ys - 370.0) / 290.0) ** 2))
        canvas[:, :, 2] = np.clip(canvas[:, :, 2] + rim_d * 54.0, 0, 255)
        canvas[:, :, 1] = np.clip(canvas[:, :, 1] + rim_d * 14.0, 0, 255)
        canvas[:, :, 0] = np.clip(canvas[:, :, 0] + rim_d * 10.0, 0, 255)

        # Subtle 35mm cinema grain
        rng = np.random.default_rng(sum(ord(c) for c in f"{l1}{l3}") + 1983)
        grain = rng.normal(0, 4.2, (H, W, 1)).astype(np.float32)
        canvas = np.clip(canvas + grain, 0, 255).astype(np.uint8)

        im = Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)).convert("RGBA")
        dr = ImageDraw.Draw(im)

        # Subtle crimson top cinema stripe + left vertical intelligence bar
        dr.rectangle([0, 0, W, 8], fill=(226, 30, 36, 255))
        dr.rectangle([48, 72, 58, 636], fill=(228, 32, 38, 255))

        # Subtle classified crosshair ticks in top-left dark backdrop
        for gx in (58, 290, 520):
            dr.line([(gx, 38), (gx, 52)], fill=(255, 255, 255, 58), width=1)

        # 1) Top Blazing Solid Vermilion Eyebrow Pill (100% legible on mobile!)
        f_pill = load_font(FONT_MONO, 24, 700)
        pill_txt = f"DECLASSIFIED  •  {yr_tag}"[:30]
        pw_p = int(dr.textlength(pill_txt, font=f_pill)) + 36
        dr.rounded_rectangle([80, 72, 80 + pw_p, 118], radius=7, fill=(224, 28, 34, 255))
        dr.text((80 + pw_p // 2, 95), pill_txt, font=f_pill, fill=(255, 252, 248, 255), anchor="mm")

        # 2) Massive Pure Bone-White Stacked Power Lines (112-130px!)
        max_lw = 575
        white_lines = [s for s in (l1, l2) if s]
        y_cur = 152 if len(white_lines) == 2 else 218
        for wl in white_lines:
            fsz = 122 if len(white_lines) == 2 else 132
            f_use = load_font(FONT_SANS, fsz, 800)
            while fsz >= 62 and dr.textlength(wl, font=f_use) > max_lw:
                fsz -= 4
                f_use = load_font(FONT_SANS, fsz, 800)
            _draw_soft_shadow_text(im, (78, y_cur), wl, f_use, (254, 252, 248, 255), anchor="la", blur_r=10)
            y_cur += int(fsz * 1.07)

        # 3) Blazing Vermilion Power Climax Banner (with subtle crimson glow + gold top edge!)
        hl_txt = l3 or "DECLASSIFIED"
        fsz_h = 98
        f_hl = load_font(FONT_SANS, fsz_h, 800)
        while fsz_h >= 50 and dr.textlength(hl_txt, font=f_hl) > 540:
            fsz_h -= 4
            f_hl = load_font(FONT_SANS, fsz_h, 800)
        dr = ImageDraw.Draw(im)
        rw = int(dr.textlength(hl_txt, font=f_hl)) + 52
        rh = int(fsz_h * 1.30)
        ry = max(y_cur + 16, 412)
        ry = min(ry, H - 122 - rh)
        # Soft red ambient glow behind power banner
        glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(glow).rounded_rectangle([72, ry - 6, 86 + rw, ry + rh + 6], radius=14, fill=(235, 32, 38, 120))
        glow = glow.filter(ImageFilter.GaussianBlur(radius=16))
        im.alpha_composite(glow)
        dr = ImageDraw.Draw(im)
        dr.rounded_rectangle([78, ry, 78 + rw, ry + rh], radius=10, fill=(224, 26, 32, 255))
        dr.line([(90, ry + 3), (78 + rw - 12, ry + 3)], fill=(255, 212, 92, 235), width=3)
        dr.text((104, ry + rh // 2), hl_txt, font=f_hl, fill=(255, 252, 248, 255), anchor="lm")

        # 4) Bottom-Left Frosted Curiosity Strip (100% legible over ANY bright background!)
        f_ts = load_font(FONT_MONO, 22, 700)
        ts_w = int(dr.textlength(ts_lbl, font=f_ts))
        by_ts = H - 84
        dr.rounded_rectangle([78, by_ts - 22, 78 + ts_w + 54, by_ts + 22], radius=7, fill=(10, 12, 18, 225), outline=(255, 255, 255, 76), width=1)
        dr.ellipse([94, by_ts - 6, 106, by_ts + 6], fill=(248, 206, 68, 255))
        dr.text((118, by_ts), ts_lbl, font=f_ts, fill=(242, 244, 248, 248), anchor="lm")

        # 5) Top-Right Authentic Tilted Rubber Stamp (NEVER overlaps YouTube's bottom-right timestamp!)
        st_badge = _draw_rubber_stamp_badge(st_lbl, color_rgba=(255, 74, 78, 252), angle=-8.5)
        im.alpha_composite(st_badge, (W - st_badge.width - 34, 28))

    else:
        # =====================================================================
        # CHANNEL 2: HISTORY UNSEALED — V21 'CINEMATIC ARCHIVAL EPIC'
        # =====================================================================
        bg = _frame_subject_right(hero_img_path, W, H, base_bgr=(11, 14, 22))

        # Rich Hollywood Teal-Shadows & Warm Golden-Hour Highlights cinema color grade!
        bg_f = bg.astype(np.float32)
        luma = (0.114 * bg_f[:, :, 0] + 0.587 * bg_f[:, :, 1] + 0.299 * bg_f[:, :, 2]) / 255.0
        hi_w = np.clip((luma - 0.35) / 0.65, 0.0, 1.0)
        sh_w = 1.0 - hi_w
        bg_f[:, :, 2] = np.clip(bg_f[:, :, 2] * (0.94 * sh_w + 1.15 * hi_w) + 6 * hi_w, 0, 255)
        bg_f[:, :, 1] = np.clip(bg_f[:, :, 1] * (1.00 * sh_w + 1.04 * hi_w), 0, 255)
        bg_f[:, :, 0] = np.clip(bg_f[:, :, 0] * (1.08 * sh_w + 0.84 * hi_w) + 8 * sh_w, 0, 255)

        # Deep Royal Midnight-Obsidian left sweep + warm bottom cinema vignette
        grad_l = np.clip(1.0 - xs / 810.0, 0.0, 1.0) ** 1.25
        grad_b = np.clip((ys - 485.0) / 235.0, 0.0, 1.0) ** 1.45
        shade = np.clip(1.0 - 0.91 * grad_l - 0.46 * grad_b, 0.08, 1.0)
        canvas = bg_f * shade[:, :, None]

        # Warm Golden-Amber Cinema Backlight Halo separating subject & headline!
        gold_d = np.exp(-(((xs - 740.0) / 340.0) ** 2 + ((ys - 330.0) / 280.0) ** 2))
        canvas[:, :, 2] = np.clip(canvas[:, :, 2] + gold_d * 46.0, 0, 255)
        canvas[:, :, 1] = np.clip(canvas[:, :, 1] + gold_d * 34.0, 0, 255)
        canvas[:, :, 0] = np.clip(canvas[:, :, 0] + gold_d * 8.0, 0, 255)
        canvas = np.clip(canvas, 0, 255).astype(np.uint8)

        im = Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)).convert("RGBA")
        dr = ImageDraw.Draw(im)

        # Signature top gold hairline + vertical Imperial Gold Documentary Pillar
        dr.rectangle([0, 0, W, 8], fill=(246, 198, 62, 255))
        dr.rectangle([50, 74, 60, 636], fill=(246, 198, 62, 255))

        # 1) Top Solid Midnight-Gold Eyebrow Pill (100% readable even over bright ivory engravings!)
        f_eye = load_font(FONT_MONO, 24, 700)
        eye_txt = f"HISTORY UNSEALED  •  {yr_tag}"[:32]
        ew = int(dr.textlength(eye_txt, font=f_eye)) + 40
        dr.rounded_rectangle([82, 74, 82 + ew, 120], radius=8, fill=(14, 18, 28, 242), outline=(246, 198, 62, 245), width=2)
        dr.text((82 + ew // 2, 97), eye_txt, font=f_eye, fill=(250, 208, 76, 255), anchor="mm")

        # 2) Massive Pure-White Stacked Movie-Poster Headline (zero cartoon black borders -> lush studio shadow!)
        max_lw = 620
        white_lines = [s for s in (l1, l2) if s]
        y_cur = 154 if len(white_lines) == 2 else 220
        for wl in white_lines:
            fsz = 122 if len(white_lines) == 2 else 134
            f_use = load_font(FONT_SANS, fsz, 800)
            while fsz >= 62 and dr.textlength(wl, font=f_use) > max_lw:
                fsz -= 4
                f_use = load_font(FONT_SANS, fsz, 800)
            _draw_soft_shadow_text(im, (82, y_cur), wl, f_use, (255, 254, 250, 255), anchor="la", blur_r=11)
            y_cur += int(fsz * 1.07)

        # 3) Radiant Imperial-Gold Climax Power Banner (blazing gold ribbon + dark obsidian ink -> unstoppable CTR!)
        hl_txt = l3 or yr_tag
        fsz_h = 98
        f_hl = load_font(FONT_SANS, fsz_h, 800)
        while fsz_h >= 50 and dr.textlength(hl_txt, font=f_hl) > 580:
            fsz_h -= 4
            f_hl = load_font(FONT_SANS, fsz_h, 800)
        dr = ImageDraw.Draw(im)
        rw = int(dr.textlength(hl_txt, font=f_hl)) + 54
        rh = int(fsz_h * 1.30)
        ry = max(y_cur + 16, 412)
        ry = min(ry, H - 122 - rh)
        glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(glow).rounded_rectangle([76, ry - 6, 90 + rw, ry + rh + 6], radius=14, fill=(248, 200, 62, 115))
        glow = glow.filter(ImageFilter.GaussianBlur(radius=16))
        im.alpha_composite(glow)
        dr = ImageDraw.Draw(im)
        dr.rounded_rectangle([82, ry, 82 + rw, ry + rh], radius=10, fill=(248, 200, 58, 255))
        dr.line([(94, ry + 3), (82 + rw - 12, ry + 3)], fill=(255, 245, 200, 240), width=3)
        dr.text((109, ry + rh // 2), hl_txt, font=f_hl, fill=(14, 16, 22, 255), anchor="lm")

        # 4) Bottom-Left Frosted Documentary Tag Pill (leaving bottom-right 100% clear for YouTube timestamp!)
        f_ts = load_font(FONT_MONO, 22, 700)
        ts_w = int(dr.textlength(ts_lbl, font=f_ts))
        by_ts = H - 84
        dr.rounded_rectangle([82, by_ts - 22, 82 + ts_w + 54, by_ts + 22], radius=7, fill=(12, 15, 24, 228), outline=(246, 198, 62, 145), width=1)
        # Gold diamond icon
        dr.polygon([(104, by_ts - 7), (111, by_ts), (104, by_ts + 7), (97, by_ts)], fill=(248, 204, 68, 255))
        dr.text((122, by_ts), ts_lbl, font=f_ts, fill=(244, 242, 236, 248), anchor="lm")

        # 5) Top-Right Sleek Obsidian-Gold Archive Year Crest (away from faces & bottom-right timestamp!)
        crest_txt = f"ARCHIVE  //  {yr_tag}"[:22]
        f_cr = load_font(FONT_MONO, 20, 700)
        cw_c = int(dr.textlength(crest_txt, font=f_cr)) + 34
        dr.rounded_rectangle([W - cw_c - 38, 34, W - 38, 76], radius=7, fill=(12, 15, 24, 224), outline=(246, 198, 62, 210), width=2)
        dr.text((W - 38 - cw_c // 2, 55), crest_txt, font=f_cr, fill=(248, 206, 74, 255), anchor="mm")

    im.convert("RGB").save(out_jpg, "JPEG", quality=94, optimize=True)
    style_lbl = "V21 DECLASSIFIED-BRIEFING" if is_btc else "V21 ARCHIVAL-EPIC"
    print(f"[{style_lbl} THUMB OK] {out_jpg} ({os.path.getsize(out_jpg)/1024:.1f} KB)")
    return out_jpg


def _frame_subject_center_shorts(img_path, W=1280, H=720, base_bgr=(12, 13, 18)):
    """
    Centers the hero archival subject (face-aware!) inside the YouTube Shorts 9:16 center viewport
    (x=437..843, upper hero zone y=55..410) over a smooth full-bleed atmospheric 1280x720 backdrop.
    Guarantees ZERO clipped subjects in Shorts 9:16/3:5 grid AND ZERO black bars in 16:9 views!
    """
    im = cv2.imread(img_path) if (img_path and os.path.exists(img_path)) else None
    if im is None:
        return np.full((H, W, 3), base_bgr, dtype=np.uint8)
    ih, iw = im.shape[:2]

    # 1) Full-bleed atmospheric blurred wings across 1280x720 (so 16:9 views look cinema-wide!)
    sc_bg = max(W / float(iw), H / float(ih))
    bg_rs = cv2.resize(im, (int(round(iw * sc_bg)), int(round(ih * sc_bg))), interpolation=cv2.INTER_AREA)
    by0 = max(0, (bg_rs.shape[0] - H) // 2)
    bx0 = max(0, (bg_rs.shape[1] - W) // 2)
    bg_full = bg_rs[by0:by0 + H, bx0:bx0 + W]
    bg_full = cv2.GaussianBlur(bg_full, (0, 0), sigmaX=24, sigmaY=24)
    bg_full = np.clip(bg_full.astype(np.float32) * 0.42, 0, 255).astype(np.uint8)

    # 2) Sharp hero plate framed cleanly inside the 9:16 Shorts center zone (560 x 500 around x=640, y=0..500)
    #    Wider than 432px (560px) with feathered edges so 3:5 and 9:16 crops see a 100% crisp edge-to-edge photo!
    box_w, box_h = 560, 495
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    fx, fy = iw * 0.5, ih * 0.34
    try:
        casc = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        faces = casc.detectMultiScale(gray, 1.12, 4, minSize=(40, 40))
        if len(faces) > 0:
            x, y, fw, fh = max(faces, key=lambda r: r[2] * r[3])
            fx = x + fw * 0.50
            fy = y + fh * 0.44
    except Exception:
        pass

    # Compute cover scale for the center hero stage without over-zooming faces
    sc = max(box_w / float(iw), box_h / float(ih))
    # For wide landscapes, zoom just enough to fill box_h cleanly while centering on subject
    rw = max(box_w, int(round(iw * sc)))
    rh = max(box_h, int(round(ih * sc)))
    rs = cv2.resize(im, (rw, rh), interpolation=cv2.INTER_LANCZOS4)

    cx_s = fx * (rw / float(iw))
    cy_s = fy * (rh / float(ih))
    # Target eyes / focal center at x = box_w/2, y = box_h * 0.42 (right in the open Shorts window!)
    sx0 = int(round(max(0, min(rw - box_w, cx_s - box_w * 0.50))))
    sy0 = int(round(max(0, min(rh - box_h, cy_s - box_h * 0.44))))
    crop = rs[sy0:sy0 + box_h, sx0:sx0 + box_w].copy()

    # Smooth feather mask blending center hero cleanly into the 16:9 cinema wings & dark bottom typography bed
    canvas = bg_full.astype(np.float32)
    hx0 = (W - box_w) // 2
    hy0 = 0
    m_x = np.ones(box_w, dtype=np.float32)
    fade_x = 58
    m_x[:fade_x] = np.linspace(0.0, 1.0, fade_x)
    m_x[-fade_x:] = np.linspace(1.0, 0.0, fade_x)
    m_y = np.ones(box_h, dtype=np.float32)
    fade_y = 95
    m_y[-fade_y:] = np.linspace(1.0, 0.0, fade_y) ** 1.3
    alpha = (m_y[:, None] * m_x[None, :])[:, :, None]

    roi = canvas[hy0:hy0 + box_h, hx0:hx0 + box_w]
    canvas[hy0:hy0 + box_h, hx0:hx0 + box_w] = crop.astype(np.float32) * alpha + roi * (1.0 - alpha)
    return np.clip(canvas, 0, 255).astype(np.uint8)


def generate_v21_shorts_thumbnail(hero_img_path, second_img_path, brand, headline_white, headline_red, stamp_badge, out_jpg,
                                  center_pill=None, teaser=None):
    """
    🔥 V21 SHORTS-NATIVE DUAL-SAFE MINIATURE ENGINE (1280x720 canvas, 100% 9:16 & 3:5 CENTER-SAFE)!
    Solves YouTube Shorts Grid center-cropping (x=437..843 at 9:16, x=424..856 at 3:5):
      - ALL typography, eyebrow pill, power banner, and focal subject are centered strictly inside
        x = 462..818 (356px safe width) and y = 26..610 (safely below '...' & well above '107 vues'!).
      - Full 1280x720 cinema backdrop ensures ZERO black bars in Search / Home / Desktop Share!
      - Matches exact V21 brand palettes:
          * BEHIND THE CURTAIN -> Cold War Steel-Platinum + Blazing Vermilion Red
          * HISTORY UNSEALED   -> Hollywood Teal-and-Gold + Radiant Imperial Gold
    """
    W, H = 1280, 720
    CX = W // 2  # 640
    SAFE_W = 352  # x = 464..816 -> >=27px clean margin even on strict 9:16 (437..843)!
    is_btc = ("BEHIND" in str(brand or "").upper()) or ("CURTAIN" in str(brand or "").upper())
    l1, l2, l3 = _split_headline_lines(headline_white, headline_red)
    yr_tag = str(center_pill or stamp_badge or "").replace("->", "–").strip().upper()[:10] or "ARCHIVE"
    ts_lbl = str(teaser or ("DECLASSIFIED FILE" if is_btc else "ARCHIVE UNSEALED")).strip().upper()[:28]

    ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
    bg = _frame_subject_center_shorts(hero_img_path, W, H, base_bgr=(11, 13, 19))

    if is_btc:
        # Steel-Platinum + Warm Tungsten Highlights split-tone
        g = cv2.cvtColor(bg, cv2.COLOR_BGR2GRAY).astype(np.float32)
        g_norm = np.clip(g / 255.0, 0.0, 1.0)
        g_s = np.clip(((g_norm - 0.44) * 1.26 + 0.47), 0.0, 1.0) * 255.0
        hi_w = np.clip((g_s - 118.0) / 137.0, 0.0, 1.0)
        sh_w = 1.0 - hi_w
        graded = cv2.merge([
            np.clip(g_s * (1.06 * sh_w + 0.90 * hi_w) + 6 * sh_w, 0, 255),
            np.clip(g_s * (1.00 * sh_w + 0.98 * hi_w) + 2 * sh_w, 0, 255),
            np.clip(g_s * (0.93 * sh_w + 1.10 * hi_w), 0, 255),
        ]).astype(np.float32)
    else:
        # Hollywood Teal-Shadows & Warm Golden-Hour Highlights
        bg_f = bg.astype(np.float32)
        luma = (0.114 * bg_f[:, :, 0] + 0.587 * bg_f[:, :, 1] + 0.299 * bg_f[:, :, 2]) / 255.0
        hi_w = np.clip((luma - 0.34) / 0.66, 0.0, 1.0)
        sh_w = 1.0 - hi_w
        graded = bg_f.copy()
        graded[:, :, 2] = np.clip(bg_f[:, :, 2] * (0.94 * sh_w + 1.15 * hi_w) + 6 * hi_w, 0, 255)
        graded[:, :, 1] = np.clip(bg_f[:, :, 1] * (1.00 * sh_w + 1.04 * hi_w), 0, 255)
        graded[:, :, 0] = np.clip(bg_f[:, :, 0] * (1.08 * sh_w + 0.84 * hi_w) + 8 * sh_w, 0, 255)

    # Smooth top micro-vignette (for top pill) + lush bottom dark stage (y=360..720 for ultra-crisp text & 'vues'!)
    top_dark = np.clip(1.0 - (ys / 110.0), 0.0, 1.0) ** 1.5
    bot_dark = np.clip((ys - 335.0) / 215.0, 0.0, 1.0) ** 1.25
    wing_dark = np.clip((np.abs(xs - CX) - 245.0) / 260.0, 0.0, 1.0) ** 1.3
    shade = np.clip(1.0 - 0.52 * top_dark - 0.88 * bot_dark - 0.34 * wing_dark, 0.07, 1.0)
    canvas = graded * shade[:, :, None]

    # Subtle channel rim backlight right behind the headline divider (y=380, x=640)
    halo = np.exp(-(((xs - CX) / 210.0) ** 2 + ((ys - 375.0) / 145.0) ** 2))
    if is_btc:
        canvas[:, :, 2] = np.clip(canvas[:, :, 2] + halo * 46.0, 0, 255)
        canvas[:, :, 1] = np.clip(canvas[:, :, 1] + halo * 12.0, 0, 255)
    else:
        canvas[:, :, 2] = np.clip(canvas[:, :, 2] + halo * 40.0, 0, 255)
        canvas[:, :, 1] = np.clip(canvas[:, :, 1] + halo * 30.0, 0, 255)

    # Subtle 35mm cinema grain
    rng = np.random.default_rng(sum(ord(c) for c in f"{l1}{l3}") + 2026)
    canvas = np.clip(canvas + rng.normal(0, 3.6, (H, W, 1)).astype(np.float32), 0, 255).astype(np.uint8)

    im = Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)).convert("RGBA")
    dr = ImageDraw.Draw(im)

    # Top full-width brand bar (visible across 100% of Shorts & 16:9 width!)
    accent_rgba = (226, 28, 34, 255) if is_btc else (246, 198, 62, 255)
    dr.rectangle([0, 0, W, 8], fill=accent_rgba)

    # 1) Top Centered Compact Eyebrow Pill (y=26..58, max width 250px -> 30px+ clear of top-right '...'!)
    f_pill = load_font(FONT_MONO, 17, 700)
    pill_txt = (f"DECLASSIFIED • {yr_tag}" if is_btc else f"UNSEALED • {yr_tag}")[:23]
    pw_p = min(252, int(dr.textlength(pill_txt, font=f_pill)) + 26)
    if is_btc:
        dr.rounded_rectangle([CX - pw_p // 2, 26, CX + pw_p // 2, 58], radius=7, fill=(222, 26, 32, 248))
        dr.text((CX, 42), pill_txt, font=f_pill, fill=(255, 252, 248, 255), anchor="mm")
    else:
        dr.rounded_rectangle([CX - pw_p // 2, 26, CX + pw_p // 2, 58], radius=7, fill=(14, 18, 28, 242), outline=(246, 198, 62, 245), width=2)
        dr.text((CX, 42), pill_txt, font=f_pill, fill=(250, 208, 76, 255), anchor="mm")

    # 2) Massive Centered Bone-White Hook Line(s) inside SAFE_W (352px)!
    white_lines = [s for s in (l1, l2) if s]
    # Keep shorts headline punchy: merge into 1 line if short, else 2 tight lines
    if len(white_lines) == 2 and len(" ".join(white_lines)) <= 13:
        white_lines = [" ".join(white_lines)]

    y_cur = 378 if len(white_lines) == 2 else 412
    for wl in white_lines:
        fsz = 66 if len(white_lines) == 2 else 74
        f_use = load_font(FONT_SANS, fsz, 800)
        while fsz >= 36 and dr.textlength(wl, font=f_use) > SAFE_W:
            fsz -= 2
            f_use = load_font(FONT_SANS, fsz, 800)
        _draw_soft_shadow_text(im, (CX, y_cur + fsz // 2), wl, f_use, (255, 253, 249, 255), anchor="mm", blur_r=9)
        y_cur += int(fsz * 1.06)

    # 3) Blazing Centered Power Climax Ribbon (Vermilion Red or Imperial Gold) strictly within SAFE_W!
    hl_txt = (l3 or yr_tag).strip()
    fsz_h = 68
    f_hl = load_font(FONT_SANS, fsz_h, 800)
    while fsz_h >= 34 and dr.textlength(hl_txt, font=f_hl) > SAFE_W - 34:
        fsz_h -= 2
        f_hl = load_font(FONT_SANS, fsz_h, 800)
    dr = ImageDraw.Draw(im)
    rw = min(SAFE_W, int(dr.textlength(hl_txt, font=f_hl)) + 38)
    rh = int(fsz_h * 1.32)
    ry = max(y_cur + 8, 466)
    ry = min(ry, 566 - rh)

    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    glow_col = (235, 32, 38, 125) if is_btc else (248, 200, 62, 120)
    ImageDraw.Draw(glow).rounded_rectangle([CX - rw // 2 - 5, ry - 5, CX + rw // 2 + 5, ry + rh + 5], radius=12, fill=glow_col)
    glow = glow.filter(ImageFilter.GaussianBlur(radius=14))
    im.alpha_composite(glow)
    dr = ImageDraw.Draw(im)
    if is_btc:
        dr.rounded_rectangle([CX - rw // 2, ry, CX + rw // 2, ry + rh], radius=9, fill=(224, 26, 32, 255))
        dr.line([(CX - rw // 2 + 10, ry + 3), (CX + rw // 2 - 10, ry + 3)], fill=(255, 212, 92, 235), width=3)
        dr.text((CX, ry + rh // 2), hl_txt, font=f_hl, fill=(255, 252, 248, 255), anchor="mm")
    else:
        dr.rounded_rectangle([CX - rw // 2, ry, CX + rw // 2, ry + rh], radius=9, fill=(248, 200, 58, 255))
        dr.line([(CX - rw // 2 + 10, ry + 3), (CX + rw // 2 - 10, ry + 3)], fill=(255, 246, 204, 240), width=3)
        dr.text((CX, ry + rh // 2), hl_txt, font=f_hl, fill=(14, 16, 22, 255), anchor="mm")

    # 4) Compact Frosted Micro-Teaser Strip at y=580..612 (40px+ safely ABOVE YouTube's '107 vues' badge!)
    f_ts = load_font(FONT_MONO, 16, 700)
    while len(ts_lbl) > 12 and dr.textlength(ts_lbl, font=f_ts) > SAFE_W - 44:
        ts_lbl = ts_lbl[:-1].rstrip()
    ts_w = int(dr.textlength(ts_lbl, font=f_ts))
    by_ts = min(604, ry + rh + 28)
    box_tw = min(SAFE_W, ts_w + 38)
    out_c = (255, 255, 255, 84) if is_btc else (246, 198, 62, 155)
    dr.rounded_rectangle([CX - box_tw // 2, by_ts - 16, CX + box_tw // 2, by_ts + 16], radius=6, fill=(10, 12, 18, 230), outline=out_c, width=1)
    dr.ellipse([CX - box_tw // 2 + 10, by_ts - 4, CX - box_tw // 2 + 18, by_ts + 4], fill=(248, 206, 68, 255))
    dr.text((CX + 7, by_ts), ts_lbl, font=f_ts, fill=(244, 244, 248, 248), anchor="mm")

    im.convert("RGB").save(out_jpg, "JPEG", quality=94, optimize=True)
    style_lbl = "V21 SHORTS-BTC" if is_btc else "V21 SHORTS-HU"
    print(f"[{style_lbl} 9:16-SAFE THUMB OK] {out_jpg} ({os.path.getsize(out_jpg)/1024:.1f} KB)")
    return out_jpg


def render_midroll_book_commercial_16x9(mode, brand, voice_mp3, voice_dur, out_mp4, work_dir):
    """
    🔥 V20.5 FULL-SCREEN 16:9 MID-ROLL 2-BOOK COMMERCIAL BREAK (for 12-30m Documentaries!)
    Renders a ~11-second Netflix-grade animated showcase featuring BOTH 3D hardcover books
    ('The Declassified Vault' + 'History Unsealed') + 33% Collector's Bundle CTA + real voiceover!
    """
    W, H, FPS = 1920, 1080, 24
    raw_dur = max(8.5, voice_dur + 1.2)
    n_frames = int(round(raw_dur * FPS))
    dur = n_frames / float(FPS)
    is_btc = (mode == "behind_the_curtain")
    main_title = "THE DECLASSIFIED VAULT" if is_btc else "HISTORY UNSEALED"
    comp_title = "HISTORY UNSEALED" if is_btc else "THE DECLASSIFIED VAULT"
    cov_main = os.path.join(ASSET_DIR, "book1_cover.png" if is_btc else "book2_cover.png")
    cov_comp = os.path.join(ASSET_DIR, "book2_cover.png" if is_btc else "book1_cover.png")

    b_main = build_3d_book_mockup(cov_main, spine_title=main_title, book_h=520)
    b_comp = build_3d_book_mockup(cov_comp, spine_title=comp_title, book_h=440)
    if b_comp is not None:
        b_comp = b_comp.rotate(-9, expand=True, resample=Image.BICUBIC)

    # Rich cinematic commercial panel
    panel = Image.new("RGBA", (1740, 860), (0, 0, 0, 0))
    dr = ImageDraw.Draw(panel)
    dr.rounded_rectangle([12, 12, 1728, 848], radius=28, fill=(10, 14, 24, 245), outline=(232, 188, 78, 250), width=4)
    dr.rounded_rectangle([28, 28, 1712, 832], radius=20, outline=(232, 188, 78, 85), width=2)

    rx = 770
    f_badge = load_font(FONT_MONO, 22, 700)
    f_h1 = load_font(FONT_SANS, 56, 800)
    f_h2 = load_font(FONT_SANS, 34, 800)
    f_sub = load_font(FONT_MONO, 22, 700)
    f_cta = load_font(FONT_SANS, 27, 800)

    dr.rounded_rectangle([rx, 88, rx + 710, 142], radius=10, fill=(208, 26, 36, 255))
    dr.text((rx + 355, 115), "OFFICIAL COLLECTOR'S EDITION  •  SAVE 33%", fill=(255, 252, 248, 255), font=f_badge, anchor="mm")
    dr.text((rx, 215), "OWN THE COMPLETE", fill=(250, 250, 248, 255), font=f_h1, anchor="lm")
    dr.text((rx, 286), "DECLASSIFIED ARCHIVES", fill=(248, 208, 86, 255), font=f_h1, anchor="lm")
    dr.text((rx, 368), f"BOOK 1: {main_title}", fill=(235, 238, 246, 255), font=f_h2, anchor="lm")
    dr.text((rx, 418), f"BOOK 2: {comp_title}", fill=(202, 210, 224, 245), font=f_h2, anchor="lm")
    dr.text((rx, 488), "174 FULL-COLOR PAGES  •  50 SECRET DOSSIERS  •  INSTANT HD PDF", fill=(176, 190, 212, 245), font=f_sub, anchor="lm")

    dr.rounded_rectangle([rx, 552, rx + 870, 650], radius=16, fill=(226, 32, 40, 255), outline=(248, 208, 86, 255), width=3)
    dr.text((rx + 435, 601), "GET THE 2-BOOK BUNDLE — LINK IN DESCRIPTION", fill=(255, 252, 248, 255), font=f_cta, anchor="mm")
    dr.text((rx, 714), "SINGLE BOOK $14.99  •  2-BOOK COLLECTOR'S BUNDLE $19.99 (SAVE 33%)", fill=(248, 208, 86, 255), font=f_sub, anchor="lm")
    dr.text((rx, 766), f"UNSEALED ARCHIVES PRESS  •  OFFICIAL STORE OF {brand}", fill=(162, 174, 194, 235), font=load_font(FONT_MONO, 18, 700), anchor="lm")

    # Audio mix with subtle cinematic bed + warm gold shimmer sfx
    from voice_engine_v15 import mix_cinema_audio_v15
    audio_m4a = os.path.join(work_dir, "midroll_ad_audio.m4a")
    mix_cinema_audio_v15(voice_mp3, dur, 0.55, audio_m4a, seed=777, sfx_plan=[(0.25, "braaam", 0.34, 0.50)])

    rng = np.random.default_rng(2026)
    n_p = 55
    px = rng.uniform(0, W, n_p); py = rng.uniform(0, H, n_p)
    pvx = rng.uniform(-18, 28, n_p); pvy = rng.uniform(-55, -18, n_p)
    pr = rng.integers(2, 5, n_p)

    err_log = open(out_mp4 + ".ff.log", "wb")
    vproc = subprocess.Popen([
        FFMPEG, "-y",
        "-f", "rawvideo", "-vcodec", "rawvideo", "-pix_fmt", "bgr24",
        "-s", f"{W}x{H}", "-r", str(FPS), "-i", "pipe:0",
        "-i", audio_m4a,
        "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "libx264", "-preset", "superfast", "-crf", "21",
        "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", "-shortest", out_mp4
    ], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=err_log)

    for fi in range(n_frames):
        t = fi / float(FPS)
        p = t / dur
        # Deep luxury navy/obsidian radial backdrop with subtle gold volumetric glow
        bg = np.full((H, W, 3), (18, 12, 8), dtype=np.uint8)
        bg = add_anamorphic_flare(bg, int(H * 0.45), int(W * (0.28 + 0.14 * math.sin(t * 0.9))), intensity=0.45, color_bgr=(65, 182, 248))
        for k in range(n_p):
            cv2.circle(bg, (int((px[k] + pvx[k] * t) % W), int((py[k] + pvy[k] * t) % H)), int(pr[k]), (75, 188, 248), -1, cv2.LINE_AA)

        a_in = ease_out(min(1.0, t / 0.48))
        a_out = ease_out(min(1.0, (dur - t) / 0.55))
        al = a_in * a_out

        frame = comp_pil(bg, panel, W / 2.0, H / 2.0, scale=0.95 + 0.05 * a_in, alpha=al, shadow=True)
        # Animated 3D floating books on the left side of the commercial panel!
        bob1 = math.sin(t * 2.1) * 9.0
        bob2 = math.sin(t * 2.1 + 1.4) * 9.0
        if b_comp is not None:
            frame = comp_pil(frame, b_comp, 585.0, H / 2.0 + 30.0 + bob2, scale=0.92 + 0.08 * a_in, alpha=al, shadow=True)
        if b_main is not None:
            frame = comp_pil(frame, b_main, 310.0, H / 2.0 - 10.0 + bob1, scale=0.94 + 0.06 * a_in, alpha=al, shadow=True)

        vproc.stdin.write(frame.tobytes())

    vproc.stdin.close()
    ret = vproc.wait()
    err_log.close()
    if ret != 0:
        raise RuntimeError(open(out_mp4 + ".ff.log", "rb").read().decode("utf-8", errors="ignore")[-600:])
    os.remove(out_mp4 + ".ff.log")
    print(f"[V20.5 MIDROLL COMMERCIAL OK] {out_mp4} ({dur:.1f}s, 1920x1080 24fps)")
    return out_mp4

