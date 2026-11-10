"""'How this board is made': the closed fold under each leaderboard (home and Leaderboard page).

Both folds reuse the homepage's original format widget (home.tournament, its components and its animation in site.js):
Continuous Learning shows the widget as it was (duel / team-duel bracket, solo, race tabs); Episodic Learning shows the
same widget style with the round robin only, flowing into the board's points table, the top three of which take the medals
(one example Open Arena board). One sentence on the workspace above each, one small rule line below."""
from __future__ import annotations

import json
from pathlib import Path

from layout import E, Site, model_logo, model_name

ROOT = Path(__file__).resolve().parent.parent
EXAMPLE_SPORT = "soccer_hsl"  # the example board: a complete Open Arena round robin

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


def episodic_widget(site: Site) -> str:
    """The format widget's look with one panel: Round robin -> Points table -> Medals, from one real Open Arena board.
    The page is served in its final state (dots on, table sorted by rank with medal colours, podium up), which is what
    no-JS and reduced-motion readers see. site.js ([data-tm-ep]) resets it to the start before it is shown: the table in
    the grid's entrant order with zero points and no ranks; each match then lights its two grid cells and adds its points;
    when the round robin is complete the rows slide into rank order, ranks and medal colours appear, then the podium."""
    import home  # noqa: PLC0415  (the widget's own pieces)
    ms = site.models
    sport, rows, games = _board(site)
    rank = {r["model"]: r["rank"] for r in rows}
    final = {r["model"]: r["points"] for r in rows}
    mx = max(final.values(), default=1) or 1
    seat = lambda m: f'<span class="tm-h" title="{E(model_name(m))}" style="--c:{E(m["colour"])}">{model_logo(site, m)}</span>'  # noqa: E731
    grid = f'<span></span>{"".join(seat(m) for m in ms)}'
    for i, mi in enumerate(ms):
        grid += seat(mi) + "".join('<i class="tm-x"></i>' if i == j else f'<i class="tm-c on" data-ep-c="{i}-{j}"></i>' for j in range(len(ms)))
    pts = ""
    for i, m in enumerate(ms):
        r = rank.get(m["name"], len(ms))
        medal = {1: " tm-pt--g", 2: " tm-pt--s", 3: " tm-pt--b"}.get(r, "")
        pts += (f'<div class="tm-pt tm-pt--ep on{medal}" data-ep-row="{i}" style="--i:{i};--r:{r - 1}">'
                f'<span><em class="ep-rk">{r}</em>{model_logo(site, m)}{E(model_name(m).split(" ")[0])}</span>'
                f'<i style="--w:{max(4, round(100 * final.get(m["name"], 0) / mx))}%"></i><b>{final.get(m["name"], 0)}</b></div>')
    data = json.dumps({"games": games, "max": mx, "final": [final.get(m["name"], 0) for m in ms]}, separators=(",", ":"))
    pod = home._podium().replace('class="tm-medal ', 'class="tm-medal on ')
    return f"""<div class="tm tm--home tm--ep" data-tm-ep data-step="md">
  <div class="tm-card"><div class="tm-pan">
    {home._stepper(["Round robin", "Points table", "Medals"])}
    <div class="tm-body">
      <div class="tm-col" data-st="rr"><div class="tm-grid" style="--n:{len(ms)}">{grid}</div></div>
      <div class="tm-col" data-st="ko"><div class="tm-pts tm-pts--ep is-sorted" style="--n:{len(ms)}">{pts}</div></div>
      <div class="tm-col" data-st="md">{pod}</div>
    </div>
    <p class="tm-rule">Each pair plays once · win 3, draw 1 · the top three take the medals</p>
  </div><span class="note tm-sch">Example: {E(sport)}</span></div>
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
    return f'<details class="lbx-how">{anchors}<summary>How this board is made</summary><div class="hb">{body}</div></details>'
