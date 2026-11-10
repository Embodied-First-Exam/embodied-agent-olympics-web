"""'How this board is made': the diagram in the fold under each leaderboard (home and Leaderboard page).

Episodic Learning: a fresh workspace before every match, then one example Open Arena round robin drawn so the board reads
straight off it (each pair plays once -> points -> ranked table -> top 3 = medals). Continuous Learning: one workspace that
persists from match to match, then the Championship formats (duel / team duel bracket, solo medal series, drone heats and
final, full-size racing). Inline SVG in the site's colours and fonts; every panel scales with its column and the flows stack
on narrow screens. Labels only inside the diagrams; one small line of rules under each."""
from __future__ import annotations

import json
from pathlib import Path

from layout import E, Site

ROOT = Path(__file__).resolve().parent.parent
EXAMPLE_SPORT = "soccer_hsl"  # the example board: a complete round robin with a points tie on the bronze line


def _svg(w: int, h: int, body: str, label: str, cls: str = "") -> str:
    return (f'<svg class="hb-svg {cls}" viewBox="0 0 {w} {h}" role="img" aria-label="{E(label)}" '
            f'preserveAspectRatio="xMidYMid meet">{body}</svg>')


def _short(name: str) -> str:
    return {"GPT-6": "Astra", "Claude": "Opus"}.get(name.split(" ")[0], name.split(" ")[0])


def _colour(site: Site, name: str) -> str:
    m = next((m for m in site.models if m["name"] == name), None)
    return f'var(--m-{m["css_key"]})' if m else "var(--fg-3)"


def _ring(site: Site, name: str) -> str:
    m = next((m for m in site.models if m["name"] == name), None)
    return f'var(--m-{m["css_key"]}-ol)' if m else "transparent"


# ---------------------------------------------------------------- workspace strips

def _workspace(fresh: bool, vertical: bool) -> str:
    """Three matches in a row (or a column). Fresh: an empty dashed workspace under each match, reset in between.
    Kept: one workspace band running under all three matches, its contents growing."""
    n = 3
    chips = [["programs · weights · notes"]] * 3  # what carries over, the same workspace in every match
    if not vertical:
        W, H, cw, gap = 760, 150, 200, 80
        x0 = (W - (n * cw + (n - 1) * gap)) / 2
        out = []
        for i in range(n):
            x = x0 + i * (cw + gap)
            out.append(f'<rect class="hb-match" x="{x}" y="8" width="{cw}" height="36" rx="18"/>'
                       f'<text class="hb-t hb-t--m" x="{x + cw / 2}" y="31">Match {i + 1}</text>')
            if fresh:
                out.append(f'<rect class="hb-ws hb-ws--fresh" x="{x}" y="62" width="{cw}" height="70" rx="12"/>'
                           f'<text class="hb-s" x="{x + cw / 2}" y="102">empty workspace</text>')
                if i:
                    ax = x - gap / 2
                    out.append(f'<path class="hb-reset" d="M{ax - 16} 97 a16 16 0 1 1 6 12.5"/>'
                               f'<path class="hb-reset" d="M{ax - 16} 89 v8 h8"/>'
                               f'<text class="hb-s hb-s--x" x="{ax}" y="138">reset</text>')
            else:
                widths = [len(c) * 6.9 + 14 for c in chips[i]]
                cx = x + (cw - sum(widths) - 5 * (len(widths) - 1)) / 2
                for c, w in zip(chips[i], widths):
                    out.append(f'<rect class="hb-chip" x="{cx:.1f}" y="80" width="{w:.1f}" height="26" rx="13"/>'
                               f'<text class="hb-c" x="{cx + w / 2:.1f}" y="98">{c}</text>')
                    cx += w + 5
        if not fresh:
            out.insert(0, f'<rect class="hb-ws hb-ws--kept" x="{x0 - 10}" y="62" width="{n * cw + (n - 1) * gap + 20}" height="70" rx="14"/>')
            for i in range(1, n):
                ax = x0 + i * (cw + gap) - gap / 2
                out.append(f'<path class="hb-carry" d="M{ax - 22} 93 H{ax + 18}"/><path class="hb-carry" d="M{ax + 12} 87 L{ax + 19} 93 L{ax + 12} 99"/>')
        return _svg(W, H, "".join(out), "Fresh workspace every match" if fresh else "One workspace per model, kept from match to match",
                    "hb-ws-h")
    W, rowh = 340, 96
    H = n * rowh + 10
    out = []
    if not fresh:
        out.append(f'<rect class="hb-ws hb-ws--kept" x="120" y="6" width="212" height="{H - 12}" rx="14"/>')
    for i in range(n):
        y = 10 + i * rowh
        out.append(f'<rect class="hb-match" x="6" y="{y + 20}" width="100" height="34" rx="17"/>'
                   f'<text class="hb-t hb-t--m" x="56" y="{y + 42}">Match {i + 1}</text>')
        if fresh:
            out.append(f'<rect class="hb-ws hb-ws--fresh" x="124" y="{y + 6}" width="206" height="62" rx="12"/>'
                       f'<text class="hb-s" x="227" y="{y + 42}">empty workspace</text>')
            if i:
                out.append(f'<text class="hb-s hb-s--x" x="227" y="{y - 4}">↻ reset</text>')
        else:
            cx = 132
            for c in chips[i]:
                w = len(c) * 6.9 + 14
                out.append(f'<rect class="hb-chip" x="{cx}" y="{y + 24}" width="{w}" height="26" rx="13"/>'
                           f'<text class="hb-c" x="{cx + w / 2}" y="{y + 42}">{c}</text>')
                cx += w + 5
            if i:
                out.append(f'<path class="hb-carry" d="M226 {y - 16} V{y + 14}"/><path class="hb-carry" d="M220 {y + 8} L226 {y + 15} L232 {y + 8}"/>')
    return _svg(W, H, "".join(out), "Fresh workspace every match" if fresh else "One workspace per model, kept from match to match",
                "hb-ws-v")


