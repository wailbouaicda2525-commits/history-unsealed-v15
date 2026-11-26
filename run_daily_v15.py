"""
run_daily_v15.py — 100% Autonomous V15 BEAST Daily 9:16 Short Factory
Reads channel_config.json so the exact same rock-solid V15 BEAST engine powers BOTH:
  - Behind The Curtain (Cold War, CIA/KGB, Nuclear Close Calls & Secret History)
  - The Daily Archive  (US/Global Tier-1 'On This Day' Viral History)
"""
import os
import json
import argparse
from datetime import datetime, timezone

from scout_v15 import scout_event
from scriptwriter_v15 import write_script_v15
from voice_engine_v15 import synthesize_voice_v15, mix_cinema_audio_v15
from renderer_v15_beast import render_v15_beast
from uploader_v15 import upload_video_to_youtube, send_telegram


def main():
    cfg = json.load(open("channel_config.json"))
    ap = argparse.ArgumentParser()
    ap.add_argument("--month", type=int, default=0)
    ap.add_argument("--day", type=int, default=0)
    ap.add_argument("--topic", default="", help="Optional topic override for Behind The Curtain mode")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--out-mp4", default="/tmp/v15_daily_work/daily_short_v15.mp4")
    ap.add_argument("--qa-out", default="/tmp/v15_daily_work/daily_short_v15_qa.jpg")
    args = ap.parse_args()

    dry = args.dry_run or (os.environ.get("DRY_RUN", "false").lower() == "true")
    privacy = os.environ.get("PRIVACY_STATUS", "public").strip() or "public"
    work_dir = os.path.dirname(os.path.abspath(args.out_mp4))
    os.makedirs(work_dir, exist_ok=True)

    now = datetime.now(timezone.utc)
    month = args.month or now.month
    day = args.day or now.day

    print(f"=== {cfg['channel_name']} [V15 BEAST] — {month:02d}/{day:02d} (mode={cfg['mode']}, dry_run={dry}) ===")
    ev = scout_event(
        mode=cfg["mode"], month=month, day=day,
        topic_override=args.topic or None,
        history_path="state/history_log.json",
        work_dir=work_dir, channel_name=cfg["channel_name"],
    )
    script = write_script_v15(ev)

    voice_mp3 = os.path.join(work_dir, "voice_v15.mp3")
    audio_m4a = os.path.join(work_dir, "audio_v15.m4a")
    voice_dur, words = synthesize_voice_v15(
        script["narration"], voice_mp3,
        voice=cfg["voice"], rate=cfg.get("voice_rate", "+3%"), pitch=cfg.get("voice_pitch", "-2Hz"),
    )

    speech_off = 0.45
    total_dur = min(58.5, round(speech_off + voice_dur + 3.2, 2))
    b = [0.0, 0.20, 0.42, 0.62, 0.81, 1.0]
    sfx_plan = [
        (0.32, "braaam", 0.44, 0.50),
        (total_dur * 0.072, "dive", 0.34, 0.50),
        (total_dur * 0.115, "radar", 0.22, 0.45),
        (total_dur * b[1] - 0.16, "whip", 0.28, 0.62),
        (total_dur * (b[1] + 0.068), "shutter", 0.42, 0.50),
        (total_dur * (b[1] + 0.082), "paper_rip", 0.34, 0.40),
        (total_dur * (b[1] + 0.145), "stamp", 0.46, 0.58),
        (total_dur * b[2] - 0.16, "whip", 0.28, 0.38),
        (total_dur * (b[2] + 0.025), "highlight", 0.26, 0.35),
        (total_dur * (b[2] + 0.075), "highlight", 0.26, 0.55),
        (total_dur * (b[2] + 0.125), "highlight", 0.26, 0.72),
        (total_dur * b[3] - 0.12, "laser", 0.38, 0.50),
        (total_dur * (b[3] + 0.068), "glitch", 0.34, 0.50),
        (total_dur * b[4] - 0.16, "whip", 0.28, 0.50),
        (total_dur - 5.4, "riser", 0.42, 0.50),
        (total_dur - 3.0, "drop", 0.54, 0.50),
    ]
    env30, spec30 = mix_cinema_audio_v15(voice_mp3, total_dur, speech_off, audio_m4a, seed=ev["year"] + day, sfx_plan=sfx_plan)
    actual_dur = render_v15_beast(
        ev, script, voice_dur, words, audio_m4a, env30, spec30,
        args.out_mp4, vertical=True, qa_out=args.qa_out,
    )

    yt_title = f"{script['title']} #Shorts"[:98]
    sources_txt = "\n".join(s for s in ev.get("sources", []) if s)
    hashtags = cfg.get("hashtags", "#Shorts #History #HistoryDocumentary #ColdWar")
    yt_desc = (
        f"{script['title']}\n\n"
        f"{ev['display_date']} ({ev['location']}): {ev['summary']}\n\n"
        f"{cfg['description_footer']}\n\n"
        f"Verified Archival Sources:\n{sources_txt}\n"
        f"Map cartography © Esri World Dark Gray Base.\n\n"
        f"{hashtags} #{ev['year']}"
    )

    if not dry:
        vid_id = upload_video_to_youtube(args.out_mp4, yt_title, yt_desc, script["tags"], privacy=privacy)
        os.makedirs("state", exist_ok=True)
        hist_p = "state/history_log.json"
        hist = json.load(open(hist_p)) if os.path.exists(hist_p) else []
        hist.append({"id": ev["id"], "date": now.strftime("%Y-%m-%d"), "title": script["title"], "video_id": vid_id})
        json.dump(hist[-10000:], open(hist_p, "w"), indent=2)

        wk_p = "state/weekly_queue.json"
        wk = json.load(open(wk_p)) if os.path.exists(wk_p) else []
        wk.append({
            "mode": cfg["mode"], "id": ev["id"], "month": month, "day": day, "year": ev["year"],
            "topic_hint": ev.get("hook_hint", ""), "date_label": ev["date_label"], "location": ev["location"],
            "title": script["title"], "script": script,
        })
        json.dump(wk[-14:], open(wk_p, "w"), indent=2)

        send_telegram(
            f"🐉 <b>{cfg['channel_name']} [V15 BEAST] — Short LIVE!</b>\n\n"
            f"📅 <b>{ev['display_date']}</b> ({ev['location']})\n"
            f"🔥 {script['title']}\n"
            f"⏱️ {actual_dur:.1f}s | AI: {script['provider']}\n"
            f"▶️ https://www.youtube.com/shorts/{vid_id}\n"
            f"🔒 Privacy: <code>{privacy}</code>"
        )
    else:
        print(f"[DRY RUN V15 OK!] {args.out_mp4} ({actual_dur:.1f}s) | QA: {args.qa_out}")


if __name__ == "__main__":
    main()
