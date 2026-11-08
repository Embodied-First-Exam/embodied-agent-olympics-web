"""Inner pages: Sports, sport pages, The Match, Competitions, Results, Watch. Each function returns (path, html).
One heading per screen, short lines, footage first; detail lives in the docs."""
from __future__ import annotations

import json
import re

import home as story
from layout import E, Site, icon, model_logo, model_name, page, slug, todo

CATEGORIES = ["Team ball", "Racket", "Precision", "Athletics", "Speed"]


# ---------------------------------------------------------------- helpers
def short_body(s: dict) -> str:
    b = s["body"]
    for known in ("Booster T1", "Unitree G1"):
        if b.startswith(known):
            return known + " humanoid"
    return re.split(r" \(|, |: ", b)[0].replace("Original ", "")


def short(text: str | None) -> str | None:
    """First clause only: '3 v 3; one agent controls...' -> '3 v 3'."""
    t = todo(text)
    if not t:
        return None
    t = re.split(r";|\(| — ", t)[0].strip().rstrip(",")
    return t[:1].upper() + t[1:]


def best_still(site: Site, s: dict) -> str:
    if s.get("still") and "640x360" not in (s["still"].get("size") or ""):
        return site.murl(s["still"]["url"])
    if s["clips"]:
        return site.murl(s["clips"][0]["poster"]["url"])
    return site.murl((s.get("still") or s["thumb"])["url"])


def phead(title: str, lead: str = "", extra: str = "") -> str:
    return (f'<section class="phead"><div class="wrap"><h1 class="display">{title}</h1>'
            f'{f"<p class=lead>{E(lead)}</p>" if lead else ""}{extra}</div></section>')


def docs_row(site: Site, line: str) -> str:
    return (f'<section class="band"><div class="wrap"><div class="docs-row"><p>{E(line)}</p>'
            f'{site.ext_link("docs", "Open the docs", "btn btn--ghost")}</div></div></section>')


def flag(colour: str) -> str:
    return f'<i class="flag" style="--c:{E(colour)}"></i>'


# ---------------------------------------------------------------- Sports
def sports_index(site: Site):
    chips = f'<button class="chip is-on" data-filter="all">All</button>' + "".join(
        f'<button class="chip" data-filter="{E(c)}">{E(c)}</button>' for c in CATEGORIES)
    cards = []
    for s in site.sports:
        hover = (f'<video muted loop playsinline preload="none" data-hover-src="{E(site.murl(s["clips"][0]["web_720p"]["url"]))}"></video>'
                 if s["clips"] else "")
        cards.append(f'<a class="sc" href="{site.sport_url(s)}" data-cat="{E(s["category"])}" data-hover>'
                     f'<span class="sc-media"><img src="{E(site.murl(s["thumb"]["url"]))}" alt="" loading="lazy">{hover}</span>'
                     f'<span class="sc-cat"><span class="tag">{E(s["category"])}</span></span>'
                     f'<span class="sc-body">{icon(s["id"])}<span class="sc-name">{E(s["name"])}</span></span></a>')
    body = phead(f"{len(site.sports)} sports.", "Real rules. Real robot bodies.",
                 f'<div class="chips" role="group" aria-label="Filter">{chips}</div>')
    body += f'<section class="band" style="padding-top:0"><div class="wrap"><div class="sgrid" data-grid>{"".join(cards)}</div></div></section>'
    return "sports/", page(site, path="sports/", title="Sports", body=body)


