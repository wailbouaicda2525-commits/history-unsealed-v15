"""
run_daily_v20.py — 100% Autonomous V20 CINEMA BEAST Daily 9:16 Short Factory
Upgrades V15 -> V20:
  - Live 2026 Groq Showrunner (qwen/qwen3.8-27b + openai/gpt-oss-120b)
  - 4-Source Real Moving Video Scout (Pixabay HD/4K + Internet Archive NARA/Prelinger + Wikimedia + NASA)
  - Explosive 3-Second Real-Video Cold Open Hook
  - Dual Real-Video Split-Screen + Johnny Harris Live-Highlighted Dossier + 3D Book Collector's Promo Outro!
"""
import os
import json
import argparse
from datetime import datetime, timezone

from scout_v15 import scout_event
from scriptwriter_v20 import write_script_v20
from video_scout_v20 import scout_real_videos_v20
from voice_engine_v15 import synthesize_voice_v15, mix_cinema_audio_v15
from renderer_v20_cinema import render_v20_cinema
from uploader_v15 import upload_video_to_youtube, send_telegram


def main():
    cfg = json.load(open("channel_config.json", encoding="utf-8"))
    ap = argparse.ArgumentParser()
    ap.add_argument("--month", type=int, default=0)
    ap.add_argument("--day", type=int, default=0)
    ap.add_argument("--topic", default="", help="Optional topic override")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--out-mp4", default="/tmp/v20_daily_work/daily_short_v20.mp4")
    ap.add_argument("--qa-out", default="/tmp/v20_daily_work/daily_short_v20_qa.jpg")
    args = ap.parse_args()

    dry = args.dry_run or (os.environ.get("DRY_RUN", "false").lower() == "true")
    privacy = os.environ.get("PRIVACY_STATUS", "public").strip() or "public"
    work_dir = os.path.dirname(os.path.abspath(args.out_mp4))
    os.makedirs(work_dir, exist_ok=True)

    now = datetime.now(timezone.utc)
    month = args.month or now.month
    day = args.day or now.day

    print(f"=== {cfg['channel_name']} [V20 CINEMA BEAST] — {month:02d}/{day:02d} (mode={cfg['mode']}, dry_run={dry}) ===")
    ev = scout_event(
        mode=cfg["mode"], month=month, day=day,
        topic_override=args.topic or None,
        history_path="state/history_log.json",
        work_dir=work_dir, channel_name=cfg["channel_name"],
    )
    script = write_script_v20(ev)

    # 🔥 V20: Scout 5 VERIFIED REAL MOVING VIDEO CLIPS (Internet Archive + Wikimedia/NASA + Pixabay HD/4K!)
    video_clips = scout_real_videos_v20(ev, script, work_dir=work_dir, vertical=True, target_clips=5, dur_sec=7.5)

    voice_mp3 = os.path.join(work_dir, "voice_v20.mp3")
    audio_m4a = os.path.join(work_dir, "audio_v20.m4a")
    voice_dur, words = synthesize_voice_v15(
        script["narration"], voice_mp3,
        voice=cfg["voice"], rate=cfg.get("voice_rate", "+4%"), pitch=cfg.get("voice_pitch", "-2Hz"),
    )

    speech_off = 0.45
    total_dur = min(59.0, round(speech_off + voice_dur + 4.55, 2))
    b = [0.0, 0.22, 0.44, 0.64, 0.82, 1.0]
    sfx_plan = [
        (0.10, "braaam", 0.46, 0.50),
        (total_dur * 0.10, "dive", 0.34, 0.50),
        (total_dur * 0.16, "sonar", 0.30, 0.56),
        (total_dur * b[1] - 0.18, "whoosh", 0.36, 0.50),
        (total_dur * (b[1] + 0.095), "shutter", 0.38, 0.52),
        (total_dur * (b[1] + 0.15), "stamp", 0.44, 0.58),
        (total_dur * b[2] - 0.18, "whoosh", 0.36, 0.50),
        (total_dur * (b[2] + 0.05), "paper", 0.34, 0.46),
        (total_dur * (b[2] + 0.11), "paper", 0.28, 0.54),
        (total_dur * b[3] - 0.18, "whoosh", 0.36, 0.50),
        (total_dur * (b[3] + 0.085), "glitch", 0.34, 0.50),
        (total_dur * b[4] - 0.18, "whoosh", 0.36, 0.50),
        (total_dur * b[4] + 0.08, "braaam", 0.36, 0.50),
        (max(1.0, total_dur - 4.2), "shutter", 0.36, 0.50),
    ]
    env30, spec30 = mix_cinema_audio_v15(
        voice_mp3, total_dur, speech_off, audio_m4a,
        seed=ev["year"] * 17 + ev["day"], sfx_plan=sfx_plan,
    )

    render_v20_cinema(
        ev, script, voice_dur, words, audio_m4a, env30, spec30,
        args.out_mp4, video_clips=video_clips, vertical=True, qa_out=args.qa_out,
        show_outro=True, show_midroll_ad=True,
    )

    yt_title = f"{script['title']} #Shorts"
    if len(yt_title) > 100:
        yt_title = script["title"][:91].rsplit(" ", 1)[0] + " #Shorts"
    yt_desc = (
        f"{cfg['description_footer']}\n\n"
        f"---\n"
        f"{script['title']}\n"
        f"Date: {ev['display_date']} | Location: {ev['location']}\n\n"
        f"{script['narration']}\n\n"
        f"{'Source Archive: ' + ev['wiki_url'] + chr(10) if ev.get('wiki_url') else ''}"
        f"{cfg['hashtags']}"
    )
    tags = list(dict.fromkeys([t.strip() for t in (script.get("tags", []) + ["history", "us history", "shorts", "documentary"]) if t.strip()]))

    if dry:
        print(f"[DRY RUN V20] Skipping YouTube upload. Title={yt_title}")
        print(f"[DRY RUN V20] Real Video Sources: {[c['source'] for c in video_clips]}")
        print(f"[DRY RUN V20] Output MP4={args.out_mp4} | QA={args.qa_out}")
        return

    vid = upload_video_to_youtube(args.out_mp4, yt_title, yt_desc, tags, privacy=privacy)
    os.makedirs("state", exist_ok=True)
    hp = "state/history_log.json"
    hist = json.load(open(hp)) if os.path.exists(hp) else []
    hist.append({
        "id": ev["id"],
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "title": script["title"],
        "video_id": vid,
    })
    json.dump(hist[-5000:], open(hp, "w"), indent=2)

    yt_url = f"https://youtube.com/shorts/{vid}"
    send_telegram(
        f"🔥 <b>{cfg['channel_name']} — V20.5 CINEMA SHORT LIVE!</b>\n"
        f"🎬 <b>{script['title']}</b>\n"
        f"🎥 Story-Locked Videos: {len(video_clips)} ({', '.join(set(c['source'] for c in video_clips))})\n"
        f"📍 {ev['display_date']} • {ev['location']}\n"
        f"🧠 Script: {script.get('source', 'v20.5')}\n"
        f"🔗 {yt_url}"
    )


if __name__ == "__main__":
    main()
