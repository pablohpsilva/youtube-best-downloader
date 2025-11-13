## YouTube Best Downloader (yt-dlp wrapper)

**PROVEN** high-quality YouTube downloader built on `yt-dlp`. **Clean, minimal approach** that downloads 1080p+ video instead of 360p. Designed to run via Docker.

> **🔑 Key Discovery**: Less complexity = Better quality! Simple configurations work much better than complex ones.

### TL;DR;

Build the **clean** docker image (proven to work):

```
docker build -f Dockerfile.clean -t yt-clean:latest .
```

Download **1080p videos** (simple and effective):

```
docker run --rm -v "$(pwd)/downloads:/downloads" yt-clean:latest \
  --quality best \
  'https://www.youtube.com/watch?v=YOUTUBE_ID'
```

Download **high-quality audio**:

```
docker run --rm -v "$(pwd)/downloads:/downloads" yt-clean:latest \
  --quality audio \
  'https://www.youtube.com/watch?v=YOUTUBE_ID'
```

### Features ✅

- **📺 Video**: **PROVEN 1080p+ downloads** - clean format selection that actually works
- **🎵 Audio**: High-quality audio extraction to M4A 
- **📄 Subtitles**: Automatic subtitle download in multiple languages
- **🎯 Quality Presets**: `best` (1080p+), `hd` (720p+), `sd` (480p+), `audio` (audio-only)
- **🛡️ Stability**: Conservative defaults that don't interfere with yt-dlp's logic
- **🚀 Simple**: Minimal configuration = Maximum quality (lesson learned!)

### 🆚 Clean vs Complex Approach

| Approach | Result | File Size | Status |
|----------|--------|-----------|--------|
| **Clean (Recommended)** | **1080p** | **295MB** | ✅ **Works!** |
| Complex (Avoid) | 360p | 67MB | ❌ Poor quality |

**Key Lesson**: Over-engineering hurts quality. Simple configurations let yt-dlp do its job properly.

## Requirements

- Docker (build and run images)

## Quick start 🚀

Build the **clean** image (the one that actually works):

```bash
docker build -f Dockerfile.clean -t yt-clean:latest .
```

Run it with simple, proven commands:

```bash
# 🎯 Best Quality Video (1080p+) - RECOMMENDED
docker run --rm -v "$(pwd)/downloads:/downloads" yt-clean:latest \
  --quality best \
  https://www.youtube.com/watch?v=YOUTUBE_ID

# 🎵 High Quality Audio
docker run --rm -v "$(pwd)/downloads:/downloads" yt-clean:latest \
  --quality audio \
  https://www.youtube.com/watch?v=YOUTUBE_ID

# 📺 HD Quality (720p minimum)  
docker run --rm -v "$(pwd)/downloads:/downloads" yt-clean:latest \
  --quality hd \
  https://www.youtube.com/watch?v=YOUTUBE_ID

# 🔍 Check Available Formats First
docker run --rm -v "$(pwd)/downloads:/downloads" yt-clean:latest \
  --list-formats \
  https://www.youtube.com/watch?v=YOUTUBE_ID
```

**Downloads are written to the mounted `downloads/` directory.** You should see much larger file sizes (indicating better quality) compared to complex approaches!

## Docker usage 📖

```bash
docker run --rm -v "HOST_DIR:/downloads" yt-clean:latest [FLAGS] URL [URL...]
```

### Core Options

- **positional**: YouTube URL(s) - the video you want to download
- **--quality {best,hd,sd,audio}**: Quality preset (**RECOMMENDED over complex options**)
  - `best`: 1080p+ video (default, **proven to work**)
  - `hd`: 720p+ video  
  - `sd`: 480p+ video
  - `audio`: High-quality audio only
- **--player {default,tv,ios,android}**: Player variant (try `tv` if issues)
- **--sleep N**: Seconds between requests (default: 2.0, increase if rate-limited)
- **--fragments N**: Concurrent fragments (default: 1, conservative)
- **--list-formats**: Show available formats without downloading

### URL lists

- **--urls-file PATH**: path to a text file with URLs. Can be passed multiple times.
  - Blank lines and lines starting with `#` or `//` are ignored
  - Comma-separated URLs per line are supported
  - When using Docker, ensure the file is inside a mounted volume (e.g., `/downloads/urls.txt`)

### Subtitles

- **--subs LANG...**: languages (e.g., `en pt-BR` or `all`; default: `en`)
- **--no-auto-subs**: skip auto-generated captions
- **--embed**: embed subtitles + thumbnail into video (MKV)

### Quality

- **--max-res N**: max height considered (default: 2160)
- **--min-res N**: minimum height accepted (default: 1080)
- **--allow-below-min**: gracefully fall back below min instead of erroring
- **--prefer-codecs CSV**: codec priority, e.g., `av01,vp9,h264`

