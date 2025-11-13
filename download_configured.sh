#!/bin/bash

# YouTube downloader with configurable quality settings
# Reads settings from quality_config.conf
# Usage: ./download_configured.sh <YouTube_URL> [quality_override]

URL="$1"
QUALITY_OVERRIDE="$2"

if [ -z "$URL" ]; then
    echo "Usage: $0 <YouTube_URL> [quality_override]"
    echo ""
    echo "Quality overrides:"
    echo "  best    - 1080p+ preferred"
    echo "  hd      - 720p minimum"
    echo "  sd      - 480p minimum"  
    echo "  low     - 360p minimum"
    echo "  audio   - Audio only"
    echo ""
    echo "Examples:"
    echo "  $0 'https://www.youtube.com/watch?v=...'       # Use config defaults"
    echo "  $0 'https://www.youtube.com/watch?v=...' hd    # Override to HD"
    echo ""
    echo "Edit quality_config.conf to change default settings."
    exit 1
fi

# Source configuration file
CONFIG_FILE="quality_config.conf"
if [ -f "$CONFIG_FILE" ]; then
    echo "📋 Loading configuration from $CONFIG_FILE..."
    source "$CONFIG_FILE"
else
    echo "⚠️ Config file not found, using defaults..."
    DEFAULT_MIN_RES=360
    DEFAULT_MAX_RES=2160
    DEFAULT_PLAYER_VARIANT=auto
    DEFAULT_SLEEP=5
    DEFAULT_CONCURRENT_FRAGMENTS=1
    ALLOW_BELOW_MIN=true
    ENABLE_VERBOSE=false
fi

# Apply quality override if specified
if [ -n "$QUALITY_OVERRIDE" ]; then
    case "$QUALITY_OVERRIDE" in
        "best")
            MIN_RES=1080
            MAX_RES=2160
            FORMAT_STRING="$FORMAT_BEST"
            ;;
        "hd")
            MIN_RES=720
            MAX_RES=2160
            FORMAT_STRING="$FORMAT_HD"
            ;;
        "sd")
            MIN_RES=480
            MAX_RES=1080
            FORMAT_STRING="$FORMAT_SD"
            ;;
        "low")
            MIN_RES=360
            MAX_RES=720
            FORMAT_STRING="$FORMAT_LOW"
            ;;
        "audio")
            echo "🎵 Downloading audio only..."
            docker run --rm -v "$(pwd)/downloads:/downloads" yt-best-dl:latest \
                --music \
                --player-variant "$DEFAULT_PLAYER_VARIANT" \
                --sleep-requests "$DEFAULT_SLEEP" \
                "$URL"
            exit $?
            ;;
        *)
            echo "❌ Unknown quality override: $QUALITY_OVERRIDE"
            exit 1
            ;;
    esac
    echo "🎯 Quality override: $QUALITY_OVERRIDE (${MIN_RES}p-${MAX_RES}p)"
else
    # Use config defaults
    MIN_RES=${DEFAULT_MIN_RES:-360}
    MAX_RES=${DEFAULT_MAX_RES:-2160}
    FORMAT_STRING="best[height>=${MIN_RES}]/best"
    echo "🎯 Using configured quality: ${MIN_RES}p-${MAX_RES}p"
fi

# Build command arguments
CMD_ARGS=(
    "--player-variant" "$DEFAULT_PLAYER_VARIANT"
    "--min-res" "$MIN_RES"
    "--max-res" "$MAX_RES"
    "--sleep-requests" "$DEFAULT_SLEEP"
    "--concurrent-fragments" "$DEFAULT_CONCURRENT_FRAGMENTS"
)

# Add conditional arguments
if [ "$ALLOW_BELOW_MIN" = "true" ]; then
    CMD_ARGS+=("--allow-below-min")
fi

if [ "$ENABLE_VERBOSE" = "true" ]; then
    CMD_ARGS+=("--verbose")
fi

if [ "$EMBED_SUBTITLES" = "true" ]; then
    CMD_ARGS+=("--embed")
fi

if [ -n "$PREFERRED_CODECS" ]; then
    CMD_ARGS+=("--prefer-codecs" "$PREFERRED_CODECS")
fi

# Add format string if we have one
if [ -n "$FORMAT_STRING" ]; then
    CMD_ARGS+=("--format" "$FORMAT_STRING")
fi

echo "🚀 Starting download..."
echo "Player: $DEFAULT_PLAYER_VARIANT | Resolution: ${MIN_RES}p-${MAX_RES}p | Sleep: ${DEFAULT_SLEEP}s"

# Execute download
docker run --rm -v "$(pwd)/downloads:/downloads" yt-best-dl:latest \
    "${CMD_ARGS[@]}" \
    "$URL"

RESULT=$?

if [ $RESULT -eq 0 ]; then
    echo ""
    echo "✅ Download completed successfully!"
    
    # Show downloaded files
    VIDEO_ID=$(echo "$URL" | sed 's/.*[?&]v=//' | cut -d'&' -f1)
    echo "📁 Downloaded files:"
    ls -la downloads/ | grep "$VIDEO_ID" | while read line; do
        file=$(echo "$line" | awk '{print $9}')
        size=$(echo "$line" | awk '{print $5}')
        echo "   📄 $file ($(numfmt --to=iec --suffix=B $size 2>/dev/null || echo "$size bytes"))"
    done
else
    echo ""
    echo "❌ Download failed! Try:"
    echo "   1. Lower quality: $0 '$URL' low"
    echo "   2. Audio only: $0 '$URL' audio"  
    echo "   3. Check formats: docker run --rm -v \"\$(pwd)/downloads:/downloads\" yt-best-dl:latest --list-formats '$URL'"
fi

exit $RESULT
