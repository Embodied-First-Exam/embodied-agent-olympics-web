"""Medal data from data/results.json (written by /data/guichi/eao-hq/tools/web/medals_sync.py from the official run):
the provisional line, shared ranks, per-sport podium cells and the dagger notes. Before results exist every helper
falls back to the placeholder look (dashes, "fills in at release")."""
from __future__ import annotations

from layout import ROOT, E, Site, model_name


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
    if sid in exhibition_ids(site):
        return f' <span class="tag tag--exh">{E(exhibition_label(site))}</span>'
    return '<sup class="mt-dag" title="May still change">†</sup>' if _row(site, sid).get("flag") else ""


def podium_cells(site: Site, sid: str) -> str:
    """Gold, silver, bronze cells of one sport: names for a decided sport, "In progress" otherwise."""
    r = _row(site, sid)
    if r.get("status") in ("in_progress", "excluded"):
        return f'<td colspan="3" class="bs-wait">{"In progress" if r["status"] == "in_progress" else "Under review"}</td>'
    return "".join(f'<td>{E(model_name(r[k])) if r.get(k) else "—"}</td>' for k in ("gold", "silver", "bronze"))


def flag_foot(site: Site, full: bool = False) -> str:
    """The dagger note: one short line (home, medal table) or one line per flagged sport."""
    flagged = [r for r in site.results.get("by_sport", []) if r.get("status") == "final" and r.get("flag")]
    if not flagged:
        return ""
    names = [site.sport_by_id[r["sport"]]["name"] if r["sport"] in site.sport_by_id else r["sport"] for r in flagged]
    if full:
        items = "".join(f"<li><b>{E(n)}</b> {E(r['flag'])}</li>" for n, r in zip(names, flagged))
        return f'<div class="mt-flags"><p>† Counted, but could still change:</p><ul>{items}</ul></div>'
    lb = site.url("leaderboard/")
    return (f'<p class="mt-flags">† Counted, but could still change: {E(", ".join(names))}. '
            f'<a href="{lb}#{CONTINUAL_BOARDS_ID}">Every sport&rsquo;s board →</a></p>')


ARENA_SHORT = ("Duel and team-duel boards: round robin, win 3, draw 1; ties by score difference, then head to head; rating (Bradley-Terry) for reference. Solo boards: the first series match, higher score first, a no-show counts 0.")


def arena_panel(site: Site, fallback_boards: str) -> str:
    """The Episodic Learning tab (Open Arena boards, code id arena): one official table per board (results.json open_arena, from medals_sync.py), or the
    placeholder grid before results exist."""
    oa = site.results.get("open_arena")
    if not isinstance(oa, dict) or not oa:
        return ('<p class="rp-note">Episodic Learning: a fresh workspace every match. An always-open leaderboard, separate from '
                'the medal table; new agents can enter at any time. Top three per sport. Drone racing, full-size '
                f'racing and Humanoid Soccer · Team run only in the Olympics Championship.</p><div class="oagrid">{fallback_boards}</div>')
    from layout import icon  # noqa: PLC0415
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
        if s["id"] in exhibition_ids(site):
            tag += f' <span class="tag tag--exh">{E(exhibition_label(site))}</span>'
        cards.append(
            f'<div class="oa oa--t{"" if b.get("complete") else " is-inc"}">{icon(s["id"])}<strong>{E(s["name"])}</strong>'
            f'<p class="oa-st">{E(b.get("status", ""))}{tag}</p>'
            '<table class="oa-tab"><thead><tr><th>#</th><th>Model</th><th>Pts</th><th>W-D-L</th><th>P</th><th>Rating</th>'
            f'</tr></thead><tbody>{rows}</tbody></table></div>')
    units = {"sprint": "m/s", "hurdles": "m/s", "javelin": "m", "stuntcar": "pts"}
    for sid, srows in solo_round1(site).items():
        s = site.sport_by_id[sid]
        body = "".join(f'<tr><td class="oa-r">{r["rank"]}</td><td class="oa-m">{E(model_name(r["model"]))}</td>'
                       f'<td class="oa-p">{"no-show" if r["no_show"] else E(format(r["value"], ".2f" if r["value"] >= 1 else ".4f"))}</td></tr>'
                       for r in srows)
        cards.append(f'<div class="oa oa--t">{icon(sid)}<strong>{E(s["name"])}</strong><p class="oa-st">First series match · fresh workspace</p>'
                     f'<table class="oa-tab"><thead><tr><th>#</th><th>Model</th><th>{E(units.get(sid, "Score"))}</th></tr></thead>'
                     f'<tbody>{body}</tbody></table></div>')
    return f'<p class="rp-note wr-note">{E(ARENA_SHORT)}</p><div class="oagrid">{"".join(cards)}</div>'


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


