#!/bin/bash

# Quality tester - helps find the best available quality for a video
# Usage: ./quality_tester.sh <YouTube_URL>

URL="$1"
if [ -z "$URL" ]; then
    echo "Usage: $0 <YouTube_URL>"
    echo "Example: $0 'https://www.youtube.com/watch?v=rGyQHyDMZZI'"
    exit 1
fi

VIDEO_ID=$(echo "$URL" | sed 's/.*[?&]v=//' | cut -d'&' -f1)

echo "🔍 YouTube Quality Tester"
echo "========================="
echo "Video: $URL"
echo "Video ID: $VIDEO_ID"
echo ""

# Test different player variants and show available formats
test_player_formats() {
    local variant=$1
    echo "📺 Testing $variant client:"
    echo "----------------------------------------"
    
    docker run --rm -v "$(pwd)/downloads:/downloads" yt-best-dl:latest \
        --list-formats \
        --player-variant "$variant" \
        "$URL" 2>/dev/null | grep -E "(ID|^[0-9]+|^[a-z]+[0-9])" | head -15
    
    echo ""
}

# Test all major player variants
for variant in tv web ios android mweb web_embedded; do
    test_player_formats "$variant"
done

echo "🎯 Quality Recommendations:"
echo "============================"
echo ""

# Test actual downloads with different quality settings
test_quality_download() {
    local min_res=$1
    local desc=$2
    
    echo "Testing ${desc} (${min_res}p minimum)..."
    
    # Use --list-formats with format filter to see what would be selected
    docker run --rm -v "$(pwd)/downloads:/downloads" yt-best-dl:latest \
        --format "best[height>=${min_res}]/best" \
        --player-variant auto \
        --simulate \
        --quiet \
        "$URL" 2>/dev/null
    
    local exit_code=$?
    if [ $exit_code -eq 0 ]; then
        echo "✅ ${desc} should work"
    else
        echo "❌ ${desc} not available"
    fi
}

# Test different quality levels
test_quality_download 1080 "Full HD"
test_quality_download 720  "HD Ready"
test_quality_download 480  "SD"
test_quality_download 360  "Low Quality"

echo ""
echo "💡 Recommended Commands:"
echo "========================"
echo ""

# Generate recommended commands based on what's likely to work
echo "# Try HD first (recommended):"
echo "./download_with_min_res.sh '$URL' 720"
echo ""

echo "# Fallback to SD if HD fails:"
echo "./download_with_min_res.sh '$URL' 480"
echo ""

echo "# Guaranteed download (any quality):"
echo "./download_with_min_res.sh '$URL' 360"
echo ""

echo "# Audio only (always works):"
echo "docker run --rm -v \"\$(pwd)/downloads:/downloads\" yt-best-dl:latest --music '$URL'"
echo ""

echo "🔧 Manual format testing:"
echo "========================="
echo ""

echo "# List all available formats:"
echo "docker run --rm -v \"\$(pwd)/downloads:/downloads\" yt-best-dl:latest --list-formats --player-variant tv '$URL'"
echo ""

echo "# Download specific format (replace 'FORMAT_ID' with actual ID):"
echo "docker run --rm -v \"\$(pwd)/downloads:/downloads\" yt-best-dl:latest --format 'FORMAT_ID' '$URL'"
echo ""

echo "# Common format IDs to try:"
echo "#   22 = 720p MP4"
echo "#   18 = 360p MP4" 
echo "#   140 = M4A audio"
echo "#   136+140 = 720p video + audio"