# ---------------------------------------------------------------- Sport page
def sport_page(site: Site, i: int):
    s = site.sports[i]
    prev_s, next_s = site.sports[i - 1], site.sports[(i + 1) % len(site.sports)]
    tick = story.tick_ms(s)
    facts = [("Body", short_body(s)), ("Format", short(s["team"])), ("Sees", short(s["sees"])),
             ("Control", f"Every {tick}" if tick else short(s["control"]))]
    spec = "".join(f'<div><dt class="kicker">{k}</dt><dd>{E(v) if v else "At release"}</dd></div>' for k, v in facts)
    tests = "".join(f"<li>{E(h)}</li>" for h in s["hard"])

    if s["clips"]:
        c = s["clips"][0]
        media = (f'<video muted loop playsinline preload="none" poster="{E(site.murl(c["poster"]["url"]))}" data-lazy data-autoplay '
                 f'data-web="{E(site.murl(c["web_720p"]["url"]))}"'
                 + (f' data-hd="{E(hd)}"' if (hd := site.murl(c["master_1440p"]["url"])) else "") + '></video>')
        tag = '<span class="tag shero-tag">Development replay</span>'
    else:
        media = f'<img src="{E(best_still(site, s))}" alt="">'
        tag = '<span class="tag shero-tag">Video at release</span>'

    bs = next((r for r in site.results.get("by_sport", []) if r["sport"] == s["id"]), {})
    pod = "".join(f'<div class="pod pod--{k}"><span>{k}</span><strong>{E(model_name(bs[k])) if bs.get(k) else "At release"}</strong></div>'
                  for k in ("gold", "silver", "bronze"))
    body = f"""
<section class="shero">
  <div class="shero-media">{media}</div><div class="shero-shade"></div>
  <div class="wrap shero-crumb"><a class="crumb" href="{site.url('sports/')}">← All sports</a></div>
  <div class="wrap shero-in">{icon(s['id'], 'pic pic--xl')}<h1 class="display">{E(s['name'])}</h1>
    <p class="shero-pitch">{E(s['pitch'])}</p></div>
  {tag}
</section>
<section class="band"><div class="wrap"><dl class="spec">{spec}</dl></div></section>
<section class="band" style="padding-top:0"><div class="wrap split2">
  <h2 class="h2">What it tests.</h2><ol class="tests">{tests}</ol>
</div></section>
<section class="band band--line"><div class="wrap split2">
  <h2 class="h2">Podium.</h2><div class="podium">{pod}</div>
</div></section>
<nav class="wrap prevnext" aria-label="More sports">
  <a href="{site.sport_url(prev_s)}"><span>←</span>{icon(prev_s['id'])}<strong>{E(prev_s['name'])}</strong></a>
  <a href="{site.sport_url(next_s)}"><strong>{E(next_s['name'])}</strong>{icon(next_s['id'])}<span>→</span></a>
</nav>"""
    return f"sports/{slug(s)}/", page(site, path="sports/", title=s["name"], body=body, description=s["pitch"], dark_top=True)


# ---------------------------------------------------------------- The Match
def match(site: Site):
    clips = story.clip_index(site)
    aw = """<figure class="three">
  <div class="th-box th-prac"><span class="kicker">Practice arena</span><strong>Resettable.<br>Never scored.</strong></div>
  <div class="th-wire"><span>change &amp; test →</span><span>← results</span></div>
  <div class="th-box th-ws"><span class="kicker">Agent workspace</span><strong>Code · weights · notes</strong></div>
  <div class="th-wire"><span>deploy →</span><span>← replay</span></div>
  <div class="th-box th-arena"><span class="kicker">Competition arena</span><strong>Real time.<br>Scored.</strong></div>
</figure>"""
    stack = "".join(f'<li><b>{k + 1:02d}</b><strong>{w}</strong></li>' for k, w in enumerate(["Perception", "Strategy", "Motion", "Joints"]))
    body = phead("How an agent plays.", "Three places. The agent decides when to use which.")
    body += f'<section class="band" style="padding-top:clamp(24px,3vw,48px)"><div class="wrap">{aw}</div></section>'
    body += story.chap3(site, clips, "01", "One match.", "Prepare, play, review, improve. The agent decides when.").replace("<i>/05</i>", "")
    body += f"""<section class="band"><div class="wrap">
  <div class="sec-h"><h2 class="h2">The whole stack.<br>Written by the agent.</h2></div>
  <ol class="stack4">{stack}</ol>
</div></section>"""
    body += docs_row(site, "Rules, protocols and evidence live in the docs.")
    return "match/", page(site, path="match/", title="The Match", body=body)