def medal_switch(site: Site, medal_html: str, win_html: str | None = None) -> str:
    """Medals | Win rate toggle around a medal table (home medal sections, leaderboard tabs); the win-rate panel defaults
    to the Championship's."""
    return (f'<div class="mw" data-mw><div class="mw-sw" role="group" aria-label="View">'
            '<button type="button" class="mw-b is-on" data-mw-v="medals" aria-pressed="true">Medals</button>'
            '<button type="button" class="mw-b" data-mw-v="win" aria-pressed="false">Win rate</button></div>'
            f'<div data-mw-p="medals">{medal_html}</div><div data-mw-p="win" hidden>{win_rate_block(site) if win_html is None else win_html}</div></div>')


# ---------------------------------------------------------------- learning modes (display names; code ids stay championship / arena)

EPISODIC, CONTINUOUS = "Episodic Learning", "Continual Learning"
EPISODIC_DEF = "A fresh workspace every match: the agent keeps nothing between matches."
CONTINUOUS_DEF = ("One workspace kept across the season: programs, weights, notes and match videos carry into every next "
                  "match of the Olympics Championship.")
# the one line under each leaderboard heading (home and Leaderboard page): board · what the agent keeps
EPISODIC_LINE = "Open Arena · Learns within each match. Every match starts from a fresh workspace."
CONTINUOUS_LINE = "Olympics Championship · Learns within each match and across matches. One workspace carries through the whole championship."


def mode_text(s: str) -> str:
    """Data texts written before the rename (sport-page notes) -> the current mode name."""
    return s.replace("Open Arena", EPISODIC) if isinstance(s, str) else s


def mode_win_table(site: Site, scope: str = "arena") -> str:
    """Win % per model over one mode's head-to-head matches (results.json win_rate; scope arena = Episodic Learning, the
    Open Arena boards; championship = Continual Learning, the Olympics Championship): # · AI agent · W–L · Win %."""
    from layout import model_logo  # noqa: PLC0415
    w = site.results.get("win_rate")
    if not w:
        return '<p class="rp-note">Results at release.</p>'
    by = {m["name"]: m for m in site.models}
    rows = [r for r in (w["scopes"].get(scope) or []) if r["model"] in by]
    body = "".join(
        f'<tr><td class="mt-rank">{i + 1}</td><td><span class="mt-model"><i class="flag" style="--c:{E(by[r["model"]]["colour"])}"></i>'
        f'{model_logo(site, by[r["model"]])}<span class="mt-who"><strong>{E(model_name(r["model"]))}</strong>'
        f'<small>{E(by[r["model"]].get("harness", ""))} · {E(by[r["model"]].get("effort", ""))} effort</small></span></span></td>'
        f'<td class="mt-n eb-wl">{r["won"]}–{r["lost"]}' + (f'–{r["drawn"]}' if r.get("drawn") else "") + '</td>'
        f'<td class="wr-pc"><span class="wr-cell"><span class="wr-bar"><i style="--c:{E(by[r["model"]]["colour"])};width:{r["pct"] or 0}%"></i></span>'
        f'<b>{"–" if r["pct"] is None else str(round(r["pct"])) + "%"}</b></span></td></tr>'
        for i, r in enumerate(rows))
    head = '<tr><th>#</th><th>AI agent</th><th>W–L</th><th>Win %</th></tr>'
    return (f'<div class="mt-wrap"><table class="mt mt--home wr eb"><thead>{head}</thead><tbody>{body}</tbody></table></div>'
            f'<p class="rp-note wr-note">{E(h2h_line(site, scope))}</p>')


