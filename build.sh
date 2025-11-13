#!/bin/bash
set -e

# YouTube Best Downloader - Docker Build and Publish Script
# Usage: ./build.sh [version] [registry]

VERSION=${1:-"1.0.0"}
REGISTRY=${2:-""}
IMAGE_NAME="youtube-downloader"
FULL_IMAGE_NAME="${REGISTRY:+$REGISTRY/}${IMAGE_NAME}"

echo "🚀 Building YouTube Downloader Docker Image"
echo "Version: $VERSION"
echo "Registry: ${REGISTRY:-"local"}"
echo "Full image name: $FULL_IMAGE_NAME"
echo ""

# Build the image
echo "📦 Building Docker image..."
docker build \
  --build-arg VERSION="$VERSION" \
  --build-arg BUILD_DATE="$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
  -t "${FULL_IMAGE_NAME}:${VERSION}" \
  -t "${FULL_IMAGE_NAME}:latest" \
  .

echo "✅ Build completed successfully!"
echo ""

# Show image info
echo "📊 Image information:"
docker images "${FULL_IMAGE_NAME}" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
echo ""

# Optional: Test the image
echo "🧪 Testing image..."
if docker run --rm "${FULL_IMAGE_NAME}:${VERSION}" --help > /dev/null 2>&1; then
    echo "✅ Image test passed!"
else
    echo "❌ Image test failed!"
    exit 1
fi

# Optional: Push to registry
if [ ! -z "$REGISTRY" ]; then
    echo ""
    read -p "🚀 Push to registry $REGISTRY? (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "📤 Pushing to registry..."
        docker push "${FULL_IMAGE_NAME}:${VERSION}"
        docker push "${FULL_IMAGE_NAME}:latest"
        echo "✅ Push completed!"
        
        # Create multi-arch manifest (optional)
        read -p "🏗️  Create multi-architecture manifest? (y/N): " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "🏗️  Creating multi-arch manifest..."
            docker manifest create "${FULL_IMAGE_NAME}:${VERSION}" \
                "${FULL_IMAGE_NAME}:${VERSION}"
            docker manifest push "${FULL_IMAGE_NAME}:${VERSION}"
            echo "✅ Multi-arch manifest created!"
        fi
    fi
fi

echo ""
echo "🎉 All done!"
echo ""
echo "Usage examples:"
echo "  docker run --rm -v \"\$(pwd)/downloads:/downloads\" ${FULL_IMAGE_NAME}:${VERSION} https://youtube.com/watch?v=VIDEO_ID"
echo "  docker-compose up youtube-downloader"
echo ""
