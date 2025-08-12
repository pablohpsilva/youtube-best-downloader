#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
YouTube Best-Quality Downloader (video/music/subtitles) using yt-dlp.

Defaults:
- Best video+audio (DASH-preferred), mux to MKV
- Prefers AV1 > VP9 > anything, up to 2160p with smart sorting
- Enforces minimum resolution >= 1080p by default (use --allow-below-min to relax)
- Sidecar .vtt subtitles kept (no embed)
- Player variant: web_embedded (often bypasses SABR), 2s request sleep
- Playlists supported

Modes:
- (default) Video
- --music        : audio-only (M4A) with cover + metadata
- --subs-only    : download captions only (no media)

Splitting:
- --split "markers or ranges"    (manual)
- --split-from-chapters          (use YouTube chapters as tracklist)

Prereqs:
  pip install yt-dlp
  ffmpeg must be installed and in PATH
"""

import argparse
import os
import sys
import time
from typing import Dict, Any, List, Tuple
import yt_dlp

from helpers import progress_hook, safe_label, parse_splits, chapters_to_cuts
from url_list import read_urls_from_file, expand_comma_separated
from vpn import run_shell_command, macos_vpn_connect, macos_vpn_disconnect
from download_video import build_video_opts
from download_music import build_music_opts, ffmpeg_split, find_audio_outputs
from download_subs import build_subs_only_opts




# ----------------------- yt-dlp option builders -----------------------

def build_common_opts(args) -> Dict[str, Any]:
    outtmpl = os.path.join(
        args.outdir,
        "%(playlist_title|)s%(playlist_index|)s%(playlist_index& - )s%(title)s [%(id)s].%(ext)s"
    )

    sub_langs = ["all"] if args.sub_langs == ["all"] else args.sub_langs
    write_auto = not args.no_auto_subs

    yt_args: Dict[str, Dict[str, List[str]]] = {"youtube": {"player_client": [args.player_variant]}}
    if args.enable_missing_pot:
        yt_args["youtube"]["formats"] = ["missing_pot"]

    opts: Dict[str, Any] = {
        "outtmpl": outtmpl,
        "noprogress": False,
        "progress_hooks": [progress_hook],
        "merge_output_format": "mkv",
        "writesubtitles": True,
        "writeautomaticsub": write_auto,
        "subtitleslangs": sub_langs,
        "subtitlesformat": "best",
        "quiet": False,
        "continuedl": True,
        "retries": 5,
        "ignoreerrors": True,
        "concurrent_fragments": args.concurrent_fragments,
        "overwrites": False,
        "clean_infojson": True,
        "sleep_interval_requests": args.sleep_requests,
        "extractor_args": yt_args,
    }

    if args.http_chunk_size:
        opts["http_chunk_size"] = args.http_chunk_size  # supports "5M" or integer bytes

    if args.cookies:
        opts["cookiefile"] = args.cookies
    if args.proxy:
        opts["proxy"] = args.proxy

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
        opts["writethumbnail"] = True

    if args.playlist_start:
        opts["playliststart"] = args.playlist_start
    if args.playlist_end:
        opts["playlistend"] = args.playlist_end

    return opts




# ----------------------- driver -----------------------

def parse_args():
    p = argparse.ArgumentParser(
        description="Download best-quality video/music + subtitles from YouTube (via yt-dlp)."
    )
    p.add_argument(
        "urls",
        nargs="*",
        help="YouTube video/playlist URLs (supports comma-separated values)",
    )
    p.add_argument("--outdir", default="downloads", help="Output directory (default: downloads)")

    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--video", action="store_true", help="Force video mode (default)")
    mode.add_argument("--music", action="store_true", help="Music-only (extract best audio)")
    mode.add_argument("--subs-only", action="store_true", help="Download only subtitles/captions")

    p.add_argument("--format", help="(Optional) Custom yt-dlp format string; overrides defaults")

    # Subtitles
    p.add_argument(
        "--subs",
        dest="sub_langs",
        nargs="+",
        default=["en"],
        help="Subtitle languages (e.g., en pt-BR) or 'all' (default: en)",
    )
    p.add_argument("--no-auto-subs", action="store_true", help="Don't download auto-generated caps")

    # Embedding OFF by default
    p.add_argument("--embed", action="store_true", help="Embed subtitles & thumbnail into video")

    # Quality knobs
    p.add_argument("--max-res", type=int, default=2160, help="Max video height (default: 2160)")
    p.add_argument("--min-res", type=int, default=1080, help="Minimum video height (default: 1080)")
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
    p.add_argument("--http-chunk-size", help="Max size per HTTP chunk, e.g., 5M or 5242880 bytes")

    # Misc
    p.add_argument("--cookies", help="Path to Netscape-format cookies file (for age/region)")
    p.add_argument("--proxy", help="Proxy, e.g., socks5://127.0.0.1:1080")
    p.add_argument("--playlist-start", type=int, help="Playlist start index (1-based)")
    p.add_argument("--playlist-end", type=int, help="Playlist end index (inclusive)")

    # URL lists
    p.add_argument(
        "--urls-file",
        dest="urls_files",
        action="append",
        help=(
            "Path to a text file with URLs (one per line, commas allowed per line). "
            "Can be given multiple times."
        ),
    )

    # VPN / command hooks
    p.add_argument("--pre-cmd", help="Shell command to run before downloads (e.g., start VPN)")
    p.add_argument("--post-cmd", help="Shell command to run after downloads")
    p.add_argument("--pre-wait", type=float, default=0.0, help="Seconds to wait after --pre-cmd")
    p.add_argument("--vpn-service", help="macOS VPN service name to connect via 'scutil --nc'")
    p.add_argument("--vpn-timeout", type=float, default=60.0, help="Seconds to wait for VPN connect")
    p.add_argument("--keep-vpn", action="store_true", help="Do not disconnect VPN on exit")

    # Splitting
    p.add_argument("--split", help="Split spec (markers or ranges). Use @file to read from file")
    p.add_argument("--split-from-chapters", action="store_true",
                   help="In --music mode, split exported audio using YouTube chapters")

    return p.parse_args()


def main():
    args = parse_args()
    os.makedirs(args.outdir, exist_ok=True)

    # Run pre-cmd if provided
    if args.pre_cmd:
        rc = run_shell_command(args.pre_cmd)
        if rc != 0:
            print("[ERR] --pre-cmd failed; aborting.", file=sys.stderr)
            sys.exit(rc)
        if args.pre_wait and args.pre_wait > 0:
            time.sleep(args.pre_wait)

    # Optionally bring up VPN (macOS)
    vpn_started_here = False
    if args.vpn_service:
        ok = macos_vpn_connect(args.vpn_service, args.vpn_timeout)
        if not ok:
            sys.exit(4)
        vpn_started_here = True

    # Build final URL list from CLI and files
    final_urls: List[str] = []
    if args.urls:
        final_urls.extend(expand_comma_separated(args.urls))
    if getattr(args, "urls_files", None):
        for path in args.urls_files:
            final_urls.extend(read_urls_from_file(path))
    # de-duplicate while preserving order
    final_urls = list(dict.fromkeys([u for u in final_urls if u and u.strip()]))
    if not final_urls:
        print("[ERR] No URLs provided. Pass positional URLs or --urls-file.", file=sys.stderr)
        sys.exit(1)

    base = build_common_opts(args)

    # Determine opts per mode
    if args.subs_only:
        opts = build_subs_only_opts(args, base)
    elif args.music:
        opts = build_music_opts(args, base)
    else:
        if args.format:
            o = dict(base)
            o.update({"format": args.format, "postprocessor_args": []})
            opts = o
        else:
            opts = build_video_opts(args, base)

    # Use extract_info so we can capture ids/durations and later locate files
    outputs: List[Dict[str, Any]] = []
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            for url in final_urls:
                info = ydl.extract_info(url, download=True)
                if info is None:
                    continue
                if "entries" in info and info["entries"]:
                    for e in info["entries"]:
                        if e:
                            outputs.append(e)
                else:
                    outputs.append(info)

        # Post step: split audio (music mode)
        if args.music:
            for info in outputs:
                vid = info.get("id")
                duration = info.get("duration")
                if not vid:
                    continue

                # precedence: manual --split overrides chapters
                cuts: List[Tuple[float, float, str]] = []
                if args.split:
                    try:
                        cuts = parse_splits(args.split, duration)
                    except Exception as e:
                        print(f"[ERR] Bad --split spec: {e}", file=sys.stderr)
                elif args.split_from_chapters:
                    cuts = chapters_to_cuts(info)
                    if not cuts:
                        print(f"[WARN] No chapters found for [{vid}]; nothing to split.", file=sys.stderr)

                if not cuts:
                    # nothing to do for this item
                    continue

                candidates = find_audio_outputs(args.outdir, vid)
                if not candidates:
                    print(f"[WARN] No audio file found for [{vid}] to split.", file=sys.stderr)
                    continue

                input_audio = max(candidates, key=lambda p: os.path.getmtime(p))
                title = info.get("title") or "track"
                stem = safe_label(f"{title} [{vid}]")
                print(f"[INFO] Splitting into {len(cuts)} segment(s)…")
                made = ffmpeg_split(input_audio, args.outdir, stem, cuts)
                if made:
                    print(f"[DONE] Created {len(made)} files.")
                else:
                    print(f"[WARN] No segments were created for [{vid}].", file=sys.stderr)

        print("\n✅ Done.")
        sys.exit(0)
    finally:
        # Always run post-cmd and optionally bring VPN down
        if args.post_cmd:
            run_shell_command(args.post_cmd)
        if args.vpn_service and vpn_started_here and not args.keep_vpn:
            macos_vpn_disconnect(args.vpn_service)


if __name__ == "__main__":
    main()
