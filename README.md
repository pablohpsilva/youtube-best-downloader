## YouTube Best Downloader (yt-dlp wrapper)

Minimal, high-quality YouTube downloader built on `yt-dlp` with sensible defaults and optional audio splitting. Designed to run via Docker. Includes a simple deduper for the `downloads` folder.

### TL;DR;

Build the docker image:

```
docker build -t yt-best-dl:latest .
```

Download videos

```
docker run --rm -v "$(pwd)/downloads:/downloads" yt-best-dl \
  --outdir /downloads \
  --player-variant web_embedded \
  --allow-below-min \
  --sleep-requests 5 --concurrent-fragments 1 \
  'https://www.youtube.com/watch?v=YOUTUBE_ID'
```

Download music and split the songs based on chapters

```
docker run --rm -v "$(pwd)/downloads:/downloads" yt-best-dl \
  --outdir /downloads \
  --player-variant web \
  --music \
  --split-from-chapters \
  --sleep-requests 5 \
  --concurrent-fragments 1 \
  'https://www.youtube.com/watch?v=YOUTUBE_ID'
```

### Features

- **Video**: best video+audio, smart codec preference (AV1 > VP9 > H.264), MKV mux, min 1080p by default
- **Music**: best audio to M4A with cover + metadata
- **Subtitles**: sidecar VTT, optional embed into MKV
- **Playlists**: full support with start/end slicing
- **Stability/perf**: player variant selection, sleep between requests, concurrent fragments, chunked HTTP
- **Splitting (music mode)**: manual markers/ranges or split from YouTube chapters
- **Deduplication**: remove duplicate files by YouTube ID-aware keys

## Requirements

- Docker (build and run images)

## Quick start

Build the image once:

```bash
docker build -t yt-best-dl .
```

Run it, mounting a host folder to `/downloads` (the container default outdir):

```bash
# Video (best quality, MKV)
docker run --rm -v "$(pwd)/downloads:/downloads" yt-best-dl \
  --outdir /downloads \
  https://www.youtube.com/watch?v=YOUTUBE_ID

# Music (M4A with metadata/cover)
docker run --rm -v "$(pwd)/downloads:/downloads" yt-best-dl \
  --outdir /downloads \
  --music \
  https://www.youtube.com/watch?v=YOUTUBE_ID

# Subtitles only (no media)
docker run --rm -v "$(pwd)/downloads:/downloads" yt-best-dl \
  --outdir /downloads \
  --subs-only \
  https://www.youtube.com/watch?v=YOUTUBE_ID
```

Downloads are written to the mounted `downloads/` directory. You can change the host path on the `-v` flag.

## Docker usage

```bash
docker run --rm -v "HOST_DIR:/downloads" yt-best-dl [FLAGS] URL [URL...]
```

### Core

- **positional**: one or more YouTube URLs (videos or playlists). Supports comma-separated values.
- **--outdir DIR**: output directory (default: `downloads`)
- **--video**: force video mode (default if no other mode chosen)
- **--music**: audio-only export (M4A)
- **--subs-only**: download only subtitles/captions
- **--format STR**: custom `yt-dlp` format string (overrides defaults)

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

## Examples

```bash
# Video, default settings
docker run --rm -v "$(pwd)/downloads:/downloads" yt-best-dl \
  --outdir /downloads \
  https://youtu.be/VIDEO

# Video, allow fallback below 1080p and prefer VP9 over AV1
docker run --rm -v "$(pwd)/downloads:/downloads" yt-best-dl \
  --outdir /downloads \
  --allow-below-min --prefer-codecs vp9,av01,h264 \
  https://youtu.be/VIDEO

# Video, embed subtitles + thumbnail into MKV
docker run --rm -v "$(pwd)/downloads:/downloads" yt-best-dl \
  --outdir /downloads \
  --embed --subs en pt-BR \
  https://youtu.be/VIDEO

# Playlist slice (items 3..7)
docker run --rm -v "$(pwd)/downloads:/downloads" yt-best-dl \
  --outdir /downloads \
  --playlist-start 3 --playlist-end 7 \
  "https://www.youtube.com/playlist?list=PL..."

# Music, manual split by markers
docker run --rm -v "$(pwd)/downloads:/downloads" yt-best-dl \
  --outdir /downloads \
  --music --split "0:00,1:23,3:45,5:00" \
  https://youtu.be/VIDEO

# Music, split from ranges with labels
docker run --rm -v "$(pwd)/downloads:/downloads" yt-best-dl \
  --outdir /downloads \
  --music --split "0:00-1:23=Intro,1:23-3:45=Verse,3:45-end=Outro" \
  https://youtu.be/VIDEO

# Music, split from a spec file
docker run --rm -v "$(pwd)/downloads:/downloads" yt-best-dl \
  --outdir /downloads \
  --music --split @splits.txt \
  https://youtu.be/VIDEO

# Music, split from YouTube chapters
docker run --rm -v "$(pwd)/downloads:/downloads" yt-best-dl \
  --outdir /downloads \
  --music --split-from-chapters \
  https://youtu.be/VIDEO

# Use a URLs file (mounted into the container)
docker run --rm -v "$(pwd)/downloads:/downloads" yt-best-dl \
  --outdir /downloads \
  --urls-file /downloads/urls.txt

# Comma-separated URLs on the CLI
docker run --rm -v "$(pwd)/downloads:/downloads" yt-best-dl \
  --outdir /downloads \
  "https://youtu.be/A1, https://youtu.be/B2" https://youtu.be/C3

# macOS built-in VPN by service name
docker run --rm -v "$(pwd)/downloads:/downloads" yt-best-dl \
  --outdir /downloads \
  --vpn-service "My VPN" --vpn-timeout 45 \
  https://youtu.be/VIDEO

# Third-party VPN CLI via hooks (example: Mullvad)
docker run --rm -v "$(pwd)/downloads:/downloads" yt-best-dl \
  --outdir /downloads \
  --pre-cmd "mullvad connect" --pre-wait 3 \
  --post-cmd "mullvad disconnect" \
  https://youtu.be/VIDEO

# Use cookies and proxy
docker run --rm -v "$(pwd)/downloads:/downloads" yt-best-dl \
  --outdir /downloads \
  --cookies /downloads/cookies.txt --proxy socks5://127.0.0.1:1080 \
  https://youtu.be/VIDEO

# Custom yt-dlp format expression (advanced)
docker run --rm -v "$(pwd)/downloads:/downloads" yt-best-dl \
  --outdir /downloads \
  --format "(bv*+ba/b)[protocol^=http]" \
  https://youtu.be/VIDEO
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

## Tips

- If you see 403s, try `--player-variant web_embedded` (default) or `--sleep-requests 2.5`.
- For unstable networks, add `--http-chunk-size 5M` and reduce `--concurrent-fragments`.
- Region/age-gated content often needs `--cookies`.
- On macOS, list available VPN services with: `scutil --nc list | cat`
