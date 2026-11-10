"""Medal data from data/results.json (written by /data/guichi/eao-hq/tools/web/medals_sync.py from the official run):
the provisional line, shared ranks, per-sport podium cells and the dagger notes. Before results exist every helper
falls back to the placeholder look (dashes, "fills in at release")."""
from __future__ import annotations

from layout import E, Site, model_name


def status_line(site: Site, default: str) -> str:
    return (site.results.get("status") or {}).get("line") or default


def rank_of(site: Site, name: str, fallback: int):
    """The model's rank in the medal table (equal records share a rank)."""
    for r in site.results.get("medal_table", []):
        if r.get("model") == name and r.get("rank") is not None:
            return r["rank"]
    return fallback


def _row(site: Site, sid: str) -> dict:
    return next((r for r in site.results.get("by_sport", []) if r.get("sport") == sid), {})


def dagger(site: Site, sid: str) -> str:
    return '<sup class="mt-dag" title="May still change">†</sup>' if _row(site, sid).get("flag") else ""


def podium_cells(site: Site, sid: str) -> str:
    """Gold, silver, bronze cells of one sport: names for a decided sport, "In progress" otherwise."""
    r = _row(site, sid)
    if r.get("status") in ("in_progress", "excluded"):
        return f'<td colspan="3" class="bs-wait">{"In progress" if r["status"] == "in_progress" else "Under review"}</td>'
    return "".join(f'<td>{E(model_name(r[k])) if r.get(k) else "—"}</td>' for k in ("gold", "silver", "bronze"))


def flag_foot(site: Site, full: bool = False) -> str:
    """The dagger note: one short line (home, medal table) or one line per flagged sport (By sport)."""
    flagged = [r for r in site.results.get("by_sport", []) if r.get("status") == "final" and r.get("flag")]
    if not flagged:
        return ""
    names = [site.sport_by_id[r["sport"]]["name"] if r["sport"] in site.sport_by_id else r["sport"] for r in flagged]
    if full:
        items = "".join(f"<li><b>{E(n)}</b> {E(r['flag'])}</li>" for n, r in zip(names, flagged))
        return f'<div class="mt-flags"><p>† Counted, but could still change:</p><ul>{items}</ul></div>'
    lb = site.url("leaderboard/")
    return (f'<p class="mt-flags">† Counted, but could still change: {E(", ".join(names))}. '
            f'<a href="{lb}#by-sport">By sport →</a></p>')


ARENA_NOTE = ("Episodic Learning: a fresh workspace every match; the agent keeps nothing between matches. An always-open "
              "leaderboard, separate from the medal table; new agents can enter at any time. Round robin: win 3, draw 1; ties "
              "by score difference. The rating (Bradley-Terry) is for reference. Drone racing and full-size racing run only in "
              "the Olympics Championship (Continuous Learning); the four solo sports' three-run series are their medal events (By sport).")


def arena_panel(site: Site, fallback_boards: str) -> str:
    """The Episodic Learning tab (Open Arena boards, code id arena): one official table per board (results.json open_arena, from medals_sync.py), or the
    placeholder grid before results exist."""
    oa = site.results.get("open_arena")
    if not isinstance(oa, dict) or not oa:
        return ('<p class="rp-note">Episodic Learning: a fresh workspace every match. An always-open leaderboard, separate from '
                'the medal table; new agents can enter at any time. Top three per sport. Drone racing, full-size '
                f'racing and Humanoid Soccer · Team run only in the Olympics Championship.</p><div class="oagrid">{fallback_boards}</div>')
    from layout import icon  # noqa: PLC0415
    st = site.results.get("open_arena_status") or {}
    cards = []
    for s in site.sports:
        b = oa.get(s["id"])
        if not b:
            continue
        rows = "".join(
            f'<tr><td class="oa-r">{E(str(r["rank"]))}</td><td class="oa-m">{E(model_name(r["model"]))}</td>'
            f'<td class="oa-p">{E(str(r["points"]))}</td><td>{r["won"]}-{r["drawn"]}-{r["lost"]}</td>'
            f'<td>{r["played"]}</td><td class="oa-x">{"" if r.get("rating") is None else E(format(r["rating"], ".0f"))}</td></tr>'
            for r in b["rows"])
        tag = "" if b.get("complete") else ' <span class="oa-inc">Incomplete</span>'
        cards.append(
            f'<div class="oa oa--t{"" if b.get("complete") else " is-inc"}">{icon(s["id"])}<strong>{E(s["name"])}</strong>'
            f'<p class="oa-st">{E(b.get("status", ""))}{tag}</p>'
            '<table class="oa-tab"><thead><tr><th>#</th><th>Model</th><th>Pts</th><th>W-D-L</th><th>P</th><th>Rating</th>'
            f'</tr></thead><tbody>{rows}</tbody></table></div>')
    upd = f' <span class="oa-upd">{E(st["line"])}</span>' if st.get("line") else ""
    return f'<p class="rp-note">{E(ARENA_NOTE)}{upd}</p><div class="oagrid">{"".join(cards)}</div>'


