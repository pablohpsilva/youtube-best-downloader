#!/bin/bash

# Easy YouTube downloader with quality presets
# Usage: ./easy_download.sh <quality_preset> <YouTube_URL>

show_help() {
    echo "🎬 Easy YouTube Downloader"
    echo "=========================="
    echo ""
    echo "Usage: $0 <quality> <YouTube_URL>"
    echo ""
    echo "Quality Options:"
    echo "  best        - Try for best available (1080p+)"
    echo "  hd          - HD quality (720p minimum)"
    echo "  sd          - Standard quality (480p minimum)"
    echo "  low         - Low quality (360p minimum)"
    echo "  any         - Any available quality"
    echo "  audio       - Audio only (M4A)"
    echo "  test        - Show available formats only"
    echo ""
    echo "Examples:"
    echo "  $0 hd 'https://www.youtube.com/watch?v=rGyQHyDMZZI'"
    echo "  $0 audio 'https://www.youtube.com/watch?v=rGyQHyDMZZI'"
    echo "  $0 test 'https://www.youtube.com/watch?v=rGyQHyDMZZI'"
    echo ""
}

QUALITY="$1"
URL="$2"

if [ -z "$QUALITY" ] || [ -z "$URL" ]; then
    show_help
    exit 1
fi

case "$QUALITY" in
    "best"|"4k"|"1080")
        echo "🎯 Downloading BEST quality (1080p+ preferred)..."
        docker run --rm -v "$(pwd)/downloads:/downloads" yt-best-dl:latest \
            --player-variant tv \
            --min-res 1080 \
            --allow-below-min \
            --format "best[height>=1080]/best[height>=720]/best[height>=480]/best" \
            --sleep-requests 8 \
            "$URL"
        ;;
        
    "hd"|"720")
        echo "🎯 Downloading HD quality (720p minimum)..."
        docker run --rm -v "$(pwd)/downloads:/downloads" yt-best-dl:latest \
            --player-variant auto \
            --min-res 720 \
            --allow-below-min \
            --format "best[height>=720]/best[height>=480]/best" \
            --sleep-requests 5 \
            "$URL"
        ;;
        
    "sd"|"480")
        echo "🎯 Downloading SD quality (480p minimum)..."
        docker run --rm -v "$(pwd)/downloads:/downloads" yt-best-dl:latest \
            --player-variant auto \
            --min-res 480 \
            --allow-below-min \
            --format "best[height>=480]/best[height>=360]/best" \
            --sleep-requests 5 \
            "$URL"
        ;;
        
    "low"|"360"|"basic")
        echo "🎯 Downloading LOW quality (360p minimum)..."
        docker run --rm -v "$(pwd)/downloads:/downloads" yt-best-dl:latest \
            --player-variant auto \
            --min-res 360 \
            --allow-below-min \
            --format "best[height>=360]/best" \
            --sleep-requests 5 \
            "$URL"
        ;;
        
    "any"|"whatever")
        echo "🎯 Downloading ANY available quality..."
        docker run --rm -v "$(pwd)/downloads:/downloads" yt-best-dl:latest \
            --format "best" \
            --player-variant web_embedded \
            --sleep-requests 5 \
            "$URL"
        ;;
        
    "audio"|"music"|"mp3")
        echo "🎵 Downloading AUDIO only..."
        docker run --rm -v "$(pwd)/downloads:/downloads" yt-best-dl:latest \
            --music \
            --player-variant auto \
            --sleep-requests 5 \
            "$URL"
        ;;
        
    "test"|"check"|"formats")
        echo "🔍 Checking available formats..."
        docker run --rm -v "$(pwd)/downloads:/downloads" yt-best-dl:latest \
            --list-formats \
            --player-variant auto \
            --verbose \
            "$URL"
        ;;
        
    *)
        echo "❌ Unknown quality preset: $QUALITY"
        echo ""
        show_help
        exit 1
        ;;
esac

# Show results if download completed
if [ $? -eq 0 ] && [ "$QUALITY" != "test" ]; then
    echo ""
    echo "✅ Download completed! Files:"
    VIDEO_ID=$(echo "$URL" | sed 's/.*[?&]v=//' | cut -d'&' -f1)
    ls -la downloads/ | grep "$VIDEO_ID" | while read line; do
        file=$(echo "$line" | awk '{print $9}')
        size=$(echo "$line" | awk '{print $5}')
        echo "📄 $file ($(numfmt --to=iec --suffix=B $size))"
    done
fi
