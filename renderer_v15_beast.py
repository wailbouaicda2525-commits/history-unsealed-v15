"""
renderer_v15_beast.py — V15 'BEAST MODE' (سطاج الوحش) CINEMA RENDER ENGINE
Supports BOTH:
  - 9:16 Vertical Shorts (1080x1920, 30 FPS)
  - 16:9 Widescreen Documentaries (1920x1080, 24 FPS)
  - V15 High-CTR 1280x720 Auto Thumbnail Generator

V15 BEAST UPGRADES OVER V10:
  1) 3D Earth Globe (sapphire-gold Fresnel atmosphere) -> Hyperspace Dive -> 3D Tilted Esri Tactical Map
     with 360-deg Rotating Military Radar Sweep Wedge + Animated Glowing Bezier Flight/Intel Arc + Split-Flap Year Slam!
  2) Multi-layer 2.5D Depth-Parallax + Sweeping Anamorphic Lens Flare -> Leica Flash ->
     Jagged Torn-Edge Vintage Newspaper Cutout + 3D Red Pushpins + Taut Detective Red String -> Tilted Polaroid + Stamp Recoil!
  3) Detective Evidence Board + Classified Dossier + Wet-Ink Exact-Fit Highlighter + LIVE 2.2x GLASS MAGNIFYING LENS SCAN!
  4) Crimson Laser Split-Screen Dual Archival Reveal -> Real Barrel-Curved CRT Monitor + Scrolling Hex Telemetry +
     16-BAND LIVE FFT SPECTRUM ANALYZER + LIVE VOICE OSCILLOSCOPE!
  5) Volumetric Glowing Embers + Giant Background Year Watermark + Spring-Pop Climax Stat Card -> Branded V15 Outro!
  6) Glassmorphic Spring-Bounce Pro Subtitles (Zero Shorts UI overlap) + Faststream CRF 22 H.264 Encoding!
"""
import os
import math
import shutil
import textwrap
import subprocess
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

try:
    import imageio_ffmpeg
    FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    FFMPEG = shutil.which("ffmpeg") or "ffmpeg"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_SANS = os.path.join(BASE_DIR, "fonts", "Montserrat-Var.ttf")
if not os.path.exists(FONT_SANS):
    FONT_SANS = "/home/user/twopercentquiz-autopilot/fonts/Montserrat-Var.ttf"
FONT_SPACE = os.path.join(BASE_DIR, "fonts", "SpaceGrotesk-Var.ttf")
if not os.path.exists(FONT_SPACE):
    FONT_SPACE = "/home/user/twopercentquiz-autopilot/fonts/SpaceGrotesk-Var.ttf"
if not os.path.exists(FONT_SPACE):
    FONT_SPACE = FONT_SANS
FONT_MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
if not os.path.exists(FONT_MONO):
    FONT_MONO = FONT_SANS


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
    t = max(0.0, min(1.0, t))
    t -= 1.0
    return t * t * ((s + 1.0) * t + s) + 1.0


def cover_plate(path, tw, th, sat=0.80, con=1.18, br=0.86):
    im = Image.open(path).convert("RGB")
    iw, ih = im.size
    sc = max(tw / iw, th / ih)
    nw, nh = max(tw, int(round(iw * sc))), max(th, int(round(ih * sc)))
    im = im.resize((nw, nh), Image.LANCZOS)
    x0 = (nw - tw) // 2
    # Rule-of-thirds upper-weighted crop so faces/heads in historical portraits are NEVER clipped!
    y0 = int(round((nh - th) * 0.24))
    im = im.crop((x0, y0, x0 + tw, y0 + th))
    im = ImageEnhance.Color(im).enhance(sat)
    im = ImageEnhance.Contrast(im).enhance(con)
    im = ImageEnhance.Brightness(im).enhance(br)
    return cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR)


def comp_rgba(dst_bgr, ov_rgba, cx, cy, alpha=1.0):
    oh, ow = ov_rgba.shape[:2]
    dh, dw = dst_bgr.shape[:2]
    x0, y0 = int(round(cx - ow / 2.0)), int(round(cy - oh / 2.0))
    sx0, sy0 = max(0, -x0), max(0, -y0)
    dx0, dy0 = max(0, x0), max(0, y0)
    cw, ch = min(ow - sx0, dw - dx0), min(oh - sy0, dh - dy0)
    if cw <= 0 or ch <= 0:
        return dst_bgr
    ov = ov_rgba[sy0:sy0 + ch, sx0:sx0 + cw]
    a = (ov[:, :, 3:4].astype(np.float32) / 255.0) * float(alpha)
    roi = dst_bgr[dy0:dy0 + ch, dx0:dx0 + cw].astype(np.float32)
    dst_bgr[dy0:dy0 + ch, dx0:dx0 + cw] = np.clip(ov[:, :, 2::-1].astype(np.float32) * a + roi * (1.0 - a), 0, 255).astype(np.uint8)
    return dst_bgr


def comp_pil(dst_bgr, pil_im, cx, cy, scale=1.0, angle=0.0, alpha=1.0, shadow=False):
    if alpha <= 0.01 or scale <= 0.05:
        return dst_bgr
    im = pil_im
    if abs(scale - 1.0) > 0.005:
        im = im.resize((max(4, int(im.width * scale)), max(4, int(im.height * scale))), Image.BICUBIC)
    if abs(angle) > 0.05:
        im = im.rotate(angle, expand=True, resample=Image.BICUBIC)
    arr = np.asarray(im)
    if shadow:
        sh = np.zeros_like(arr)
        sh[:, :, 3] = (arr[:, :, 3].astype(np.float32) * 0.52).astype(np.uint8)
        dst_bgr = comp_rgba(dst_bgr, sh, cx + 14, cy + 20, alpha=alpha)
    return comp_rgba(dst_bgr, arr, cx, cy, alpha=alpha)


def add_anamorphic_flare(frame, y_pos, x_center, intensity=0.45, color_bgr=(60, 185, 255)):
    """Cinematic horizontal anamorphic lens flare streak sweeping across highlights."""
    if intensity <= 0.02:
        return frame
    H, W = frame.shape[:2]
    yc = int(max(12, min(H - 13, y_pos)))
    xc = int(max(0, min(W - 1, x_center)))
    band_h = 34
    y0, y1 = max(0, yc - band_h), min(H, yc + band_h)
    yy = np.linspace(-1.0, 1.0, y1 - y0, dtype=np.float32)[:, None]
    xx = (np.arange(W, dtype=np.float32)[None, :] - xc) / (W * 0.42)
    streak = np.exp(-yy * yy * 14.0) * np.exp(-xx * xx * 2.2) * intensity
    core = np.exp(-yy * yy * 42.0) * np.exp(-xx * xx * 18.0) * intensity * 0.9
    col = np.array(color_bgr, dtype=np.float32)[None, None, :]
    roi = frame[y0:y1, :].astype(np.float32)
    roi += streak[:, :, None] * col + core[:, :, None] * 255.0
    frame[y0:y1, :] = np.clip(roi, 0, 255).astype(np.uint8)
    return frame


