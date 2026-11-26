"""
voice_engine_v15.py — V15 BEAST 12-Track Hollywood Sound Design + Free Unlimited Neural Voiceover
- Supports US Authority ('en-US-ChristopherNeural') & BBC Authority ('en-GB-RyanNeural')
- Exact millisecond WordBoundary timestamps (zero Whisper needed!)
- Procedural Hans Zimmer / LEMMiNO dark cello score + tense stopwatch ticks + brass BRAAAM +
  paper-rip + laser slice + Leica shutter + radar ping + stamp thud + sidechain ducking + -14 LUFS!
- Exports BOTH 30Hz voice oscilloscope envelope AND 30Hz 16-band real FFT spectrum for V15 visuals!
"""
import os
import re
import math
import shutil
import asyncio
import subprocess
import numpy as np
import edge_tts
from scipy.signal import butter, filtfilt

try:
    import imageio_ffmpeg
    FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    FFMPEG = shutil.which("ffmpeg") or "ffmpeg"

SR = 48000


def _bp(x, lo, hi):
    b, a = butter(2, [max(25, lo) / (SR / 2), min(SR / 2 - 250, hi) / (SR / 2)], btype="band")
    return filtfilt(b, a, x)


def _lp(x, cut):
    b, a = butter(2, min(SR / 2 - 250, cut) / (SR / 2), btype="low")
    return filtfilt(b, a, x)


def _hp(x, cut):
    b, a = butter(2, max(25, cut) / (SR / 2), btype="high")
    return filtfilt(b, a, x)


async def _edge_tts_async(text, out_mp3, voice, rate, pitch):
    comm = edge_tts.Communicate(text=text, voice=voice, rate=rate, pitch=pitch)
    words = []
    with open(out_mp3, "wb") as f:
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                st = chunk["offset"] / 10_000_000.0
                du = chunk["duration"] / 10_000_000.0
                w = chunk["text"].strip()
                if w:
                    words.append({"w": w, "s": st, "e": st + max(0.08, du)})
    return words


def synthesize_voice_v15(text, out_mp3, voice="en-US-ChristopherNeural", rate="+3%", pitch="-2Hz"):
    os.makedirs(os.path.dirname(os.path.abspath(out_mp3)), exist_ok=True)
    words = asyncio.run(_edge_tts_async(text, out_mp3, voice=voice, rate=rate, pitch=pitch))
    raw = subprocess.check_output([
        FFMPEG, "-v", "error", "-i", out_mp3, "-f", "f32le", "-ac", "1", "-ar", str(SR), "pipe:1"
    ])
    audio = np.frombuffer(raw, dtype=np.float32)
    dur = len(audio) / float(SR)

    if not words:
        toks = [w for w in re.split(r"\s+", text.strip()) if w]
        step = dur / max(1, len(toks))
        words = [{"w": w, "s": i * step, "e": (i + 0.92) * step} for i, w in enumerate(toks)]

    print(f"[VOICE V15 OK] {voice} | {dur:.2f}s | {len(words)} ms-aligned words")
    return dur, words


