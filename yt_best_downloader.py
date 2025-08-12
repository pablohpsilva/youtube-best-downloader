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
import re
import glob
import subprocess
from typing import Dict, Any, List, Optional, Tuple
import yt_dlp


# ----------------------- helpers -----------------------

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


def safe_label(s: str) -> str:
    s = s.strip() or "part"
    return re.sub(r'[\\/:*?"<>|]+', "_", s)


def parse_timecode(s: str) -> float:
    """Accept HH:MM:SS, MM:SS, or MM (minutes)."""
    s = s.strip()
    if not s:
        raise ValueError("empty timecode")
    parts = s.split(":")
    if len(parts) == 3:
        h, m, sec = parts
        return int(h) * 3600 + int(m) * 60 + float(sec)
    if len(parts) == 2:
        m, sec = parts
        return int(m) * 60 + float(sec)
    return float(s) * 60.0  # just minutes


def read_split_spec(spec: str) -> str:
    """Return the raw spec string; if @file, load from file."""
    spec = spec.strip()
    if spec.startswith("@"):
        path = spec[1:]
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return spec


def parse_splits(spec: str, duration: Optional[float]) -> List[Tuple[float, float, str]]:
    """
    Returns list of (start, end, label).
    Supports:
      - markers: "0:00,1:23,3:45,5:00"
      - ranges : "0:00-1:23=Intro,1:23-3:45=Verse,3:45-end=Outro"
    'end' or blank end means 'until file end' (requires duration).
    """
    raw = read_split_spec(spec)
    tokens = [t.strip() for t in re.split(r"[,\n;]+", raw) if t.strip()]
    if not tokens:
        raise ValueError("No split tokens found")

    ranges_mode = any("-" in t for t in tokens)
    cuts: List[Tuple[float, float, str]] = []

    if ranges_mode:
        for t in tokens:
            if "=" in t:
                range_part, label = t.split("=", 1)
            else:
                range_part, label = t, ""
            if "-" not in range_part:
                raise ValueError(f"Invalid range: {t}")
            start_s, end_s = [x.strip() for x in range_part.split("-", 1)]
            start = parse_timecode(start_s)
            if end_s.lower() in ("", "end"):
                if duration is None:
                    raise ValueError("End not specified and duration unknown; cannot infer end")
                end = float(duration)
            else:
                end = parse_timecode(end_s)
            if end <= start:
                raise ValueError(f"End must be > start: {t}")
            cuts.append((start, end, safe_label(label) if label else ""))
    else:
        markers = [parse_timecode(t) for t in tokens]
        markers = sorted(m for m in markers if m >= 0)
        if len(markers) < 2:
            raise ValueError("Need at least two markers to define segments")
        if duration is None:
            duration = markers[-1]
        for i in range(len(markers) - 1):
            cuts.append((markers[i], markers[i + 1], ""))
        if markers[-1] < duration:
            cuts.append((markers[-1], float(duration), ""))

    for idx, (a, b, name) in enumerate(cuts, 1):
        if not name:
            cuts[idx - 1] = (a, b, f"part{idx:02d}")
    return cuts


def chapters_to_cuts(info: Dict[str, Any]) -> List[Tuple[float, float, str]]:
    """
    Build cuts from yt-dlp's parsed chapters.
    Each cut is numbered (01, 02, …) and uses the chapter title as the label.
    """
    chapters = info.get("chapters") or []
    if not chapters:
        return []
    duration = info.get("duration")
    cuts: List[Tuple[float, float, str]] = []
    for i, ch in enumerate(chapters):
        start = float(ch.get("start_time") or 0.0)
        # figure out end: chapter's end_time, else next start, else full duration
        next_start = None
        if i + 1 < len(chapters):
            next_start = chapters[i + 1].get("start_time")
        end = ch.get("end_time") or next_start or duration or start
        end = float(end)
        if end <= start:
            continue
        title = ch.get("title") or f"part{i+1:02d}"
        label = f"{i+1:02d} - {safe_label(title)}"
        cuts.append((start, end, label))
    return cuts


