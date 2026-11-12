"""'How this board is made': the closed fold under each leaderboard (home and Leaderboard page).

Both folds reuse the homepage's original format widget (home.tournament, its components and its animation in site.js):
Continual Learning shows the widget as it was (duel / team-duel bracket, solo, race tabs); Episodic Learning shows the
same widget style with the round robin only, flowing into the board's points table, the top three of which take the medals
(one example Open Arena board). One sentence on the workspace above each, one small rule line below."""
from __future__ import annotations

import json
from pathlib import Path

from layout import E, Site, model_logo, model_name, short_name

ROOT = Path(__file__).resolve().parent.parent
EXAMPLE_SPORT = "soccer_hsl"  # the duel / team-duel example board: a complete Open Arena round robin
EXAMPLE_SOLO = "stuntcar"  # the solo example board: the first match of the stunt car medal series

EPISODIC_WS = ("Fresh workspace: every match starts from an empty workspace. The solo sports count their first match of the "
               "medal series, which also starts from an empty workspace; its score ranks the board.")
CONTINUOUS_WS = "One workspace per model: programs, weights and notes carry from match to match through the whole championship."
EPISODIC_RULE = ("Equal points: score difference, then head to head (billiards: fewer balls left is better). Solo: higher score "
                 "first; a no-show counts 0. Win rate and head-to-head: duel and team-duel matches only; a level match counts for "
                 "its official winner; no-shows are left out.")
CONTINUOUS_RULE = ("A level knockout match goes to the sport's tie-break. Win rate and head-to-head: duel and team-duel matches "
                   "only, counted as in Episodic Learning.")


def _board(site: Site) -> tuple[str, list, list]:
    """The example board: (sport name, standings, matches as [row index, column index, row points, column points]),
    indices in the site's model order (the order of the widget's grid and of the unsorted points table)."""
    f = ROOT / "data" / "sport_pages" / f"{EXAMPLE_SPORT}.json"
    if not f.is_file():
        return "", [], []
    d = json.loads(f.read_text(encoding="utf-8"))
    rr = next((s for s in (d.get("open_arena") or {}).get("stages") or [] if s["id"] == "round_robin"), None) or {}
    name = site.sport_by_id[EXAMPLE_SPORT]["name"] if EXAMPLE_SPORT in site.sport_by_id else EXAMPLE_SPORT
    idx = {m["name"]: k for k, m in enumerate(site.models)}
    games = []
    for m in rr.get("matches") or []:
        if m.get("status") != "resolved":
            continue
        a, b = (s["model"] for s in m["sides"])
        if a not in idx or b not in idx:
            continue
        w = m.get("winner")
        games.append([idx[a], idx[b], 3 if w == a else 1 if w is None else 0, 3 if w == b else 1 if w is None else 0])
    return name, sorted(rr.get("standings") or [], key=lambda r: r["rank"]), games


def _pts_rows(site: Site, final: dict, rank: dict, fmt) -> str:
    """Points / score rows in the grid's entrant order (--i); --r is the row's place once sorted (ties keep entrant order)."""
    ms = site.models
    mx = max(final.values(), default=1) or 1
    order = sorted(range(len(ms)), key=lambda k: (rank.get(ms[k]["name"], len(ms)), k))
    place = {k: p for p, k in enumerate(order)}
    out = ""
    for i, m in enumerate(ms):
        r = rank.get(m["name"], len(ms))
        medal = {1: " tm-pt--g", 2: " tm-pt--s", 3: " tm-pt--b"}.get(r, "")
        v = final.get(m["name"], 0)
        out += (f'<div class="tm-pt tm-pt--ep on{medal}" data-ep-row="{i}" style="--i:{i};--r:{place[i]}">'
                f'<span><em class="ep-rk">{r}</em>{model_logo(site, m)}{E(short_name(m))}</span>'
                f'<i style="--w:{max(4, round(100 * v / mx)) if v else 0}%"></i><b>{fmt(v)}</b></div>')
    return out


def _rr_panel(site: Site) -> tuple[str, dict]:
    import home  # noqa: PLC0415  (the widget's own pieces)
    ms = site.models
    sport, rows, games = _board(site)
    rank = {r["model"]: r["rank"] for r in rows}
    final = {r["model"]: r["points"] for r in rows}
    seat = lambda m: f'<span class="tm-h" title="{E(model_name(m))}" style="--c:{E(m["colour"])}">{model_logo(site, m)}</span>'  # noqa: E731
    grid = f'<span></span>{"".join(seat(m) for m in ms)}'
    for i, mi in enumerate(ms):
        grid += seat(mi) + "".join('<i class="tm-x"></i>' if i == j else f'<i class="tm-c on" data-ep-c="{i}-{j}"></i>' for j in range(len(ms)))
    pod = home._podium().replace('class="tm-medal ', 'class="tm-medal on ')
    html = f"""<div class="tm-pan" data-ep-panel="h2h">
    {home._stepper(["Round robin", "Points table", "Medals"])}
    <div class="tm-body">
      <div class="tm-col" data-st="rr"><div class="tm-grid" style="--n:{len(ms)}">{grid}</div></div>
      <div class="tm-col" data-st="ko"><div class="tm-pts tm-pts--ep is-sorted" style="--n:{len(ms)}">{_pts_rows(site, final, rank, str)}</div></div>
      <div class="tm-col" data-st="md">{pod}</div>
    </div>
    <p class="tm-rule">Each pair plays once · win 3, draw 1 · the top three take the medals <span class="tm-ex">Example: {E(sport)}</span></p>
  </div>"""
    data = {"kind": "rr", "games": games, "max": max(final.values(), default=1) or 1, "final": [final.get(m["name"], 0) for m in ms], "dec": 0}
    return html, data


