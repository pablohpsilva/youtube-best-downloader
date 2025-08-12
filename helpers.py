import re
import sys
from typing import Any, Dict, List, Optional, Tuple


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