# ---------------------------------------------------------------- the example round robin (Episodic)

def _example(site: Site) -> dict | None:
    f = ROOT / "data" / "sport_pages" / f"{EXAMPLE_SPORT}.json"
    if not f.is_file():
        return None
    d = json.loads(f.read_text(encoding="utf-8"))
    rr = next((s for s in (d.get("open_arena") or {}).get("stages") or [] if s["id"] == "round_robin"), None)
    if not rr or not rr.get("standings"):
        return None
    order = [r["model"] for r in sorted(rr["standings"], key=lambda r: r["rank"])]
    pts = {}
    for m in rr["matches"]:
        if m.get("status") != "resolved":
            continue
        a, b = (s["model"] for s in m["sides"])
        w = m.get("winner")
        pts[(a, b)] = 3 if w == a else 1 if w is None else 0
        pts[(b, a)] = 3 if w == b else 1 if w is None else 0
    return {"order": order, "pts": pts, "standings": sorted(rr["standings"], key=lambda r: r["rank"]),
            "sport": site.sport_by_id[EXAMPLE_SPORT]["name"] if EXAMPLE_SPORT in site.sport_by_id else EXAMPLE_SPORT}


def _rr_grid(site: Site, ex: dict) -> str:
    n, c, x0, y0 = len(ex["order"]), 34, 96, 30  # names in x 4-90, cells from 96
    out = []
    for j, name in enumerate(ex["order"]):
        out.append(f'<circle cx="{x0 + j * c + c / 2}" cy="{y0 - 12}" r="6" fill="{_colour(site, name)}" stroke="{_ring(site, name)}"/>')
    for i, a in enumerate(ex["order"]):
        y = y0 + i * c
        out.append(f'<circle cx="10" cy="{y + c / 2}" r="6" fill="{_colour(site, a)}" stroke="{_ring(site, a)}"/>'
                   f'<text class="hb-c hb-c--l" x="22" y="{y + c / 2 + 4.5}">{E(_short(a))}</text>')
        for j, b in enumerate(ex["order"]):
            x = x0 + j * c
            if i == j:
                out.append(f'<rect class="hb-cell hb-cell--x" x="{x + 1}" y="{y + 1}" width="{c - 2}" height="{c - 2}" rx="4"/>')
                continue
            p = ex["pts"].get((a, b))
            cls = {3: "w", 1: "d", 0: "l"}.get(p, "n")
            out.append(f'<rect class="hb-cell hb-cell--{cls}" x="{x + 1}" y="{y + 1}" width="{c - 2}" height="{c - 2}" rx="4"/>'
                       f'<text class="hb-n" x="{x + c / 2}" y="{y + c / 2 + 5}">{"" if p is None else p}</text>')
    W, H = x0 + n * c + 8, y0 + n * c + 8
    return _svg(W, H, "".join(out), "Round robin: each pair plays once; the row model scores 3 for a win, 1 for a draw, 0 for a loss")


