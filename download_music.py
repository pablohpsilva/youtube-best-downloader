import glob
import os
import subprocess
import sys
from typing import Any, Dict, List, Tuple

from helpers import chapters_to_cuts, progress_hook, safe_label


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


def ffmpeg_split(input_path: str, outdir: str, base_stem: str, cuts: List[Tuple[float, float, str]]) -> List[str]:
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
    exts = ("m4a", "mp3", "opus", "aac", "flac", "wav")
    id_token = glob.escape(f"[{video_id}]")
    matches: List[str] = []
    for ext in exts:
        pattern = os.path.join(outdir, f"*{id_token}.{ext}")
        matches.extend(glob.glob(pattern))
    return sorted(matches)