# ---------------------------------------------------------------- win rate (results.json win_rate, from medals_sync.py)


def win_rate_block(site: Site) -> str:
    """Win % per model over the Olympics Championship's head-to-head matches (duel + team duel); one value per model."""
    from layout import model_logo  # noqa: PLC0415
    w = site.results.get("win_rate")
    if not w:
        return '<p class="rp-note">Win rates at release.</p>'
    by = {m["name"]: m for m in site.models}
    rows = [r for r in (w["scopes"].get("championship") or []) if r["model"] in by]
    body = "".join(
        f'<tr><td class="mt-rank">{i + 1}</td><td><span class="mt-model"><i class="flag" style="--c:{E(by[r["model"]]["colour"])}"></i>'
        f'{model_logo(site, by[r["model"]])}<span class="mt-who"><strong>{E(model_name(r["model"]))}</strong>'
        f'<small>{E(by[r["model"]].get("harness", ""))} · {E(by[r["model"]].get("effort", ""))} effort</small></span></span></td>'
        f'<td class="wr-pc"><span class="wr-cell"><span class="wr-bar"><i style="--c:{E(by[r["model"]]["colour"])};width:{r["pct"] or 0}%"></i></span>'
        f'<b>{"–" if r["pct"] is None else str(round(r["pct"])) + "%"}</b></span></td></tr>'
        for i, r in enumerate(rows))
    table = (f'<table class="mt mt--home wr"><thead><tr><th>#</th><th>AI agent</th><th>Win %</th></tr></thead><tbody>{body}</tbody></table>')
    lv, ff = (w.get("level_decided") or {}).get("championship", 0), [f for f in w.get("forfeits") or [] if f.get("scope") == "championship"]
    names = {s["id"]: s["name"] for s in site.sports}
    run = ", ".join(names.get(x, x) for x in w.get("running") or [])
    not_counted = ", ".join(names.get(x, x) for x in w.get("not_counted") or [])
    ex = "; ".join(f'{f["fixture"]} ({names.get(f["sport"], f["sport"])}, {f["absent"]} {"did not start" if f.get("kind") == "no-show" else "stopped mid-match"})' for f in ff)
    det = (f'<details class="wr-ex"><summary>How it is counted</summary><p>Olympics Championship matches of the {len(w.get("sports") or [])} duel and '
           f'team-duel sports (round robin and knockout), official result; win % = wins / matches played. {lv} matches ended level and were decided '
           f'by coin toss, lot, shoot-out or the sport\'s tie-break: they count as the official winner\'s win. Left out for both sides ({len(ff)}): '
           f'{E(ex)}. Not included: {E(not_counted)}.' + (f' Provisional while it runs: {E(run)}.' if run else "") + '</p></details>')
    return (f'{table}<p class="rp-note wr-note">Championship head-to-head matches; solo and race sports not included; no-shows excluded.</p>{det}')


def medal_switch(site: Site, medal_html: str) -> str:
    """Medals | Win rate toggle around a medal table (home medal section, leaderboard Championship tab)."""
    return (f'<div class="mw" data-mw><div class="mw-sw" role="group" aria-label="View">'
            '<button type="button" class="mw-b is-on" data-mw-v="medals" aria-pressed="true">Medals</button>'
            '<button type="button" class="mw-b" data-mw-v="win" aria-pressed="false">Win rate</button></div>'
            f'<div data-mw-p="medals">{medal_html}</div><div data-mw-p="win" hidden>{win_rate_block(site)}</div></div>')


# ---------------------------------------------------------------- learning modes (display names; code ids stay championship / arena)

EPISODIC, CONTINUOUS = "Episodic Learning", "Continuous Learning"
EPISODIC_DEF = "A fresh workspace every match: the agent keeps nothing between matches."
CONTINUOUS_DEF = ("One workspace kept across the season: programs, weights, notes and match videos carry into every next "
                  "match of the Olympics Championship.")


def mode_text(s: str) -> str:
    """Data texts written before the rename (sport-page notes) -> the current mode name."""
    return s.replace("Open Arena", EPISODIC) if isinstance(s, str) else s


