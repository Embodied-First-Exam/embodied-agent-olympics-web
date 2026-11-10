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

EPISODIC_WS = "Fresh workspace: every match starts from an empty workspace."
CONTINUOUS_WS = "One workspace per model: programs, weights and notes carry from match to match through the whole championship."
EPISODIC_RULE = ("Equal points: score difference, then head to head (billiards: fewer balls left is better). Win rate and "
                 "head-to-head count every match; a level match counts for its official winner; no-shows are left out.")
CONTINUOUS_RULE = ("A level knockout match goes to the sport's tie-break. Win rate and head-to-head: duel and team-duel matches "
                   "only, counted as in Episodic Learning.")


def _standings(site: Site) -> tuple[str, list]:
    f = ROOT / "data" / "sport_pages" / f"{EXAMPLE_SPORT}.json"
    if not f.is_file():
        return "", []
    d = json.loads(f.read_text(encoding="utf-8"))
    rr = next((s for s in (d.get("open_arena") or {}).get("stages") or [] if s["id"] == "round_robin"), None)
    name = site.sport_by_id[EXAMPLE_SPORT]["name"] if EXAMPLE_SPORT in site.sport_by_id else EXAMPLE_SPORT
    return name, sorted((rr or {}).get("standings") or [], key=lambda r: r["rank"])


def episodic_widget(site: Site) -> str:
    """The format widget's look with one panel: Round robin -> Points table -> Medals. site.js animates it like the
    widget's other panels (data-g = rr, ko, md light up stage by stage)."""
    import home  # noqa: PLC0415  (the widget's own pieces)
    ms = site.models
    sport, rows = _standings(site)
    by = {m["name"]: m for m in ms}
    seat = lambda m: f'<span class="tm-h" title="{E(model_name(m))}" style="--c:{E(m["colour"])}">{model_logo(site, m)}</span>'  # noqa: E731
    grid = f'<span></span>{"".join(seat(m) for m in ms)}'
    for i, mi in enumerate(ms):
        grid += seat(mi) + "".join('<i class="tm-x"></i>' if i == j else '<i class="tm-c" data-g="rr"></i>' for j in range(len(ms)))
    mx = max((r["points"] for r in rows), default=1) or 1
    pts = "".join(
        f'<div class="tm-pt tm-pt--ep{" tm-pt--" + "gsb"[r["rank"] - 1] if r["rank"] <= 3 else ""}" data-g="ko">'
        f'<span>{r["rank"]}{model_logo(site, by[r["model"]]) if r["model"] in by else ""}{E(model_name(r["model"]).split(" ")[0])}</span>'
        f'<i style="--w:{max(4, round(100 * r["points"] / mx))}%"></i><b>{r["points"]}</b></div>'
        for r in rows)
    return f"""<div class="tm tm--home tm--ep" data-tm data-fmt="rr">
  <div class="tm-card"><div class="tm-pan" data-fmt-panel="rr">
    {home._stepper(["Round robin", "Points table", "Medals"])}
    <div class="tm-body">
      <div class="tm-col" data-st="rr"><div class="tm-grid" style="--n:{len(ms)}">{grid}</div></div>
      <div class="tm-col" data-st="ko"><div class="tm-pts tm-pts--ep">{pts}</div></div>
      <div class="tm-col" data-st="md">{home._podium(seq=True)}</div>
    </div>
    <p class="tm-rule">Each pair plays once · win 3, draw 1 · the top three take the medals</p>
  </div><span class="note tm-sch">Example: {E(sport)}</span></div>
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