def episodic_board(site: Site) -> str:
    return mode_win_table(site, "arena")


def h2h_records(site: Site) -> dict:
    """Every counted head-to-head match of the duel and team-duel sports, from the sport-page data (data/sport_pages):
    [sport index, mode (0 = Episodic / Open Arena board, 1 = Continual / Championship), row model, other model, winner
    (model index, -1 = draw), level (1 = decided at a level score)]. Same rule as the win-rate table: official result, a
    level match counts for the official winner; forfeits, no-shows and matches a side did not finish are left out."""
    import json  # noqa: PLC0415
    from pathlib import Path  # noqa: PLC0415
    root = Path(__file__).resolve().parent.parent / "data" / "sport_pages"
    names = [m["name"] for m in site.models]
    idx = {n: i for i, n in enumerate(names)}
    w = site.results.get("win_rate") or {}
    left_out = {f["fixture"] for f in w.get("forfeits") or []}
    h2h = [x for f in site.cfg["formats"] if f["id"] in ("duel", "team") for x in f["sports"]
           if x in site.sport_by_id and x not in exhibition_ids(site)]
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


# ---------------------------------------------------------------- Episodic Learning medal table (from results.json open_arena)

EPISODIC_MEDAL_RULE = ("Medals = the top 3 of each sport's Episodic Learning board (Open Arena), in the board's official order: "
                       "win 3, draw 1; ties by score difference, then head to head.")


def solo_round1(site: Site) -> dict:
    """The solo sports' Episodic boards: each model's FIRST match of the medal series, played from a fresh workspace
    (data/sport_pages/<sport>.json championship rows, match 1, from the official records). Ranked by that match's score
    with the series' own rule: higher first; a match without a valid result (no-show) counts 0. Equal scores share a
    rank (the series' later tie-breaks, best round and then lots, do not apply to a single round).
    -> {sport: [{model, value, no_show, rank}]}"""
    import json  # noqa: PLC0415
    from pathlib import Path  # noqa: PLC0415
    root = Path(__file__).resolve().parent.parent / "data" / "sport_pages"
    solo = [x for f in site.cfg["formats"] if f["id"] == "solo" for x in f["sports"] if x in site.sport_by_id]
    out = {}
    for sid in solo:
        f = root / f"{sid}.json"
        if not f.is_file():
            continue
        ch = json.loads(f.read_text(encoding="utf-8")).get("championship") or {}
        rows = []
        for r in ch.get("rows") or []:
            m1 = next((m for m in r.get("matches") or [] if m.get("match") == 1), None)
            if m1 is None or m1.get("pending"):
                continue
            rows.append({"model": r["model"], "value": 0.0 if m1.get("no_show") else float(m1.get("value") or 0),
                         "no_show": bool(m1.get("no_show")), "fixture": m1.get("id")})
        rows.sort(key=lambda r: -r["value"])
        for i, r in enumerate(rows):
            r["rank"] = rows[i - 1]["rank"] if i and rows[i - 1]["value"] == r["value"] else i + 1
        if rows:
            out[sid] = rows
    return out