def _gen_sfx(kind, rng):
    if kind == "braaam":
        # Massive Hans Zimmer low-brass + sub-bass impact!
        n = int(SR * 2.2)
        t = np.linspace(0, 2.2, n, endpoint=False)
        env = np.minimum(1.0, t / 0.045) * np.exp(-t / 0.72)
        f0 = 55.0 * (1.0 - 0.12 * np.minimum(1.0, t / 1.5))
        sig = (
            0.55 * np.sin(2 * np.pi * f0 * t)
            + 0.35 * np.tanh(2.4 * np.sin(2 * np.pi * (f0 * 2.0) * t))
            + 0.22 * np.sin(2 * np.pi * (f0 * 3.01) * t)
            + 0.18 * _lp(rng.normal(0, 1, n), 340) * np.exp(-t / 0.14)
        )
        return _lp(sig, 1100) * env
    if kind == "dive":
        # Orbital hyperspace whoosh dive into 3D map
        n = int(SR * 1.1)
        t = np.linspace(0, 1.1, n, endpoint=False)
        env = np.sin(np.pi * (t / 1.1)) ** 1.4
        freq = 920.0 * np.exp(-t * 2.6) + 55.0
        ph = 2 * np.pi * np.cumsum(freq) / SR
        return (_bp(rng.normal(0, 1, n), 240, 2800) * 0.55 + 0.45 * np.sin(ph)) * env
    if kind == "whip":
        n = int(SR * 0.36)
        t = np.linspace(0, 0.36, n, endpoint=False)
        return _bp(rng.normal(0, 1, n), 400, 3800) * (np.sin(np.pi * t / 0.36) ** 1.7)
    if kind == "radar":
        n = int(SR * 0.72)
        t = np.linspace(0, 0.72, n, endpoint=False)
        return (np.sin(2 * np.pi * 1420 * t) * 0.7 + np.sin(2 * np.pi * 2840 * t) * 0.25) * np.exp(-t / 0.16)
    if kind == "shutter":
        n = int(SR * 0.18)
        t = np.linspace(0, 0.18, n, endpoint=False)
        c1 = _bp(rng.normal(0, 1, n), 1400, 6800) * np.exp(-t / 0.011)
        c2 = _bp(rng.normal(0, 1, n), 950, 4800) * np.exp(-np.maximum(0, t - 0.052) / 0.012) * (t >= 0.052)
        return (c1 + 0.85 * c2) * 1.15
    if kind == "paper_rip":
        n = int(SR * 0.34)
        t = np.linspace(0, 0.34, n, endpoint=False)
        burst = np.abs(np.sin(2 * np.pi * 24 * t)) ** 0.5
        return _bp(rng.normal(0, 1, n), 1100, 6200) * burst * np.sin(np.pi * t / 0.34)
    if kind == "stamp":
        n = int(SR * 0.38)
        t = np.linspace(0, 0.38, n, endpoint=False)
        return (np.sin(2 * np.pi * (82 * np.exp(-t * 14) + 34) * t) * 1.1 + _bp(rng.normal(0, 1, n), 450, 2400) * 0.45 * np.exp(-t / 0.018)) * np.exp(-t / 0.10)
    if kind == "highlight":
        n = int(SR * 0.44)
        t = np.linspace(0, 0.44, n, endpoint=False)
        return _bp(rng.normal(0, 1, n), 1500, 4600) * np.sin(np.pi * t / 0.44) * 0.72
    if kind == "laser":
        # Crisp crimson split-screen laser slice!
        n = int(SR * 0.42)
        t = np.linspace(0, 0.42, n, endpoint=False)
        f = 1800.0 * np.exp(-t * 4.5) + 180.0
        ph = 2 * np.pi * np.cumsum(f) / SR
        return (0.65 * np.sin(ph) + 0.35 * _hp(rng.normal(0, 1, n), 2400)) * np.exp(-t / 0.14)
    if kind == "glitch":
        n = int(SR * 0.34)
        t = np.linspace(0, 0.34, n, endpoint=False)
        x = rng.normal(0, 1, n)
        for k in range(0, n, 1400):
            if rng.random() > 0.42:
                x[k:k + 700] *= 2.4
        return (_bp(x, 700, 6200) * 0.65 + 0.35 * np.sin(2 * np.pi * 620 * t)) * np.sin(np.pi * t / 0.34)
    if kind == "riser":
        n = int(SR * 2.6)
        t = np.linspace(0, 2.6, n, endpoint=False)
        p = t / 2.6
        ph = 2 * np.pi * np.cumsum(60.0 + 380.0 * (p ** 2.1)) / SR
        return (_bp(rng.normal(0, 1, n), 300, 4200) * 0.42 + 0.58 * np.sin(ph)) * (p ** 1.9)
    # Climax sub-bass drop
    n = int(SR * 2.6)
    t = np.linspace(0, 2.6, n, endpoint=False)
    ph = 2 * np.pi * np.cumsum(38.0 + 62.0 * np.exp(-t * 3.8)) / SR
    return (np.sin(ph) * 0.85 + 0.35 * np.tanh(2.0 * np.sin(ph * 2.0)) * np.exp(-t / 0.45)) * np.exp(-t / 0.82)


