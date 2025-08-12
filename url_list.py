import sys
from typing import List


def read_urls_from_file(path: str) -> List[str]:
    urls: List[str] = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                s = line.strip()
                if not s:
                    continue
                if s.startswith("#") or s.startswith("//"):
                    continue
                parts = [p.strip() for p in s.split(",")]
                urls.extend([p for p in parts if p])
    except FileNotFoundError:
        print(f"[ERR] URLs file not found: {path}", file=sys.stderr)
        sys.exit(3)
    except Exception as e:
        print(f"[ERR] Failed to read URLs file '{path}': {e}", file=sys.stderr)
        sys.exit(3)
    return urls


def expand_comma_separated(values: List[str]) -> List[str]:
    out: List[str] = []
    for v in values or []:
        if v is None:
            continue
        parts = [p.strip() for p in v.split(",")]
        out.extend([p for p in parts if p])
    return out


