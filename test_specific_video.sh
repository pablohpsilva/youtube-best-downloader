#!/bin/bash

# Test script specifically for the requested video
# https://www.youtube.com/watch?v=rGyQHyDMZZI

set -e

TARGET_URL="https://www.youtube.com/watch?v=rGyQHyDMZZI"

echo "🎯 Testing specific video: $TARGET_URL"
echo "==============================================="

# Rebuild the Docker image with all latest fixes
echo "📦 Rebuilding Docker image..."
docker build -t yt-best-dl:latest .

echo ""
echo "🎵 Test 1: Audio download (should work reliably)"
echo "================================================"
docker run --rm -v "$(pwd)/downloads:/downloads" yt-best-dl:latest \
    --music \
    --player-variant auto \
    --sleep-requests 5 \
    --concurrent-fragments 1 \
    --verbose \
    "$TARGET_URL"

echo ""
echo "📹 Test 2: Video download with maximum flexibility"
echo "=================================================="
docker run --rm -v "$(pwd)/downloads:/downloads" yt-best-dl:latest \
    --player-variant auto \
    --sleep-requests 5 \
    --concurrent-fragments 1 \
    --allow-below-min \
    --verbose \
    "$TARGET_URL"

# If video fails, try with simple format
if [ $? -ne 0 ]; then
    echo ""
    echo "🔧 Test 3: Fallback with simple format selection"
    echo "================================================"
    docker run --rm -v "$(pwd)/downloads:/downloads" yt-best-dl:latest \
        --format "best[height<=720]/best" \
        --player-variant auto \
        --sleep-requests 5 \
        --concurrent-fragments 1 \
        --verbose \
        "$TARGET_URL"
fi

echo ""
echo "📂 Checking downloaded files..."
ls -la downloads/ | grep "rGyQHyDMZZI" || echo "No files found with video ID"

echo ""
echo "✅ Test completed for $TARGET_URL"
