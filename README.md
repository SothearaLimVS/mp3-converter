# YouTube → MP3

A personal, single-user YouTube to MP3 converter. No accounts, no database, no telemetry.

## Local run

```bash
pip install -r requirements.txt
# make sure ffmpeg is on your PATH
python app.py
```

Open http://localhost:5000.

## Deploy to Render (free tier)

Render is the easiest free option that supports Docker.

1. **Push this folder to GitHub.**
   - Create a new GitHub repo (e.g. `mp3-converter`).
   - From this folder:
     ```bash
     git init
     git add .
     git commit -m "init"
     git branch -M main
     git remote add origin https://github.com/<your-username>/mp3-converter.git
     git push -u origin main
     ```

2. **Create a Render account** at https://render.com (sign in with GitHub for one-click repo access).

3. **New Web Service:**
   - Click **New +** → **Web Service**.
   - Connect your GitHub account if you haven't, then pick the `mp3-converter` repo.
   - Render auto-detects the `Dockerfile`. Confirm:
     - **Environment:** Docker
     - **Region:** pick the one closest to you
     - **Instance Type:** Free
     - **Branch:** main
   - Leave build/start commands empty — the Dockerfile handles everything.
   - Click **Create Web Service**.

4. **First build takes ~3–5 min** (installing ffmpeg + Python deps). When the log shows `Listening at: http://0.0.0.0:8000`, you're live.

5. **Your public URL** appears at the top of the service page, e.g. `https://mp3-converter-xxxx.onrender.com`. Open it on your phone, then **Share → Add to Home Screen** (iOS) or **Install app** (Android Chrome) to launch like a native app.

### Notes about the free tier
- Render free instances **spin down after 15 min of inactivity** — first request after a nap takes ~30 s to wake up.
- Disk is ephemeral, which is fine here: each MP3 is auto-deleted after download (or 5 min max).

## Alternatives
- **Railway** / **Fly.io**: same `Dockerfile` works. On Fly: `fly launch` from this folder, accept the Dockerfile, deploy.

## Legal
For personal use with content you have the right to download. You are responsible for complying with YouTube's Terms of Service and copyright law in your jurisdiction.
