from typing import Any, Dict
from helpers import progress_hook


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


