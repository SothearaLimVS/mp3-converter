import os, re, shutil, threading, time, uuid, tempfile
from flask import Flask, request, jsonify, send_file, render_template, after_this_request
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

app = Flask(__name__)
DOWNLOAD_DIR = tempfile.gettempdir()
TTL_SECONDS = 300
COOKIES_CANDIDATES = [
    "/etc/secrets/cookies.txt",
    os.path.join(os.path.dirname(__file__), "cookies.txt"),
]
WRITABLE_COOKIES = os.path.join(tempfile.gettempdir(), "yt_cookies.txt")

def _setup_cookies():
    for p in COOKIES_CANDIDATES:
        if os.path.exists(p):
            try:
                shutil.copyfile(p, WRITABLE_COOKIES)
                os.chmod(WRITABLE_COOKIES, 0o600)
                return WRITABLE_COOKIES
            except OSError:
                pass
    return None

ACTIVE_COOKIES = _setup_cookies()

def base_ydl_opts():
    opts = {"quiet": True, "no_warnings": True, "noplaylist": True}
    if ACTIVE_COOKIES:
        opts["cookiefile"] = ACTIVE_COOKIES
    return opts

def safe_filename(name: str) -> str:
    name = re.sub(r'[\\/:*?"<>|\r\n\t]+', "", name).strip()
    return (name or "audio")[:120]

def schedule_delete(path: str, delay: int = TTL_SECONDS):
    def _rm():
        time.sleep(delay)
        try: os.remove(path)
        except OSError: pass
    threading.Thread(target=_rm, daemon=True).start()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/preview", methods=["POST"])
def preview():
    url = (request.json or {}).get("url", "").strip()
    if not url:
        return jsonify(error="Please provide a URL."), 400
    try:
        with YoutubeDL({**base_ydl_opts(), "skip_download": True}) as ydl:
            info = ydl.extract_info(url, download=False)
        return jsonify(
            title=info.get("title"),
            thumbnail=info.get("thumbnail"),
            duration=info.get("duration"),
            uploader=info.get("uploader"),
        )
    except DownloadError as e:
        return jsonify(error=friendly_error(str(e))), 400
    except Exception as e:
        return jsonify(error=f"Could not fetch video info: {e}"), 400

@app.route("/convert", methods=["POST"])
def convert():
    data = request.json or {}
    url = (data.get("url") or "").strip()
    quality = str(data.get("quality") or "192")
    if quality not in {"128", "192", "320"}:
        quality = "192"
    if not url:
        return jsonify(error="Please provide a URL."), 400

    job_id = uuid.uuid4().hex
    out_template = os.path.join(DOWNLOAD_DIR, f"{job_id}.%(ext)s")
    ydl_opts = {
        **base_ydl_opts(),
        "format": "bestaudio/best",
        "outtmpl": out_template,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": quality,
        }],
    }
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
        mp3_path = os.path.join(DOWNLOAD_DIR, f"{job_id}.mp3")
        if not os.path.exists(mp3_path):
            return jsonify(error="Conversion failed."), 500

        title = safe_filename(info.get("title") or "audio")
        download_name = f"{title}.mp3"

        @after_this_request
        def cleanup(response):
            schedule_delete(mp3_path, delay=10)
            return response

        schedule_delete(mp3_path, delay=TTL_SECONDS)
        return send_file(mp3_path, as_attachment=True, download_name=download_name, mimetype="audio/mpeg")
    except DownloadError as e:
        return jsonify(error=friendly_error(str(e))), 400
    except Exception as e:
        return jsonify(error=f"Conversion error: {e}"), 500

def friendly_error(msg: str) -> str:
    print(f"[yt-dlp error] {msg}", flush=True)
    m = msg.lower()
    if "sign in" in m or "confirm you" in m or "not a bot" in m or "bot" in m:
        return "YouTube is blocking the server. The site owner needs to upload a cookies.txt file."
    if "age" in m and "restrict" in m: return "This video is age-restricted and can't be downloaded."
    if "private" in m: return "This video is private."
    if "not available in your country" in m or "geo" in m: return "This video is region-locked."
    if "unavailable" in m or "removed" in m: return "Video is unavailable or has been removed."
    if "unsupported url" in m or "is not a valid url" in m: return "That doesn't look like a valid YouTube URL."
    return "Could not process this video. Check the URL and try again."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