def _points_table(site: Site, ex: dict) -> str:
    rows, rh, top = ex["standings"], 34, 14
    mx = max(r["points"] for r in rows) or 1
    out = []
    for k, r in enumerate(rows):
        y = top + k * rh
        medal = {1: "g", 2: "s", 3: "b"}.get(r["rank"])
        out.append(f'<text class="hb-n hb-n--r" x="14" y="{y + 21}">{r["rank"]}</text>'
                   f'<circle cx="34" cy="{y + 16}" r="6" fill="{_colour(site, r["model"])}" stroke="{_ring(site, r["model"])}"/>'
                   f'<text class="hb-c hb-c--l" x="46" y="{y + 21}">{E(_short(r["model"]))}</text>'
                   f'<rect class="hb-bar-bg" x="122" y="{y + 10}" width="120" height="12" rx="6"/>'
                   f'<rect class="hb-bar{" hb-bar--" + medal if medal else ""}" x="122" y="{y + 10}" width="{max(4, 120 * r["points"] / mx):.1f}" height="12" rx="6"/>'
                   f'<text class="hb-n" x="266" y="{y + 21}">{r["points"]}</text>')
        if k < len(rows) - 1 and rows[k + 1]["points"] == r["points"]:  # equal points: bracket, decided by score difference
            out.append(f'<path class="hb-tie" d="M284 {y + 8} h6 v{rh + 16} h-6"/>'
                       f'<text class="hb-s hb-s--tie" x="296" y="{y + rh / 2 + 20}">score diff.</text>')
    W, H = 370, top + len(rows) * rh + 6
    return _svg(W, H, "".join(out), "Points table, ranked by points")


def _medals(site: Site, ex: dict) -> str:
    out = []
    for k, r in enumerate(ex["standings"][:3]):
        y = 18 + k * 50
        m = "gsb"[k]
        out.append(f'<circle class="hb-medal hb-medal--{m}" cx="24" cy="{y + 16}" r="15"/><text class="hb-n hb-n--md" x="24" y="{y + 21}">{k + 1}</text>'
                   f'<circle cx="58" cy="{y + 16}" r="6" fill="{_colour(site, r["model"])}" stroke="{_ring(site, r["model"])}"/>'
                   f'<text class="hb-t hb-t--l" x="72" y="{y + 22}">{E(_short(r["model"]))}</text>')
    return _svg(180, 176, "".join(out), "Top 3 of the board get gold, silver and bronze")


# ---------------------------------------------------------------- Championship formats (Continuous)

def _step(kind: str, label: str) -> str:
    """One small step of a format flow: a 160 x 120 panel with its graphic and a label underneath."""
    g = []
    if kind == "rr":
        for i in range(5):
            for j in range(5):
                cls = "x" if i == j else ("w" if (i + j) % 3 == 0 else "d")
                g.append(f'<rect class="hb-cell hb-cell--{cls}" x="{45 + j * 14}" y="{12 + i * 14}" width="12" height="12" rx="2"/>')
    elif kind == "sf":
        for k, t in enumerate(("1 v 4", "2 v 3")):
            g.append(f'<rect class="hb-box" x="34" y="{12 + k * 38}" width="92" height="30" rx="8"/>'
                     f'<text class="hb-c" x="80" y="{32 + k * 38}">{t}</text>')
    elif kind == "fin":
        g.append('<rect class="hb-box hb-box--g" x="30" y="12" width="100" height="30" rx="8"/><text class="hb-c" x="80" y="32">Final</text>'
                 '<rect class="hb-box hb-box--b" x="30" y="50" width="100" height="30" rx="8"/><text class="hb-c" x="80" y="70">Bronze</text>')
    elif kind == "pod":
        for x, h, m, n in ((40, 34, "s", 2), (66, 50, "g", 1), (92, 24, "b", 3)):
            g.append(f'<rect class="hb-pod hb-pod--{m}" x="{x}" y="{86 - h}" width="26" height="{h}" rx="3"/>'
                     f'<text class="hb-n hb-n--sm" x="{x + 13}" y="{82 - h}">{n}</text>')
    elif kind == "runs":
        for k, w in enumerate((46, 64, 82)):
            g.append(f'<text class="hb-c hb-c--l" x="22" y="{30 + k * 24}">{k + 1}</text>'
                     f'<rect class="hb-bar" x="38" y="{20 + k * 24}" width="{w}" height="12" rx="6"/>')
    elif kind == "mean":
        g.append('<text class="hb-t" x="34" y="56">x̄</text><rect class="hb-bar hb-bar--g" x="54" y="42" width="64" height="16" rx="8"/>')
    elif kind == "trial":
        for k in range(3):
            g.append(f'<path class="hb-lap" d="M30 {24 + k * 24} q25 -14 50 0 t50 0"/>')
    elif kind == "heats":
        for k, seeds in enumerate(((1, 4, 5), (2, 3, 6))):
            g.append(f'<rect class="hb-box" x="{18 + k * 64}" y="18" width="58" height="66" rx="8"/>')
            for q, s in enumerate(seeds):
                g.append(f'<text class="hb-c" x="{47 + k * 64}" y="{38 + q * 18}">#{s}</text>')
    elif kind == "fin4":
        g.append('<rect class="hb-box hb-box--g" x="30" y="18" width="100" height="66" rx="8"/>')
        for q in range(4):
            g.append(f'<circle class="hb-dot" cx="{50 + q * 20}" cy="51" r="6"/>')
    elif kind == "races":
        for k in range(3):
            g.append(f'<rect class="hb-box" x="{22 + k * 40}" y="22" width="34" height="58" rx="6"/>'
                     f'<text class="hb-c" x="{39 + k * 40}" y="56">{k + 1}</text>')
    elif kind == "f1":
        for k, (p, w) in enumerate(((25, 80), (18, 58), (15, 48))):
            g.append(f'<text class="hb-c hb-c--l" x="20" y="{30 + k * 24}">{p}</text>'
                     f'<rect class="hb-bar" x="44" y="{20 + k * 24}" width="{w}" height="12" rx="6"/>')
    return _svg(160, 118, "".join(g) + f'<text class="hb-t hb-t--s" x="80" y="110">{E(label)}</text>', label, "hb-step")


