#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
YouTube Best-Quality Downloader (video/music/subtitles) using yt-dlp.

Defaults:
- Best video+audio (DASH-preferred), mux to MKV
- Prefers AV1 > VP9 > anything, up to 2160p with smart sorting
- Enforces minimum resolution >= 1080p by default (errors if not available)
- Sidecar .vtt subtitles kept (no embed)
- Player variant: web_embedded (often bypasses SABR), 2s request sleep
- Playlists supported

Modes:
- (default) Video
- --music        : audio-only (M4A) with cover + metadata
- --subs-only    : download captions only (no media)

Prereqs:
  pip install yt-dlp
  ffmpeg must be installed and in PATH
"""

import argparse
import os
import sys
from typing import Dict, Any, List, Optional
import yt_dlp


def human_size(n: Optional[float]) -> str:
    if n is None:
        return "unknown"
    units = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while n >= 1024 and i < len(units) - 1:
        n /= 1024
        i += 1
    return f"{n:.2f}{units[i]}"


def progress_hook(d: Dict[str, Any]):
    status = d.get("status")
    if status == "downloading":
        total = d.get("total_bytes") or d.get("total_bytes_estimate")
        downloaded = d.get("downloaded_bytes", 0)
        speed = d.get("speed")
        eta = d.get("eta")
        msg = f"[DL] {human_size(downloaded)}/{human_size(total)}"
        if speed:
            msg += f" at {human_size(speed)}/s"
        if eta:
            msg += f", ETA {eta}s"
        print(msg, end="\r", flush=True)
    elif status == "finished":
        print("\n[DL] Download finished, now post-processing…")
    elif status == "error":
        print("\n[ERR] A download error occurred.")


def build_common_opts(args) -> Dict[str, Any]:
    # Output template: include playlist info if present; include ID to avoid collisions
    outtmpl = os.path.join(
        args.outdir,
        "%(playlist_title|)s%(playlist_index|)s%(playlist_index& - )s%(title)s [%(id)s].%(ext)s"
    )

    sub_langs = ["all"] if args.sub_langs == ["all"] else args.sub_langs
    write_auto = not args.no_auto_subs

    # Build extractor_args with chosen player variant and optional missing_pot
    yt_args: Dict[str, Dict[str, List[str]]] = {"youtube": {"player_client": [args.player_variant]}}
    if args.enable_missing_pot:
        yt_args["youtube"]["formats"] = ["missing_pot"]

    opts: Dict[str, Any] = {
        "outtmpl": outtmpl,
        "noprogress": False,
        "progress_hooks": [progress_hook],
        "merge_output_format": "mkv",  # safest for mixed codecs + subs
        "writesubtitles": True,
        "writeautomaticsub": write_auto,
        "subtitleslangs": sub_langs,
        "subtitlesformat": "best",
        "quiet": False,
        "continuedl": True,
        "retries": 5,
        "ignoreerrors": True,                          # continue through playlist errors
        "concurrent_fragments": args.concurrent_fragments,
        "overwrites": False,
        "clean_infojson": True,
        "sleep_interval_requests": args.sleep_requests,
        "extractor_args": yt_args,
    }

    if args.http_chunk_size:
        opts["http_chunk_size"] = args.http_chunk_size

    if args.cookies:
        opts["cookiefile"] = args.cookies

    if args.proxy:
        opts["proxy"] = args.proxy

    # Embedding is OFF by default; enable only if --embed is passed
    if args.embed:
        opts["embedsubtitles"] = True
        opts["postprocessors"] = [
            {"key": "FFmpegMetadata"},
            {"key": "FFmpegEmbedSubtitle"},
            {"key": "EmbedThumbnail"},
        ]
        opts["writethumbnail"] = True
    else:
        opts["embedsubtitles"] = False
        opts["writethumbnail"] = True  # still save thumbnail beside file

    # Playlist slicing
    if args.playlist_start:
        opts["playliststart"] = args.playlist_start
    if args.playlist_end:
        opts["playlistend"] = args.playlist_end

    return opts


def build_video_opts(args, base_opts: Dict[str, Any]) -> Dict[str, Any]:
    maxh = args.max_res
    minh = args.min_res
    o = dict(base_opts)

    # Build a format expression.
    # If allow_below_min = False (default), we *only* accept >= min_res (errors otherwise).
    # If allow_below_min = True, we gracefully fall back down the ladder.
    codec_order = ":".join(args.prefer_codecs.split(","))  # e.g., "av01:vp9:h264"

    if not args.allow_below_min:
        fmt = (
            f"(bv*[height>={minh}][vcodec^=av01]/"
            f" bv*[height>={minh}][vcodec^=vp9]/"
            f" bv*[height>={minh}])+"    # video-only >= min
            f"(ba[acodec^=opus]/ba)"     # pair with best audio
        )
    else:
        fmt = (
            f"(bv*[height<={maxh}][height>={minh}][vcodec^=av01]/"
            f" bv*[height<={maxh}][height>={minh}][vcodec^=vp9]/"
            f" bv*[height<={maxh}][height>={minh}]/"
            f" bv*[height<={maxh}]/"     # allow anything <= max
            f" bv*)+"                    # ultimate fallback
            f"(ba[acodec^=opus]/ba)"
        )

    o.update({
        "format": fmt,
        "format_sort": [f"res:{maxh}", "fps", f"codec:{codec_order}", "vbr", "hdr"],
        "format_sort_force": True,
        "postprocessor_args": [],
    })
    return o


def build_music_opts(args, base_opts: Dict[str, Any]) -> Dict[str, Any]:
    o = dict(base_opts)
    o.update(
        {
            "format": "bestaudio/best",
            "embedsubtitles": False,  # never embed subs in audio
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "m4a",
                    "preferredquality": "0",
                },
                {"key": "FFmpegMetadata"},
                {"key": "EmbedThumbnail"},
            ],
        }
    )
    o["writethumbnail"] = True
    return o


def build_subs_only_opts(args, base_opts: Dict[str, Any]) -> Dict[str, Any]:
    o = dict(base_opts)
    o.update({"skip_download": True, "embedsubtitles": False})
    o.pop("postprocessors", None)  # no media postprocessing
    return o


def download(urls: List[str], ydl_opts: Dict[str, Any]) -> int:
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return 0 if ydl.download(urls) == 0 else 1
    except Exception as e:
        print(f"[ERR] {e}", file=sys.stderr)
        return 2


def parse_args():
    p = argparse.ArgumentParser(
        description="Download best-quality video/music + subtitles from YouTube (via yt-dlp)."
    )
    p.add_argument("urls", nargs="+", help="YouTube video/playlist URLs")
    p.add_argument("--outdir", default="downloads", help="Output directory (default: downloads)")

    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--video", action="store_true", help="Force video mode (default)")
    mode.add_argument("--music", action="store_true", help="Music-only (extract best audio)")
    mode.add_argument("--subs-only", action="store_true", help="Download only subtitles/captions")

    p.add_argument("--format", help="(Optional) Custom yt-dlp format string; overrides defaults")

    # Subtitle defaults: English only (change as needed)
    p.add_argument(
        "--subs",
        dest="sub_langs",
        nargs="+",
        default=["en"],
        help="Subtitle languages (e.g., en pt-BR) or 'all' (default: en)",
    )
    p.add_argument("--no-auto-subs", action="store_true", help="Don't download auto-generated caps")

    # Embedding OFF by default; pass --embed to burn subs into MKV and embed cover/metadata
    p.add_argument("--embed", action="store_true", help="Embed subtitles & thumbnail into video")

    # Quality knobs
    p.add_argument("--max-res", type=int, default=2160,
                   help="Max video height to consider (default: 2160)")
    p.add_argument("--min-res", type=int, default=1080,
                   help="Minimum video height to accept (default: 1080)")
    p.add_argument("--allow-below-min", action="store_true",
                   help="Allow fallback below --min-res instead of erroring")
    p.add_argument("--prefer-codecs", default="av01,vp9,h264",
                   help="Codec priority, comma-separated (default: av01,vp9,h264)")

    # Stability/perf knobs
    p.add_argument("--player-variant",
                   choices=["web", "web_embedded", "web_safari", "ios", "android", "tv"],
                   default="web_embedded",
                   help="Specific YouTube player variant (default: web_embedded)")
    p.add_argument("--enable-missing-pot", action="store_true",
                   help="Enable formats that usually require a PO token (may 403)")
    p.add_argument("--sleep-requests", dest="sleep_requests", type=float, default=2.0,
                   help="Seconds to sleep between HTTP requests (default: 2.0)")
    p.add_argument("--concurrent-fragments", type=int, default=4,
                   help="Number of HLS/DASH fragments to fetch in parallel (default: 4)")
    p.add_argument("--http-chunk-size", default=None,
                   help="Max size per HTTP chunk, e.g., 5M, 10M (default: yt-dlp default)")

    # Misc
    p.add_argument("--cookies", help="Path to Netscape-format cookies file (for age/region)")
    p.add_argument("--proxy", help="Proxy, e.g., socks5://127.0.0.1:1080")
    p.add_argument("--playlist-start", type=int, help="Playlist start index (1-based)")
    p.add_argument("--playlist-end", type=int, help="Playlist end index (inclusive)")
    return p.parse_args()


def main():
    args = parse_args()
    os.makedirs(args.outdir, exist_ok=True)

    base = build_common_opts(args)

    if args.subs_only:
        opts = build_subs_only_opts(args, base)
    elif args.music:
        opts = build_music_opts(args, base)
    else:
        if args.format:
            # If user provided a custom format, honor it (no min-res enforcement here).
            o = dict(base)
            o.update({"format": args.format, "postprocessor_args": []})
            opts = o
        else:
            opts = build_video_opts(args, base)

    code = download(args.urls, opts)
    if code == 0:
        print("\n✅ Done.")
    else:
        print("\n⚠️ Finished with some issues. See messages above.", file=sys.stderr)
    sys.exit(code)


if __name__ == "__main__":
    main()