def sample_25d_beast(plate, W, H, p, style=0, flare_phase=None):
    """V15 Multi-Layer 2.5D Depth-Parallax Push + Edge Tilt-Shift Bokeh + Optional Anamorphic Flare."""
    ph, pw = plate.shape[:2]
    t = ease_io(p)
    if style == 0:
        z = 1.04 + 0.14 * t; cx = pw * (0.48 + 0.04 * t); cy = ph * (0.49 - 0.02 * t)
    elif style == 1:
        z = 1.15 - 0.11 * t; cx = pw * (0.52 - 0.05 * t); cy = ph * (0.50 + 0.02 * t)
    else:
        z = 1.03 + 0.13 * t; cx = pw * (0.50 + 0.03 * math.sin(t * 2.4)); cy = ph * (0.52 - 0.04 * t)
    M = np.float32([[z, 0, W / 2.0 - cx * z], [0, z, H / 2.0 - cy * z]])
    out = cv2.warpAffine(plate, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    # Subtle depth separation: slight radial edge bokeh (simulates 35mm f/1.4 cinema lens!)
    soft = cv2.GaussianBlur(out, (15, 15), 0)
    band = max(40, H // 9)
    out[:band] = cv2.addWeighted(out[:band], 0.55, soft[:band], 0.45, 0)
    out[-band:] = cv2.addWeighted(out[-band:], 0.55, soft[-band:], 0.45, 0)
    if flare_phase is not None:
        fx = W * (0.15 + 0.70 * flare_phase)
        fi = math.sin(math.pi * max(0.0, min(1.0, flare_phase))) * 0.42
        out = add_anamorphic_flare(out, int(H * 0.36), int(fx), intensity=fi, color_bgr=(72, 195, 255))
    return out


def build_torn_newspaper(headline, date_label, location, width=840):
    """Creates a realistic jagged torn-paper vintage archival newspaper headline clipping!"""
    h = 250
    im = Image.new("RGBA", (width, h), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    rng = np.random.default_rng(abs(hash(headline)) % 99991)
    # Jagged torn top & bottom polygon!
    pts = []
    for x in range(18, width - 18, 16):
        pts.append((x, int(14 + rng.integers(-6, 7))))
    pts.append((width - 14, h - 18))
    for x in range(width - 18, 18, -16):
        pts.append((x, int(h - 14 + rng.integers(-7, 6))))
    pts.append((14, 18))
    dr.polygon(pts, fill=(232, 224, 204, 252), outline=(168, 156, 134, 255))
    # Subtle newsprint aging speckles
    for _ in range(160):
        px, py = int(rng.integers(24, width - 24)), int(rng.integers(24, h - 24))
        dr.point((px, py), fill=(185, 174, 150, 140))

    f_mast = load_font(FONT_MONO, 20)
    f_hl = load_font(FONT_SANS, 44, 800)
    dr.line([(36, 56), (width - 36, 56)], fill=(35, 32, 28, 220), width=3)
    dr.line([(36, 63), (width - 36, 63)], fill=(35, 32, 28, 160), width=1)
    dr.text((width // 2, 36), f"THE ARCHIVE CHRONICLE  •  {date_label}  •  EXTRA EDITION", fill=(165, 28, 32, 250), font=f_mast, anchor="mm")

    wrapped = textwrap.fill(headline.upper(), width=26)
    lines = wrapped.split("\n")[:2]
    y_start = 120 if len(lines) == 2 else 142
    for idx, ln in enumerate(lines):
        dr.text((width // 2, y_start + idx * 52), ln, fill=(18, 16, 15, 255), font=f_hl, anchor="mm")
    dr.line([(36, h - 34), (width - 36, h - 34)], fill=(45, 40, 35, 175), width=2)
    return im


def draw_pushpin(frame, x, y):
    """3D glossy crimson detective corkboard pushpin with cast shadow."""
    cv2.circle(frame, (int(x) + 7, int(y) + 9), 15, (8, 8, 10), -1, cv2.LINE_AA)
    cv2.circle(frame, (int(x), int(y)), 15, (28, 24, 185), -1, cv2.LINE_AA)
    cv2.circle(frame, (int(x) - 2, int(y) - 2), 11, (44, 40, 240), -1, cv2.LINE_AA)
    cv2.circle(frame, (int(x) - 5, int(y) - 5), 4, (195, 205, 255), -1, cv2.LINE_AA)


def apply_magnifying_lens(frame, cx, cy, radius=135, zoom=1.85):
    """Live 2.2x optical glass magnifying lens gliding over forensic dossier evidence!"""
    H, W = frame.shape[:2]
    cx, cy = int(cx), int(cy)
    r = int(radius)
    x0, x1 = max(0, cx - r), min(W, cx + r)
    y0, y1 = max(0, cy - r), min(H, cy + r)
    if x1 - x0 < 20 or y1 - y0 < 20:
        return frame
    src_r = max(12, int(r / zoom))
    sx0, sx1 = max(0, cx - src_r), min(W, cx + src_r)
    sy0, sy1 = max(0, cy - src_r), min(H, cy + src_r)
    crop = frame[sy0:sy1, sx0:sx1]
    if crop.size == 0:
        return frame
    mag = cv2.resize(crop, (x1 - x0, y1 - y0), interpolation=cv2.INTER_CUBIC)
    # Enhance contrast inside lens slightly
    mag = np.clip(mag.astype(np.float32) * 1.08 + 6, 0, 255).astype(np.uint8)

    yy, xx = np.ogrid[y0 - cy:y1 - cy, x0 - cx:x1 - cx]
    dist2 = xx * xx + yy * yy
    mask = dist2 <= (r - 5) ** 2
    roi = frame[y0:y1, x0:x1]
    roi[mask] = mag[mask]
    # Glass rim + crimson optical crosshair + diagonal specular reflection!
    cv2.circle(frame, (cx + 8, cy + 10), r, (10, 10, 14), 10, cv2.LINE_AA)
    cv2.circle(frame, (cx, cy), r, (50, 56, 68), 9, cv2.LINE_AA)
    cv2.circle(frame, (cx, cy), r - 4, (205, 215, 228), 2, cv2.LINE_AA)
    cv2.ellipse(frame, (cx - r // 3, cy - r // 3), (r // 3, r // 7), -35, 0, 360, (235, 242, 255), 3, cv2.LINE_AA)
    cv2.line(frame, (cx - 16, cy), (cx + 16, cy), (50, 48, 240), 2, cv2.LINE_AA)
    cv2.line(frame, (cx, cy - 16), (cx, cy + 16), (50, 48, 240), 2, cv2.LINE_AA)
    return frame


def build_subtitle_cues(words, speech_off, vertical=True):
    max_words = 3 if vertical else 6
    cues = []
    buf = []
    for w in words:
        buf.append({"w": w["w"], "s": w["s"] + speech_off, "e": w["e"] + speech_off})
        end_p = bool(w["w"]) and w["w"][-1] in ".!?,"
        if len(buf) >= max_words or end_p:
            cues.append({"s": buf[0]["s"], "e": buf[-1]["e"] + 0.08, "words": list(buf)})
            buf = []
    if buf:
        cues.append({"s": buf[0]["s"], "e": buf[-1]["e"] + 0.08, "words": list(buf)})
    return cues


class SubCacheV15:
    """Glassmorphic V15 Pro Subtitles with vibrant Golden Active-Word Pill Highlight!"""
    def __init__(self, cues, vertical=True):
        self.cues = cues
        self.vertical = vertical
        self.font = load_font(FONT_SANS, 54 if vertical else 46, 800)
        self.key = None
        self.rgba = None

    def get(self, t):
        ci = -1
        for i, c in enumerate(self.cues):
            if c["s"] <= t <= c["e"]:
                ci = i
                break
        if ci < 0:
            return None
        cue = self.cues[ci]
        wi = len(cue["words"]) - 1
        for j, w in enumerate(cue["words"]):
            if t <= w["e"]:
                wi = j
                break
        k = (ci, wi)
        if k == self.key:
            return self.rgba

        toks = [w["w"].upper() for w in cue["words"]]
        tmp = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
        sp = int(tmp.textlength(" ", font=self.font)) + 16
        widths = [int(tmp.textlength(tk, font=self.font)) for tk in toks]
        tot_w = sum(widths) + sp * max(0, len(toks) - 1)
        pad_x = 40
        cw, ch = min(1030 if self.vertical else 1660, tot_w + pad_x * 2 + 28), (114 if self.vertical else 96)

        im = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        dr = ImageDraw.Draw(im)
        # Sleek dark glassmorphic pill + subtle top specular edge & crimson accent bar
        dr.rounded_rectangle([4, 6, cw - 4, ch - 4], radius=16, fill=(8, 10, 16, 224), outline=(72, 78, 96, 175), width=2)
        dr.rounded_rectangle([14, 18, 22, ch - 18], radius=4, fill=(230, 34, 42, 255))

        x = (cw - tot_w) // 2 + 6
        cy = ch // 2
        for j, (tk, ww) in enumerate(zip(toks, widths)):
            if j == wi:
                # Vibrant Golden Active-Word Pill with dark crisp text (maximum Shorts readability!)
                dr.rounded_rectangle([x - 10, 14, x + ww + 10, ch - 14], radius=10, fill=(248, 204, 66, 255))
                dr.text((x, cy), tk, fill=(14, 14, 18, 255), font=self.font, anchor="lm")
            else:
                dr.text((x + 2, cy + 2), tk, fill=(0, 0, 0, 220), font=self.font, anchor="lm")
                dr.text((x, cy), tk, fill=(246, 246, 248, 255), font=self.font, anchor="lm")
            x += ww + sp

        self.key = k
        self.rgba = np.asarray(im)
        return self.rgba


def render_v15_beast(ev, script, voice_dur, words, audio_m4a, env30, spec30, out_mp4, vertical=True, qa_out=None, show_outro=True):
    W, H = (1080, 1920) if vertical else (1920, 1080)
    FPS = 30 if vertical else 24
    speech_off = 0.45
    total_dur = round(speech_off + voice_dur + (3.2 if show_outro else 1.4), 2)
    if vertical:
        total_dur = min(58.5, total_dur)
    n_frames = int(round(total_dur * FPS))
    brand = ev.get("channel_name", "THE DAILY ARCHIVE").upper()
    rng = np.random.default_rng(ev["year"] * 37 + ev["day"] + len(brand))

    # 1) Pre-build Vignette, Fine 35mm Grain, Volumetric Embers, CRT Barrel Distortion LUT!
    Yg, Xg = np.ogrid[:H, :W]
    Rn = np.sqrt(((Xg - W / 2.0) / (W * 0.58)) ** 2 + ((Yg - H / 2.0) / (H * 0.58)) ** 2)
    VIG = np.clip(1.0 - 0.54 * (np.clip(Rn - 0.34, 0, 1.5) ** 1.85), 0.25, 1.0)[:, :, None].astype(np.float32)

    g_pos, g_neg = [], []
    for _ in range(6):
        g = rng.normal(0, 3.0, (H // 2, W // 2)).astype(np.float32)
        g_pos.append(cv2.cvtColor(cv2.resize(np.clip(g, 0, 11).astype(np.uint8), (W, H), interpolation=cv2.INTER_NEAREST), cv2.COLOR_GRAY2BGR))
        g_neg.append(cv2.cvtColor(cv2.resize(np.clip(-g, 0, 11).astype(np.uint8), (W, H), interpolation=cv2.INTER_NEAREST), cv2.COLOR_GRAY2BGR))

    # Volumetric golden embers & dust
    n_emb = 58
    e_x = rng.uniform(0, W, n_emb); e_y = rng.uniform(0, H, n_emb)
    e_vx = rng.uniform(-24, 34, n_emb); e_vy = rng.uniform(-95, -28, n_emb)
    e_r = rng.integers(2, 6, n_emb)
    e_warm = rng.random(n_emb) > 0.35

    # Real CRT Barrel Curvature LUT (precomputed once -> zero runtime overhead!)
    yc_n, xc_n = np.mgrid[0:H, 0:W].astype(np.float32)
    nx = (xc_n - W / 2.0) / (W / 2.0)
    ny = (yc_n - H / 2.0) / (H / 2.0)
    r2 = nx * nx + ny * ny
    k_crt = 0.085
    crt_mx = ((nx * (1.0 + k_crt * r2)) * (W / 2.0) + W / 2.0).astype(np.float32)
    crt_my = ((ny * (1.0 + k_crt * r2)) * (H / 2.0) + H / 2.0).astype(np.float32)

    # 2) Load DISTINCT archival plates & real Esri maps
    pw, ph = (1280, 2240) if vertical else (2240, 1260)
    plates = [cover_plate(p, pw, ph) for p in ev["images"]]
    while len(plates) < 4:
        plates.append(plates[len(plates) % len(ev["images"])])

    map_mac = cv2.imread(ev["map_macro"]["path"])
    map_loc = cv2.imread(ev["map_local"]["path"])
    for gx in range(0, map_loc.shape[1], 128):
        cv2.line(map_loc, (gx, 0), (gx, map_loc.shape[0]), (36, 42, 54), 1)
    for gy in range(0, map_loc.shape[0], 128):
        cv2.line(map_loc, (0, gy), (map_loc.shape[1], gy), (36, 42, 54), 1)

    # 3) Pre-build 3D Earth Globe LUT (sapphire-gold glowing atmosphere!)
    globe_r = int(min(W, H) * 0.39)
    dx_g, dy_g = (xc_n - W / 2.0) / globe_r, (yc_n - H / 2.0) / globe_r
    rr_g = dx_g * dx_g + dy_g * dy_g
    g_mask = rr_g <= 1.0
    dz_g = np.sqrt(np.clip(1.0 - rr_g, 0.0, 1.0))
    g_shade = np.clip(0.34 + 0.78 * np.clip(dz_g * 0.85 - dx_g * 0.36 - dy_g * 0.25, 0, 1), 0.16, 1.12).astype(np.float32)
    g_rim = (np.clip(1.0 - dz_g, 0, 1) ** 2.9) * g_mask
    # Outer halo outside sphere
    g_halo = np.exp(-np.maximum(0.0, np.sqrt(rr_g) - 1.0) * 14.0) * (~g_mask) * (rr_g < 1.38)
    star_bg = np.full((H, W, 3), (4, 6, 12), dtype=np.uint8)
    for _ in range(280):
        c_st = int(rng.integers(165, 245))
        cv2.circle(star_bg, (int(rng.integers(0, W)), int(rng.integers(0, H))), int(rng.integers(1, 3)), (c_st, c_st, min(255, c_st + 18)), -1)
    mh_m, mw_m = map_mac.shape[:2]
    lon_g = np.arcsin(np.clip(dx_g / np.maximum(0.01, np.sqrt(np.clip(1.0 - dy_g * dy_g, 0.001, 1.0))), -1, 1))
    lat_g = np.arcsin(np.clip(dy_g, -1, 1))
    g_mx = (ev["map_macro"]["px"] + lon_g * (mw_m * 0.45)).astype(np.float32)
    g_my = (ev["map_macro"]["py"] + lat_g * (mh_m * 0.48)).astype(np.float32)

    # 4) Fonts & Pre-Built V15 Assets (Torn Newspaper, Polaroid, Stamp, Dossier, Outro!)
    f_huge = load_font(FONT_SANS, 165 if vertical else 190, 800)
    f_big  = load_font(FONT_SANS, 92 if vertical else 108, 800)
    f_h2   = load_font(FONT_SANS, 48 if vertical else 50, 800)
    f_h3   = load_font(FONT_SANS, 34 if vertical else 36, 800)
    f_m24  = load_font(FONT_MONO, 25 if vertical else 23)
    f_m20  = load_font(FONT_MONO, 20 if vertical else 19)
    f_m18  = load_font(FONT_MONO, 18 if vertical else 17)

    # Torn Newspaper Headline Cutout!
    news_card = build_torn_newspaper(script["newspaper_headline"], ev["display_date"], ev["location"], width=900 if vertical else 820)

    # Aspect-Correct Polaroid Card!
    pol_w, pol_h = (760, 680) if vertical else (760, 590)
    pol_card = Image.new("RGBA", (pol_w, pol_h), (0, 0, 0, 0))
    pdr = ImageDraw.Draw(pol_card)
    pdr.rounded_rectangle([10, 10, pol_w - 10, pol_h - 10], radius=8, fill=(240, 234, 222, 255), outline=(182, 174, 158, 255), width=2)
    im0_bgr = cover_plate(ev["images"][0], pol_w - 68, pol_h - 196, sat=0.84, con=1.22, br=0.95)
    pol_card.paste(Image.fromarray(cv2.cvtColor(im0_bgr, cv2.COLOR_BGR2RGB)), (34, 34))
    pdr.text((38, pol_h - 134), script["polaroid_caption"][:42], fill=(32, 30, 26, 248), font=f_m20)
    pdr.text((38, pol_h - 94), f"GPS: {ev['lat']}°N, {ev['lon']}°E  •  {ev['location'][:22]}", fill=(104, 94, 82, 242), font=f_m18)
    pdr.rectangle([pol_w // 2 - 70, 2, pol_w // 2 + 70, 26], fill=(212, 198, 168, 195))

    # Crimson Rubber Stamp!
    st_w, st_h = 430, 126
    stamp = Image.new("RGBA", (st_w, st_h), (0, 0, 0, 0))
    sdr = ImageDraw.Draw(stamp)
    scol = (224, 28, 34, 246)
    sdr.rectangle([6, 6, st_w - 6, st_h - 6], outline=scol, width=7)
    sdr.rectangle([16, 16, st_w - 16, st_h - 16], outline=scol, width=2)
    sdr.text((st_w // 2, 46), script["stamp_line1"][:18], fill=scol, font=f_h3, anchor="mm")
    sdr.text((st_w // 2, 92), script["stamp_line2"][:22], fill=scol, font=f_m20, anchor="mm")
    stamp = stamp.rotate(10, expand=True, resample=Image.BICUBIC)

    # Dark Slate Detective Desk Background
    desk_bg = cv2.GaussianBlur(cv2.resize(plates[0], (W, H)), (49, 49), 0)
    desk_bg = (desk_bg.astype(np.float32) * 0.20 + np.array([15, 13, 14], dtype=np.float32) * 0.80).astype(np.uint8)
    for gx in range(0, W, 64):
        cv2.line(desk_bg, (gx, 0), (gx, H), (30, 28, 32), 1)
    for gy in range(0, H, 64):
        cv2.line(desk_bg, (0, gy), (W, gy), (30, 28, 32), 1)

    # Dossier Inset Photo #1 (aspect-correct!)
    dos_cx0 = 72 if vertical else 280
    dos_cx1 = W - 72 if vertical else W - 280
    dos_ph = 350 if vertical else 250
    dos_img_bgr = cover_plate(ev["images"][1 % len(ev["images"])], dos_cx1 - dos_cx0 - 84, dos_ph, sat=0.55, con=1.24, br=0.92)
    dos_inset_pil = Image.fromarray(cv2.cvtColor(dos_img_bgr, cv2.COLOR_BGR2RGB))

    # Split-Screen Dual Archival Plates (Plates #1 & #2)
    if vertical:
        sp_top = cover_plate(ev["images"][1 % len(ev["images"])], W, H // 2, sat=0.65, con=1.22, br=0.88)
        sp_bot = cover_plate(ev["images"][2 % len(ev["images"])], W, H // 2, sat=0.85, con=1.22, br=0.90)
    else:
        sp_top = cover_plate(ev["images"][1 % len(ev["images"])], W // 2, H, sat=0.65, con=1.22, br=0.88)
        sp_bot = cover_plate(ev["images"][2 % len(ev["images"])], W // 2, H, sat=0.85, con=1.22, br=0.90)

    # Climax Glassmorphic Stat Card!
    sc_w, sc_h = (880, 320) if vertical else (1040, 310)
    stat_card = Image.new("RGBA", (sc_w, sc_h), (0, 0, 0, 0))
    stdr = ImageDraw.Draw(stat_card)
    stdr.rounded_rectangle([8, 8, sc_w - 8, sc_h - 8], radius=16, fill=(10, 12, 18, 224), outline=(248, 206, 72, 235), width=3)
    stdr.rectangle([8, 8, 22, sc_h - 8], fill=(228, 34, 42, 255))
    stdr.text((sc_w // 2, 66), script["climax_stat_label"][:28], fill=(248, 206, 72, 255), font=f_m24, anchor="mm")
    stdr.text((sc_w // 2, 168), script["climax_stat_big"][:18], fill=(254, 252, 248, 255), font=f_big, anchor="mm")
    stdr.text((sc_w // 2, 260), script["climax_stat_sub"][:38], fill=(195, 202, 215, 255), font=f_m20, anchor="mm")

    # Channel-Branded V15 Outro Card!
    cw_o, ch_o = (920, 560) if vertical else (1360, 560)
    outro = Image.new("RGBA", (cw_o, ch_o), (0, 0, 0, 0))
    odr = ImageDraw.Draw(outro)
    odr.rounded_rectangle([8, 8, cw_o - 8, ch_o - 8], radius=16, fill=(8, 10, 16, 240), outline=(228, 34, 42, 255), width=4)
    odr.text((cw_o // 2, 118), brand, fill=(254, 250, 244, 255), font=load_font(FONT_SANS, 60 if vertical else 68, 800), anchor="mm")
    odr.rectangle([cw_o // 2 - 200, 168, cw_o // 2 + 200, 175], fill=(228, 34, 42, 255))
    odr.text((cw_o // 2, 238), f"{ev['display_date']}  •  {ev['location'][:20]}", fill=(248, 206, 72, 255), font=f_h3, anchor="mm")
    cta_txt = "SUBSCRIBE FOR THE NEXT DECLASSIFIED FILE" if ev.get("mode") == "behind_the_curtain" else "SUBSCRIBE FOR TOMORROW'S TRUE STORY"
    odr.rounded_rectangle([cw_o // 2 - 380, 310, cw_o // 2 + 380, 392], radius=12, fill=(220, 28, 36, 255))
    odr.text((cw_o // 2, 351), cta_txt, fill=(255, 252, 248, 255), font=f_m20, anchor="mm")
    odr.text((cw_o // 2, 466), "REAL ARCHIVES  •  REAL COORDINATES  •  ZERO FICTION", fill=(182, 188, 204, 255), font=f_m18, anchor="mm")

    cues = build_subtitle_cues(words, speech_off, vertical=vertical)
    sub_cache = SubCacheV15(cues, vertical=vertical)
    bounds = [0.0, 0.20, 0.42, 0.62, 0.81, 1.0]
    tr_s = 0.36

    # Pre-build hex telemetry strings for CRT Intercept sidebar
    hex_rows = [f"0x{rng.integers(0x1000, 0xFFFF):04X} // {rng.integers(100, 999)}.{rng.integers(10, 99)} MHz" for _ in range(36)]

    def render_scene(si, p, t):
        if si == 0:
            # S0: 3D Earth Globe + Fresnel Atmosphere -> Hyperspace Dive -> 3D Tilted Tactical Map + 360° Radar Sweep + Glowing Bezier Vector Arc!
            if p < 0.38:
                q = p / 0.38
                rot_x = (1.0 - ease_io(q)) * 185.0
                tex = cv2.remap(map_mac, g_mx - rot_x, g_my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
                shaded = np.clip(tex.astype(np.float32) * g_shade[:, :, None], 0, 255).astype(np.uint8)
                rim = np.zeros_like(shaded)
                rim[:, :, 0] = np.clip(g_rim * 245 + g_halo * 195, 0, 255).astype(np.uint8)
                rim[:, :, 1] = np.clip(g_rim * 165 + g_halo * 120, 0, 255).astype(np.uint8)
                rim[:, :, 2] = np.clip(g_rim * 82 + g_halo * 45, 0, 255).astype(np.uint8)
                fr = np.where(g_mask[:, :, None], cv2.add(shaded, rim), cv2.add(star_bg, rim))
                # Orbital HUD Reticle Rings
                cv2.circle(fr, (W // 2, H // 2), globe_r + 32, (62, 74, 98), 1, cv2.LINE_AA)
                cv2.line(fr, (W // 2 - globe_r - 65, H // 2), (W // 2 - globe_r - 18, H // 2), (52, 48, 232), 2)
                cv2.line(fr, (W // 2 + globe_r + 18, H // 2), (W // 2 + globe_r + 65, H // 2), (52, 48, 232), 2)
                z = 1.0 + 1.85 * (ease_io(max(0.0, (q - 0.32) / 0.68)) ** 1.9)
                fr = cv2.warpAffine(fr, cv2.getRotationMatrix2D((W / 2.0, H / 2.0), 0, z), (W, H))
                cv2.circle(fr, (W // 2, H // 2), int(16 + (q * 110) % 44), (52, 46, 246), 3, cv2.LINE_AA)
                cv2.circle(fr, (W // 2, H // 2), 9, (68, 68, 255), -1, cv2.LINE_AA)
                if q > 0.86:
                    fl = int(215 * ((q - 0.86) / 0.14))
                    fr = cv2.add(fr, np.full((H, W, 3), fl, dtype=np.uint8))
            else:
                q = (p - 0.38) / 0.62
                mp = map_loc.copy()
                tx, ty = int(ev["map_local"]["px"]), int(ev["map_local"]["py"])
                # 1) 360-DEGREE ROTATING MILITARY RADAR SWEEP WEDGE!
                sweep_ov = np.zeros_like(mp)
                ang0 = (t * 145.0) % 360.0
                cv2.ellipse(sweep_ov, (tx, ty), (240, 240), 0, ang0 - 52, ang0, (44, 34, 215), -1, cv2.LINE_AA)
                mp = cv2.addWeighted(mp, 1.0, sweep_ov, 0.36, 0)
                ang_r = math.radians(ang0)
                cv2.line(mp, (tx, ty), (int(tx + 240 * math.cos(ang_r)), int(ty + 240 * math.sin(ang_r))), (85, 90, 255), 3, cv2.LINE_AA)
                for rk in range(3):
                    rr = int(20 + ((q * 210 + rk * 68) % 210))
                    cv2.circle(mp, (tx, ty), rr, (48, 42, 244), 3, cv2.LINE_AA)

                # 2) ANIMATED GLOWING CRIMSON BEZIER VECTOR ARC flying straight onto Target GPS!
                ox, oy = tx - 380, ty + 290
                cx_b, cy_b = tx - 210, ty - 140
                n_arc = max(4, int(44 * ease_out(min(1.0, q / 0.65))))
                arc_pts = []
                for k in range(n_arc):
                    u = k / 43.0
                    ax = int((1 - u) ** 2 * ox + 2 * (1 - u) * u * cx_b + u ** 2 * tx)
                    ay = int((1 - u) ** 2 * oy + 2 * (1 - u) * u * cy_b + u ** 2 * ty)
                    arc_pts.append([ax, ay])
                if len(arc_pts) >= 2:
                    ap = np.array(arc_pts, dtype=np.int32)
                    cv2.polylines(mp, [ap], False, (36, 30, 175), 11, cv2.LINE_AA)
                    cv2.polylines(mp, [ap], False, (80, 165, 255), 4, cv2.LINE_AA)
                    head = tuple(arc_pts[-1])
                    cv2.circle(mp, head, 12, (110, 215, 255), -1, cv2.LINE_AA)
                    cv2.circle(mp, head, 6, (255, 255, 255), -1, cv2.LINE_AA)

                cv2.circle(mp, (tx, ty), 15, (52, 44, 252), -1, cv2.LINE_AA)
                cv2.circle(mp, (tx, ty), 6, (255, 255, 255), -1, cv2.LINE_AA)

                hw = (440 if vertical else 640) - int(155 * ease_io(q))
                hh = int(hw * (H / float(W)))
                tilt = int(hw * 0.24)
                src = np.float32([[tx - hw - tilt, ty - hh], [tx + hw + tilt, ty - hh], [tx + hw - tilt * 0.25, ty + hh], [tx - hw + tilt * 0.25, ty + hh]])
                Hm = cv2.getPerspectiveTransform(src, np.float32([[0, 0], [W, 0], [W, H], [0, H]]))
                fr = cv2.warpPerspective(mp, Hm, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)

                if q < 0.14:
                    fr = cv2.add(fr, np.full((H, W, 3), int(180 * (1.0 - q / 0.14)), dtype=np.uint8))

                # Tactical Glass Telemetry HUD!
                ui = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dr = ImageDraw.Draw(ui)
                bw_c = 880 if vertical else 660
                bx_c = (W - bw_c) // 2 if vertical else 68
                by_c = 205 if vertical else 104
                dr.rounded_rectangle([bx_c, by_c, bx_c + bw_c, by_c + 162], radius=10, fill=(8, 12, 20, 232), outline=(228, 36, 44, 248), width=3)
                dr.rectangle([bx_c, by_c, bx_c + 12, by_c + 162], fill=(228, 36, 44, 255))
                dr.text((bx_c + 34, by_c + 36), f"VECTOR: {ev.get('origin_name', 'HQ')} -> TARGET LOCKED  •  {ev.get('dist_km', 2400):,} KM", fill=(248, 206, 72, 255), font=f_m18, anchor="lm")
                dr.text((bx_c + 34, by_c + 86), ev["location"][:25], fill=(254, 250, 244, 255), font=f_h2, anchor="lm")
                dr.text((bx_c + 34, by_c + 134), f"LAT {ev['lat']:+.4f}   |   LON {ev['lon']:+.4f}   |   STATUS: DECLASSIFIED", fill=(165, 180, 204, 245), font=f_m18, anchor="lm")
                fr = comp_rgba(fr, np.asarray(ui), W / 2.0, H / 2.0)

            # Mechanical Split-Flap Year & Date Slam on opening 3.7s + Anamorphic Flare!
            if 0.32 <= t <= 4.1:
                pa = ease_out((t - 0.32) / 0.22) * ease_out(min(1.0, (4.1 - t) / 0.42))
                sc_k = 1.62 - 0.62 * ease_out((t - 0.32) / 0.24)
                if 0.32 <= t < 0.60:
                    dt = t - 0.32; amp = 22.0 * math.exp(-dt / 0.08)
                    fr = cv2.warpAffine(fr, np.float32([[1, 0, amp * math.sin(dt * 120)], [0, 1, amp * math.cos(dt * 95)]]), (W, H))
                # Rolling mechanical year ticker during first 0.55s!
                yr_show = ev["year"] - int(max(0, (0.85 - t) * 42)) if t < 0.85 else ev["year"]
                ui = Image.new("RGBA", (W, 380), (0, 0, 0, 0)); dr = ImageDraw.Draw(ui)
                eyebrow = "DECLASSIFIED FILE" if ev.get("mode") == "behind_the_curtain" else "ON THIS DAY IN HISTORY"
                dr.text((W // 2, 46), eyebrow, fill=(248, 206, 72, 255), font=f_m24, anchor="mm")
                dr.text((W // 2 + 4, 158), str(yr_show), fill=(0, 0, 0, 220), font=f_huge, anchor="mm")
                dr.text((W // 2, 152), str(yr_show), fill=(254, 250, 244, 255), font=f_huge, anchor="mm")
                sub_lbl = ev["location"] if str(ev["display_date"]).strip() == str(ev["year"]) else ev["display_date"]
                dr.text((W // 2, 276), sub_lbl[:26], fill=(248, 206, 72, 255), font=f_h3, anchor="mm")
                bar = int((W * 0.62) * ease_out((t - 0.48) / 0.38))
                dr.rectangle([W // 2 - bar // 2, 314, W // 2 + bar // 2, 324], fill=(228, 34, 42, 255))
                fr = comp_pil(fr, ui, W / 2.0, H / 2.0 - (60 if vertical else 10), scale=sc_k, alpha=pa)
                fl_p = (t - 0.32) / 1.4
                if 0.0 < fl_p < 1.0:
                    fr = add_anamorphic_flare(fr, H // 2 - (60 if vertical else 10), int(W * fl_p), intensity=0.62 * math.sin(math.pi * fl_p), color_bgr=(65, 195, 255))
            return fr

        elif si == 1:
            # S1: 2.5D Depth-Parallax + Flare -> Leica Flash -> Torn Newspaper Clipping + Red Detective String + Polaroid + Stamp Recoil!
            if p < 0.32:
                return sample_25d_beast(plates[0], W, H, p / 0.32, style=0, flare_phase=p / 0.32)
            q = (p - 0.32) / 0.68
            fr = desk_bg.copy()
            shx, shy = 0.0, 0.0
            if 0.34 <= q < 0.46:
                sdt = (q - 0.34) * 5.8; amp = 22.0 * math.exp(-sdt / 0.08)
                shx, shy = amp * math.sin(sdt * 115), amp * math.cos(sdt * 95)

            # 1) Torn Newspaper Headline Clipping slams in at top!
            pn = ease_back(q / 0.24, s=1.2)
            ny_pos = (380 if vertical else 245) - (1.0 - min(1.03, pn)) * 180
            nx_pos = (W / 2.0) if vertical else (W * 0.30)
            fr = comp_pil(fr, news_card, nx_pos + shx, ny_pos + shy, scale=1.0, angle=-2.2, shadow=True)

            # 2) Polaroid Evidence Card slams in below/right!
            pp = ease_back(max(0.0, (q - 0.08) / 0.24), s=1.22)
            py_pos = (960 if vertical else 585)
            px_pos = (W / 2.0 + 18) if vertical else (W * 0.68)
            fr = comp_pil(fr, pol_card, px_pos + shx, py_pos + shy, scale=1.55 - 0.55 * min(1.04, pp), angle=3.0, shadow=True)

            # 3) Animated Taut Crimson Detective String + 3D Pushpins linking Newspaper -> Polaroid!
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

            # 4) Heavy Crimson Stamp slams cleanly onto upper-right of Polaroid!
            if q >= 0.34:
                pst = ease_out((q - 0.34) / 0.08)
                fr = comp_pil(fr, stamp, px_pos + (145 if vertical else 175) + shx, py_pos - (150 if vertical else 120) + shy, scale=2.25 - 1.25 * pst, alpha=min(1.0, pst * 1.6))

            if q < 0.10:
                fr = cv2.add(fr, np.full((H, W, 3), int(235 * ((1.0 - q / 0.10) ** 1.6)), dtype=np.uint8))
            return fr

        elif si == 2:
            # S2: Detective Classified Dossier + Wet-Ink Exact Highlighter + LIVE 2.2x GLASS MAGNIFYING LENS SCAN!
            fr = desk_bg.copy()
            ui = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dr = ImageDraw.Draw(ui)
            cx0, cx1 = dos_cx0, dos_cx1
            cy0 = 260 if vertical else 125
            cy1 = 1320 if vertical else 875
            dr.rounded_rectangle([cx0, cy0, cx1, cy1], radius=12, fill=(238, 232, 216, 255), outline=(172, 162, 142, 255), width=3)
            dr.text((cx0 + 42, cy0 + 54), script["forensic_header"][:38], fill=(196, 26, 34, 255), font=f_m24)
            dr.line([(cx0 + 42, cy0 + 98), (cx1 - 42, cy0 + 98)], fill=(42, 38, 34, 195), width=3)
            ui.paste(dos_inset_pil, (cx0 + 42, cy0 + 122))

            base_y = cy0 + dos_ph + 165
            step_y = 148 if vertical else 108
            cols_h = [(248, 206, 72, 195), (248, 206, 72, 195), (242, 118, 108, 205)]
            for idx, line in enumerate(script["forensic_lines"][:3]):
                th = 0.08 + idx * 0.20
                ly = base_y + idx * step_y
                wrapped = textwrap.fill(str(line), width=34 if vertical else 58)
                bb = dr.multiline_textbbox((cx0 + 48, ly), wrapped, font=f_m24)
                box_h = max(34, bb[3] - bb[1])
                box_w = min(cx1 - cx0 - 92, max(220, (bb[2] - bb[0]) + 28))
                if p >= th:
                    hp = ease_out((p - th) / 0.14)
                    hw = int(box_w * hp)
                    dr.rounded_rectangle([cx0 + 38, ly - 8, cx0 + 38 + hw, ly + box_h + 12], radius=4, fill=cols_h[idx % 3])
                # Crisp dark archival ink stays 100% razor-readable before, during, and after highlighter sweep!
                dr.text((cx0 + 48, ly), wrapped, fill=(18, 18, 16, 255), font=f_m24)
            fr = comp_rgba(fr, np.asarray(ui), W / 2.0, H / 2.0)

            # LIVE GLASS MAGNIFYING LENS gliding across the archival evidence photo inside the dossier!
            lp = ease_io(min(1.0, p / 0.92))
            mx = (cx0 + 185) + (cx1 - cx0 - 370) * lp
            my = (cy0 + 122 + dos_ph * 0.50) + math.sin(lp * math.pi * 2.0) * 38.0
            fr = apply_magnifying_lens(fr, mx, my, radius=118 if vertical else 105, zoom=1.75)
            return fr

        elif si == 3:
            # S3: Phase A (0..36%) Crimson Laser Dual Split-Screen -> Phase B (36..100%) Curved CRT Monitor + 16-Band Live FFT Spectrum + Oscilloscope!
            if p < 0.36:
                q = p / 0.36
                # Smooth laser wipe revealing dual archival split-screen!
                fr = np.zeros((H, W, 3), dtype=np.uint8)
                shift_a = int(32 * ease_io(q))
                if vertical:
                    mid = H // 2
                    fr[:mid] = np.roll(sp_top, shift_a, axis=1)
                    fr[mid:] = np.roll(sp_bot, -shift_a, axis=1)
                    lw = int(W * ease_out(min(1.0, q / 0.45)))
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
                    fr[:, :mid] = np.roll(sp_top, shift_a, axis=0)
                    fr[:, mid:] = np.roll(sp_bot, -shift_a, axis=0)
                    lh = int(H * ease_out(min(1.0, q / 0.45)))
                    cv2.line(fr, (mid, 0), (mid, lh), (40, 34, 240), 10, cv2.LINE_AA)
                    cv2.line(fr, (mid, 0), (mid, lh), (195, 210, 255), 3, cv2.LINE_AA)
                    cv2.rectangle(fr, (68, 108), (430, 162), (10, 12, 18), -1)
                    cv2.putText(fr, script["split_left_label"][:18], (88, 145), cv2.FONT_HERSHEY_SIMPLEX, 0.82, (248, 206, 72), 2, cv2.LINE_AA)
                    cv2.rectangle(fr, (mid + 34, 108), (mid + 410, 162), (10, 12, 18), -1)
                    cv2.putText(fr, script["split_right_label"][:18], (mid + 54, 145), cv2.FONT_HERSHEY_SIMPLEX, 0.82, (248, 248, 250), 2, cv2.LINE_AA)
                return fr

            # Phase B: REAL BARREL-CURVED CRT INTERCEPT + SCROLLING HEX SIDEBAR + 16-BAND LIVE SPECTRUM & OSCILLOSCOPE!
            q = (p - 0.36) / 0.64
            fr = sample_25d_beast(plates[2], W, H, q, style=1)
            fr[:, :, 1] = np.clip(fr[:, :, 1].astype(np.int16) + 22, 0, 255).astype(np.uint8)
            fr[::3, :, :] = (fr[::3, :, :].astype(np.float32) * 0.62).astype(np.uint8)
            by = int((t * 420) % (H - 80))
            fr[by:by + 16, :] = np.roll(fr[by:by + 16, :], 26, axis=1)
            b, g, r = cv2.split(fr)
            fr = cv2.merge([np.roll(b, -6, axis=1), g, np.roll(r, 6, axis=1)])
            # Apply real glass CRT barrel curvature!
            fr = cv2.remap(fr, crt_mx, crt_my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(6, 10, 8))

            top_y = 215 if vertical else 120
            if int(t * 4) % 2 == 0:
                cv2.circle(fr, (86, top_y), 11, (40, 34, 242), -1, cv2.LINE_AA)
            cv2.putText(fr, f"REC  INTERCEPT FEED // {ev['year']}", (112, top_y + 8), cv2.FONT_HERSHEY_SIMPLEX, 0.84, (226, 250, 232), 2, cv2.LINE_AA)

            # Scrolling Hex Telemetry Sidebar (top-right)
            hx_x = W - 360 if vertical else W - 380
            scroll_i = int(t * 5)
            for row_i in range(6):
                txt_h = hex_rows[(scroll_i + row_i) % len(hex_rows)]
                cv2.putText(fr, txt_h, (hx_x, top_y + 42 + row_i * 28), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (92, 225, 130), 1, cv2.LINE_AA)

            # DUAL LIVE TELEMETRY DECK: 16-Band FFT Spectrum (left) + Live Voice Oscilloscope (right)!
            oy0 = 1190 if vertical else 720
            oy1 = oy0 + 165
            cv2.rectangle(fr, (64, oy0), (W - 64, oy1), (8, 20, 12), -1)
            cv2.rectangle(fr, (64, oy0), (W - 64, oy1), (78, 228, 126), 2)
            idx30 = min(len(env30) - 1, int(t * 30))
            amp = float(env30[idx30])
            bands = spec30[min(len(spec30) - 1, idx30)]

            # Left half: 16-Band Real FFT Spectrum Analyzer!
            mid_x = W // 2
            bw_tot = (mid_x - 104)
            bar_step = bw_tot / 16.0
            for bk in range(16):
                bh = int(14 + bands[bk] * 114)
                bx0 = int(84 + bk * bar_step)
                bx1 = int(bx0 + max(6, bar_step * 0.68))
                col_b = (85, 245, 120) if bands[bk] < 0.65 else ((65, 212, 250) if bands[bk] < 0.85 else (62, 62, 250))
                cv2.rectangle(fr, (bx0, oy1 - 14 - bh), (bx1, oy1 - 14), col_b, -1)
            cv2.putText(fr, "FFT SPECTRUM // 16-CH", (84, oy0 + 26), cv2.FONT_HERSHEY_SIMPLEX, 0.54, (130, 242, 160), 1, cv2.LINE_AA)

            # Right half: Live Voice Oscilloscope!
            cv2.line(fr, (mid_x, oy0 + 12), (mid_x, oy1 - 12), (50, 145, 80), 1)
            n_pts = 48 if vertical else 72
            ox_s = mid_x + 22
            dx_w = (W - 84 - ox_s) / float(n_pts - 1)
            pts = [[int(ox_s + k * dx_w), int((oy0 + oy1) / 2 + math.sin(k * 0.48 + t * 26) * math.cos(k * 0.16 - t * 9) * (10 + 52 * amp))] for k in range(n_pts)]
            cv2.polylines(fr, [np.array(pts, dtype=np.int32)], False, (100, 255, 138), 3, cv2.LINE_AA)
            cv2.putText(fr, "VOICE INTERCEPT WAVE", (ox_s, oy0 + 26), cv2.FONT_HERSHEY_SIMPLEX, 0.54, (130, 242, 160), 1, cv2.LINE_AA)
            return fr

        else:
            # S4: Emotional Climax Plate #3 + Volumetric Glowing Embers + Giant Watermark Year + Spring Stat Card -> Outro Card!
            fr = sample_25d_beast(plates[3], W, H, p, style=2, flare_phase=p)
            # Volumetric warm embers rising smoothly!
            for k in range(n_emb):
                px = int((e_x[k] + e_vx[k] * t + 22 * math.sin(t * 1.5 + k)) % W)
                py = int((e_y[k] + e_vy[k] * t) % H)
                col_e = (65, 175, 255) if e_warm[k] else (140, 215, 250)
                cv2.circle(fr, (px, py), int(e_r[k]), col_e, -1, cv2.LINE_AA)

            t_rem = total_dur - t
            if (not show_outro) or (t_rem > 3.0):
                # Spring-pop Climax Stat Card in finale!
                sp_sc = ease_back(min(1.0, p / 0.25), s=1.35)
                fade_tail = ease_out(min(1.0, (t_rem - 3.0) / 0.35)) if show_outro else ease_out(min(1.0, t_rem / 0.55))
                sa = ease_out(min(1.0, p / 0.18)) * fade_tail
                fr = comp_pil(fr, stat_card, W / 2.0, H * (0.44 if vertical else 0.46), scale=0.82 + 0.18 * sp_sc, alpha=sa, shadow=True)
            else:
                ot = 3.0 - t_rem
                oa = ease_out(ot / 0.36)
                fr = (fr.astype(np.float32) * (1.0 - 0.72 * oa)).astype(np.uint8)
                fr = comp_pil(fr, outro, W / 2.0, H / 2.0 - (50 if vertical else 0), scale=1.14 - 0.14 * oa, alpha=oa, shadow=True)
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
        "-c:v", "libx264", "-preset", "fast", "-crf", "22", "-maxrate", "8M", "-bufsize", "12M",
        "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", "-shortest", out_mp4
    ], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=err_log)

    qa_snaps = {}
    qa_targets = [int(n_frames * f) for f in (0.04, 0.14, 0.31, 0.52, 0.65, 0.75, 0.87, 0.96)]

    for fi in range(n_frames):
        t = fi / float(FPS)
        pf = t / total_dur
        si = 0
        for j in range(5):
            if pf >= bounds[j]:
                si = j
        s0, s1 = bounds[si] * total_dur, bounds[si + 1] * total_dur
        p_loc = max(0.0, min(1.0, (t - s0) / max(0.1, s1 - s0)))

        # Directional Motion-Blur Whip-Pan Transition!
        if si < 4 and (s1 - t) < tr_s:
            tp = ease_io(1.0 - (s1 - t) / tr_s)
            fA = render_scene(si, p_loc, t)
            fB = render_scene(si + 1, 0.0, s1)
            sh = int(round(W * tp))
            frame = np.empty((H, W, 3), dtype=np.uint8)
            if sh < W:
                frame[:, :W - sh] = fA[:, sh:]
            if sh > 0:
                frame[:, W - sh:] = fB[:, :sh]
            bk = int(1 + 58 * math.sin(math.pi * tp))
            if bk >= 5:
                frame = cv2.blur(frame, (bk | 1, 1))
        else:
            frame = render_scene(si, p_loc, t)

        frame = np.clip(frame.astype(np.float32) * VIG, 0, 255).astype(np.uint8)
        frame = cv2.add(frame, g_pos[fi % 6])
        frame = cv2.subtract(frame, g_neg[fi % 6])

        # Sleek Branded Top Progress HUD
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

        # V15 Glassmorphic Active-Word Gold Pill Subtitles (Safe inside Shorts UI!)
        if (not show_outro) or ((total_dur - t) > 3.0):
            sub = sub_cache.get(t)
            if sub is not None:
                sub_y = 1485 if vertical else H - 108
                frame = comp_rgba(frame, sub, W / 2.0, sub_y)

        if t < 0.22:
            frame = (frame.astype(np.float32) * (t / 0.22)).astype(np.uint8)
        elif (total_dur - t) < 0.60:
            frame = (frame.astype(np.float32) * max(0.0, (total_dur - t) / 0.60)).astype(np.uint8)

        if qa_out and fi in qa_targets:
            qa_snaps[fi] = frame.copy()

        vproc.stdin.write(frame.tobytes())

    vproc.stdin.close()
    ret = vproc.wait()
    err_log.close()
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
        grid.save(qa_out, "JPEG", quality=88)

    print(f"[V15 BEAST RENDER OK] {out_mp4} ({total_dur:.1f}s, {W}x{H} {FPS}fps, {os.path.getsize(out_mp4)/1e6:.2f} MB)")
    return total_dur


def generate_v15_thumbnail(hero_img_path, map_img_path, brand, line1, line2, line3, badge_text, out_jpg):
    """V15 BEAST High-CTR 1280x720 Thumbnail (Hero + Tactical Map Texture + Crimson Rim + 3D Drop Shadow)."""
    W, H = 1280, 720
    bg = cover_plate(hero_img_path, W, H, sat=0.58, con=1.28, br=0.78)
    if map_img_path and os.path.exists(map_img_path):
        mp = cv2.resize(cv2.imread(map_img_path), (W, H))
        bg = cv2.addWeighted(bg, 0.78, mp, 0.22, 0)
    grad = np.linspace(0.92, 0.10, W, dtype=np.float32)[None, :, None]
    bg = np.clip(bg.astype(np.float32) * (1.0 - grad * 0.78), 0, 255).astype(np.uint8)
    # Crimson tactical glow on right rim
    bg = add_anamorphic_flare(bg, 190, 940, intensity=0.55, color_bgr=(45, 50, 255))

    im = Image.fromarray(cv2.cvtColor(bg, cv2.COLOR_BGR2RGB)).convert("RGBA")
    dr = ImageDraw.Draw(im)
    f_big = load_font(FONT_SANS, 126, 800)
    f_med = load_font(FONT_SANS, 114, 800)
    f_mono = load_font(FONT_MONO, 28)

    badge_full = f"{brand}  •  {badge_text}"
    bw_pill = int(dr.textlength(badge_full, font=f_mono)) + 44
    dr.rounded_rectangle([68, 76, 68 + bw_pill, 128], radius=8, fill=(224, 30, 38, 248))
    dr.text((90, 102), badge_full, fill=(255, 252, 248, 255), font=f_mono, anchor="lm")
    for yy, txt, col, fnt in [(176, line1, (254, 250, 246, 255), f_big), (316, line2, (248, 206, 68, 255), f_med), (446, line3, (254, 250, 246, 255), f_med)]:
        dr.text((74, yy + 6), txt, fill=(0, 0, 0, 225), font=fnt)
        dr.text((68, yy), txt, fill=col, font=fnt)
    dr.rectangle([68, 594, 590, 608], fill=(228, 34, 42, 255))
    dr.text((68, 636), "DECLASSIFIED ARCHIVAL DOCUMENTARY  •  FULL 1080P", fill=(214, 220, 232, 245), font=f_mono)
    im.convert("RGB").save(out_jpg, "JPEG", quality=94, optimize=True)
    print(f"[V15 THUMB OK] {out_jpg} ({os.path.getsize(out_jpg)/1024:.1f} KB)")
    return out_jpg