def episodic_medals(site: Site) -> dict:
    """Gold / silver / bronze per model over the Episodic Learning boards (one match, fresh workspace), aggregated like the
    Championship medal table. Boards: the 12 duel and team-duel Open Arena round robins (results.json open_arena rows,
    official order: points, score difference, head to head) and the 4 solo sports' first series match (solo_round1).
    Rank 1 / 2 / 3 -> gold / silver / bronze; a shared rank shares the medal; a board with fewer than three ranked
    entrants gives fewer medals. Only complete boards count (an incomplete one is listed as in progress). Drone racing and
    full-size racing have no Episodic board."""
    oa = site.results.get("open_arena") or {}
    names = [m["name"] for m in site.models]
    tally = {n: {"gold": 0, "silver": 0, "bronze": 0} for n in names}
    counted, pending, podiums, close = [], [], {}, []
    solo = solo_round1(site)
    for s in site.sports:
        b = oa.get(s["id"])
        if s["id"] in exhibition_ids(site):  # exhibition: board shown, no medals (data/exhibition.json)
            continue
        if s["id"] in solo:
            rows = [{"model": r["model"], "rank": r["rank"]} for r in solo[s["id"]]]
        elif isinstance(b, dict) and b.get("rows"):
            if not b.get("complete"):
                pending.append(s["id"])
                continue
            rows = sorted(b["rows"], key=lambda r: r["rank"])
            # medal places decided on a tie-break (equal points across a medal boundary): listed for review
            for a, c in zip(rows, rows[1:]):
                if a["points"] == c["points"] and a["rank"] <= 3:
                    close.append({"sport": s["id"], "ranks": [a["rank"], c["rank"]], "models": [a["model"], c["model"]], "points": a["points"],
                                  "diff": [a["score_for"] - a["score_against"], c["score_for"] - c["score_against"]]})
        else:
            continue
        counted.append(s["id"])
        pod = {}
        for r in rows:
            k = {1: "gold", 2: "silver", 3: "bronze"}.get(r["rank"])
            if k and r["model"] in tally:
                tally[r["model"]][k] += 1
                pod.setdefault(k, []).append(r["model"])
        podiums[s["id"]] = pod
    key = lambda n: (tally[n]["gold"], tally[n]["silver"], tally[n]["bronze"])  # noqa: E731
    order = sorted(names, key=lambda n: tuple(-x for x in key(n)))
    table = []
    for i, n in enumerate(order):
        rank = table[-1]["rank"] if table and key(order[i - 1]) == key(n) else i + 1
        table.append({"model": n, **tally[n], "rank": rank})
    no_board = [s["id"] for s in site.sports if s["id"] not in counted and s["id"] not in pending
                and s["id"] not in exhibition_ids(site)]
    return {"table": table, "counted": counted, "pending": pending, "no_board": no_board, "podiums": podiums, "close": close,
            "solo": solo}


def medal_rows_html(site: Site, table: list) -> str:
    """Rank · AI agent · Gold · Silver · Bronze, the home medal-table layout, for any list of {model, gold, silver, bronze, rank}."""
    from layout import model_logo  # noqa: PLC0415
    by = {m["name"]: m for m in site.models}
    body = "".join(
        f'<tr><td class="mt-rank">{r["rank"]}</td>'
        f'<td><span class="mt-model"><i class="flag" style="--c:{E(by[r["model"]]["colour"])}"></i>{model_logo(site, by[r["model"]])}<span class="mt-who"><strong>{E(model_name(r["model"]))}</strong>'
        f'<small>{E(by[r["model"]].get("harness", ""))} · {E(by[r["model"]].get("effort", ""))} effort</small></span></span></td>'
        + "".join(f'<td class="mt-n">{r[c]}</td>' for c in ("gold", "silver", "bronze")) + "</tr>"
        for r in table if r["model"] in by)
    head = "".join(f"<th>{h}</th>" for h in ["Rank", "AI agent"]) + "".join(
        f'<th class="mt-mh"><i class="medal medal--{c}"></i>{w}</th>' for c, w in (("g", "Gold"), ("s", "Silver"), ("b", "Bronze")))
    return f'<div class="mt-wrap"><table class="mt mt--home"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def episodic_medal_block(site: Site) -> str:
    """The Episodic Learning medal table (rule: medals.episodic_medals)."""
    return f'<div class="mt-home">{medal_rows_html(site, episodic_medals(site)["table"])}</div>'