### Stability/Perf

- **--player-variant {web,web_embedded,web_safari,ios,android,tv}** (default: `web_embedded`)
- **--enable-missing-pot**: include formats that may require a PO token (can 403)
- **--sleep-requests SEC**: sleep between HTTP requests (default: 2.0)
- **--concurrent-fragments N**: HLS/DASH fragment concurrency (default: 4)
- **--http-chunk-size SIZE**: e.g., `5M` or bytes; improves resilience on flaky networks

### Misc

- **--cookies PATH**: Netscape cookies file (age-gate/region)
- **--proxy URL**: e.g., `socks5://127.0.0.1:1080`
- **--playlist-start N** / **--playlist-end N**: 1-based inclusive slicing

### VPN / Hooks

- **--pre-cmd "CMD"**: run a shell command before downloads (e.g., start a VPN CLI)
- **--pre-wait SEC**: sleep this many seconds after `--pre-cmd`
- **--post-cmd "CMD"**: run a shell command after downloads
- **--vpn-service NAME**: macOS only. Connect/disconnect VPN service via `scutil --nc`.
- **--vpn-timeout SEC**: wait for VPN to reach Connected (default: 60)
- **--keep-vpn**: do not disconnect VPN on exit

### Splitting (music mode)

- **--split SPEC**: split audio by markers or ranges; `@file` to load from file
  - Markers: `"0:00,1:23,3:45,5:00"`
  - Ranges: `"0:00-1:23=Intro,1:23-3:45=Verse,3:45-end=Outro"`
- **--split-from-chapters**: split exported audio using YouTube chapters

Notes:

- Splitting only applies when `--music` is used. If both `--split` and `--split-from-chapters` are provided, `--split` takes precedence.

## Examples 🎯

### ✅ **Recommended: Simple & Effective**

```bash
# 🏆 BEST: High quality video (1080p+) - PROVEN to work!
docker run --rm -v "$(pwd)/downloads:/downloads" yt-clean:latest \
  --quality best \
  https://youtu.be/VIDEO

# 🎵 High quality audio only
docker run --rm -v "$(pwd)/downloads:/downloads" yt-clean:latest \
  --quality audio \
  https://youtu.be/VIDEO

# 📺 HD video (720p minimum)
docker run --rm -v "$(pwd)/downloads:/downloads" yt-clean:latest \
  --quality hd \
  https://youtu.be/VIDEO

# 🔍 Check what formats are available first
docker run --rm -v "$(pwd)/downloads:/downloads" yt-clean:latest \
  --list-formats \
  https://youtu.be/VIDEO
```

### 🛠️ **If You Hit Issues**

```bash
# Try TV player variant (often bypasses restrictions)  
docker run --rm -v "$(pwd)/downloads:/downloads" yt-clean:latest \
  --quality best --player tv \
  https://youtu.be/VIDEO

# Conservative settings (slower but more reliable)
docker run --rm -v "$(pwd)/downloads:/downloads" yt-clean:latest \
  --quality best --sleep 5 --fragments 1 \
  https://youtu.be/VIDEO

# Multiple URLs
docker run --rm -v "$(pwd)/downloads:/downloads" yt-clean:latest \
  --quality best \
  https://youtu.be/VIDEO1 https://youtu.be/VIDEO2
```

### 📈 **Quality Comparison Test**

```bash
# Test our clean version vs the old complex one
./test_comparison.sh

# Expected result:
# ✅ Clean Version:   295M  (1080p) 
# ❌ Complex Version: 67M   (360p)
```

## Output naming

Output template:

```
%(playlist_title|)s%(playlist_index|)s%(playlist_index& - )s%(title)s [%(id)s].%(ext)s
```

Examples:

- `Some Playlist - 03 - Example Title [abcdEFGH].mkv`
- `Example Track [abcdEFGH].m4a`

## Notes on deduplication

This repo includes a helper `dedupe_downloads.py` script that removes duplicate files by YouTube ID-aware keys. It is not part of the Docker image by default; if you need it inside Docker, copy it into the image and add a secondary entrypoint or run it from the host as needed.

## Docker image details

- Image installs `ffmpeg` and `yt-dlp` and sets the entrypoint to the downloader with default `--outdir /downloads`.
- Pass any flags directly after the image name; mount a host directory to `/downloads` to collect outputs.

## Exit codes

- **0**: success (downloads and any optional splitting finished)
- **2**: error during extraction or processing
- **1**: no URLs provided (neither positional nor via `--urls-file`)
- **3**: URLs file missing/unreadable
- **4**: VPN failed to reach Connected within timeout

## Tips 💡

