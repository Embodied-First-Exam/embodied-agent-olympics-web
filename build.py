#!/usr/bin/env python3
"""Build the Embodied Olympics public site into ./dist (Python 3.10+, standard library only).

    python3 build.py                 build into ./dist
    python3 build.py --serve 49861   build, then serve http://localhost:49861/ (rebuilds when a source file changes)
    python3 build.py --base /eo/     build for a sub-path (e.g. GitHub Pages project site)
"""
from __future__ import annotations

import argparse
import functools
import hashlib
import http.server
import json
import os
import re
import shutil
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

import importlib  # noqa: E402

import layout  # noqa: E402
import medals  # noqa: E402
import home  # noqa: E402
import pages  # noqa: E402

DIST = ROOT / "dist"
WATCHED = [ROOT / "site.json", ROOT / "data", ROOT / "src", ROOT / "assets"]


def load(name: str):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def icon_sprite() -> str:
    """All sport pictograms as one inline <symbol> sprite; strokes follow currentColor."""
    syms = []
    for f in sorted((ROOT / "assets/icons").glob("*.svg")):
        t = f.read_text(encoding="utf-8")
        vb = re.search(r'viewBox="([^"]+)"', t).group(1)
        inner = re.sub(r"^.*?<svg[^>]*>|</svg>\s*$", "", t, flags=re.S)
        inner = re.sub(r"<title>.*?</title>", "", inner)
        inner = inner.replace("#0D0E10", "currentColor")
        syms.append(f'<symbol id="i-{f.stem}" viewBox="{vb}" fill="none" stroke="currentColor" stroke-width="2.3" '
                    f'stroke-linecap="round" stroke-linejoin="round">{inner}</symbol>')
    return f'<svg width="0" height="0" style="position:absolute" aria-hidden="true">{"".join(syms)}</svg>'


def build(base: str | None = None) -> int:
    importlib.reload(layout)  # pick up template edits while serving
    importlib.reload(medals)
    importlib.reload(home)
    importlib.reload(pages)
    cfg = load("site.json")
    if base:
        cfg["base"] = base
    cfg["_sprite"] = icon_sprite()
    # build version for cache busting: content of the stylesheets and scripts plus the build time (changes every build)
    h = hashlib.sha1(str(time.time()).encode())
    for f in sorted((ROOT / "assets").glob("css/*.css")) + sorted((ROOT / "assets").glob("js/*.js")):
        h.update(f.read_bytes())
    cfg["_v"] = h.hexdigest()[:10]
    if os.environ.get("EO_KIMI_CHART"):  # preview variants of the dark-theme Kimi chart line (v1 / v2 / v3)
        cfg["kimi_chart"] = os.environ["EO_KIMI_CHART"]
    for k in ("replay_base", "highlight_base"):  # a preview build can point the player at local copies
        if os.environ.get(f"EO_{k.upper()}"):
            cfg[k] = os.environ[f"EO_{k.upper()}"]
    site = layout.Site(cfg, load("data/sports.json")["sports"], load("data/models.json")["models"],
                load("data/media.json"), load("data/results.json"))

    out = [home.home(site), pages.sports_index(site), pages.match(site), pages.competitions(site),
           pages.results(site), pages.documents(site), pages.watch(site), pages.not_found(site)]
    out += [pages.sport_page(site, i) for i in range(len(site.sports))]

    if DIST.exists():
        shutil.rmtree(DIST)
    for path, html in out:
        target = DIST / path if path.endswith(".html") else DIST / path / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(html, encoding="utf-8")
    shutil.copytree(ROOT / "assets", DIST / "assets", ignore=shutil.ignore_patterns("icons"))
    if (ROOT / "data/timelines").is_dir():  # match timelines for the replay player's scoreboard overlay
        shutil.copytree(ROOT / "data/timelines", DIST / "timelines")
    for old, new in cfg.get("redirects", {}).items():  # old URLs keep working
        if old.startswith("_"):
            continue
        target = site.url(new)
        page = DIST / old / "index.html"
        page.parent.mkdir(parents=True, exist_ok=True)
        page.write_text(f'<!doctype html><meta charset="utf-8"><title>Moved</title><link rel="canonical" href="{target}">'
                        f'<script>location.replace("{target}"+location.hash)</script>'
                        f'<meta http-equiv="refresh" content="0; url={target}"><a href="{target}">Moved here</a>\n', encoding="utf-8")
    if (ROOT / "CNAME").is_file():  # custom domain for GitHub Pages
        shutil.copy(ROOT / "CNAME", DIST / "CNAME")
    return len(out)


def mtime() -> float:
    return max((p.stat().st_mtime for w in WATCHED for p in ([w] if w.is_file() else w.rglob("*")) if p.is_file()),
               default=0)


def serve(port: int, host: str, base: str | None):
    def watch():
        last = mtime()
        while True:
            time.sleep(0.7)
            now = mtime()
            if now != last:
                last = now
                try:
                    print(f"  rebuilt ({build(base)} pages)", flush=True)
                except Exception as e:  # keep serving the last good build
                    print(f"  build failed: {e!r}", flush=True)

    threading.Thread(target=watch, daemon=True).start()

    class Handler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def send_head(self):  # serve dist/404.html for missing pages
            path = self.translate_path(self.path)
            if not Path(path).exists() and not Path(path, "index.html").exists():
                self.path = "/404.html"
            return super().send_head()

        def end_headers(self):
            self.send_header("Cache-Control", "no-store")
            super().end_headers()

    httpd = http.server.ThreadingHTTPServer((host, port), functools.partial(Handler, directory=str(DIST)))
    print(f"\n  Embodied Olympics  →  http://localhost:{port}/\n  (edits rebuild automatically; Ctrl-C stops)\n", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--serve", type=int, metavar="PORT", help="serve after building")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--base", help="URL base path (default from site.json)")
    a = ap.parse_args()
    n = build(a.base)
    print(f"built {n} pages into {DIST}")
    if a.serve:
        serve(a.serve, a.host, a.base)