def ffmpeg_split(input_path: str, outdir: str, base_stem: str,
                 cuts: List[Tuple[float, float, str]]) -> List[str]:
    """
    Split input_path into multiple files using ffmpeg, preferring stream copy.
    Falls back to re-encode if copy fails.
    """
    made: List[str] = []
    for (start, end, label) in cuts:
        out_path = os.path.join(outdir, f"{base_stem} - {label}.m4a")
        suffix = 2
        stem_only = f"{base_stem} - {label}"
        while os.path.exists(out_path):
            out_path = os.path.join(outdir, f"{stem_only} ({suffix}).m4a")
            suffix += 1

        duration = max(0.01, end - start)
        cmd_copy = [
            "ffmpeg", "-v", "error", "-nostdin", "-y",
            "-ss", f"{start}", "-t", f"{duration}",
            "-i", input_path,
            "-c", "copy", "-movflags", "+faststart",
            out_path,
        ]
        res = subprocess.run(cmd_copy, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if res.returncode != 0 or not os.path.exists(out_path) or os.path.getsize(out_path) == 0:
            cmd_re = [
                "ffmpeg", "-v", "error", "-nostdin", "-y",
                "-ss", f"{start}", "-t", f"{duration}",
                "-i", input_path,
                "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
                out_path,
            ]
            res2 = subprocess.run(cmd_re, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if res2.returncode != 0:
                print(f"[ERR] Failed to create segment {label}", file=sys.stderr)
                continue
        made.append(out_path)
        print(f"[OK] Wrote {out_path}")
    return made


def find_audio_outputs(outdir: str, video_id: str) -> List[str]:
    """
    Find audio files produced for a given video ID (pattern matches our outtmpl).
    Handles literal square brackets around the ID.
    """
    exts = ("m4a", "mp3", "opus", "aac", "flac", "wav")
    id_token = glob.escape(f"[{video_id}]")  # escape [] so glob matches literally
    matches: List[str] = []
    for ext in exts:
        pattern = os.path.join(outdir, f"*{id_token}.{ext}")
        matches.extend(glob.glob(pattern))
    return sorted(matches)


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


def build_video_opts(args, base_opts: Dict[str, Any]) -> Dict[str, Any]:
    maxh = args.max_res
    minh = args.min_res
    o = dict(base_opts)
    codec_order = ":".join(args.prefer_codecs.split(","))

    if not args.allow_below_min:
        fmt = (
            f"(bv*[height>={minh}][vcodec^=av01]/"
            f" bv*[height>={minh}][vcodec^=vp9]/"
            f" bv*[height>={minh}])+(ba[acodec^=opus]/ba)"
        )
    else:
        fmt = (
            f"(bv*[height<={maxh}][height>={minh}][vcodec^=av01]/"
            f" bv*[height<={maxh}][height>={minh}][vcodec^=vp9]/"
            f" bv*[height<={maxh}][height>={minh}]/"
            f" bv*[height<={maxh}]/ bv*)+(ba[acodec^=opus]/ba)"
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
            "embedsubtitles": False,
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
    o.pop("postprocessors", None)
    return o


# ----------------------- driver -----------------------

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

    # Splitting
    p.add_argument("--split", help="Split spec (markers or ranges). Use @file to read from file")
    p.add_argument("--split-from-chapters", action="store_true",
                   help="In --music mode, split exported audio using YouTube chapters")

    return p.parse_args()


def main():
    args = parse_args()
    os.makedirs(args.outdir, exist_ok=True)

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
            for url in args.urls:
                info = ydl.extract_info(url, download=True)
                if info is None:
                    continue
                if "entries" in info and info["entries"]:
                    for e in info["entries"]:
                        if e:
                            outputs.append(e)
                else:
                    outputs.append(info)
    except Exception as e:
        print(f"[ERR] {e}", file=sys.stderr)
        sys.exit(2)

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


if __name__ == "__main__":
    main()
