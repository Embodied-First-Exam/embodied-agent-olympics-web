"""Leaderboard components shared by the home page and the Leaderboard page.

medal_board()  the medal table: one row per model, the medals themselves drawn as a unit chart (one disc per medal)
               next to the three counts. No sub-labels; harness and effort are on the row's tooltip.
sport_card()   one sport's board as a card: rank, logo, model, one value with a bar in the model's colour.
podium_card()  a knockout sport's card: gold, silver, bronze and the final's score.
"""
from __future__ import annotations

from layout import E, Site, icon, model_logo, model_name

MEDALS = (("gold", "g", "Gold"), ("silver", "s", "Silver"), ("bronze", "b", "Bronze"))


def _by(site: Site) -> dict:
    return {m["name"]: m for m in site.models}


def _tip(m: dict) -> str:
    bits = [m.get("harness"), f'{m["effort"]} effort' if m.get("effort") else None]
    return " · ".join(b for b in bits if b)


def _colour(m: dict) -> str:
    """--c (and --ol, the outline for a colour that vanishes into the dark ground) for a model."""
    ol = f';--cd:{E(m["outline_dark"])}' if m.get("outline_dark") else ""
    return f'--c:{E(m["colour"])}{ol}'


def medal_board(site: Site, rows: list, released: bool = True) -> str:
    """rows: [{model, gold, silver, bronze, rank}], already in ranking order."""
    by = _by(site)
    head = "".join(f'<span class="mdb-h" role="columnheader"><i class="mdisc mdisc--{c}"></i><span class="sr">{w}</span></span>'
                   for _, c, w in MEDALS)
    body = []
    for r in rows:
        m = by.get(r["model"])
        if not m:
            continue
        k = 0
        dots = []
        for key, c, _ in MEDALS:
            n = r.get(key) or 0
            if n:
                dots.append("<span>" + "".join(f'<i class="mdisc mdisc--{c}" style="--i:{k + j}"></i>' for j in range(n)) + "</span>")
                k += n
        nums = "".join(
            f'<span class="mdb-n{" is-0" if not r.get(key) else ""}" role="cell">{"—" if r.get(key) is None else r[key]}</span>'
            for key, _, _ in MEDALS)
        rank = r.get("rank") if released else "—"
        body.append(
            f'<div class="mdb-row{" is-1" if rank == 1 else ""}" role="row" title="{E(_tip(m))}">'
            f'<span class="mdb-rank" role="cell">{rank}</span>'
            f'<span class="mdb-who" role="rowheader">{model_logo(site, m)}<strong>{E(model_name(m))}</strong></span>'
            f'<span class="mdb-dots" aria-hidden="true">{"".join(dots)}</span>{nums}</div>')
    return (f'<div class="mdb{"" if released else " is-empty"}" role="table" aria-label="Medal table">'
            f'<div class="mdb-row mdb-head" role="row"><span class="sr" role="columnheader">Rank</span>'
            f'<span class="sr" role="columnheader">AI agent</span><span></span>{head}</div>{"".join(body)}</div>')


def _fmt(v) -> str:
    if isinstance(v, str):
        return v
    if isinstance(v, int) or float(v).is_integer():
        return str(int(v))
    return format(v, ".2f" if abs(v) >= 1 else ".4f")


def sport_card(site: Site, s: dict, rows: list, unit: str, href: str | None = None, tag: str = "", medals: bool = False,
               foot: str = "") -> str:
    """rows: [(rank, model name, value | None, label | None)]; the bar is value / best value.
    medals=True draws a medal disc on ranks 1-3 (boards that award medals)."""
    by = _by(site)
    vals = [v for _, _, v, _ in rows if isinstance(v, (int, float))]
    top = max(vals, default=0) or 1
    disc = {1: "g", 2: "s", 3: "b"}
    items = []
    for rank, name, v, label in rows:
        m = by.get(name)
        if not m:
            continue
        w = max(0.0, min(1.0, (v or 0) / top)) if isinstance(v, (int, float)) else 0
        r = (f'<i class="mdisc mdisc--{disc[rank]}"></i>' if medals and rank in disc else f'<span class="bc-r">{E(str(rank))}</span>')
        items.append(
            f'<li class="bc-row{" is-1" if rank == 1 else ""}" style="{_colour(m)}" title="{E(_tip(m))}">{r}{model_logo(site, m)}'
            f'<b>{E(model_name(m))}</b><span class="bc-bar"><i style="width:{w * 100:.1f}%"></i></span>'
            f'<em>{E(label if label is not None else _fmt(v))}</em></li>')
    return _card(site, s, f'<ol class="bc-rows{"" if vals else " bc-rows--plain"}">{"".join(items)}</ol>{foot}', unit, href, tag)


def podium_card(site: Site, s: dict, podium: list, final: str = "", href: str | None = None, tag: str = "") -> str:
    """podium: [(medal class g|s|b, model name)]; final: the final's score line (already HTML)."""
    by = _by(site)
    items = "".join(
        f'<li class="bc-row bc-row--p{" is-1" if c == "g" else ""}" title="{E(_tip(by[n]))}"><i class="mdisc mdisc--{c}"></i>'
        f'{model_logo(site, by[n])}<b>{E(model_name(n))}</b></li>' for c, n in podium if n in by)
    return _card(site, s, f'<ol class="bc-rows">{items}</ol>{final}', "", href, tag)


def _card(site: Site, s: dict, body: str, unit: str, href: str | None, tag: str) -> str:
    head = (f'<header class="bc-h">{icon(s["id"])}<h4>{E(s["name"])}</h4>{tag}'
            f'{f"<span class=bc-u>{E(unit)}</span>" if unit else ""}</header>')
    more = f'<a class="bc-more" href="{E(href)}" aria-label="{E(s["name"])}: full results"><span class="arr">→</span></a>' if href else ""
    return f'<article class="bc">{head}{body}{more}</article>'