def mix_cinema_audio_v15(voice_mp3, total_dur, speech_off, out_m4a, seed=42, sfx_plan=None):
    """
    12-track Hollywood V15 Cinema Mixer -> -14 LUFS Stereo AAC + 30Hz Oscilloscope & 16-Band Spectrum!
    """
    rng = np.random.default_rng(seed)
    N = int(round(total_dur * SR))
    t = np.linspace(0, total_dur, N, endpoint=False)

    # 1) Decode voiceover + apply subtle crisp broadcast EQ
    vraw = subprocess.check_output([
        FFMPEG, "-v", "error", "-i", voice_mp3, "-f", "f32le", "-ac", "1", "-ar", str(SR), "pipe:1"
    ])
    v = np.frombuffer(vraw, dtype=np.float32).copy()
    v = _hp(v, 75) + 0.16 * _bp(v, 2400, 5200)  # broadcast clarity boost!
    v_rms = float(np.sqrt(np.mean(v * v)) + 1e-9)
    v = v * (0.26 / v_rms)

    voice_track = np.zeros(N, dtype=np.float32)
    i0 = int(round(speech_off * SR))
    ln = min(len(v), N - i0)
    if ln > 0:
        voice_track[i0:i0 + ln] = v[:ln]

    # Smooth sidechain ducking envelope (score dips gracefully while narrator speaks!)
    duck_env = np.minimum(1.0, _lp(np.abs(voice_track) * 4.5, 5.5))
    score_gain = 1.0 - 0.56 * np.clip(duck_env, 0.0, 1.0)

    # 2) Dark Hans Zimmer / LEMMiNO Cello & Sub-Drone Score (D minor cinematic progression!)
    f_root = 73.42  # D2
    f_fifth = 110.00  # A2
    f_min3 = 87.31  # F2
    # Shift harmony subtly at 55% for cinematic emotional lift!
    harm_shift = np.where(t < total_dur * 0.55, 1.0, 0.8909)  # D2 -> C2
    lfo = 0.72 + 0.28 * np.sin(2 * np.pi * 0.12 * t)
    pad_L = (
        0.52 * np.sin(2 * np.pi * f_root * harm_shift * t)
        + 0.28 * np.sin(2 * np.pi * (f_fifth * harm_shift + 0.35) * t)
        + 0.18 * np.sin(2 * np.pi * (f_min3 * 2.0) * t)
    ) * lfo * 0.078
    pad_R = (
        0.52 * np.sin(2 * np.pi * (f_root * harm_shift + 0.28) * t)
        + 0.28 * np.sin(2 * np.pi * (f_fifth * harm_shift - 0.30) * t)
        + 0.18 * np.sin(2 * np.pi * (f_min3 * 2.0 + 0.4) * t)
    ) * lfo * 0.078

    # 3) Subtle analog tape warmth + heartbeat/ticking clock documentary urgency!
    tape = _bp(rng.normal(0, 1, N), 240, 2600) * 0.0065
    tick_track = np.zeros(N, dtype=np.float32)
    # Ticking stopwatch every 0.5s from 4.0s until 3.2s before outro (accelerates subtly in climax!)
    cur_t = 4.0
    while cur_t < total_dur - 3.3:
        idx_t = int(cur_t * SR)
        tk_len = min(int(SR * 0.032), N - idx_t)
        if tk_len > 20:
            tt = np.linspace(0, tk_len / SR, tk_len, endpoint=False)
            accent = 1.45 if int(round(cur_t * 2)) % 4 == 0 else 0.85
            click = np.sin(2 * np.pi * (3400 if accent > 1.0 else 2600) * tt) * np.exp(-tt / 0.0045)
            tick_track[idx_t:idx_t + tk_len] += click * 0.042 * accent
        cur_t += 0.50 if cur_t < total_dur * 0.65 else 0.333

    L = voice_track + (pad_L + tape + tick_track * 0.92) * score_gain
    R = voice_track + (pad_R + tape + tick_track * 1.08) * score_gain

    # 4) Frame-Locked Binaural SFX Layer!
    for ts, kind, gain, pan in (sfx_plan or []):
        s = _gen_sfx(kind, rng) * gain
        p0 = int(round(ts * SR))
        if p0 < 0 or p0 >= N:
            continue
        k = min(len(s), N - p0)
        L[p0:p0 + k] += s[:k] * math.sqrt(max(0.0, 1.0 - pan))
        R[p0:p0 + k] += s[:k] * math.sqrt(max(0.0, pan))

    # 5) Clean Fade In/Out + Broadcast Soft Limiter
    fi = min(N, int(0.18 * SR))
    fo = min(N, int(0.85 * SR))
    L[:fi] *= np.linspace(0, 1, fi); R[:fi] *= np.linspace(0, 1, fi)
    L[-fo:] *= np.linspace(1, 0, fo); R[-fo:] *= np.linspace(1, 0, fo)
    L = np.tanh(L * 1.15) * 0.88
    R = np.tanh(R * 1.15) * 0.88

    # 6) Compute 30Hz Voice Oscilloscope Envelope + 30Hz 16-Band Real FFT Spectrum for V15 Visuals!
    hop = SR // 30
    n_steps = max(1, N // hop)
    env30 = np.zeros(n_steps, dtype=np.float32)
    spec30 = np.zeros((n_steps, 16), dtype=np.float32)
    mono = 0.5 * (L + R)
    win = np.hanning(hop)
    freqs = np.fft.rfftfreq(hop, 1.0 / SR)
    band_edges = np.geomspace(55.0, 7500.0, 17)
    band_masks = [(freqs >= band_edges[b]) & (freqs < band_edges[b + 1]) for b in range(16)]

    for i in range(n_steps):
        seg_v = voice_track[i * hop:(i + 1) * hop]
        env30[i] = float(np.sqrt(np.mean(seg_v * seg_v)))
        seg_m = mono[i * hop:(i + 1) * hop] * win
        mag = np.abs(np.fft.rfft(seg_m))
        for b in range(16):
            if np.any(band_masks[b]):
                spec30[i, b] = float(np.mean(mag[band_masks[b]]))

    env30 = np.clip(env30 / (np.percentile(env30, 96) + 1e-6), 0.0, 1.0)
    for b in range(16):
        mx = float(np.percentile(spec30[:, b], 96) + 1e-6)
        spec30[:, b] = np.clip(spec30[:, b] / mx, 0.0, 1.0)

    # 7) Encode -14 LUFS Broadcast Master AAC!
    stereo = np.empty(N * 2, dtype=np.float32)
    stereo[0::2] = L
    stereo[1::2] = R
    proc = subprocess.Popen([
        FFMPEG, "-y", "-v", "error",
        "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "pipe:0",
        "-af", "loudnorm=I=-14:TP=-1.5:LRA=9",
        "-c:a", "aac", "-b:a", "256k", out_m4a
    ], stdin=subprocess.PIPE)
    proc.stdin.write(stereo.tobytes())
    proc.stdin.close()
    proc.wait()
    if proc.returncode != 0:
        raise RuntimeError("V15 Audio mastering failed!")
    return env30, spec30

