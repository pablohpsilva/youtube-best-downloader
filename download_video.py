from typing import Any, Dict
from helpers import progress_hook


def build_video_opts(args, base_opts: Dict[str, Any]) -> Dict[str, Any]:
    maxh = args.max_res
    minh = args.min_res
    o = dict(base_opts)
    codec_order = ":".join(args.prefer_codecs.split(","))

    # More flexible format selection with progressive fallbacks
    if not args.allow_below_min:
        # Strict minimum resolution with multiple fallback options
        fmt = (
            f"(bv*[height>={minh}][vcodec^=av01]+ba[acodec^=opus]/ba)/"
            f"(bv*[height>={minh}][vcodec^=vp9]+ba[acodec^=opus]/ba)/"
            f"(bv*[height>={minh}]+ba[acodec^=opus]/ba)/"
            f"(bv*[height>={minh}]+ba)/"
            f"(b[height>={minh}])/"
            f"best[height>={minh}]/"
            f"best"
        )
    else:
        # Progressive quality fallbacks
        fmt = (
            f"(bv*[height<={maxh}][height>={minh}][vcodec^=av01]+ba[acodec^=opus]/ba)/"
            f"(bv*[height<={maxh}][height>={minh}][vcodec^=vp9]+ba[acodec^=opus]/ba)/"
            f"(bv*[height<={maxh}][height>={minh}]+ba[acodec^=opus]/ba)/"
            f"(bv*[height<={maxh}][height>={minh}]+ba)/"
            f"(bv*[height<={maxh}]+ba[acodec^=opus]/ba)/"
            f"(bv*[height<={maxh}]+ba)/"
            f"(bv*+ba[acodec^=opus]/ba)/"
            f"(bv*+ba)/"
            f"(b[height<={maxh}])/"
            f"(b)/"
            f"best"
        )

    o.update({
        "format": fmt,
        "format_sort": [f"res:{maxh}", "fps", f"codec:{codec_order}", "vbr", "hdr"],
        "format_sort_force": False,  # Allow yt-dlp to override if needed
        "postprocessor_args": [],
        # Additional fallback options
        "ignoreerrors": False,  # Don't ignore format errors for video mode
        "allow_unplayable_formats": False,
    })
    return o


