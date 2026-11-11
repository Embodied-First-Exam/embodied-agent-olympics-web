"""Shared page chrome: <head>, top bar, footer, and small helpers used by every page."""
from __future__ import annotations

import html
import re

from pathlib import Path

E = html.escape
ROOT = Path(__file__).resolve().parent.parent


class Site:
    """Everything a page needs: config + data, plus URL helpers."""

    def __init__(self, cfg: dict, sports: list, models: list, media: dict, results: dict):
        self.cfg = cfg
        self.sports = sports
        self.sport_by_id = {s["id"]: s for s in sports}
        # model colours as CSS variables (page() writes them per theme): m["colour"] becomes the style value used in
        # every --c:... attribute, so the light / dark variants and the light-theme outline follow the theme
        for m in models:
            k = m["entry"].split("@")[0].split("-")[0]
            m.setdefault("hex", m["colour"])
            m["css_key"] = k
            m["colour"] = f"var(--m-{k});--ol:var(--m-{k}-ol)"
        self.models = models
        # the entries on each leaderboard (models.json "boards", default both): every model is on Episodic Learning;
        # an Episodic-only entrant (Claude Fable 5.2, 11-10) stays out of every Continual Learning table and widget
        self.continual_models = [m for m in models if "continual" in m.get("boards", ["episodic", "continual"])]
        self.media = media
        self.results = results
        self.icon_ids = set()

    # ---- URLs
    def url(self, path: str = "") -> str:
        """A site-internal link, respecting the configured base path."""
        base = self.cfg.get("base", "/").rstrip("/") + "/"
        return base + path.lstrip("/")

    def murl(self, path: str | None) -> str | None:
        """A media path from the data files -> the URL the page uses.

        media_base "local": files live in the repo under assets/media/ (tools/fetch_media.py puts them there);
        a 2560x1440 master maps to assets/media/release/full/prev-<clip>-1440p.mp4 when that file exists.
        Returns None when a file is not available, so callers can fall back (e.g. HD -> 720p) or hide a link."""
        if not path:
            return None
        if path.startswith("http"):
            return path
        if self.cfg.get("media_base") != "local":
            return self.cfg["media_base"].rstrip("/") + path
        if path.startswith("/exam-media/masters/"):
            rel = f"assets/media/release/full/prev-{path.split('/')[3]}-1440p.mp4"
        else:
            rel = "assets/media" + path
        return self.url(rel) if (ROOT / rel).is_file() else None

    def asset(self, path: str) -> str:
        """An asset URL; stylesheets and scripts carry the build version (?v=) so browsers fetch each new build."""
        v = self.cfg.get("_v")
        q = f"?v={v}" if v and path.endswith((".css", ".js")) else ""
        return self.url("assets/" + path) + q

    def sport_url(self, s: dict) -> str:
        return self.url(f"sports/{slug(s)}/")

    # ---- edition label
    def edition_label(self) -> str:
        ed = self.cfg.get("edition")
        return f'{self.cfg["edition_ordinal"]} · {ed}' if ed else self.cfg["edition_ordinal"]

    def ext_link(self, key: str, label: str, cls: str = "") -> str:
        href = self.cfg["links"].get(key)
        if href:
            return f'<a class="{cls}" href="{E(href)}" target="_blank" rel="noopener">{E(label)} <span class="ext">↗</span></a>'
        return f'<a class="{cls} is-todo" href="#" aria-disabled="true" title="Link coming at release">{E(label)} <span class="ext">↗</span></a>'


def slug(s: dict) -> str:
    return s["page_url"].rstrip("/").split("/")[-1]


def model_name(m: dict | str) -> str:
    """Display name: drop the '(TODO: ...)' notes kept in the data files."""
    name = m["name"] if isinstance(m, dict) else m
    return re.sub(r"\s*\(TODO[^)]*\)", "", name).strip()


def short_name(m: dict) -> str:
    """One-word label for matrices and widgets: models.json "short", else the first word of the name."""
    return m.get("short") or model_name(m).split(" ")[0]


