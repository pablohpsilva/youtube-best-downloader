#!/bin/bash

# Script to fix YouTube quality issues by testing multiple strategies

TARGET_URL="${1:-https://www.youtube.com/watch?v=rGyQHyDMZZI}"

echo "🔧 Fixing YouTube Quality Issues for: $TARGET_URL"
echo "======================================================="

# Rebuild with latest fixes
echo "📦 Rebuilding Docker image with JavaScript runtime fixes..."
docker build -t yt-best-dl:latest .

echo ""
echo "🔍 Step 1: Check available formats"
echo "=================================="
docker run --rm -v "$(pwd)/downloads:/downloads" yt-best-dl:latest \
    --list-formats \
    --verbose \
    "$TARGET_URL"

echo ""
echo "🎯 Step 2: Try with TV client (often has more formats)"
echo "====================================================="
docker run --rm -v "$(pwd)/downloads:/downloads" yt-best-dl:latest \
    --list-formats \
    --player-variant tv \
    "$TARGET_URL"

echo ""
echo "📹 Step 3: Download with TV client (best quality available)"
echo "==========================================================="
docker run --rm -v "$(pwd)/downloads:/downloads" yt-best-dl:latest \
    --player-variant tv \
    --max-res 2160 \
    --allow-below-min \
    --verbose \
    "$TARGET_URL"

# If TV client fails, try other strategies
if [ $? -ne 0 ]; then
    echo ""
    echo "🔄 Step 4: Fallback - Try with web client"
    echo "=========================================="
    docker run --rm -v "$(pwd)/downloads:/downloads" yt-best-dl:latest \
        --player-variant web \
        --format "best[height<=1080]/best[height<=720]/best" \
        --sleep-requests 10 \
        --verbose \
        "$TARGET_URL"

    if [ $? -ne 0 ]; then
        echo ""
        echo "🆘 Step 5: Last resort - Simple download"
        echo "========================================"
        docker run --rm -v "$(pwd)/downloads:/downloads" yt-best-dl:latest \
            --format "best" \
            --player-variant web_embedded \
            --sleep-requests 15 \
            "$TARGET_URL"
    fi
fi

echo ""
echo "📊 Final Results - Downloaded Files:"
echo "===================================="
ls -la downloads/ | grep "$(echo "$TARGET_URL" | sed 's/.*v=//' | sed 's/&.*//')" | while read line; do
    file=$(echo "$line" | awk '{print $9}')
    size=$(echo "$line" | awk '{print $5}')
    
    if [[ "$file" == *.mp4 ]] || [[ "$file" == *.mkv ]] || [[ "$file" == *.webm ]]; then
        echo "🎬 VIDEO: $file ($size bytes)"
        # Try to get video info
        if command -v ffprobe >/dev/null 2>&1; then
            ffprobe -v quiet -show_streams -select_streams v:0 "downloads/$file" 2>/dev/null | grep -E "(width|height)=" || echo "   Could not determine resolution"
        fi
    elif [[ "$file" == *.m4a ]] || [[ "$file" == *.mp3 ]]; then
        echo "🎵 AUDIO: $file ($size bytes)"
    elif [[ "$file" == *.vtt ]] || [[ "$file" == *.srt ]]; then
        echo "📝 SUBTITLES: $file ($size bytes)"
    else
        echo "📄 OTHER: $file ($size bytes)"
    fi
done

echo ""
echo "✅ Quality fix attempt completed!"
echo ""
echo "💡 If you still get low quality, try these manual commands:"
echo ""
echo "# For maximum quality (if available):"
echo "docker run --rm -v \"\$(pwd)/downloads:/downloads\" yt-best-dl:latest \\"
echo "    --player-variant tv \\"
echo "    --format \"best[height>=720]/best\" \\"
echo "    \"$TARGET_URL\""
echo ""
echo "# For guaranteed HD (if available):"
echo "docker run --rm -v \"\$(pwd)/downloads:/downloads\" yt-best-dl:latest \\"
echo "    --format \"22/best[height>=720]/18/best\" \\"
echo "    --player-variant tv \\"
echo "    \"$TARGET_URL\""