def episodic_board(site: Site) -> str:
    """The Episodic Learning board for the home page: win % per model over the fresh-workspace head-to-head matches
    (results.json win_rate, scope arena) and how many of the per-sport boards each model tops (results.json open_arena)."""
    from layout import model_logo  # noqa: PLC0415
    w = site.results.get("win_rate")
    if not w:
        return '<p class="rp-note">Results at release.</p>'
    by = {m["name"]: m for m in site.models}
    oa = site.results.get("open_arena") or {}
    tables = {k: b for k, b in oa.items() if isinstance(b, dict) and b.get("rows")}
    led = {}
    for b in tables.values():
        for r in b["rows"]:
            if r.get("rank") == 1:
                led[r["model"]] = led.get(r["model"], 0) + 1
    rows = [r for r in (w["scopes"].get("arena") or []) if r["model"] in by]
    body = "".join(
        f'<tr><td class="mt-rank">{i + 1}</td><td><span class="mt-model"><i class="flag" style="--c:{E(by[r["model"]]["colour"])}"></i>'
        f'{model_logo(site, by[r["model"]])}<span class="mt-who"><strong>{E(model_name(r["model"]))}</strong>'
        f'<small>{E(by[r["model"]].get("harness", ""))} · {E(by[r["model"]].get("effort", ""))} effort</small></span></span></td>'
        f'<td class="mt-n eb-led">{led.get(r["model"], 0)}<small> of {len(tables)}</small></td>'
        f'<td class="mt-n eb-wl">{r["won"]}–{r["lost"]}' + (f'–{r["drawn"]}' if r.get("drawn") else "") + '</td>'
        f'<td class="wr-pc"><span class="wr-cell"><span class="wr-bar"><i style="--c:{E(by[r["model"]]["colour"])};width:{r["pct"] or 0}%"></i></span>'
        f'<b>{"–" if r["pct"] is None else str(round(r["pct"])) + "%"}</b></span></td></tr>'
        for i, r in enumerate(rows))
    head = '<tr><th>#</th><th>AI agent</th><th>Boards led</th><th>W–L</th><th>Win %</th></tr>'
    lv = (w.get("level_decided") or {}).get("arena", 0)
    st = (site.results.get("open_arena_status") or {}).get("line")
    lb = site.url("leaderboard/")
    return (f'<div class="mt-wrap"><table class="mt mt--home wr eb">{f"<thead>{head}</thead>"}<tbody>{body}</tbody></table></div>'
            f'<p class="rp-note wr-note">Head-to-head matches of the {len(w.get("sports") or [])} duel and team-duel sports, official results; '
            f'win % = wins / matches played; {lv} matches level at full time count for the official winner (coin toss, lot, shoot-out or the '
            f'sport\'s tie-break); no-shows left out. Boards led = sports whose round robin the model tops.'
            + (f' {E(st)}.' if st else "") + f' <a class="link" href="{lb}#arena">Every sport\'s board →</a></p>')


def h2h_records(site: Site) -> dict:
    """Every counted head-to-head match of the duel and team-duel sports, from the sport-page data (data/sport_pages):
    [sport index, mode (0 = Episodic / Open Arena board, 1 = Continuous / Championship), row model, other model, winner
    (model index, -1 = draw), level (1 = decided at a level score)]. Same rule as the win-rate table: official result, a
    level match counts for the official winner; forfeits, no-shows and matches a side did not finish are left out."""
    import json  # noqa: PLC0415
    from pathlib import Path  # noqa: PLC0415
    root = Path(__file__).resolve().parent.parent / "data" / "sport_pages"
    names = [m["name"] for m in site.models]
    idx = {n: i for i, n in enumerate(names)}
    w = site.results.get("win_rate") or {}
    left_out = {f["fixture"] for f in w.get("forfeits") or []}
    h2h = [x for f in site.cfg["formats"] if f["id"] in ("duel", "team") for x in f["sports"] if x in site.sport_by_id]
    sports, out = [], []
    for sid in h2h:
        f = root / f"{sid}.json"
        if not f.is_file():
            continue
        d = json.loads(f.read_text(encoding="utf-8"))
        si = len(sports)
        sports.append({"id": sid, "name": site.sport_by_id[sid]["name"]})
        for mode, key in ((0, "open_arena"), (1, "championship")):
            for st in (d.get(key) or {}).get("stages") or []:
                for m in st.get("matches") or []:
                    if m.get("status") != "resolved" or m.get("decided_by") == "forfeit" or m["id"] in left_out:
                        continue
                    a, b = (s.get("model") for s in m["sides"])
                    if a not in idx or b not in idx or a == b:
                        continue
                    sc = {s["model"]: s.get("score") for s in m["sides"]}
                    win = idx.get(m.get("winner"), -1)
                    level = int(win >= 0 and sc[a] == sc[b])
                    out.append([si, mode, idx[a], idx[b], win, level])
    return {"models": names, "sports": sports, "matches": out}
