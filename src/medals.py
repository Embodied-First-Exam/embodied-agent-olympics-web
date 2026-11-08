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