def todo(v) -> str | None:
    """None for a value that is missing or still TODO."""
    if v is None:
        return None
    if isinstance(v, str) and (v.strip() == "" or v.strip().upper().startswith("TODO")):
        return None
    return v


_LOGO_CACHE: dict = {}


def model_logo(site: "Site", m: dict, cls: str = "mlogo") -> str:
    """The model's logo as inline SVG (fill follows currentColor); empty if none is mapped in site.json."""
    key = site.cfg.get("model_icons", {}).get(m["name"])
    if not key:
        return ""
    if key not in _LOGO_CACHE:
        from pathlib import Path
        f = Path(__file__).resolve().parent.parent / "assets" / "models" / f"{key}.svg"
        svg = f.read_text(encoding="utf-8") if f.exists() else ""
        svg = re.sub(r"<title>.*?</title>", "", svg)
        svg = re.sub(r'\s(width|height|style)="[^"]*"', "", svg, count=3)
        _LOGO_CACHE[key] = svg
    svg = _LOGO_CACHE[key]
    return svg.replace("<svg ", f'<svg class="{cls}" aria-hidden="true" ', 1) if svg else ""


def ink_on(hex_colour: str) -> str:
    """Dark or light foreground for a colour background (WCAG relative luminance)."""
    r, g, b = (int(hex_colour[i:i + 2], 16) / 255 for i in (1, 3, 5))
    lin = lambda v: v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4  # noqa: E731
    return "#0B0C0E" if 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b) > 0.3 else "#FFFFFF"


def icon(sport_id: str, cls: str = "pic") -> str:
    return f'<svg class="{cls}" aria-hidden="true"><use href="#i-{E(sport_id)}"/></svg>'


MARK = (
    '<svg class="mark" viewBox="0 0 32 32" aria-hidden="true">'
    '<path d="M24 5H7v22h17M7 16h9" fill="none" stroke="currentColor" stroke-width="4" '
    'stroke-linecap="round" stroke-linejoin="round"/>'
    '<circle cx="22.5" cy="16" r="3.4" fill="var(--accent)"/></svg>'
)

def brand_mark(site: "Site") -> str:
    """Chi's 01 Arena mark: silver on the dark bar (dark theme), the black ink version in the light theme (CSS swaps them)."""
    return (f'<img class="mark mark--light" src="{site.asset("brand/mark-light.png")}" alt="" width="50" height="22">'
            f'<img class="mark mark--ink" src="{site.asset("brand/mark-ink.png")}" alt="" width="50" height="22">')


THEME_ICONS = (
    '<svg class="i-sun" viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round">'
    '<circle cx="12" cy="12" r="4.2"/><path d="M12 2.5v2.2M12 19.3v2.2M2.5 12h2.2M19.3 12h2.2M5.3 5.3l1.6 1.6M17.1 17.1l1.6 1.6M5.3 18.7l1.6-1.6M17.1 6.9l1.6-1.6"/></svg>'
    '<svg class="i-moon" viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round">'
    '<path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z"/></svg>'
)

NAV = [
    ("sports/", "Sports"),
    ("leaderboard/", "Leaderboard"),
    # ("documents/", "Documents"),   # hidden until the docs site exists (Chi 11-10)
]


