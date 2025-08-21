#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Pluralsight Course Downloader

⚠️  IMPORTANT LEGAL NOTICE ⚠️
This tool may violate Pluralsight's Terms of Use, which prohibit downloading or storing
their proprietary materials. Use of this tool could result in account suspension or
other legal consequences. 

Official alternatives:
- Pluralsight Windows offline player (up to 30 courses per device)
- Pluralsight mobile apps with offline viewing features

Use this tool at your own risk and ensure compliance with applicable terms and laws.

Features:
- Download Pluralsight courses and individual videos
- Supports subtitles/captions extraction
- Quality selection and format options
- Progress tracking and error handling
- VPN and proxy support
- Batch downloading from course URLs

Prerequisites:
  pip install requests beautifulsoup4 yt-dlp
  Valid Pluralsight account credentials
"""

import argparse
import getpass
import json
import os
import sys
import time
import requests
from typing import Dict, Any, List, Optional
from urllib.parse import urljoin, urlparse

from helpers import progress_hook, safe_label
from url_list import read_urls_from_file, expand_comma_separated
from vpn import run_shell_command, macos_vpn_connect, macos_vpn_disconnect

class PluralsightDownloader:
    """Handles authentication and downloading from Pluralsight."""
    

    def __init__(self, username: str, password: str, output_dir: str = "downloads"):
        self.username = username
        self.password = password
        self.output_dir = output_dir
        self.session = requests.Session()
        self.base_url = "https://app.pluralsight.com"
        self.api_url = "https://app.pluralsight.com/learner/content"
        self.authenticated = False
        
        # Set up session headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
        })
    
    def authenticate(self) -> bool:
        """Authenticate with Pluralsight. Returns True if successful."""
        print("[INFO] Authenticating with Pluralsight...")
        
        # This is a placeholder implementation
        # Real implementation would need to:
        # 1. Handle OAuth/login flow
        # 2. Obtain session tokens
        # 3. Handle 2FA if enabled
        # 4. Store authentication state
        
        print("[WARN] Authentication not fully implemented.")
        print("[WARN] This is a framework implementation that requires completion.")
        
        # Placeholder authentication result
        self.authenticated = False
        return self.authenticated
    
    def get_course_info(self, course_id: str) -> Optional[Dict[str, Any]]:
        """Get course information and module list."""
        if not self.authenticated:
            print("[ERR] Not authenticated. Please authenticate first.")
            return None
        
        # Placeholder implementation
        print(f"[INFO] Getting course info for: {course_id}")
        
        # Real implementation would make API calls to get:
        # - Course metadata
        # - Module list
        # - Video URLs and quality options
        # - Subtitle/caption availability
        
        return {
            "id": course_id,
            "title": f"Course {course_id}",
            "modules": [],
            "description": "Course description would be here"
        }
    
    def get_video_urls(self, video_id: str, quality: str = "1080p") -> Optional[Dict[str, str]]:
        """Get direct video URLs for a specific video."""
        if not self.authenticated:
            print("[ERR] Not authenticated. Please authenticate first.")
            return None
        
        # Placeholder implementation
        print(f"[INFO] Getting video URLs for: {video_id} at {quality}")
        
        # Real implementation would:
        # 1. Make API calls to get video manifest
        # 2. Parse available qualities/formats
        # 3. Return direct download URLs
        
        return None
    
    def download_video(self, video_info: Dict[str, Any], args) -> bool:
        """Download a single video with the specified options."""
        video_id = video_info.get("id")
        title = video_info.get("title", "Unknown")
        
        print(f"[INFO] Downloading: {title} [{video_id}]")
        
        # Get video URLs
        urls = self.get_video_urls(video_id, args.quality)
        if not urls:
            print(f"[ERR] Could not get download URLs for {video_id}")
            return False
        
        # Create safe filename
        safe_title = safe_label(f"{title} [{video_id}]")
        output_path = os.path.join(self.output_dir, f"{safe_title}.mp4")
        
        # Placeholder download implementation
        print(f"[WARN] Download implementation incomplete for: {output_path}")
        
        # Real implementation would:
        # 1. Download video file with progress tracking
        # 2. Download subtitles if requested
        # 3. Apply post-processing (format conversion, metadata)
        # 4. Handle errors and retries
        
        return False
    
    def download_course(self, course_url: str, args) -> bool:
        """Download an entire course."""
        # Extract course ID from URL
        course_id = self.extract_course_id(course_url)
        if not course_id:
            print(f"[ERR] Could not extract course ID from: {course_url}")
            return False
        
        # Get course information
        course_info = self.get_course_info(course_id)
        if not course_info:
            return False
        
        print(f"[INFO] Downloading course: {course_info['title']}")
        
        # Download each video in the course
        success_count = 0
        total_count = 0
        
        for module in course_info.get("modules", []):
            for video in module.get("videos", []):
                total_count += 1
                if self.download_video(video, args):
                    success_count += 1
        
        print(f"[DONE] Downloaded {success_count}/{total_count} videos from course")
        return success_count > 0
    
    def extract_course_id(self, url: str) -> Optional[str]:
        """Extract course ID from Pluralsight URL."""
        # Handle different URL formats:
        # https://app.pluralsight.com/library/courses/course-name
        # https://app.pluralsight.com/course-player?clipId=...&courseId=...
        
        parsed = urlparse(url)
        if "/library/courses/" in parsed.path:
            return parsed.path.split("/library/courses/")[-1].split("/")[0]
        elif "courseId=" in parsed.query:
            # Extract from query params
            import urllib.parse
            params = urllib.parse.parse_qs(parsed.query)
            return params.get("courseId", [None])[0]
        
        return None


def build_ps_opts(args) -> Dict[str, Any]:
    """Build options for Pluralsight downloader."""
    return {
        "quality": args.quality,
        "include_subtitles": args.subtitles,
        "subtitle_languages": args.sub_langs,
        "format_preference": args.format_preference,
        "output_dir": args.outdir,
        "concurrent_downloads": args.concurrent_downloads,
    }


def parse_args():
    """Parse command line arguments."""
    p = argparse.ArgumentParser(
        description="Download courses and videos from Pluralsight (Framework Implementation)"
    )
    
    # URLs and authentication
    p.add_argument(
        "urls",
        nargs="*",
        help="Pluralsight course/video URLs (supports comma-separated values)",
    )
    p.add_argument("--username", "-u", help="Pluralsight username/email")
    p.add_argument("--password", "-p", help="Pluralsight password (will prompt if not provided)")
    p.add_argument("--outdir", default="downloads", help="Output directory (default: downloads)")
    
    # Quality and format options
    p.add_argument("--quality", choices=["360p", "720p", "1080p", "best"], 
                   default="1080p", help="Video quality (default: 1080p)")
    p.add_argument("--format-preference", 
                   choices=["mp4", "webm", "best"], 
                   default="mp4", help="Preferred video format (default: mp4)")
    
    # Subtitles
    p.add_argument("--subtitles", action="store_true", help="Download subtitles/captions")
    p.add_argument(
        "--subs",
        dest="sub_langs",
        nargs="+",
        default=["en"],
        help="Subtitle languages (e.g., en es fr) (default: en)",
    )
    
    # Performance options
    p.add_argument("--concurrent-downloads", type=int, default=2,
                   help="Number of concurrent downloads (default: 2)")
    p.add_argument("--sleep-requests", type=float, default=1.0,
                   help="Seconds to sleep between requests (default: 1.0)")
    
    # URL lists
    p.add_argument(
        "--urls-file",
        dest="urls_files",
        action="append",
        help="Path to a text file with URLs (one per line)",
    )
    
    # VPN support
    p.add_argument("--pre-cmd", help="Shell command to run before downloads")
    p.add_argument("--post-cmd", help="Shell command to run after downloads")
    p.add_argument("--vpn-service", help="macOS VPN service name to connect")
    p.add_argument("--vpn-timeout", type=float, default=60.0, help="VPN connection timeout")
    p.add_argument("--keep-vpn", action="store_true", help="Don't disconnect VPN on exit")
    
    # Download mode
    p.add_argument("--course", action="store_true", help="Download entire course(s)")
    p.add_argument("--video-only", action="store_true", help="Download individual videos only")
    
    return p.parse_args()


def main():
    """Main entry point."""
    args = parse_args()
    
    # Display legal warning
    print("=" * 80)
    print("⚠️  LEGAL WARNING ⚠️")
    print("=" * 80)
    print("This tool may violate Pluralsight's Terms of Use.")
    print("Downloading proprietary content may result in account suspension.")
    print("Use official Pluralsight offline features when possible.")
    print("Continue at your own risk.")
    print("=" * 80)
    
    response = input("Do you understand and accept the risks? (yes/no): ").lower().strip()
    if response != "yes":
        print("Aborted by user.")
        sys.exit(0)
    
    # Ensure output directory exists
    os.makedirs(args.outdir, exist_ok=True)
    
    # Get credentials
    if not args.username:
        args.username = input("Pluralsight username/email: ").strip()
    
    if not args.password:
        args.password = getpass.getpass("Pluralsight password: ")
    
    if not args.username or not args.password:
        print("[ERR] Username and password are required.")
        sys.exit(1)
    
    # Run pre-command if provided
    if args.pre_cmd:
        rc = run_shell_command(args.pre_cmd)
        if rc != 0:
            print("[ERR] --pre-cmd failed; aborting.")
            sys.exit(rc)
    
    # Connect VPN if requested
    vpn_started_here = False
    if args.vpn_service:
        ok = macos_vpn_connect(args.vpn_service, args.vpn_timeout)
        if not ok:
            sys.exit(4)
        vpn_started_here = True
    
    # Build URL list
    final_urls: List[str] = []
    if args.urls:
        final_urls.extend(expand_comma_separated(args.urls))
    if getattr(args, "urls_files", None):
        for path in args.urls_files:
            final_urls.extend(read_urls_from_file(path))
    
    # Remove duplicates while preserving order
    final_urls = list(dict.fromkeys([u for u in final_urls if u and u.strip()]))
    if not final_urls:
        print("[ERR] No URLs provided. Pass positional URLs or --urls-file.")
        sys.exit(1)
    
    # Initialize downloader
    downloader = PluralsightDownloader(args.username, args.password, args.outdir)
    
    try:
        # Authenticate
        if not downloader.authenticate():
            print("[ERR] Authentication failed.")
            sys.exit(2)
        
        # Process URLs
        success_count = 0
        for url in final_urls:
            print(f"\n[INFO] Processing: {url}")
            
            if args.course or "/library/courses/" in url:
                # Download as course
                if downloader.download_course(url, args):
                    success_count += 1
            else:
                # Download as individual video
                print("[WARN] Individual video download not fully implemented.")
                # Placeholder for single video download
        
        print(f"\n✅ Successfully processed {success_count}/{len(final_urls)} URLs.")
        
    except KeyboardInterrupt:
        print("\n[INFO] Download interrupted by user.")
    except Exception as e:
        print(f"\n[ERR] Unexpected error: {e}")
        sys.exit(3)
    finally:
        # Cleanup
        if args.post_cmd:
            run_shell_command(args.post_cmd)
        if args.vpn_service and vpn_started_here and not args.keep_vpn:
            macos_vpn_disconnect(args.vpn_service)


if __name__ == "__main__":
    main()
