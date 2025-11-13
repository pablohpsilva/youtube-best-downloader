#!/bin/bash

# Test script for YouTube downloader fixes
# Tests multiple strategies to resolve signature/n-challenge issues

set -e

echo "🔧 Testing YouTube Downloader Fixes..."

# Test URL (using the same URL from the error log)
TEST_URL="https://www.youtube.com/watch?v=rGyQHyDMZZI"

# Rebuild the Docker image with all fixes
echo "📦 Rebuilding Docker image with JavaScript runtime support..."
docker build -t yt-best-dl:latest .

echo ""
echo "🔍 Step 1: List available formats (diagnosis)"
echo "=============================================="
docker run --rm -v "$(pwd)/downloads:/downloads" yt-best-dl:latest \
    --list-formats \
    --player-variant auto \
    --verbose \
    "$TEST_URL"

echo ""
echo "🎵 Step 2: Try audio-only download (most reliable)"
echo "=================================================="
docker run --rm -v "$(pwd)/downloads:/downloads" yt-best-dl:latest \
    --music \
    --player-variant auto \
    --sleep-requests 10 \
    --concurrent-fragments 1 \
    --verbose \
    "$TEST_URL"

echo ""
echo "📹 Step 3: Try video download with new auto player variant"
echo "=========================================================="
docker run --rm -v "$(pwd)/downloads:/downloads" yt-best-dl:latest \
    --player-variant auto \
    --sleep-requests 10 \
    --concurrent-fragments 1 \
    --allow-below-min \
    --verbose \
    "$TEST_URL"

echo ""
echo "🔍 Step 4: Test specific player variants if auto fails"
echo "======================================================"

for variant in ios android mweb web_embedded; do
    echo "Testing player variant: $variant"
    if docker run --rm -v "$(pwd)/downloads:/downloads" yt-best-dl:latest \
        --list-formats \
        --player-variant "$variant" \
        "$TEST_URL" 2>/dev/null | grep -q "format code"; then
        echo "✅ $variant has available formats"
        
        # Try downloading with this variant
        docker run --rm -v "$(pwd)/downloads:/downloads" yt-best-dl:latest \
            --player-variant "$variant" \
            --sleep-requests 10 \
            --concurrent-fragments 1 \
            --allow-below-min \
            "$TEST_URL" && echo "✅ Download successful with $variant" && break
    else
        echo "❌ $variant has no available formats or failed"
    fi
done

echo ""
echo "✅ Test completed! Check downloads/ folder for results."
echo ""
echo "💡 If downloads still fail, YouTube may be blocking this specific video."
echo "   Try with a different video URL or use these commands:"
echo ""
echo "   # For format debugging:"
echo "   docker run --rm -v ./downloads:/downloads yt-best-dl:latest --list-formats --verbose YOUR_URL"
echo ""
echo "   # For audio-only (most reliable):"
echo "   docker run --rm -v ./downloads:/downloads yt-best-dl:latest --music --player-variant auto YOUR_URL"