def board_counts(site: Site) -> dict:
    """What each leaderboard is based on, counted from the sport-page records (data/sport_pages) and the official
    left-out list (results.json win_rate.forfeits: no-shows and matches a side did not finish):
    episodic = sports with an Open Arena round robin (its matches played) plus the solo sports (their first series match); continuous = all sports with a Championship,
    every match played (duel / team-duel round robin and knockout, the solo sports' series matches, the drone time-trial
    matches, heats and final, the full-size races); h2h = the duel and team-duel matches behind win rate and head-to-head."""
    import json  # noqa: PLC0415
    import re  # noqa: PLC0415
    from pathlib import Path  # noqa: PLC0415
    root = Path(__file__).resolve().parent.parent / "data" / "sport_pages"
    left = {(f["scope"], f["fixture"]) for f in (site.results.get("win_rate") or {}).get("forfeits") or []}
    exh = exhibition_ids(site)
    h2h = {x for f in site.cfg["formats"] if f["id"] in ("duel", "team") for x in f["sports"] if x not in exh}

    def fixtures(o, out):
        if isinstance(o, dict):
            i = o.get("id") or o.get("fixture")
            if isinstance(i, str) and re.match(r"^[A-Z0-9]{4}-F\d+$", i):
                out.setdefault(i, o)  # the match record, not its nested replay entry (same fixture id)
            for v in o.values():
                fixtures(v, out)
        elif isinstance(o, list):
            for v in o:
                fixtures(v, out)
    c = {"ep_sports": 0, "ep_played": 0, "ep_h2h": 0, "co_sports": 0, "co_played": 0, "co_h2h": 0}
    solo1 = solo_round1(site)
    for s in site.sports:
        f = root / f"{s['id']}.json"
        if not f.is_file() or s["id"] in exh:
            continue
        d = json.loads(f.read_text(encoding="utf-8"))
        oa, ch = {}, {}
        fixtures(d.get("open_arena") or {}, oa)
        fixtures(d.get("championship") or {}, ch)
        played = lambda fx, scope: sum(1 for k, m in fx.items() if (scope, k) not in left and not m.get("no_show")  # noqa: E731
                                       and m.get("status") in (None, "resolved") and not m.get("pending"))
        if oa:
            c["ep_sports"] += 1
            c["ep_played"] += played(oa, "arena")
            if s["id"] in h2h:
                c["ep_h2h"] += played(oa, "arena")
        elif s["id"] in solo1:  # solo: the first series match, fresh workspace
            c["ep_sports"] += 1
            c["ep_played"] += sum(1 for r in solo1[s["id"]] if not r["no_show"])
        if ch:
            c["co_sports"] += 1
            n = played(ch, "championship")
            c["co_played"] += n
            if s["id"] in h2h:
                c["co_h2h"] += n
    c["h2h_sports"] = len([x for x in h2h if x in site.sport_by_id])
    return c


def count_line(site: Site, key: str) -> str:
    c = board_counts(site)
    if key == "episodic":
        return f'{c["ep_sports"]} sports · {c["ep_played"]} matches played'
    return f'{c["co_sports"]} sports · {c["co_played"]} matches and races played'


def h2h_line(site: Site, scope: str) -> str:
    """The one footnote under Win rate and Head-to-head: what the totals are based on."""
    c = board_counts(site)
    n = c["ep_h2h"] if scope == "arena" else c["co_h2h"]
    return (f'{c["h2h_sports"]} duel and team-duel sports · {n} matches played. Solo sports, drone and racing have no '
            f'head-to-head matches.')


# ---------------------------------------------------------------- exhibition sports (data/exhibition.json)
# An exhibition sport keeps its page, results and replays but counts in no medal table, win rate or head-to-head, on
# both boards and for every entrant (models added later included). apply_exhibition() runs once per build, after
# results.json is loaded, and recomputes the medal table and win rate from the official data minus those sports, so a
# re-run of medals_sync.py / sportpage_sync.py needs no change.


def exhibition(site: Site) -> dict:
    if "_exhibition" not in site.cfg:
        import json  # noqa: PLC0415
        f = ROOT / "data" / "exhibition.json"
        site.cfg["_exhibition"] = json.loads(f.read_text(encoding="utf-8")) if f.is_file() else {}
    return site.cfg["_exhibition"]


def exhibition_ids(site: Site) -> set:
    return {x for x in (exhibition(site).get("sports") or {}) if x in site.sport_by_id}


def exhibition_label(site: Site) -> str:
    return (exhibition(site).get("label") or {}).get("en") or "Exhibition (not in the medal table)"


def _rank_table(rows: list) -> list:
    """Gold, then silver, then bronze; equal records share a rank (1, 1, 3) — the rule of medals_sync.rank_table."""
    key = lambda r: (r["gold"], r["silver"], r["bronze"])  # noqa: E731
    rows = sorted(rows, key=lambda r: tuple(-x for x in key(r)))
    for i, r in enumerate(rows):
        r["rank"] = rows[i - 1]["rank"] if i and key(rows[i - 1]) == key(r) else i + 1
    return rows


