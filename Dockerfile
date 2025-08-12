FROM python:3.12-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg ca-certificates && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
RUN pip install --no-cache-dir "yt-dlp[default]"

COPY yt_best_downloader.py /app/yt_best_downloader.py

# bake default outdir so passing a URL doesn’t override it
ENTRYPOINT ["python", "/app/yt_best_downloader.py", "--outdir", "/downloads"]