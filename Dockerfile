# YouTube Best Downloader - Production Docker Image
# Multi-stage build for optimization
FROM python:3.12-slim as base

# Build arguments for dynamic versioning
ARG VERSION=1.0.0
ARG BUILD_DATE
ARG VCS_REF

# Metadata labels for publishing
LABEL maintainer="YouTube Python Project"
LABEL version="${VERSION}"
LABEL description="Minimal, high-quality YouTube downloader built on yt-dlp with sensible defaults"
LABEL org.opencontainers.image.title="YouTube Best Downloader"
LABEL org.opencontainers.image.description="Advanced YouTube downloader with audio splitting and subtitle support"
LABEL org.opencontainers.image.version="${VERSION}"
LABEL org.opencontainers.image.source="https://github.com/username/youtube-python"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.created="${BUILD_DATE}"
LABEL org.opencontainers.image.revision="${VCS_REF}"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    XDG_CACHE_HOME=/home/ytdl/.cache \
    PATH=/usr/bin:$PATH \
    NODE_PATH=/usr/lib/node_modules

# Install system dependencies in a single layer
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ffmpeg \
        ca-certificates \
        curl \
        nodejs \
        npm && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get autoremove -y && \
    apt-get clean

# Create non-root user for security
RUN groupadd -r ytdl && useradd -r -g ytdl -m -d /home/ytdl -s /bin/false ytdl

# Set working directory
WORKDIR /app

# Copy and install Python requirements first (for better caching)
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Ensure yt-dlp can find Node.js for JavaScript execution
RUN which node && node --version

# Copy application code
COPY *.py /app/

# Create downloads and cache directories and set permissions
RUN mkdir -p /downloads /home/ytdl/.cache/yt-dlp && \
    chown -R ytdl:ytdl /app /downloads /home/ytdl

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import yt_dlp; print('OK')" || exit 1

# Switch to non-root user
USER ytdl

# Expose volume for downloads
VOLUME ["/downloads"]

# Set default entry point with baked outdir
ENTRYPOINT ["python", "/app/yt_best_downloader.py", "--outdir", "/downloads"]