def apply_exhibition(site: Site) -> None:
    """Take the exhibition sports out of results.json's medal table and win rate (in memory, every build)."""
    res = site.results
    exh = exhibition_ids(site)
    if not exh or not res or res.get("_exhibition_applied"):
        return
    res["_exhibition_applied"] = sorted(exh)
    by = res.get("by_sport") or []
    if by and any(r.get("gold") for r in by):
        names = [m["name"] for m in site.models]
        tally = {n: {"gold": 0, "silver": 0, "bronze": 0} for n in names}
        for r in by:
            if r.get("status") != "final" or r["sport"] in exh:
                continue
            for k in ("gold", "silver", "bronze"):
                if r.get(k) in tally:
                    tally[r[k]][k] += 1
        res["medal_table"] = _rank_table([{"model": n, **c} for n, c in tally.items()])
    w = res.get("win_rate")
    if w:
        d = h2h_records(site)  # official results of the duel / team-duel sports, exhibitions already left out
        ms = d["models"]
        scopes = {}
        for key, mode in (("both", None), ("championship", 1), ("arena", 0)):
            acc = {n: {"played": 0, "won": 0, "drawn": 0, "lost": 0} for n in ms}
            for _, md, a, b, win, _ in d["matches"]:
                if mode is not None and md != mode:
                    continue
                for e in (a, b):
                    c = acc[ms[e]]
                    c["played"] += 1
                    c["won" if win == e else ("drawn" if win == -1 else "lost")] += 1
            rows = [{"model": n, **c, "pct": round(100 * c["won"] / c["played"], 1) if c["played"] else None} for n, c in acc.items()]
            rows.sort(key=lambda r: (-(r["pct"] or 0), -r["won"]))
            scopes[key] = rows
        lv = {"both": 0, "championship": 0, "arena": 0}
        for _, md, _, _, _, level in d["matches"]:
            lv["both"] += level
            lv["arena" if md == 0 else "championship"] += level
        w["scopes"], w["level_decided"] = scopes, lv
        w["forfeits"] = [f for f in w.get("forfeits") or [] if f.get("sport") not in exh]
        w["sports"] = [x for x in w.get("sports") or [] if x not in exh]
        w["not_counted"] = list(w.get("not_counted") or []) + sorted(exh)


def notes_fold(site: Site, key: str) -> str:
    """Short notes on counted results and the exhibitions, inside a board's 'How this board is made' fold."""
    ex = exhibition(site)
    names = {s["id"]: s["name"] for s in site.sports}
    exh = sorted(exhibition_ids(site), key=lambda x: [s["id"] for s in site.sports].index(x))
    items = []
    if exh:
        items.append(f'<li><b>{E(" and ".join(names[x] for x in exh))}</b>: exhibitions in this edition. Their results and replays '
                     'stay on their pages; they count in no medal table, win rate or head-to-head.</li>')
    items += [f'<li><b>{E(names.get(sid, sid))}</b>: {E(en)}</li>' for sid, en, *_ in (ex.get("notes") or {}).get(key) or []
              if sid in names and sid not in exh]
    if not items:
        return ""
    return f'<div class="hb-notes"><h4>Notes on the results</h4><ul>{"".join(items)}</ul></div>'


def exhibition_notice(site: Site, sid: str) -> str:
    """The notice block on an exhibition sport's page."""
    x = (exhibition(site).get("sports") or {}).get(sid)
    if not x or sid not in site.sport_by_id:
        return ""
    en = x.get("en") or {}
    pts = "".join(f"<li>{E(p)}</li>" for p in en.get("points") or [])
    return (f'<section class="band exh-note" id="exhibition"><div class="wrap"><div class="exh-box">'
            f'<span class="tag tag--exh">{E(exhibition_label(site))}</span><h2 class="exh-h">{E(en.get("title", ""))}</h2>'
            f'<ul class="exh-pts">{pts}</ul></div></div></section>')


# ---------------------------------------------------------------- Continual Learning: every sport's board (Olympics Championship)

