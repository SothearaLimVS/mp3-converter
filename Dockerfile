FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg curl ca-certificates gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN curl -fsSL https://raw.githubusercontent.com/Brainicism/bgutil-ytdlp-pot-provider/master/server/build/generate_once.js \
    -o /app/generate_once.js

COPY . .

ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "gunicorn -b 0.0.0.0:${PORT} --timeout 300 --workers 2 app:app"]