def page(site: Site, *, path: str, title: str | None, body: str, description: str | None = None,
         dark_top: bool = False, body_class: str = "", css: tuple = ()) -> str:
    """Wrap a page body in the full document."""
    cfg = site.cfg
    full_title = f"{title} · {cfg['name']}" if title else f"{cfg['name']} — {cfg['tagline']}"
    desc = description or cfg["description"]
    nav = "".join(
        f'<a href="{site.url(p)}"{" aria-current=page" if path.startswith(p) else ""}>{E(label)}</a>'
        for p, label in NAV
    )
    topbar = f"""
<header class="top{' top--over' if dark_top else ''}" data-top>
  <div class="top-in">
    <a class="brand" href="{site.url()}" aria-label="{E(cfg['name'])} home">{brand_mark(site)}<span class="brand-word">{E(cfg['name'])}</span></a>
    <nav class="nav" aria-label="Main">{nav}</nav>
    <button class="theme-btn" type="button" data-theme-toggle aria-label="Switch to day mode">{THEME_ICONS}</button>
    <button class="menu-btn" type="button" aria-label="Menu" aria-expanded="false" data-menu><span></span><span></span></button>
  </div>
</header>"""
    return f"""<!doctype html>
<html lang="en"{f' data-kc="{E(site.cfg["kimi_chart"])}"' if site.cfg.get("kimi_chart") else ""}>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(full_title)}</title>
<meta name="description" content="{E(desc)}">
<meta property="og:title" content="{E(full_title)}">
<meta property="og:description" content="{E(desc)}">
<meta name="theme-color" content="#08090B">
<script>try{{var t=localStorage.getItem("eo-theme");if(t)document.documentElement.dataset.theme=t}}catch(e){{}}</script>
<link rel="icon" href="{site.asset('brand/favicon-16.png')}" type="image/png" sizes="16x16">
<link rel="icon" href="{site.asset('brand/favicon-32.png')}" type="image/png" sizes="32x32">
<link rel="icon" href="{site.asset('brand/favicon-64.png')}" type="image/png" sizes="64x64">
<link rel="apple-touch-icon" href="{site.asset('brand/apple-touch-icon.png')}">
<link rel="preload" href="{site.asset('fonts/intertight-var.woff2')}" as="font" type="font/woff2" crossorigin>
<style>{model_vars(site)}</style>
<link rel="stylesheet" href="{site.asset('css/site.css')}">
<link rel="stylesheet" href="{site.asset('css/story.css')}">
{"".join(f'<link rel="stylesheet" href="{site.asset(c)}">' for c in css)}
</head>
<body class="{body_class}">
{icon_sprite(site)}
<a class="skip" href="#main">Skip to content</a>
{topbar}
<main id="main">
{body}
</main>
{footer(site)}
<script src="{site.asset('js/site.js')}" defer></script>
</body>
</html>
"""


def model_vars(site: Site) -> str:
    """--m-<model>: the model colour (same in both themes) and --m-<model>-ol: a thin outline on every mark where the colour
    would vanish into the ground (dark theme: Kimi black -> light outline); colour_light replaces a colour that is too pale on white (GLM).
    Dark overlays on footage (.sbo, .stagebg, .shero) use the dark set in both themes."""
    dark = ";".join(f'--m-{m["css_key"]}:{m["hex"]};--m-{m["css_key"]}-ol:{m.get("outline_dark") or "transparent"}' for m in site.models)
    light = ";".join((f'--m-{m["css_key"]}:{m["colour_light"]};' if m.get("colour_light") else "") + f'--m-{m["css_key"]}-ol:transparent'
                     for m in site.models)
    return f':root{{{dark}}}:root[data-theme="light"]{{{light}}}:root[data-theme="light"] .sbo,:root[data-theme="light"] .stagebg,:root[data-theme="light"] .shero{{{dark}}}'


def footer(site: Site) -> str:
    cfg = site.cfg
    explore = "".join(f'<li><a href="{site.url(p)}">{E(l)}</a></li>' for p, l in NAV + [("watch/", "Watch")])
    res = "".join(f"<li>{site.ext_link(k, l)}</li>" for k, l in [("docs", "Docs"), ("code", "Code"), ("paper", "Paper")])
    return f"""
<footer class="foot">
  <div class="wrap">
    <div class="foot-top">
      <a class="foot-brand" href="{site.url()}">{brand_mark(site)}<span>{E(cfg['name'])}</span></a>
    </div>
    <div class="foot-cols"><ul>{explore}</ul><ul>{res}</ul></div>
    <p class="foot-fine">A research benchmark. Not affiliated with or endorsed by the International Olympic Committee. Footage: replays of recorded simulation runs.</p>
  </div>
</footer>"""


def icon_sprite(site: Site) -> str:
    return site.cfg.get("_sprite", "")
