#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Clean YouTube Downloader - Back to basics, built right
Focused on quality over complexity
"""

import argparse
import os
import sys
import yt_dlp
from typing import Dict, Any

def progress_hook(d):
    if d['status'] == 'downloading':
        percent = d.get('_percent_str', 'N/A')
        speed = d.get('_speed_str', 'N/A')
        print(f"\r[DL] {percent} at {speed}", end='', flush=True)
    elif d['status'] == 'finished':
        print(f"\n[DL] Download finished, now post-processing…")

def build_opts(args) -> Dict[str, Any]:
    """Build yt-dlp options with minimal interference"""
    
    # Output template  
    outtmpl = os.path.join(
        args.outdir,
        "%(title)s [%(id)s].%(ext)s"
    )
    
    # Base options - keep it simple
    opts = {
        "outtmpl": outtmpl,
        "progress_hooks": [progress_hook],
        "writesubtitles": True,
        "writeautomaticsub": True,
        "subtitleslangs": ["en"],
        "writethumbnail": True,
        "sleep_interval_requests": args.sleep,
        "concurrent_fragments": args.fragments,
    }
    
    # Quality selection - prioritize resolution over stability
    if args.quality == "best":
        opts["format"] = "bestvideo[height>=1080]+bestaudio/best[height>=1080]/bestvideo[height>=720]+bestaudio/best[height>=720]/best"
    elif args.quality == "hd":
        opts["format"] = "best[height>=720]/best"  
    elif args.quality == "sd":
        opts["format"] = "best[height>=480]/best"
    elif args.quality == "audio":
        opts["format"] = "bestaudio/best"
        opts["postprocessors"] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'm4a',
            'preferredquality': '0',
        }]
    else:  # any
        opts["format"] = "best"
    
    # Player variant
    if args.player != "default":
        opts["extractor_args"] = {
            "youtube": {
                "player_client": [args.player]
            }
        }
    
    return opts

def main():
    parser = argparse.ArgumentParser(description="Clean YouTube Downloader")
    parser.add_argument("url", help="YouTube URL")
    parser.add_argument("--outdir", default="downloads", help="Output directory")
    parser.add_argument("--quality", choices=["best", "hd", "sd", "any", "audio"], 
                       default="best", help="Quality preset")
    parser.add_argument("--player", choices=["default", "web", "tv", "ios", "android"],
                       default="default", help="Player variant") 
    parser.add_argument("--sleep", type=float, default=2.0, help="Sleep between requests")
    parser.add_argument("--fragments", type=int, default=1, help="Concurrent fragments")
    parser.add_argument("--list-formats", action="store_true", help="List available formats")
    
    args = parser.parse_args()
    
    os.makedirs(args.outdir, exist_ok=True)
    
    opts = build_opts(args)
    
    if args.list_formats:
        opts["listformats"] = True
        
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([args.url])
        print("\n✅ Success!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
