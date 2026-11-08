#!/usr/bin/env python3
"""Copy every media file the site uses into assets/media/, so the site serves its own media (no lab-server links).

    python3 tools/fetch_media.py            download what is missing from site.json "media_origin"
    python3 tools/fetch_media.py --check    only list what is missing

Paths in data/*.json (e.g. /eo/media/x.mp4) map to assets/media/eo/media/x.mp4. 2560x1440 masters are not
downloaded (too large); put a master at assets/media/release/full/prev-<clip>-1440p.mp4 to enable HD for a clip.
Needs the campus network or VPN when downloading.
"""
from __future__ import annotations

import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def media_paths() -> set[str]:
    found: set[str] = set()

    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if k == "url" and isinstance(v, str) and v.startswith("/"):
                    found.add(v)
                else:
                    walk(v)
        elif isinstance(o, list):
            for x in o:
                walk(x)

    for f in ("data/sports.json", "data/media.json"):
        walk(json.loads((ROOT / f).read_text(encoding="utf-8")))
    for f in (ROOT / "src").glob("*.py"):  # literal media paths in the templates
        found |= set(re.findall(r'"(/eo/[^"]+\.(?:jpg|png|mp4))"', f.read_text(encoding="utf-8")))
    return {p for p in found if not p.startswith("/exam-media/masters/")}


def main() -> int:
    origin = json.loads((ROOT / "site.json").read_text(encoding="utf-8"))["media_origin"].rstrip("/")
    missing = sorted(p for p in media_paths() if not (ROOT / ("assets/media" + p)).is_file())
    if "--check" in sys.argv:
        print("\n".join(missing) or "all media present")
        return 1 if missing else 0
    for p in missing:
        dest = ROOT / ("assets/media" + p)
        dest.parent.mkdir(parents=True, exist_ok=True)
        print("fetch", p)
        with urllib.request.urlopen(origin + p, timeout=60) as r:
            dest.write_bytes(r.read())
    print(f"done: {len(missing)} file(s) fetched")
    return 0


if __name__ == "__main__":
    sys.exit(main())