FORMATS = [  # name, sports, steps
    ("Duel · Team duel", "12 sports", [("rr", "Round robin"), ("sf", "Semifinals"), ("fin", "Final + bronze"), ("pod", "Medals")]),
    ("Solo", "Sprint · Hurdles · Javelin · Stunt Car", [("runs", "3 matches"), ("mean", "Mean score"), ("pod", "Medals")]),
    ("Drone racing", "1 sport", [("trial", "Time trial"), ("heats", "2 heats of 3"), ("fin4", "Final of 4"), ("pod", "Medals")]),
    ("Full-size racing", "1 sport", [("races", "3 races"), ("f1", "F1 points"), ("pod", "Medals")]),
]


def _flow(steps: list) -> str:
    parts = []
    for k, (kind, label) in enumerate(steps):
        if k:
            parts.append('<span class="hb-arr" aria-hidden="true">→</span>')
        parts.append(f'<div class="hb-flow-s">{_step(kind, label)}</div>')
    return f'<div class="hb-flow">{"".join(parts)}</div>'


# ---------------------------------------------------------------- the two folds

EPISODIC_RULE = ("Equal points: score difference, then head to head (billiards: fewer balls left is better). Win rate and "
                 "head-to-head count every match; a level match counts for its official winner; no-shows are left out.")
CONTINUOUS_RULE = ("Round robin scored as in Episodic Learning; a level knockout match goes to the sport's tie-break. Win rate and "
                   "head-to-head: duel and team-duel matches only, counted the same way.")


def fold(site: Site, key: str) -> str:
    if key == "episodic":
        ex = _example(site)
        board = ""
        if ex:
            board = (f'<p class="hb-cap">Round robin → points → ranking → medals <span>example: {E(ex["sport"])}</span></p>'
                     f'<div class="hb-flow hb-flow--rr"><div class="hb-flow-s hb-flow-s--grid">{_rr_grid(site, ex)}<span class="hb-lab">Each pair plays once · win 3, draw 1</span></div>'
                     '<span class="hb-arr" aria-hidden="true">→</span>'
                     f'<div class="hb-flow-s hb-flow-s--tab">{_points_table(site, ex)}<span class="hb-lab">Points table → ranking</span></div>'
                     '<span class="hb-arr" aria-hidden="true">→</span>'
                     f'<div class="hb-flow-s hb-flow-s--med">{_medals(site, ex)}<span class="hb-lab">Top 3 = medals</span></div></div>')
        body = (f'<p class="hb-cap">Fresh workspace every match</p>{_workspace(True, False)}{_workspace(True, True)}'
                f'{board}<p class="hb-rule">{E(EPISODIC_RULE)}</p>')
    else:
        rows = "".join(f'<div class="hb-fmt"><p class="hb-fmt-h"><b>{E(n)}</b> <span>{E(s)}</span></p>{_flow(st)}</div>'
                       for n, s, st in FORMATS)
        body = (f'<p class="hb-cap">1 workspace per model; state carries over</p>{_workspace(False, False)}{_workspace(False, True)}'
                f'<p class="hb-cap">Championship formats</p>{rows}<p class="hb-rule">{E(CONTINUOUS_RULE)}</p>')
    anchors = '<span class="anchor" id="medal-allocation"></span><span class="anchor" id="formats"></span>' if key == "continuous" else ""
    return f'<details class="lbx-how">{anchors}<summary>How this board is made</summary><div class="hb">{body}</div></details>'
