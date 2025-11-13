#!/bin/bash

# Flexible YouTube downloader with adjustable minimum resolution
# Usage: ./download_with_min_res.sh <URL> [min_resolution]

URL="$1"
MIN_RES="${2:-360}"  # Default to 360p if not specified

if [ -z "$URL" ]; then
    echo "Usage: $0 <YouTube_URL> [min_resolution]"
    echo ""
    echo "Examples:"
    echo "  $0 'https://youtube.com/watch?v=...'           # Try 360p minimum"
    echo "  $0 'https://youtube.com/watch?v=...' 480       # Try 480p minimum"  
    echo "  $0 'https://youtube.com/watch?v=...' 720       # Try 720p minimum"
    echo "  $0 'https://youtube.com/watch?v=...' 1080      # Try 1080p minimum"
    echo ""
    echo "Available resolutions: 144, 240, 360, 480, 720, 1080, 1440, 2160"
    exit 1
fi

echo "🎯 Downloading with minimum resolution: ${MIN_RES}p"
echo "URL: $URL"
echo "=================================================="

# Function to test download with specific min resolution
test_download() {
    local min_res=$1
    local player_variant=$2
    local format_string=$3
    
    echo "🔄 Testing ${player_variant} client with min ${min_res}p..."
    
    docker run --rm -v "$(pwd)/downloads:/downloads" yt-best-dl:latest \
        --player-variant "$player_variant" \
        --min-res "$min_res" \
        --allow-below-min \
        --max-res 2160 \
        --format "$format_string" \
        --sleep-requests 8 \
        --concurrent-fragments 1 \
        --verbose \
        "$URL"
    
    return $?
}

# Progressive quality attempts with different strategies
echo "📊 Step 1: Check what formats are available..."
docker run --rm -v "$(pwd)/downloads:/downloads" yt-best-dl:latest \
    --list-formats \
    --player-variant auto \
    "$URL" | head -20

echo ""
echo "🎬 Step 2: Attempting downloads with min ${MIN_RES}p..."

# Strategy 1: TV client with flexible format
if test_download "$MIN_RES" "tv" "best[height>=${MIN_RES}]/best[height>=720]/best[height>=480]/best[height>=360]/best"; then
    echo "✅ SUCCESS with TV client (min ${MIN_RES}p)!"
    exit 0
fi

# Strategy 2: Web client with format codes
echo "🌐 Trying web client with format fallbacks..."
if test_download "$MIN_RES" "web" "22/136+140/135+140/134+140/18/best[height>=${MIN_RES}]/best"; then
    echo "✅ SUCCESS with web client!"
    exit 0
fi

# Strategy 3: iOS client
echo "📱 Trying iOS client..."
if test_download "$MIN_RES" "ios" "best[height>=${MIN_RES}]/best[height>=360]/best"; then
    echo "✅ SUCCESS with iOS client!"
    exit 0
fi

# Strategy 4: Android client  
echo "🤖 Trying Android client..."
if test_download "$MIN_RES" "android" "best[height>=${MIN_RES}]/best[height>=360]/best"; then
    echo "✅ SUCCESS with Android client!"
    exit 0
fi

# Strategy 5: Lower the minimum progressively
if [ "$MIN_RES" -gt 360 ]; then
    echo ""
    echo "⬇️ Trying lower quality thresholds..."
    
    for lower_res in 720 480 360; do
        if [ "$lower_res" -lt "$MIN_RES" ]; then
            echo "📉 Attempting with ${lower_res}p minimum..."
            if test_download "$lower_res" "auto" "best[height>=${lower_res}]/best"; then
                echo "✅ SUCCESS with ${lower_res}p minimum!"
                exit 0
            fi
        fi
    done
fi

# Last resort: any quality
echo ""
echo "🆘 Last resort: downloading any available quality..."
docker run --rm -v "$(pwd)/downloads:/downloads" yt-best-dl:latest \
    --format "best" \
    --player-variant web_embedded \
    --sleep-requests 10 \
    "$URL"

if [ $? -eq 0 ]; then
    echo "⚠️ Downloaded with whatever quality was available (likely 360p)"
else
    echo "❌ All download attempts failed!"
    exit 1
fi

echo ""
echo "📁 Downloaded files:"
ls -la downloads/ | grep "$(echo "$URL" | sed 's/.*[?&]v=//' | cut -d'&' -f1)" || echo "No files found"