def _solo_panel(site: Site) -> tuple[str, dict]:
    """The solo example: the first match of one solo sport's medal series (fresh workspace), score -> ranking -> medals."""
    import home  # noqa: PLC0415
    import medals  # noqa: PLC0415
    ms = site.models
    rows = medals.solo_round1(site).get(EXAMPLE_SOLO) or []
    rank = {r["model"]: r["rank"] for r in rows}
    final = {r["model"]: r["value"] for r in rows}
    ns = {r["model"]: r["no_show"] for r in rows}
    dec = 1
    fmt = lambda v: f"{v:.{dec}f}"  # noqa: E731
    runs = "".join(
        f'<div class="ep-run on" data-ep-c="{i}"><span class="tm-h" style="--c:{E(m["colour"])}">{model_logo(site, m)}</span>'
        f'<span class="ep-run-l">{E(short_name(m))}</span><i class="ep-run-b">{"no-show" if ns.get(m["name"]) else "match 1"}</i></div>'
        for i, m in enumerate(ms))
    pod = home._podium().replace('class="tm-medal ', 'class="tm-medal on ')
    name = site.sport_by_id[EXAMPLE_SOLO]["name"] if EXAMPLE_SOLO in site.sport_by_id else EXAMPLE_SOLO
    html = f"""<div class="tm-pan" data-ep-panel="solo">
    {home._stepper(["First match", "Score → ranking", "Medals"])}
    <div class="tm-body">
      <div class="tm-col" data-st="rr"><div class="ep-runs"><span class="tm-bl2">Match 1 of the medal series · fresh workspace</span>{runs}</div></div>
      <div class="tm-col" data-st="ko"><div class="tm-pts tm-pts--ep is-sorted" style="--n:{len(ms)}">{_pts_rows(site, final, rank, fmt)}</div></div>
      <div class="tm-col" data-st="md">{pod}</div>
    </div>
    <p class="tm-rule">One match each from a fresh workspace · higher score first · the top three take the medals <span class="tm-ex">Example: {E(name)}, first match</span></p>
  </div>"""
    data = {"kind": "solo", "seq": [[k, final.get(m["name"], 0)] for k, m in enumerate(ms)], "max": max(final.values(), default=1) or 1,
            "final": [final.get(m["name"], 0) for m in ms], "dec": dec}
    return html, data


def episodic_widget(site: Site) -> str:
    """The format widget's look with two tabs, as the old widget: Duel · Team duel (round robin -> points table -> medals,
    one real Open Arena board) and Solo (the first match of one solo medal series -> score -> ranking -> medals).
    Served in its final state (what no-JS and reduced-motion readers see; without JS both panels show). site.js
    ([data-tm-ep]) resets a panel to its start before it is shown: rows in the grid's entrant order, zero bars, no ranks;
    results fill in; only then do the rows slide into rank order with ranks and medal colours; then the podium."""
    from layout import icon  # noqa: PLC0415
    rr, rr_data = _rr_panel(site)
    solo, solo_data = _solo_panel(site)
    btns = [("h2h", ["badminton", "tennis", "soccer_hsl", "basketball"], "Duel · Team duel", "12 sports · round robin"),
            ("solo", ["sprint", "hurdles", "javelin", "stuntcar"], "Solo", "4 sports · first match of the series")]
    tabs = "".join(f'<button type="button" class="tm-o{" is-on" if k == 0 else ""}" data-ep-tab="{key}" aria-pressed="{str(k == 0).lower()}">'
                   f'<span class="tm-o-ic">{"".join(icon(s) for s in ids)}</span><strong>{n}</strong><span>{d}</span></button>'
                   for k, (key, ids, n, d) in enumerate(btns))
    data = json.dumps({"h2h": rr_data, "solo": solo_data}, separators=(",", ":"))
    return f"""<div class="tm tm--home tm--ep" data-tm-ep data-step="md">
  <div class="tm-others tm-others--ep" role="tablist" aria-label="Formats">{tabs}</div>
  <div class="tm-card">{rr}{solo}</div>
  <script type="application/json" data-ep-data>{data}</script>
</div>"""


def fold(site: Site, key: str) -> str:
    import home  # noqa: PLC0415
    if key == "episodic":
        body = f'<p class="hb-ws">{E(EPISODIC_WS)}</p>{episodic_widget(site)}<p class="hb-rule">{E(EPISODIC_RULE)}</p>'
        anchors = ""
    else:
        body = (f'<p class="hb-ws">{E(CONTINUOUS_WS)}</p>{home.tournament(site, head=False, home=True)}'
                f'<p class="hb-rule">{E(CONTINUOUS_RULE)}</p>')
        anchors = '<span class="anchor" id="medal-allocation"></span><span class="anchor" id="formats"></span>'
    import medals  # noqa: PLC0415
    body += medals.notes_fold(site, key)
    return f'<details class="lbx-how">{anchors}<summary>How this board is made</summary><div class="hb">{body}</div></details>'