# ---------------------------------------------------------------- Competitions
def competitions(site: Site):
    boards = [("var(--gold)", "Medals · Persistent", "Olympics Championship", ["Six models, one schedule.", "Code, weights and notes carry over.", "Round robin, semifinals, final."]),
              ("var(--accent)", "Always open · Fresh", "Open Arena", ["New models join any time.", "Every match starts from scratch.", "Every agent plays every other."])]
    bh = "".join(f'<article class="board" style="--c:{c}"><span class="kicker">{k}</span><h2>{n}</h2>'
                 f'<ul>{"".join(f"<li>{x}</li>" for x in pts)}</ul></article>' for c, k, n, pts in boards)
    short_line = {"duel": "One against one.", "team": "Team against team.", "race": "Many on one course.", "solo": "Three runs. Improve between."}
    fmts = "".join(
        f'<div class="fmt"><h3>{E(f["name"])}</h3><p>{short_line.get(f["id"], "")}</p>'
        f'<div class="fmt-pics">{"".join(icon(x) for x in f["sports"] if x in site.sport_by_id)}</div></div>'
        for f in site.cfg["formats"])
    body = phead("Two ways<br>to compete.")
    body += f'<section class="band" style="padding-top:0"><div class="wrap boards">{bh}</div></section>'
    body += f'<section class="band" style="padding-top:clamp(24px,3vw,48px)"><div class="wrap">{story.tournament(site)}</div></section>'
    body += f'<section class="band"><div class="wrap"><div class="sec-h"><h2 class="h2">Four formats.</h2></div><div class="formats">{fmts}</div></div></section>'
    body += f"""<section class="band band--line"><div class="wrap">
  <div class="sec-h"><h2 class="h2">Did it really<br>get better?</h2><span class="tag tag--pending">Curves at release</span></div>
  <div class="static">{story.growth_panels()}</div>
</div></section>"""
    body += docs_row(site, "Schedules, seeds and scoring live in the docs.")
    return "competitions/", page(site, path="competitions/", title="Competitions", body=body)


# ---------------------------------------------------------------- Results
def medal_table(site: Site) -> str:
    rows = {r["model"]: r for r in site.results.get("medal_table", [])}
    released = any(r.get("gold") is not None for r in rows.values())
    models = list(site.models)
    if released:
        models.sort(key=lambda m: tuple(-(rows.get(m["name"], {}).get(k) or 0) for k in ("gold", "silver", "bronze")))
    cell = lambda v: "—" if v is None else E(str(v))  # noqa: E731
    body = []
    for i, m in enumerate(models):
        r = rows.get(m["name"], {})
        g, s, b = r.get("gold"), r.get("silver"), r.get("bronze")
        tot = None if g is None else (g or 0) + (s or 0) + (b or 0)
        body.append(f'<tr><td class="mt-rank">{i + 1 if released else "—"}</td>'
                    f'<td><span class="mt-model">{flag(m["colour"])}{model_logo(site, m)}<strong>{E(model_name(m))}</strong></span></td>'
                    f'<td class="mt-n">{cell(g)}</td><td class="mt-n">{cell(s)}</td><td class="mt-n">{cell(b)}</td><td class="mt-n">{cell(tot)}</td></tr>')
    head = "".join(f"<th>{h}</th>" for h in ["#", "Model", '<i class="medal medal--g"></i>Gold', '<i class="medal medal--s"></i>Silver',
                                           '<i class="medal medal--b"></i>Bronze', "Total"])
    return f'<div class="mt-wrap"><table class="mt{"" if released else " is-empty"}"><thead><tr>{head}</tr></thead><tbody>{"".join(body)}</tbody></table></div>'


