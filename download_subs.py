from typing import Any, Dict


def build_subs_only_opts(args, base_opts: Dict[str, Any]) -> Dict[str, Any]:
    o = dict(base_opts)
    o.update({"skip_download": True, "embedsubtitles": False})
    o.pop("postprocessors", None)
    return o