CONTINUAL_BOARDS_ID = "continual-boards"  # the grid's anchor; the old "#by-sport" tab links land here too
_DECIDED = {"coin_toss": "coin toss", "toss": "coin toss", "lot": "lot", "lots": "lot", "shootout": "penalties",
            "pso": "penalties", "sudden_death": "sudden death", "walks": "tie-break", "chess_clock": "tie-break"}
_MEDAL_WORD = {1: ("g", "Gold"), 2: ("s", "Silver"), 3: ("b", "Bronze")}


def _sport_page(sid: str) -> dict:
    import json  # noqa: PLC0415
    f = ROOT / "data" / "sport_pages" / f"{sid}.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.is_file() else {}


def _ko_line(m: dict | None, label: str, first: str | None, sid: str) -> str:
    """One knockout match in one line, its winner's score first: 'Final · TEN2-F18 · 7:4'."""
    if not m or m.get("status") not in (None, "resolved"):
        return ""
    db = (m.get("decided_by") or "").lower()
    sides = m.get("sides") or []
    a = next((s for s in sides if s.get("model") == (first or m.get("winner"))), sides[0] if sides else {})
    b = next((s for s in sides if s is not a), {})
    if db == "forfeit":
        score = "forfeit"
    else:
        score = f'{a.get("score", "–")}:{b.get("score", "–")}' + (" balls left" if sid == "billiards" else "")
        if db in _DECIDED:
            score += f", {_DECIDED[db]}"
    return f'<p class="co-ko"><span>{E(label)}</span> · {E(m["id"])} · <b>{E(score)}</b></p>'


def _medal_label(rank) -> str:
    c, w = _MEDAL_WORD.get(rank, ("", ""))
    return f'<i class="medal medal--{c}"></i>{w}' if w else E(str(rank))


def _ranked_table(head: str, rows: list) -> str:
    """Place · Model · value rows (solo and race boards): medal label on places 1-3."""
    body = "".join(f'<tr><td class="oa-r co-mr{" is-m" if r in _MEDAL_WORD else ""}">{_medal_label(r)}</td>'
                   f'<td class="oa-m">{E(model_name(m))}</td><td class="oa-p">{E(v)}</td></tr>' for r, m, v in rows)
    return (f'<table class="oa-tab co-tab"><thead><tr><th>Place</th><th>Model</th><th>{E(head)}</th></tr></thead>'
            f'<tbody>{body}</tbody></table>')


