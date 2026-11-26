# THE DAILY ARCHIVE — V15 BEAST 100% Zero-Touch YouTube Autopilot ($0/month)

Autonomous **Tier-1 US / Anglosphere** `On This Day` & Blockbuster Historical Turning Points YouTube factory powered by **V15 BEAST MODE** (`en-US-ChristopherNeural`, Esri Dark 3D Cartography, Real Archival Photography, Oscilloscope + 16-Band Spectrum, Auto High-CTR Thumbnails) — with **100% ZERO topic overlap** with `Behind The Curtain`.

## Publishing Cadence (Fully Automatic)
- **4× Daily V15 BEAST Shorts (`9:16`, 1080×1920 @ 30fps):**
  `daily_shorts_4x.yml` → `30 12,16,20,0 * * *` (07:30, 11:30, 15:30, 19:30 US EST — pulls the top 4 distinct US/Tier-1 `On This Day` stories each day + seamless 60-topic dedicated US Blockbuster Vault if any calendar day has fewer than 4).
- **1× Massive Adaptive Deep Single-Topic Documentary EVERY 2 DAYS (`16:9`, 1920×1080 @ 24fps + Auto High-CTR Thumbnail):**
  `longform_doc_every_2days.yml` → `0 19 2-30/2 * *` (Even calendar days at 19:00 UTC / 2:00 PM US EST — staggered on alternating days from Channel 1).
  - **Natural Adaptive Runtime (12 to 30 minutes!):** Automatically scales from **7 chapters (~12–15 min)** up to **15 chapters (~25–30 min)** based on real historical depth — zero artificial 15-min ceiling and zero fluff padding!
  - **Parallel Multi-Core Rendering:** Renders chapters concurrently across GitHub Actions' 4-vCPU runner (~18–24 min even for a 28–30 min 1080p film!).

## Required GitHub Secrets (`Settings → Secrets and variables → Actions`)
| Secret | Required | Description |
|---|---|---|
| `YOUTUBE_CLIENT_ID` | **Yes** | Google Cloud OAuth Desktop Client ID (**dedicated free GCP Project #2 for The Daily Archive**) |
| `YOUTUBE_CLIENT_SECRET` | **Yes** | Google Cloud OAuth Desktop Client Secret |
| `YOUTUBE_REFRESH_TOKEN` | **Yes** | Refresh token generated via `python3 get_refresh_token.py` (authorized on `The Daily Archive` channel ONLY) |
| `GEMINI_API_KEY` | Recommended | Free key from `aistudio.google.com` (100% unique investigative scripts) |
| `GROQ_API_KEY` | Optional | Free backup key from `console.groq.com` (`llama-3.3-70b-versatile`) |
| `TELEGRAM_BOT_TOKEN` | Optional | Telegram bot alerts when each Short / Documentary goes live |
| `TELEGRAM_CHAT_ID` | Optional | Your Telegram chat ID |

## Important Quota, Warmup & Free Minutes Setup
1. **Dedicated 2nd Free Google Cloud Project ($0):** Peak day uses `4 × 1,600 + 1,650 = 8,050 / 10,000` free YouTube Data API v3 units. Create a **2nd free Google Cloud Project** strictly for `The Daily Archive` so both channels each get their own `10,000 units/day` quota!
2. **Unlimited Free GitHub Actions Minutes:** Keep this repo **Public** to receive **UNLIMITED free GitHub Actions minutes** (GitHub Secrets stay 100% encrypted and hidden; `.gitignore` blocks all credentials).
3. **One-Time Phone Verification (REQUIRED for >15 min Videos & Custom Thumbnails!):** Verify `The Daily Archive` once at `youtube.com/verify` + unlock Advanced Features in YouTube Studio before turning on full 4 Shorts/day + 20–30 min documentaries.
4. **Important Windows Upload Note:** Push via `git push` (not web drag-and-drop), because GitHub's web uploader skips hidden `.github/workflows/` folders.