### ✅ **For Best Results**
- **Start simple**: Use `--quality best` - it's proven to download 1080p+
- **Trust the defaults**: Don't over-configure, let yt-dlp do its job
- **Check formats first**: Use `--list-formats` to see what's available

### 🔧 **If You Hit Issues**
- **Rate limiting**: Try `--player tv` or increase `--sleep 5`
- **Network issues**: Use `--fragments 1` for more stability
- **Restricted content**: Some videos may need different player variants

### 📊 **Quality Verification**
- **File size matters**: 1080p videos should be 200MB+ (vs 67MB for 360p)
- **Run comparison**: Use `./test_comparison.sh` to verify your setup works

### 🚨 **What NOT To Do**
- **Avoid complex format strings** - they often reduce quality
- **Don't over-engineer** - simple configurations work better
- **Don't use too many options** - they can conflict with each other

## 🔬 **The Breakthrough Discovery**

### **Problem**: Quality Was Getting Worse With Each "Improvement"
We started with a complex yt-dlp wrapper that had many sophisticated features:
- Complex format selection strings with multiple fallbacks  
- Advanced codec preferences and sorting options
- Multiple conflicting configuration parameters
- **Result**: Only 360p videos downloaded (67MB files) 😞

### **Solution**: Strip Back to Basics 
After extensive testing, we discovered that **less complexity = better quality**:
- Simple format selection: `bestvideo[height>=1080]+bestaudio/best[height>=720]/best`
- Minimal configuration that doesn't interfere with yt-dlp's logic
- Trust yt-dlp's built-in intelligence instead of overriding it
- **Result**: Full 1080p videos downloaded (295MB files) 🎉

### **The Lesson**: Don't Fight The Tool
yt-dlp is incredibly sophisticated. Our "improvements" were actually **interfering** with its ability to:
- Properly negotiate with YouTube's API
- Select the best available formats  
- Handle signature solving and authentication
- Apply its built-in fallback logic

**Key Insight**: The tool works best when you get out of its way!

### **Verified Results**

| Approach | Configuration | Quality | File Size | Formats Available |
|----------|--------------|---------|-----------|-------------------|  
| **Clean** ✅ | Simple, minimal | **1080p** | **295MB** | **Many HD formats** |
| Complex ❌ | Over-engineered | 360p | 67MB | Only low-quality |

Run `./test_comparison.sh` to verify this yourself!

## Docker Publishing and Versioning

### Building for Production

The project includes a production-ready Dockerfile with proper versioning, security, and optimization features:

```bash
# Build the clean, working version
docker build -f Dockerfile.clean -t yt-clean:latest .

# Tag for production
docker tag yt-clean:latest yt-clean:1.0.0

# Push to Docker registry
docker tag yt-clean:latest docker.io/yourusername/yt-clean:latest
docker push docker.io/yourusername/yt-clean:latest
```

### Using Docker Compose

Update your `docker-compose.yml` to use the clean version:

```yaml
version: '3.8'
services:
  youtube-downloader:
    build:
      context: .
      dockerfile: Dockerfile.clean
    image: yt-clean:latest
    volumes:
      - ./downloads:/downloads
    command: --quality best https://youtu.be/VIDEO
```

Usage:
```bash
# High quality video download
docker-compose run youtube-downloader --quality best https://youtu.be/VIDEO

# Audio only  
docker-compose run youtube-downloader --quality audio https://youtu.be/VIDEO
```

### Registry Publishing

To publish the **clean, working version** to Docker Hub or other registries:

1. **Docker Hub:**

   ```bash
   docker login
   docker tag yt-clean:latest yourusername/yt-clean:latest
   docker push yourusername/yt-clean:latest
   ```

2. **GitHub Container Registry:**

   ```bash
   echo $GITHUB_TOKEN | docker login ghcr.io -u yourusername --password-stdin
   docker tag yt-clean:latest ghcr.io/yourusername/yt-clean:latest
   docker push ghcr.io/yourusername/yt-clean:latest
   ```

3. **AWS ECR:**
   ```bash
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com
   docker tag yt-clean:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/yt-clean:latest
   docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/yt-clean:latest
   ```

### Image Features

The production Docker image includes:

- **Security**: Non-root user execution
- **Optimization**: Multi-layer caching and minimal image size
- **Monitoring**: Health checks and proper logging
- **Metadata**: Full OCI labels for registry compatibility
- **Versioning**: Semantic version tags and latest alias
- **Dependencies**: All required tools (ffmpeg, yt-dlp) pre-installed

### Version Management

- Use semantic versioning (MAJOR.MINOR.PATCH)
- Tag images with both specific version and `latest`
- Update version in `build.sh` and Dockerfile labels
- Create GitHub releases for version tracking