def continual_panel(site: Site) -> str:
    """The Continual Learning tab's per-sport boards (Olympics Championship), the Episodic grid's card style and order:
    duel and team-duel sports first (podium of the knockout, final and bronze-match scores, round-robin standings), then
    the solo sports (mean of three matches) and the race sports (drone: final race series; racing: points over three
    races). Medals from results.json by_sport; matches and standings from data/sport_pages (read only)."""
    from layout import icon, model_logo  # noqa: PLC0415
    by = {m["name"]: m for m in site.models}
    fmt_of = {x: f["id"] for f in site.cfg["formats"] for x in f["sports"]}
    groups = {"h2h": [], "solo": [], "race": []}
    for s in site.sports:
        sid, d = s["id"], _sport_page(s["id"])
        ch, r = d.get("championship") or {}, _row(site, s["id"])
        if not ch or not r:
            continue
        tag = f' <span class="tag tag--exh">{E(exhibition_label(site))}</span>' if sid in exhibition_ids(site) else ""
        if r.get("status") != "final":
            tag += ' <span class="oa-inc">In progress</span>'
        more = site.sport_url(s) + "#records"
        fmt = fmt_of.get(sid)
        if fmt in ("duel", "team"):
            st = {x["id"]: x for x in ch.get("stages") or []}
            pod = "".join(
                f'<div class="co-pd"><span class="co-ml"><i class="medal medal--{k[0]}"></i>{k.title()}</span>'
                f'<span class="co-who">{model_logo(site, by[r[k]])}<span><b>{E(model_name(r[k]))}</b>'
                f'<small>{E(by[r[k]].get("harness", ""))} · {E(by[r[k]].get("effort", ""))} effort</small></span></span></div>'
                for k in ("gold", "silver", "bronze") if r.get(k) in by)
            fin = ((st.get("final") or {}).get("matches") or [None])[0]
            brz = ((st.get("bronze") or {}).get("matches") or [None])[0]
            ko = _ko_line(fin, "Final", r.get("gold"), sid) + _ko_line(brz, "Bronze match", r.get("bronze"), sid)
            rr = sorted((st.get("round_robin") or {}).get("standings") or [], key=lambda x: x["rank"])
            table = ""
            if rr:
                table = ('<p class="co-sub">Round robin · win 3, draw 1</p>'
                         '<table class="oa-tab"><thead><tr><th>#</th><th>Model</th><th>Pts</th><th>W-D-L</th><th>P</th></tr></thead><tbody>'
                         + "".join(f'<tr><td class="oa-r">{x["rank"]}</td><td class="oa-m">{E(model_name(x["model"]))}</td>'
                                   f'<td class="oa-p">{x["points"]}</td><td>{x["won"]}-{x["drawn"]}-{x["lost"]}</td><td>{x["played"]}</td></tr>'
                                   for x in rr) + '</tbody></table>')
            n = ch.get("played")
            line = "Round robin, then semifinals and final" + (f" · {n} matches" if n else "")
            body = f'<div class="co-pod">{pod}</div>{ko}{table}'
            link = "Full bracket"
            key = "h2h"
        elif fmt == "solo":
            unit = ch.get("unit") or "Score"
            dec = lambda v: format(v, ".2f" if v >= 1 else ".4f")  # noqa: E731  the Episodic solo cards' format
            rows = [(x["rank"], x["model"], dec(float(x["mean"] or 0))) for x in sorted(ch.get("rows") or [], key=lambda x: x["rank"])]
            line = "Mean of three matches · workspace kept between matches"
            body = _ranked_table(f"Mean · {'pts' if unit == 'pts' else unit}", rows)
            link, key = "Full results", "solo"
        elif fmt == "race" and ch.get("races"):  # drone: time trial -> two heats -> four-drone final; medals from the final
            fin = next((x for x in ch["races"] if x.get("stage") == "final"), {})
            pts = {x["model"]: x["points"] for x in fin.get("rows") or []}
            rows = [(x["rank"], x["model"], str(pts[x["model"]]) if x["model"] in pts else "out in heats")
                    for x in sorted(ch.get("ranking") or [], key=lambda x: x["rank"])]
            nr = max((len(x.get("places") or []) for x in fin.get("rows") or []), default=0)
            line = f"Time trial, two heats, then a four-drone final of {nr} races · fewer points is better"
            body = _ranked_table("Final pts", rows) + (f'<p class="co-ko"><span>Final</span> · {E(fin["id"])}</p>' if fin.get("id") else "")
            link, key = "Full results", "race"
        elif fmt == "race":  # full-size racing: points over the race series, ties by the last race
            rows = [(x["rank"], x["model"], format(x["points"], "g")) for x in sorted(ch.get("rows") or [], key=lambda x: x["rank"])]
            nr = len(ch.get("series") or [])
            line = f"{nr} races · F1 points for classified finishers · ties by the last race"
            body = _ranked_table("Pts", rows)
            link, key = "Full results", "race"
        else:
            continue
        groups[key].append(
            f'<div class="oa oa--t co">{icon(sid)}<strong>{E(s["name"])}</strong><p class="oa-st">{E(line)}{tag}</p>'
            f'{body}<a class="co-more" href="{E(more)}">{link} →</a></div>')
    cards = groups["h2h"] + groups["solo"] + groups["race"]
    if not cards:
        return ""
    return (f'<span class="anchor" id="{CONTINUAL_BOARDS_ID}"></span><span class="anchor" id="by-sport"></span>'
            '<h3 class="rm-h rs-boards-h">Every sport&rsquo;s board</h3>'
            '<p class="rp-note wr-note">Olympics Championship podium of each sport. Duel and team sports: medals from the '
            'final and the bronze match. Solo sports: the mean of three matches. Drone: the final race series. Full-size racing: '
            'points over the race series.</p>'
            f'<div class="oagrid">{"".join(cards)}</div>')
