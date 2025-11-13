#!/bin/bash

# High-quality video downloader with multiple fallback strategies
# Usage: ./download_hd_video.sh <YouTube_URL>

URL="${1}"
if [ -z "$URL" ]; then
    echo "Usage: $0 <YouTube_URL>"
    echo "Example: $0 'https://www.youtube.com/watch?v=rGyQHyDMZZI'"
    exit 1
fi

echo "🎯 Downloading HD video: $URL"
echo "=================================================="

# Strategy 1: TV client (often bypasses restrictions)
echo "📺 Trying TV client for maximum quality..."
docker run --rm -v "$(pwd)/downloads:/downloads" yt-best-dl:latest \
    --player-variant tv \
    --format "best[height>=1080]/best[height>=720]/best" \
    --sleep-requests 8 \
    --concurrent-fragments 1 \
    --verbose \
    "$URL"

if [ $? -eq 0 ]; then
    echo "✅ Success with TV client!"
    exit 0
fi

# Strategy 2: Web client with specific format codes
echo ""
echo "🌐 Trying web client with HD format codes..."
docker run --rm -v "$(pwd)/downloads:/downloads" yt-best-dl:latest \
    --player-variant web \
    --format "22/136+140/135+140/134+140/18/best" \
    --sleep-requests 10 \
    --verbose \
    "$URL"

if [ $? -eq 0 ]; then
    echo "✅ Success with web client and format codes!"
    exit 0
fi

# Strategy 3: iOS client (sometimes works better)
echo ""
echo "📱 Trying iOS client..."
docker run --rm -v "$(pwd)/downloads:/downloads" yt-best-dl:latest \
    --player-variant ios \
    --format "best[height<=1080]/best" \
    --sleep-requests 5 \
    --verbose \
    "$URL"

if [ $? -eq 0 ]; then
    echo "✅ Success with iOS client!"
    exit 0
fi

# Strategy 4: Android client
echo ""
echo "🤖 Trying Android client..."
docker run --rm -v "$(pwd)/downloads:/downloads" yt-best-dl:latest \
    --player-variant android \
    --format "best[height<=720]/best" \
    --sleep-requests 5 \
    "$URL"

if [ $? -eq 0 ]; then
    echo "✅ Success with Android client!"
    exit 0
fi

# Strategy 5: Last resort with basic format
echo ""
echo "🆘 Last resort: basic download..."
docker run --rm -v "$(pwd)/downloads:/downloads" yt-best-dl:latest \
    --format "best" \
    --player-variant web_embedded \
    --sleep-requests 15 \
    "$URL"

if [ $? -eq 0 ]; then
    echo "⚠️ Downloaded with basic quality (may be low resolution)"
else
    echo "❌ All download strategies failed!"
    exit 1
fi