def results(site: Site):
    by = {r["sport"]: r for r in site.results.get("by_sport", [])}
    groups = []
    for cat in CATEGORIES:
        rows = "".join(
            f'<tr><td><a class="bs-sport" href="{site.sport_url(s)}">{icon(s["id"])}{E(s["name"])}</a></td><td>{E(short(s["kind"]) or "")}</td>'
            + "".join(f'<td>{E(model_name(by.get(s["id"], {})[k])) if by.get(s["id"], {}).get(k) else "—"}</td>' for k in ("gold", "silver", "bronze"))
            + "</tr>" for s in site.sports if s["category"] == cat and s.get("medals"))
        if rows:
            groups.append(f'<tbody><tr class="bs-cat"><th colspan="5">{E(cat)}</th></tr>{rows}</tbody>')
    by_sport = ('<table class="bs"><thead><tr><th>Sport</th><th>Format</th><th><i class="medal medal--g"></i>Gold</th>'
                f'<th><i class="medal medal--s"></i>Silver</th><th><i class="medal medal--b"></i>Bronze</th></tr></thead>{"".join(groups)}</table>')
    oa = site.results.get("open_arena")
    oa = oa if isinstance(oa, dict) else {}
    boards = "".join(
        f'<div class="oa">{icon(s["id"])}<strong>{E(s["name"])}</strong><ol>'
        + ("".join(f'<li><span>{k + 1}</span>{E(model_name(t.get("model", "")))}</li>' for k, t in enumerate((oa.get(s["id"]) or [])[:3]))
           or "".join(f"<li><span>{k}</span>—</li>" for k in (1, 2, 3)))
        + "</ol></div>" for s in site.sports)
    mc = "".join(f'<article class="mcard" style="--c:{E(m["colour"])}">{model_logo(site, m)}<h3>{E(model_name(m))}</h3><p>{E(m["maker"])}'
                 f'{" · " + E(m["harness"]) if todo(m["harness"]) else ""}</p></article>' for m in site.models)
    tabs = [("medals", "Medal table"), ("by-sport", "By sport"), ("arena", "Open Arena"), ("models", "Models")]
    tab_btns = "".join(f'<button role="tab" class="tab{" is-on" if k == 0 else ""}" data-tab="{t}">{l}</button>' for k, (t, l) in enumerate(tabs))
    body = phead("Results.", extra=f'<div class="phead-row" style="margin-top:28px"><span class="tag tag--pending">Results at release</span></div>'
                                    f'<div class="tabs" role="tablist">{tab_btns}</div>')
    body += f"""<section class="band" style="padding-top:0"><div class="wrap">
  <div class="panel is-on" data-panel="medals">{medal_table(site)}</div>
  <div class="panel" data-panel="by-sport">{by_sport}</div>
  <div class="panel" data-panel="arena"><div class="oagrid">{boards}</div></div>
  <div class="panel" data-panel="models"><div class="mgrid">{mc}</div></div>
</div></section>"""
    return "results/", page(site, path="results/", title="Results", body=body)


# ---------------------------------------------------------------- Watch
def watch(site: Site):
    clips = []
    for s in site.sports:
        for c in s["clips"]:
            clips.append({"id": c["id"], "sport": s["name"], "sport_id": s["id"], "shows": c["shows"],
                          "src": site.murl(c["web_720p"]["url"]), "master": site.murl(c["master_1440p"]["url"]),
                          "poster": site.murl(c["poster"]["url"])})
    first = clips[0]
    tiles = "".join(f'<button class="wtile{" is-on" if k == 0 else ""}" type="button" data-clip="{E(c["id"])}">'
                    f'<span class="wtile-img"><img src="{E(c["poster"])}" alt="" loading="lazy"></span>'
                    f'<span class="wtile-t">{icon(c["sport_id"])}{E(c["sport"])}</span></button>' for k, c in enumerate(clips))
    body = phead("Watch.", extra='<div class="phead-row" style="margin-top:24px"><span class="tag">Replays from development</span></div>')
    body += f"""<section class="band" style="padding-top:0"><div class="wrap">
  <figure class="wplayer" style="margin-top:0">
    <video controls playsinline preload="metadata" poster="{E(first['poster'])}" src="{E(first['src'])}" data-wvideo></video>
    <figcaption><strong data-wtitle>{E(first['sport'])}</strong>
      <a class="link" data-wmaster href="{E(first['master'] or '#')}"{'' if first['master'] else ' hidden'} target="_blank" rel="noopener">Full resolution <span class="ext">↗</span></a></figcaption>
  </figure>
  <div class="wgrid">{tiles}</div>
  <script type="application/json" data-wclips>{json.dumps({c['id']: c for c in clips})}</script>
</div></section>"""
    return "watch/", page(site, path="watch/", title="Watch", body=body)


def not_found(site: Site):
    body = phead("Off the field.", "This page does not exist.", f'<p style="margin-top:32px"><a class="btn btn--light" href="{site.url()}">Home</a></p>')
    return "404.html", page(site, path="", title="Not found", body=body)
