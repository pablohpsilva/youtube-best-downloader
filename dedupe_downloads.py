#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Dedupe files in the downloads directory, preferring the latter (newer mtime) entries.

Deduplication key:
- Primary: (YouTube ID in square brackets, exact suffix after the ID, file extension)
  Example file name patterns handled:
    "Title [VIDEOID].m4a"                      → key: (videoid, "", "m4a")
    "Title [VIDEOID] - 01 - Part.m4a"          → key: (videoid, "- 01 - Part", "m4a")

- Fallback for non-matching names: (normalized stem, extension)
  Normalization removes trailing " (N)" copy suffix and collapses spaces, case-insensitive.

Only the newest file by modification time is kept for each key; others are deleted.
"""

import os
import re
import sys
from typing import Dict, List, Tuple


DOWNLOADS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "downloads"))


YOUTUBE_NAMING_RE = re.compile(
    r"^(?P<prefix>.+?) \[(?P<id>[A-Za-z0-9_-]{8,})\](?P<suffix>.*?)\.(?P<ext>[A-Za-z0-9]+)$"
)


def normalize_copy_suffix(stem: str) -> str:
    # Remove trailing " (N)" Finder/Explorer copy suffix
    stem = re.sub(r"\s*\(\d+\)$", "", stem)
    # Collapse whitespace
    stem = re.sub(r"\s+", " ", stem).strip()
    return stem.lower()


def build_key(filename: str) -> Tuple[str, str, str]:
    name = os.path.basename(filename)
    m = YOUTUBE_NAMING_RE.match(name)
    if m:
        video_id = m.group("id").lower()
        suffix = m.group("suffix").strip().lower()  # includes leading dash/space if present
        ext = m.group("ext").lower()
        return (video_id, suffix, ext)
    # Fallback: use normalized stem
    stem, ext = os.path.splitext(name)
    return ("noid", normalize_copy_suffix(stem), ext.lstrip(".").lower())


def main() -> int:
    target_dir = DOWNLOADS_DIR
    if len(sys.argv) > 1:
        target_dir = os.path.abspath(sys.argv[1])
    if not os.path.isdir(target_dir):
        print(f"[ERR] Not a directory: {target_dir}", file=sys.stderr)
        return 2

    key_to_files: Dict[Tuple[str, str, str], List[Tuple[str, float]]] = {}
    total_files = 0
    for entry in os.scandir(target_dir):
        if not entry.is_file():
            continue
        total_files += 1
        key = build_key(entry.name)
        try:
            mtime = entry.stat().st_mtime
        except FileNotFoundError:
            # Might have been removed concurrently
            continue
        key_to_files.setdefault(key, []).append((entry.path, mtime))

    removed = 0
    kept = 0
    for key, files in key_to_files.items():
        if len(files) == 1:
            kept += 1
            continue
        # Sort by mtime ascending; keep the newest (last)
        files.sort(key=lambda x: x[1])
        to_delete = files[:-1]
        to_keep = files[-1]
        kept += 1
        for path, _ in to_delete:
            try:
                os.remove(path)
                removed += 1
                print(f"[DEL] {os.path.basename(path)} (duplicate of key={key})")
            except FileNotFoundError:
                pass
            except Exception as e:
                print(f"[ERR] Failed to delete {path}: {e}", file=sys.stderr)
        print(f"[KEEP] {os.path.basename(to_keep[0])} (newest for key={key})")

    print(f"\nDone. Scanned {total_files} files. Kept {kept}, removed {removed} duplicates.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())



