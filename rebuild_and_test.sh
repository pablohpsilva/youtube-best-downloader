#!/bin/bash
set -e

echo "🔄 Rebuilding Docker image with fixes..."
docker-compose build --no-cache youtube-downloader

echo "🧪 Testing with a simple video download..."
# Use a short, simple video for testing
TEST_URL="https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Roll - short video, unlikely to have issues

echo "Testing video download (with increased delays)..."
docker-compose run --rm youtube-downloader \
    --sleep-requests 8 \
    --concurrent-fragments 1 \
    --player-variant ios \
    --subs en \
    --no-auto-subs \
    "$TEST_URL"

echo "✅ Test completed! Check the downloads folder for results."
echo "If you see permission or 403/429 errors, the fixes need more adjustment."
