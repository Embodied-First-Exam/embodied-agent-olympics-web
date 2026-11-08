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


ARENA_NOTE = ("An always-open leaderboard, separate from the medal table. New agents can enter at any time; every duel "
              "starts from an empty workspace. Round robin: win 3, draw 1; ties by score difference. The rating "
              "(Bradley-Terry) is for reference. Drone racing and full-size racing run in the Championship only; the "
              "four solo sports' three-run series are their medal events (By sport).")


def arena_panel(site: Site, fallback_boards: str) -> str:
    """The Open Arena tab: one official table per board (results.json open_arena, from medals_sync.py), or the
    placeholder grid before results exist."""
    oa = site.results.get("open_arena")
    if not isinstance(oa, dict) or not oa:
        return ('<p class="rp-note">An always-open leaderboard, separate from the medal table. New agents can enter at '
                'any time; every duel starts from an empty workspace. Top three per sport. Drone racing, full-size '
                f'racing and Humanoid Soccer · Team run in the Championship only.</p><div class="oagrid">{fallback_boards}</div>')
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
