"""The sport page (SPORTPAGE, 11-08): four blocks, one screen each where possible.

    01 Overview                    footage, name, one line; body, format, observation, action, control, GPU kit;
                                   what the athlete sees and controls (robot camera + broadcast, one line each)
    02 Competition records         podium; Olympics Championship by stage and Open Arena, every match with its score,
                                   result and replay (replays sit in the records, there is no separate replay wall)
    03 Challenges & capabilities   why the sport is hard = what it tests: the sport card's skills grouped by the four
                                   capabilities; each skill opens to its real-sport meaning, test, pass line, readings
    04 Agent performance & growth  A what the agents achieved, B how they built it (model selector),
                                   C Checkpoint Evaluation (performance growth + capability growth)

Data contract: data/sport_pages/<sport id>.json (schema eo-sportpage/1), written by the coordinator's
tools/web/sportpage_sync.py from the official run; a sport without that file keeps the old page (pages.sport_page).
Top-level keys the template reads:
  format            duel | team | solo | race (site.json formats)
  status            final | in_progress;  provisional (bool);  podium {gold, silver, bronze} (model names)
  championship      duel/team: {stages: [{id: round_robin, standings: [...], matches: [...]}, {id: semi_final|final|bronze,
                    matches}]};  race: {races: [{name, rows: [{place, model, places, points, best_time_s}], races, replay}],
                    trial: [{seed, model, mean, matches: [{id, match, value, best_time_s, replay}]}], scoring}
  open_arena        same shape as a duel championship (round robin only) or null (sport has no Open Arena)
  match             {id, label?, labels, sides: [{seat, model, score}], winner, note, replay}
  replay            {kind: full | compressed | highlight | states, seconds, path (in the media repo)} or null
  capabilities      {skills: [{id, group phys|comp|eng|adap, name, real, measure, line, secondary, three_checks}],
                    off: [{name, group, why}], results: {model: {skill: {status pass|fail|na, reading?, checkpoint}}},
                    pass_marks: page | derived}
  agents            {per_model: {model: {matches, versions, switches, model_calls, output_tokens, reviews, gpu,
                    train_code, practice_world, realtime_rehearsal, seat_matches}},
                    checkpoint: {kind, measure, ref, count, lines: {model: [{cp, x, mean, n}]}, verdict: {model: text},
                    capability: {n, names, ref, lines: {model: [{cp, x, n_pass}]}}}}
  notes             hand-written: {challenge, achieved: [{text, evidence: [...]}], built: {model: [lines]}}
  interface         hand-written + rendered: {sees, controls, details: [lines], moment, camera {src, w, h, label}
                    (or {text, label} for a sport without a camera), broadcast {src, w, h, label}}; images under
                    assets/img/pov/; absent = the card is hidden
Replays link only when site.json replay_base is set (a public host of the media repo); until then each match shows its
replay type and length with "at release".
"""
from __future__ import annotations

import json
import re

import home as story
import medals
from layout import ROOT, E, Site, icon, model_logo, model_name, page, slug

GROUPS = [("phys", "Physical"), ("comp", "Competitive"), ("eng", "Engineering"), ("adap", "Adaptive")]
SHORT = {"Claude Opus 5.5": "Opus", "GPT-6 Astra": "Astra", "Gemini 4 Argon": "Gemini", "Kimi 3.1 Pro": "Kimi",
         "DeepSeek V4.1 Flash": "DeepSeek", "GLM 5.3 Flash": "GLM"}
REPLAY_KIND = {"full": "Full match replay", "compressed": "Time-compressed replay", "highlight": "Selected highlight",
               "states": "Replay"}


def load(sport_id: str) -> dict | None:
    p = ROOT / "data" / "sport_pages" / f"{sport_id}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else None


# ---------------------------------------------------------------- small pieces
def _m(site: Site, name: str) -> dict:
    return next((m for m in site.models if m["name"] == name), {"name": name, "colour": "#888", "harness": "", "effort": ""})


def who(site: Site, name: str, cls: str = "", sub: bool = False, note: str = "") -> str:
    if not name:
        return '<span class="sp-who is-tbd"><span class="sp-who-t"><strong>To be decided</strong></span></span>'
    m = _m(site, name)
    s = f'<small>{E(m.get("harness", ""))} · {E(m.get("effort", ""))} effort</small>' if sub else ""
    if note:
        s += f'<small class="seats">{E(note)}</small>'
    return (f'<span class="sp-who {cls}"><i class="flag" style="--c:{E(m["colour"])}"></i>{model_logo(site, m)}'
            f'<span class="sp-who-t"><strong><span class="nm-f">{E(model_name(m))}</span><span class="nm-s">{E(SHORT.get(m["name"], model_name(m)))}</span></strong>{s}</span></span>')


def mmss(s: float | None) -> str:
    if s is None:
        return ""
    s = int(round(s))
    return f"{s // 60}:{s % 60:02d}"


def media_url(site: Site, r: dict | None, which: str = "replay") -> str | None:
    """URL of a match video from site.json replay_base / highlight_base (null = not hosted yet). A base may carry
    {path} (file path in the media repo), {key} (sport key) and {fixture}; without placeholders the path is appended."""
    if not r:
        return None
    base = site.cfg.get(f"{which}_base")
    if not base or (which == "replay" and not r.get("path")) or (which == "highlight" and not r.get("highlight")):
        return None
    vals = {"path": r.get("path") or "", "key": r.get("key") or "", "fixture": r.get("fixture") or ""}
    if "{" in base:
        return base.format(**vals)
    return base.rstrip("/") + "/" + vals["path"]


def play_attrs(site: Site, r: dict | None, title: str) -> str:
    """data-* for the in-page player (sport.js); empty when there is no playable video."""
    src, hl = media_url(site, r), media_url(site, r, "highlight")
    if not src and hl:  # no full video (e.g. Open Arena: recorded states only), but a highlight reel exists
        return f' data-play="{E(hl)}" data-kind="Selected highlight" data-title="{E(title)}"'
    if not src:
        return ""
    kind = REPLAY_KIND.get(r.get("kind"), "Replay")
    tl = r.get("fixture") and (ROOT / "data" / "timelines" / f'{r["fixture"]}.json').is_file()
    return (f' data-play="{E(src)}" data-kind="{E(kind)}" data-title="{E(title)}"'
            + (f' data-hl="{E(hl)}"' if hl else "")
            + (f' data-tl="{E(site.url("timelines/" + r["fixture"] + ".json"))}"' if tl else ""))


def no_replay_why(r: dict | None) -> str:
    if r and r.get("kind") == "states":
        return "No replay (recorded states only)"
    return "No replay"


def replay(site: Site, r: dict | None, compact: bool = False, title: str = "") -> str:
    """The replay slot of a match: a play button when the video is hosted, else its type and length, 'at release'."""
    if not r or (r.get("kind") == "states" and not play_attrs(site, r, title)):
        return f'<span class="rp rp--none" title="{E(no_replay_why(r))}">No replay</span>'
    kind = REPLAY_KIND.get(r.get("kind"), "Replay") if r.get("kind") != "states" else "Selected highlight"
    length = mmss(r.get("seconds"))
    label = (f'<b>▶</b>{"" if compact else E(kind)}{(" · " if not compact else "") + length if length else ""}')
    pa = play_attrs(site, r, title)
    if pa:
        return f'<button type="button" class="rp"{pa} aria-label="Play: {E(title or kind)}">{label}</button>'
    return f'<span class="rp rp--wait" title="{E(kind)}{" · " + length if length else ""} · at release">{label}</span>'


def secs(v) -> str:
    return f"{v:.1f} s" if v else "–"


def small_secs(v) -> str:
    return f"<small>{v:.1f} s</small>" if v else ""


def score_of(m: dict, model: str):
    return next((s["score"] for s in m["sides"] if s["model"] == model), None)


def seat_note(side: dict) -> str:
    """Team duel with one agent per robot: '3 agents · A1 A2 A3'."""
    s = side.get("seats")
    return f'{len(s)} agents · {" ".join(s)}' if s else ""


def card_match(site: Site, m: dict, title: str) -> str:
    """One knockout match as a small score card: two rows, winner bright, the replay slot under it."""
    pend = m.get("status") == "pending"
    rows = "".join(
        f'<div class="kc-r{" is-w" if s["model"] == m["winner"] or pend else ""}">{who(site, s["model"], note=seat_note(s))}'
        f'<b class="kc-s">{E(str(s["score"])) if s["score"] is not None else "–"}</b></div>' for s in m["sides"])
    note = f'<p class="kc-note">{E(m["note"])}</p>' if m.get("note") else ""
    ttl = f'{title} · ' + " v ".join(f'{model_name(_m(site, s["model"]))} {s["score"]}' for s in m["sides"])
    pa = "" if pend else play_attrs(site, m.get("replay"), ttl)
    attrs = f' tabindex="0" role="button" aria-label="Play: {E(ttl)}"{pa}' if pa else (f' title="{E(no_replay_why(m.get("replay")))}"' if not pend else "")
    return (f'<article class="kc{" kc--play" if pa else ""}"{attrs}><header><span class="kicker">{E(title)}</span><span class="mx-id">{E(m["id"])}</span></header>'
            f'{rows}{note}<footer>{"" if pend else replay(site, m.get("replay"), title=ttl)}</footer></article>')


def row_match(site: Site, m: dict, tag: str = "") -> str:
    """One match as a list row: tag, side A, score, side B, note, replay."""
    a, b = (m["sides"] + [{"model": "", "score": None}] * 2)[:2]
    sa, sb = ("–" if a["score"] is None else a["score"]), ("–" if b["score"] is None else b["score"])
    pend = m.get("status") == "pending"
    wa, wb = (a["model"] == m["winner"] or pend), (b["model"] == m["winner"] or pend)
    return (f'<li class="mx{" is-pend" if pend else ""}"><span class="mx-tag">{E(tag)}</span>'
            f'<span class="mx-a{" is-w" if wa else ""}">{who(site, a["model"], note=seat_note(a))}</span>'
            f'<span class="mx-sc"><b{" class=is-w" if wa else ""}>{E(str(sa))}</b><i>:</i><b{" class=is-w" if wb else ""}>{E(str(sb))}</b></span>'
            f'<span class="mx-b{" is-w" if wb else ""}">{who(site, b["model"], note=seat_note(b))}</span>'
            f'<span class="mx-n">{E(m.get("note") or "")}</span><span class="mx-id">{E(m["id"])}</span>'
            f'<span class="mx-r">{"" if pend else replay(site, m.get("replay"), compact=True)}</span></li>')


def standings(site: Site, rows: list, qualify: int = 0) -> str:
    body = "".join(
        f'<tr{" class=is-q" if qualify and r["rank"] <= qualify else ""}><td class="st-r">{r["rank"]}</td><td>{who(site, r["model"])}</td>'
        f'<td class="st-n">{r["won"]}-{r["drawn"]}-{r["lost"]}</td><td class="st-n">{E(str(r["for"]))}:{E(str(r["against"]))}</td>'
        f'<td class="st-n st-p">{r["points"]}</td></tr>' for r in rows)
    return ('<table class="st"><thead><tr><th>#</th><th>AI agent</th><th>W-D-L</th><th>Score</th><th>Pts</th></tr></thead>'
            f'<tbody>{body}</tbody></table>')


# ---------------------------------------------------------------- 01 overview
def overview(site: Site, s: dict, d: dict) -> str:
    from pages import GPU_KIT, best_still, short_body  # noqa: PLC0415
    fmt = next((f for f in site.cfg["formats"] if f["id"] == d.get("format")), {})
    tick = story.tick_ms(s)
    hz = f"{1000 // int(tick.split()[0])} Hz · every {tick}" if tick else None
    # the command without its rate (the Control cell has it): cut at "every <n> ms" only, so "A target for every joint
    # every 20 ms" keeps "every joint"; a placeholder (TODO) shows as "At release"
    action = re.sub(r"\s+every \d[\d.]*\s*(?:ms|s)\b.*$", "", (s.get("control") or "").split(";")[0]).strip()
    action = None if action.upper() in ("", "TODO") else action
    sees = re.sub(r"\s*\([^)]*\)", "", (s.get("sees") or "").split(";")[0])
    team = (s.get("team") or "").split(";")[0]
    if (d.get("championship") or {}).get("trial"):  # race with a time trial: the stages are the format
        team = "time trial, heats, final"
    elif (d.get("championship") or {}).get("series") is not None:
        team = "series of six-car races"
    elif d.get("format") == "solo":
        team = "three-match series"
    band = s.get("band") or {}                 # hand-checked cells from the official task (data/sports.json `band`)
    action = band.get("action") or action
    hz = band.get("control") or hz
    facts = [("Body", short_body(s)), ("Format", f'{fmt.get("name", "")} · {team}' if team else fmt.get("name")),
             ("Observation", sees), ("Action", action), ("Control", hz), ("Training", GPU_KIT.get(s["id"]))]
    spec = "".join(f'<div><dt class="kicker">{k}</dt><dd>{E(v) if v else "At release"}</dd></div>' for k, v in facts)
    if s["clips"]:
        c = s["clips"][0]
        media = (f'<video muted loop playsinline preload="none" poster="{E(site.murl(c["poster"]["url"]))}" data-lazy data-autoplay '
                 f'data-web="{E(site.murl(c["web_720p"]["url"]))}"'
                 + (f' data-hd="{E(hd)}"' if (hd := site.murl(c["master_1440p"]["url"])) else "") + '></video>')
        tag = (f'<span class="tag shero-tag">Official match · {E(c["match"])}</span>' if c.get("match")
               else '<span class="tag shero-tag">Development replay</span>')
    else:
        media = f'<img src="{E(best_still(site, s))}" alt="">'
        tag = '<span class="tag shero-tag">Video at release</span>'
    return f"""
<section class="shero sp-hero" id="overview">
  <div class="shero-media">{media}</div><div class="shero-shade"></div>
  <div class="wrap shero-crumb"><a class="crumb" href="{site.url('sports/')}">← All sports</a></div>
  <div class="wrap shero-in"><span class="sp-n">01<i>/04</i> · Overview</span>{icon(s['id'], 'pic pic--xl')}<h1 class="display">{E(s['name'])}</h1>
    <p class="shero-pitch">{E(s['pitch'])}</p></div>
  {tag}
</section>
<section class="sp-specband"><div class="wrap"><dl class="spec sp-spec">{spec}</dl></div></section>""" + athlete_view(site, d)


def athlete_view(site: Site, d: dict) -> str:
    """01b 'What the athlete sees and controls' (POVCARD, 11-09): the robot's own camera and the broadcast at the same
    instant of a real match, one line each for what the program receives and what it commands, the full interface
    folded. Data: d["interface"] (see the module docstring). Hidden when the sport has no interface yet."""
    it = d.get("interface")
    if not it:
        return ""

    def fig(x: dict, cls: str) -> str:
        if not x:
            return ""
        if x.get("src"):
            w, h = int(x.get("w") or 16), int(x.get("h") or 9)
            body = (f'<span class="pov-img"><img src="{E(site.asset(x["src"]))}" width="{w}" height="{h}" '
                    f'alt="{E(x.get("alt") or x.get("label") or "")}" loading="lazy"></span>')
        else:                                   # a sport without a camera: the observation as text
            w, h = 4, 3
            body = f'<span class="pov-img pov-txt"><pre>{E(x.get("text") or "")}</pre></span>'
        return (f'<figure class="pov-fig {cls}" style="--ar:{w / h:.4f}">{body}'
                f'<figcaption>{E(x.get("label") or "")}</figcaption></figure>')

    lines = "".join(f"<li>{E(t)}</li>" for t in it.get("details") or [])
    more = (f'<details class="pov-more"><summary>Full interface <span class="arr">▾</span></summary>'
            f'<ul>{lines}</ul></details>') if lines else ""
    moment = f'<p class="pov-moment">{E(it["moment"])}</p>' if it.get("moment") else ""
    return f"""
<section class="sp-pov" aria-labelledby="pov-h"><div class="wrap">
  <h2 class="pov-h" id="pov-h">What the athlete sees and controls</h2>
  <div class="pov-shots">{fig(it.get("camera") or {}, "is-cam")}{fig(it.get("broadcast") or {}, "is-bc")}</div>
  {moment}
  <dl class="pov-lines"><div><dt>Sees</dt><dd>{E(it.get("sees") or "At release")}</dd></div>
    <div><dt>Controls</dt><dd>{E(it.get("controls") or "At release")}</dd></div></dl>
  {more}
</div></section>"""


def subnav(site: Site) -> str:
    items = [("overview", "Overview"), ("records", "Records"), ("capabilities", "Capabilities"), ("agents", "Agents")]
    return ('<nav class="sp-sub" aria-label="On this page" data-spnav><div class="wrap">'
            + "".join(f'<a href="#{k}" data-spnav-a="{k}">{v}</a>' for k, v in items) + "</div></nav>")


def head(n: str, title: str, lede: str = "", extra: str = "") -> str:
    return (f'<header class="ch-head sp-head"><span class="ch-n">{n}<i>/04</i></span><h2>{title}</h2>'
            f'{f"<p>{E(lede)}</p>" if lede else ""}{extra}</header>')


# ---------------------------------------------------------------- 02 competition records
def podium(site: Site, d: dict) -> str:
    p = d.get("podium") or {}
    if not any(p.values()):
        txt = "Medals when the Championship ends" if d.get("status") == "in_progress" else "Medals at release"
        return f'<div class="sp-pod is-empty"><span class="tag tag--pending">{txt}</span></div>'
    cells = "".join(
        f'<div class="sp-pd sp-pd--{k}"><span class="kicker"><i class="medal medal--{k[0]}"></i>{k}</span>{who(site, p[k], sub=True)}</div>'
        for k in ("gold", "silver", "bronze") if p.get(k))
    return f'<div class="sp-pod">{cells}</div>'


def _mark(m: dict) -> str:
    """P = penalty shoot-out, T = coin toss or lot, F = forfeit / no-show, TB = the sport's other tie-break."""
    db = (m.get("decided_by") or "").lower()
    if db in ("shootout", "sudden_death", "pso"):
        return "P"
    if db in ("coin_toss", "lot", "lots", "toss"):
        return "T"
    if db == "forfeit" or (m.get("note") or "").startswith("Forfeit"):
        return "F"
    if db in ("walks", "chess_clock"):
        return "TB"
    return ""


MARK_WORDS = {"P": "won on penalties (shoot-out)", "T": "decided by coin toss or lot", "F": "forfeit: one side did not start",
              "TB": "level, decided by the sport's tie-break rule"}


def cross_table(site: Site, rr: dict, anchor: str = "m") -> str:
    """Round robin as a 6 x 6 cross table in the home page grid's order and colours. Each cell: the result from the row
    model's view (W / D / L) and the score, row model first; a click opens the match's row in the folded list."""
    ms = site.models
    names = [m["name"] for m in ms]
    cell = {}
    for m in rr.get("matches", []):
        if len(m["sides"]) < 2:
            continue
        a, b = m["sides"][0], m["sides"][1]
        for x, y in ((a, b), (b, a)):
            if x["model"] in names and y["model"] in names:
                prev = cell.get((x["model"], y["model"]))
                if prev and prev.get("status") != "pending" and m.get("status") == "pending":
                    continue
                cell[(x["model"], y["model"])] = {**m, "_me": x, "_op": y}
    hdr = "".join(f'<span class="tm-h xt-hd" title="{E(model_name(m))}" style="--c:{E(m["colour"])}">{model_logo(site, m)}</span>' for m in ms)
    body, used = [], set()
    for mi in ms:
        row = [f'<span class="tm-h xt-rh" title="{E(model_name(mi))}" style="--c:{E(mi["colour"])}">{model_logo(site, mi)}</span>']
        for mj in ms:
            if mi is mj:
                row.append('<i class="tm-x xt-x"></i>')
                continue
            c = cell.get((mi["name"], mj["name"]))
            if not c or c.get("status") == "pending":
                tip = f'{model_name(mi)} v {model_name(mj)}' + (f' · {c["id"]} · not played yet' if c else " · not played yet")
                row.append(f'<span class="xt-c xt-p" title="{E(tip)}">–</span>')
                continue
            me, op = c["_me"], c["_op"]
            res = "W" if c["winner"] == mi["name"] else ("L" if c["winner"] == mj["name"] else "D")
            mk = _mark(c)
            used.add(mk)
            so = c.get("shootout") or {}
            sotxt = f' · shoot-out {so.get(mi["name"], "?")}:{so.get(mj["name"], "?")}' if so else ""
            r = c.get("replay") or {}
            rp = f' · {REPLAY_KIND.get(r.get("kind"), "Replay")} {mmss(r.get("seconds"))}, click to play'.rstrip() if media_url(site, r) else " · no replay yet"
            word = {"W": "won", "L": "lost", "D": "drew"}[res]
            tip = (f'{c["id"]} · {model_name(mi)} {word} {me["score"]}:{op["score"]} v {model_name(mj)}'
                   + (f' · {MARK_WORDS[mk]}' if mk else "") + sotxt + rp)
            tag = res + (f"·{mk}" if mk else "")
            ttl = f'{c["id"]} · {model_name(mi)} {me["score"]}:{op["score"]} {model_name(mj)}'
            pa = play_attrs(site, r, ttl)
            inner = f'<b>{tag}</b><span>{E(str(me["score"]))}:{E(str(op["score"]))}</span>'
            if pa:
                row.append(f'<button type="button" class="xt-c xt-{res.lower()} xt-play" title="{E(tip)}"{pa}>{inner}</button>')
            else:
                why = no_replay_why(r) if r.get("kind") == "states" or not r.get("path") else "Replay at release"
                tip = tip.replace(" · no replay yet", "") + f" · {why}"
                row.append(f'<span class="xt-c xt-{res.lower()} xt-np" title="{E(tip)}">{inner}</span>')
        body.append("".join(row))
    legend = ('<span><b class="xt-k xt-w">W</b>row model won</span><span><b class="xt-k xt-l">L</b>row model lost</span>'
              '<span><b class="xt-k xt-d">D</b>draw</span><span><b class="xt-k xt-p">–</b>not played yet</span>'
              + "".join(f'<span><b class="xt-k">·{k}</b>{MARK_WORDS[k]}</span>' for k in ("P", "T", "F", "TB") if k in used)
              + '<span>Score: row model first</span>')
    return (f'<div class="xt-wrap"><div class="xt" style="--n:{len(ms)}"><span class="xt-corner"></span>{hdr}'
            f'{"".join(body)}</div></div><p class="xt-legend">{legend}</p>')


def _diff(r: dict) -> str:
    """Score difference as the standings rank it (data "diff"; lower-is-better sports such as billiards give
    against - for), else for - against."""
    d = r.get("diff")
    if d is None:
        d = (r["for"] or 0) - (r["against"] or 0)
    return ("+" if d > 0 else "") + str(d)


def standings_big(site: Site, rows: list, qualify: int = 0) -> str:
    body = "".join(
        f'<tr{" class=is-q" if qualify and r["rank"] <= qualify else ""}><td class="st-r">{r["rank"]}</td><td>{who(site, r["model"])}</td>'
        f'<td class="st-n">{r["won"]}-{r["drawn"]}-{r["lost"]}</td>'
        f'<td class="st-n">{_diff(r)}</td>'
        f'<td class="st-n st-p">{r["points"]}</td></tr>' for r in rows)
    foot = (f'<p class="sb-q"><i></i>Top {qualify} go to the semifinals</p>' if qualify else "")
    return ('<table class="st sb"><thead><tr><th>#</th><th>AI agent</th><th>W-D-L</th><th>Diff</th><th>Pts</th></tr></thead>'
            f'<tbody>{body}</tbody></table>{foot}')


def podium_box(site: Site, d: dict) -> str:
    p = d.get("podium") or {}
    if not any(p.values()):
        return ('<div class="pb pb--wait"><h3 class="cr-h">Medals</h3><span class="tag tag--pending">'
                f'{"Medals when the Championship ends" if d.get("status") != "final" else "Medals at release"}</span></div>')
    cells = "".join(f'<div class="pb-m pb-{k}"><span class="kicker"><i class="medal medal--{k[0]}"></i>{k}</span>{who(site, p[k], sub=True)}</div>'
                    for k in ("gold", "silver", "bronze") if p.get(k))
    return f'<div class="pb"><h3 class="cr-h">Medals</h3>{cells}</div>'


def bracket(site: Site, st: dict, has_rr: bool) -> str:
    """Semifinals on the left, final and bronze on the right, wired like the home page bracket."""
    get = lambda sid, k: ((st.get(sid) or {}).get("matches") or [None, None])[k] if len((st.get(sid) or {}).get("matches") or []) > k else None  # noqa: E731
    def card(m, title, cls=""):
        if m:
            return card_match(site, m, m.get("label") or title).replace('<article class="kc"', f'<article class="kc {cls}"', 1)
        wait = {"Semifinal 1": "1st v 4th of the round robin", "Semifinal 2": "2nd v 3rd of the round robin"}.get(title, "After the semifinals")
        return f'<article class="kc kc--tbd {cls}"><header><span class="kicker">{title}</span></header><p class="kc-note kc-wait">{wait}</p></article>'
    sf = sorted((st.get("semi_final") or {}).get("matches", []), key=lambda m: m.get("label") or m["id"])
    s1, s2 = (sf + [None, None])[:2]
    fin, brz = get("final", 0), get("bronze", 0)
    return f"""
<div class="kb">
  <div class="kb-col">{card(s1, "Semifinal 1")}{card(s2, "Semifinal 2")}</div>
  <svg class="kb-wires" viewBox="0 0 40 200" preserveAspectRatio="none" aria-hidden="true"><path d="M0 50 H20 V92 H40"/><path d="M0 150 H20 V108 H40"/></svg>
  <div class="kb-col kb-col--r">{card(fin, "Final", "kc--fin")}{card(brz, "Bronze match", "kc--brz")}</div>
</div>"""


def rr_list(site: Site, rr: dict, anchor: str, numbered: bool = False) -> str:
    ms = rr.get("matches", [])
    if numbered:
        rows = "".join(row_match(site, m, f"#{k + 1}").replace('<li class="mx', f'<li id="{anchor}-{m["id"]}" class="mx', 1) for k, m in enumerate(ms))
    else:
        by = {}
        for m in ms:
            by.setdefault(m["labels"].get("round") or 0, []).append(m)
        rows = "".join(row_match(site, m, f"R{r}").replace('<li class="mx', f'<li id="{anchor}-{m["id"]}" class="mx', 1) for r in sorted(by) for m in by[r])
    played = sum(1 for m in ms if m.get("status") != "pending")
    return (f'<details class="cr-all" data-xt-list><summary>All {len(ms)} round-robin matches{f" · {played} played" if played < len(ms) else ""} · scores and replays '
            f'<span class="arr">↓</span></summary><ol class="mxl">{rows}</ol></details>')


def duel_champ(site: Site, ch: dict, d: dict | None = None) -> str:
    st = {x["id"]: x for x in ch["stages"]}
    rr = st.get("round_robin") or {"matches": [], "standings": []}
    played = sum(1 for m in rr["matches"] if m.get("status") != "pending")
    total = len(rr["matches"])
    sub = "" if played == total else f"{played} of {total} played"
    return f"""
<div class="cx-row">
  <div class="cx-l"><h3 class="cr-h">Round robin <span>{sub}</span></h3>{cross_table(site, rr, "cm")}</div>
  <div class="cx-r"><h3 class="cr-h">Standings <span>win 3 · draw 1</span></h3>{standings_big(site, rr["standings"], 4)}</div>
</div>
<div class="cx-row cx-row--2">
  <div class="cx-l"><h3 class="cr-h">Knockout</h3>{bracket(site, st, bool(rr))}</div>
  <div class="cx-r">{podium_box(site, d or {})}</div>
</div>"""


def race_champ(site: Site, ch: dict) -> str:
    def table(rc: dict, final: bool) -> str:
        n = max((len(r["places"]) for r in rc["rows"]), default=0)
        hd = "".join(f"<th>R{k + 1}</th>" for k in range(n))
        body = "".join(
            f'<tr{" class=is-q" if (not final and r["place"] <= 2) else ""}><td class="st-r">{r["place"]}</td><td>{who(site, r["model"])}</td>'
            + "".join(f'<td class="st-n pl pl-{x}">{x}</td>' for x in r["places"])
            + f'<td class="st-n st-p">{r["points"]}</td><td class="st-n">{secs(r["best_time_s"])}</td></tr>'
            for r in rc["rows"])
        return (f'<article class="rc{" rc--final" if final else ""}"><header><h3 class="cr-h">{E(rc["name"])}</h3><span class="mx-id">{E(rc["id"])}</span>'
                f'{replay(site, rc.get("replay"))}</header>'
                f'<table class="st"><thead><tr><th>#</th><th>AI agent</th>{hd}<th>Pts</th><th>Best finish</th></tr></thead><tbody>{body}</tbody></table></article>')
    fin = [r for r in ch["races"] if r["stage"] == "final"]
    heats = [r for r in ch["races"] if r["stage"] == "heat"]
    trial = "".join(
        f'<tr><td class="st-r">{t["seed"]}</td><td>{who(site, t["model"])}</td>'
        + "".join(f'<td class="st-n tt">{m["value"]:.2f}{small_secs(m.get("best_time_s"))}'
                  f'{replay(site, m.get("replay"), compact=True)}</td>' for m in t["matches"])
        + f'<td class="st-n st-p">{t["mean"]:.2f}</td></tr>' for t in ch["trial"])
    return f"""
<div class="cr-race">
  {"".join(table(r, True) for r in fin)}
  <div class="rc-heats">{"".join(table(r, False) for r in heats)}</div>
</div>
<details class="cr-all" open><summary>Time trial · seeding for the heats <span class="arr">↓</span></summary>
  <table class="st st--tt"><thead><tr><th>Seed</th><th>AI agent</th><th>Match 1</th><th>Match 2</th><th>Match 3</th><th>Mean</th></tr></thead><tbody>{trial}</tbody></table>
  <p class="cr-rule">Course progress per match: 1 + (180 s − time) / 180 s for a finished round (best of three), below 1 by gates passed. Heats and final: points 1-2-3-4 per race, fewer is better.</p>
</details>"""


def solo_champ(site: Site, ch: dict) -> str:
    u = ch.get("unit") or ""
    fmtv = (lambda v: f"{v:.2f}") if u in ("m/s", "m") else (lambda v: f"{v:.1f}")  # noqa: E731
    body = []
    for r in ch["rows"]:
        vals = [m["value"] for m in r["matches"] if m["value"] is not None]
        top = max(vals) if vals else None
        cells = "".join(
            (f'<td class="st-n tt is-ns" title="Did not start: counts 0">{fmtv(m["value"] or 0)}<small>no-show</small></td>' if m.get("no_show") else
             f'<td class="st-n tt{" is-best" if m["value"] == top else ""}">{fmtv(m["value"])}{replay(site, m.get("replay"), compact=True)}</td>'
             if m["value"] is not None else '<td class="st-n tt is-pend">Pending</td>') for m in r["matches"])
        body.append(f'<tr><td class="st-r">{r["rank"]}</td><td>{who(site, r["model"])}</td>{cells}'
                    f'<td class="st-n st-p">{fmtv(r["mean"]) if r["mean"] is not None else "–"}</td></tr>')
    how = "Mean" if ch.get("rank_by") == "mean" else "Best"
    return f"""
<div class="cr-solo"><h3 class="cr-h">Three-match series <span>ranked by the {E(ch.get("rank_by") or "")} · {E(u)}</span></h3>
  <table class="st st--tt st--solo"><thead><tr><th>#</th><th>AI agent</th><th>Match 1</th><th>Match 2</th><th>Match 3</th><th>{how} ({E(u)})</th></tr></thead>
  <tbody>{"".join(body)}</tbody></table>
  <p class="cr-rule">{E(ch.get("scoring") or "")}{" A no-show (the program did not start) counts 0." if any(m.get("no_show") for r in ch["rows"] for m in r["matches"]) else ""}</p></div>"""


def points_race_champ(site: Site, ch: dict) -> str:
    races = ch.get("series") or []
    hd = "".join(f'<th>Race {r["race"]}<span class="th-rp">{replay(site, r.get("replay"), compact=True) if not r["pending"] else "Pending"}</span></th>' for r in races)
    body = []
    for row in ch["rows"]:
        n = row["model"]
        cells = "".join(
            ('<td class="st-n is-pend">–</td>' if r["pending"] else
             f'<td class="st-n"><b class="pl pl-{r["ranks"].get(n)}">{r["ranks"].get(n, "–")}</b><small>{E(str(r["points"].get(n, "")))} pts</small></td>')
            for r in races)
        body.append(f'<tr><td class="st-r">{row["rank"]}</td><td>{who(site, n)}</td>{cells}<td class="st-n st-p">{row["points"]:g}</td></tr>')
    pend = [r for r in races if r["pending"]]
    note = (f' Race {pend[0]["race"]} is being re-run; the table and the medals settle when it lands.' if pend else "")
    return f"""
<div class="cr-solo"><h3 class="cr-h">Series of races <span>{"standings after " + str(len(races) - len(pend)) + " of " + str(len(races)) if pend else "final standings"}</span></h3>
  <table class="st st--race"><thead><tr><th>#</th><th>AI agent</th>{hd}<th>Points</th></tr></thead><tbody>{"".join(body)}</tbody></table>
  <p class="cr-rule">{E(ch.get("scoring") or "")}{E(note)} Each cell: place, then points.</p></div>"""


def arena(site: Site, oa: dict) -> str:
    rr = next(x for x in oa["stages"] if x["id"] == "round_robin")
    status = oa.get("status_line") or ""
    top = (rr.get("standings") or [{}])[0].get("model")
    note = (f"Final standings: {model_name(_m(site, top))} tops the Episodic Learning board." if oa.get("complete") and top
            else f"Standings so far ({status.lower()}).")
    return f"""
<div class="cx-row">
  <div class="cx-l"><h3 class="cr-h">Round robin <span>{E(status)}</span></h3>{cross_table(site, rr, "am")}</div>
  <div class="cx-r"><h3 class="cr-h">Standings <span>win 3 · draw 1</span></h3>{standings_big(site, rr["standings"])}</div>
</div>
<p class="cr-rule cx-note">{E(note)} Episodic Learning: every match starts from an empty workspace. Separate from the medals.</p>"""


def records(site: Site, d: dict) -> str:
    ch, oa = d.get("championship") or {}, d.get("open_arena")
    if ch.get("races"):
        champ = race_champ(site, ch)
    elif ch.get("series") is not None:
        champ = points_race_champ(site, ch)
    elif ch.get("rows") is not None and ch.get("unit") is not None:
        champ = solo_champ(site, ch)
    elif ch.get("stages"):
        champ = duel_champ(site, ch, d)
    else:
        champ = '<p class="cr-rule">Records at release.</p>'
    status = "Final" if d.get("status") == "final" else "In progress"
    prov = " · provisional" if d.get("provisional") else ""
    team_note = ""
    if any(s.get("seats") for st in ch.get("stages", []) for m in st.get("matches", []) for s in m["sides"]):
        team_note = '<p class="cr-rule cr-team">Each robot is its own agent: a side is three agents of the same model, one per seat.</p>'
    champ_sub = "Olympics Championship · medals" if d.get("format") != "solo" else "Medal series · 3 matches"
    tabs = [("champ", medals.CONTINUOUS, champ_sub, team_note + champ)]
    if oa:
        tabs.append(("arena", medals.EPISODIC, "Fresh workspace · always open", arena(site, oa)))
    btns = "".join(f'<button type="button" class="tab{" is-on" if k == 0 else ""}" data-sptab="{t}" role="tab">{l}<small>{E(sub)}</small></button>'
                   for k, (t, l, sub, _) in enumerate(tabs))
    panels = "".join(f'<div class="sp-panel{" is-on" if k == 0 else ""}" data-sppanel="{t}">{body}</div>' for k, (t, _, _, body) in enumerate(tabs))
    rp = ("Click a result or a knockout card to play the full match: unedited, in real time." if site.cfg.get("replay_base")
          else "Every match has its own recording: the full match, unedited, in real time. Replays go online at release.")
    return f"""
<section class="band sp-block" id="records" data-snav="Records">
  <div class="wrap">
    {head("02", "Competition records.", "", f'<div class="sp-head-r"><span class="tag tag--pending">{status}{prov}</span></div>')}
    {"" if d.get("format") in ("duel", "team") else podium(site, d)}
    <div class="tabs sp-tabs" role="tablist" data-sptabs>{btns}</div>
    <div class="sp-panels">{panels}</div>
    <p class="rp-legend"><span class="rp rp--wait"><b>▶</b></span>{E(rp)}</p>
  </div>
</section>"""


# ---------------------------------------------------------------- 03 challenges & capabilities
def capabilities(site: Site, s: dict, d: dict) -> str:
    cap = d.get("capabilities") or {}
    notes = d.get("notes") or {}
    lede = notes.get("challenge") or s.get("pitch")
    models = [m["name"] for m in site.models]
    res = cap.get("results") or {}
    tested = [m for m in models if res.get(m)]
    hdr = "".join(f'<span class="sk-m" title="{E(model_name(_m(site, m)))}">{model_logo(site, _m(site, m))}'
                  f'<i class="flag" style="--c:{E(_m(site, m)["colour"])}"></i><em>{E(SHORT.get(m, m))}</em></span>' for m in models)
    mark = {"pass": ("●", "Passed"), "fail": ("○", "Not passed"), "na": ("–", "Not evaluated")}
    groups = []
    for gid, gname in GROUPS:
        sks = [x for x in cap.get("skills", []) if x.get("group") == gid]
        offs = [o for o in cap.get("off", []) if o.get("group") == gid]
        rows = []
        for sk in sks:
            cells, reads = [], []
            for m in models:
                r = (res.get(m) or {}).get(sk["id"])
                stt = r["status"] if r else "na"
                sym, word = mark[stt]
                cells.append(f'<span class="sk-c sk-c--{stt}" title="{E(model_name(_m(site, m)))}: {word}{(" (" + E(r["reading"]) + ")") if r and stt == "na" and r.get("reading") else ""}">{sym}</span>')
                if r and (stt != "na" or r.get("reading")):
                    reads.append(f'<li>{who(site, m)}<span class="sk-rd sk-rd--{stt}">{word}</span>'
                                 f'<span class="sk-at">{E(r.get("reading") or "")}{" · " if r.get("reading") else ""}{E(r["checkpoint"])}</span></li>')
            badge = '<em class="sk-v" title="Passes all three test checks">Validated test</em>' if sk.get("three_checks") else ""
            sec = '<em class="sk-2">Secondary</em>' if sk.get("secondary") else ""
            det = "".join(f'<div><dt class="kicker">{k}</dt><dd>{E(v) if v else "At release"}</dd></div>' for k, v in
                          (("In the real sport", sk.get("real")), ("Test", sk.get("measure")), ("Pass line", sk.get("line"))))
            reads_html = (f'<ul class="sk-reads">{"".join(reads)}</ul>' if reads
                          else '<p class="sk-none">No model program tested on this skill yet.</p>')
            rows.append(f'<details class="sk"><summary><span class="sk-name">{E(sk["name"])}{badge}{sec}</span>'
                        f'<span class="sk-cells">{"".join(cells)}</span></summary>'
                        f'<div class="sk-d"><dl>{det}</dl>{reads_html}</div></details>')
        for o in offs:
            rows.append(f'<div class="sk sk--off"><span class="sk-name">{E(o["name"])}</span><span class="sk-why">{E(o["why"])}</span></div>')
        if not sks and not offs and gid in ("eng", "adap"):
            rows.append('<div class="sk sk--off"><span class="sk-name">Read across checkpoints</span>'
                        '<span class="sk-why">How the agent builds and improves shows in its versions over the season: '
                        '<a class="jl" href="#growth">Checkpoint Evaluation ↓</a></span></div>')
        if rows:
            groups.append(f'<div class="sk-g"><h3 class="sk-gh">{gname}<span>{len(sks)} skill{"s" if len(sks) != 1 else ""}</span></h3>{"".join(rows)}</div>')
    legend = "".join(f'<span><b class="sk-c sk-c--{k}">{v[0]}</b>{v[1]}</span>' for k, v in mark.items())
    any_mark = any(r.get("status") in ("pass", "fail") for mm in res.values() for r in mm.values())
    how = ("Pass marks at release." if not any_mark else
           "Pass marks apply each test's stated line to the published readings." if cap.get("pass_marks") == "derived"
           else "Pass marks as published by the skill tests.")
    cov = (f"Programs tested: {', '.join(model_name(_m(site, m)) for m in tested)}." if tested and len(tested) < len(models)
           else "")
    return f"""
<section class="band band--line sp-block" id="capabilities" data-snav="Capabilities">
  <div class="wrap">
    {head("03", "What it tests.", lede)}
    <div class="sk-tab">
      <div class="sk-top"><span class="kicker">Skill · each model's latest tested program</span><span class="sk-cells sk-cells--h">{hdr}</span></div>
      {"".join(groups) or '<p class="cr-rule">Skill list at release.</p>'}
    </div>
    <p class="sk-legend">{legend}<span class="sk-foot">{E(how)} {E(cov)} Provisional.</span></p>
  </div>
</section>"""


# ---------------------------------------------------------------- 04 agents
def _fact(k: str, v) -> str:
    return f'<div><dt class="kicker">{k}</dt><dd>{v}</dd></div>' if v not in (None, "") else ""


def built(site: Site, d: dict) -> str:
    per = (d.get("agents") or {}).get("per_model") or {}
    notes = ((d.get("notes") or {}).get("built")) or {}
    order = [m["name"] for m in site.models if m["name"] in per]
    place = {r["model"]: r["rank"] for r in ((d.get("championship") or {}).get("ranking") or [])}
    order.sort(key=lambda n: place.get(n, 9))
    chips = "".join(f'<button type="button" class="ms{" is-on" if k == 0 else ""}" data-msel="{k}" style="--c:{E(_m(site, n)["colour"])}">'
                    f'{model_logo(site, _m(site, n))}<span>{E(model_name(_m(site, n)))}</span></button>' for k, n in enumerate(order))
    panels = []
    for k, n in enumerate(order):
        p = per[n]
        sm = p.get("seat_matches") or p.get("matches")
        tok = f'{p["output_tokens"] / 1e6:.1f} M' if p.get("output_tokens") else None
        gpu = p.get("gpu")
        gpu = None if not gpu else gpu.replace("yes in ", "Used in ").replace(" (max ", " matches · up to ").replace(" GPU-min)", " GPU-min").replace("no (0/", "Not used (0 of ")
        facts = "".join([
            _fact("Place", E(f'{place[n]} of {len(place)}') if n in place else None),
            _fact("Matches", E(str(p.get("matches")))),
            _fact("Versions deployed", E(f'{p["versions"]}' + (f' · {p["switches"]} mid-match' if p.get("switches") is not None else "")) if p.get("versions") is not None else None),
            _fact("GPU training kit", E(gpu) if gpu else None),
            _fact("Training code", E(f'{p["train_code"]} of {sm} matches') if p.get("train_code") is not None and sm else None),
            _fact("Practice world", E(f'{p["practice_world"]} of {sm} matches' + (f' · real-time rehearsal in {p["realtime_rehearsal"]}' if p.get("realtime_rehearsal") else "")) if p.get("practice_world") is not None and sm else None),
            _fact("Reviews written", E(p["reviews"].replace("/", " of ")) if p.get("reviews") else None),
            _fact("Model calls", E(f'{p["model_calls"]:,}' + (f' · {tok} output tokens' if tok else "")) if p.get("model_calls") else None),
        ])
        lines = "".join(f"<li>{E(medals.mode_text(x))}</li>" for x in notes.get(n, []))
        panels.append(f'<div class="mp{" is-on" if k == 0 else ""}" data-mpanel="{k}"><div class="mp-h">{who(site, n, sub=True)}</div>'
                      f'<dl class="mp-f">{facts}</dl>{f"<ul class=mp-n>{lines}</ul>" if lines else ""}</div>')
    return (f'<div class="ab-b"><h3 class="ab-h"><span>B</span>How they built it</h3><div class="ms-row" role="tablist">{chips}</div>'
            f'{"".join(panels)}<p class="cr-rule">Counts over each model\'s official matches of this sport (Olympics Championship and Episodic Learning). '
            f'Training code = matches whose saved output holds training scripts. Provisional.</p></div>')


def achieved(site: Site, d: dict) -> str:
    items = ((d.get("notes") or {}).get("achieved")) or []
    if not items:
        return '<div class="ab-a"><h3 class="ab-h"><span>A</span>What agents achieved</h3><p class="cr-rule">Analysis at release.</p></div>'
    li = "".join(f'<li><p>{E(medals.mode_text(x["text"]))}</p><span class="ev">{" ".join(f"<em>{E(medals.mode_text(e))}</em>" for e in x.get("evidence", []))}</span></li>' for x in items)
    return f'<div class="ab-a"><h3 class="ab-h"><span>A</span>What agents achieved</h3><ol class="ach">{li}</ol></div>'


def _chart(site: Site, lines: dict, key: str, ymax: float, ref: float | None, ylab: str, fmt, step: bool = False,
           xmax: int | None = None, yticks: list | None = None) -> str:
    W, H, L, R, T, B = 560, 300, 40, 12, 12, 44
    xs = sorted({p["x"] for pts in lines.values() for p in pts})
    xmax = xmax or (max(xs) if xs else 1)
    X = lambda x: L + (x - 0.5) / max(xmax - 0.5, 1e-9) * (W - L - R)  # noqa: E731
    Y = lambda y: T + (1 - y / ymax) * (H - T - B)  # noqa: E731
    grid = ""
    if not yticks:
        stp = 0.1 if ymax <= 0.6 else (0.25 if ymax <= 1.5 else 0.5)
        yticks = [round(k * stp, 2) for k in range(int(round(ymax / stp)) + 1)]
    for t in yticks:
        grid += f'<line x1="{L}" x2="{W - R}" y1="{Y(t):.1f}" y2="{Y(t):.1f}" class="cg"/><text x="{L - 8}" y="{Y(t) + 4:.1f}" class="ct" text-anchor="end">{fmt(t)}</text>'
    for x in range(1, int(xmax) + 1):
        grid += f'<text x="{X(x):.1f}" y="{H - 24}" class="ct" text-anchor="middle">{x}</text>'
    grid += f'<text x="{X(0.5):.1f}" y="{H - 24}" class="ct" text-anchor="middle">Start</text>'
    if ref is not None:
        grid += f'<line x1="{L}" x2="{W - R}" y1="{Y(ref):.1f}" y2="{Y(ref):.1f}" class="cref"/><text x="{L + 6}" y="{Y(ref) - 6:.1f}" class="ct cref-t">Reference program</text>'
    ser = []
    for mi, m in enumerate(site.models):
        off = (mi - 2.5) * 1.7 if step else 0  # step lines often coincide: a small offset keeps each one visible
        pts = sorted(lines.get(m["name"]) or [], key=lambda p: p["x"])
        if not pts:
            continue
        c = m["colour"]
        if step:
            d = ""
            for i, p in enumerate(pts):
                d += (f"M{X(p['x']):.1f},{Y(p[key]) + off:.1f}" if i == 0 else f"H{X(p['x']):.1f}V{Y(p[key]) + off:.1f}")
        else:
            d = "M" + " L".join(f"{X(p['x']):.1f},{Y(p[key]):.1f}" for p in pts)
        dots = "".join(f'<circle cx="{X(p["x"]):.1f}" cy="{Y(p[key]) + off:.1f}" r="3.6"><title>{E(model_name(m))} · '
                       f'{"start" if p["cp"].startswith("kickoff") else "after match " + p["cp"].split(":")[1]} · {fmt(p[key])}'
                       f'{f" (n={p.get(chr(110))})" if p.get("n") else ""}</title></circle>' for p in pts)
        ser.append(f'<g class="cs" data-series="{E(m["name"])}" style="--c:{E(c)}"><path class="cs-case" d="{d}"/><path d="{d}"/>{dots}</g>')
    return (f'<svg class="chart" viewBox="0 0 {W} {H}" role="img" aria-label="{E(ylab)}">{grid}{"".join(ser)}'
            f'<text x="{(L + W - R) / 2:.0f}" y="{H - 4}" class="ct ct-x" text-anchor="middle">Program saved after match n</text></svg>')


def growth(site: Site, d: dict) -> str:
    ck = (d.get("agents") or {}).get("checkpoint")
    if not ck:
        return '<div class="ab-c" id="growth"><h3 class="ab-h"><span>C</span>Checkpoint Evaluation</h3><p class="cr-rule">Curves at release.</p></div>'
    lines = {k: v for k, v in (ck.get("lines") or {}).items() if v}
    cap0 = {k: v for k, v in ((ck.get("capability") or {}).get("lines") or {}).items() if v}
    if not lines and cap0:
        cap = ck["capability"]
        n = cap.get("n") or max(p["n_pass"] for pts in cap0.values() for p in pts)
        xmax = int(max(p["x"] for pts in cap0.values() for p in pts))
        capc = _chart(site, cap0, "n_pass", n, cap.get("ref"), "Card capabilities passed", lambda v: f"{int(round(v))}",
                      step=True, xmax=xmax, yticks=list(range(0, int(n) + 1)))
        cnt = ck.get("count") or {}
        legend = "".join(f'<button type="button" class="lg" data-lg="{E(m["name"])}" style="--c:{E(m["colour"])}" aria-pressed="true"><i></i>{E(model_name(m))}</button>'
                         for m in site.models if m["name"] in cap0)
        return (f'<div class="ab-c" id="growth"><h3 class="ab-h"><span>C</span>Checkpoint Evaluation</h3><div class="lg-row" data-lgs>{legend}</div>'
                f'<div class="cgrid" data-charts><figure class="cfig"><figcaption><strong>Performance growth</strong><span>{E(ck["measure"])}</span></figcaption>'
                f'<p class="cr-rule">At release: {cnt.get("ok", 0)} of {cnt.get("planned", 0)} replays done.</p></figure>'
                f'<figure class="cfig"><figcaption><strong>Capability growth</strong><span>Card capabilities passed, of {n}</span></figcaption>{capc}</figure></div>'
                '<p class="cr-rule">Frozen programs of every checkpoint replayed with no model calls.</p></div>')
    if not lines:
        cnt = ck.get("count") or {}
        return ('<div class="ab-c" id="growth"><h3 class="ab-h"><span>C</span>Checkpoint Evaluation</h3>'
                f'<p class="cr-rule">Curves at release{f": {cnt.get(chr(111) + chr(107), 0)} of {cnt[chr(112) + chr(108) + chr(97) + chr(110) + chr(110) + chr(101) + chr(100)]} replays done" if cnt.get("planned") else ""}.</p></div>')
    vmax = max([p["mean"] for pts in lines.values() for p in pts] + [ck.get("ref") or 0])
    duel = ck.get("kind") == "duel"
    ymax = 0.5 if duel and vmax <= 0.5 else (1.0 if vmax <= 1.0 else round(vmax + 0.25, 1))
    xmax = int(max(p["x"] for pts in lines.values() for p in pts))
    perf = _chart(site, lines, "mean", ymax, ck.get("ref"), ck["measure"], lambda v: f"{v:.2f}".rstrip("0").rstrip(".") if v else "0", xmax=xmax)
    cap = ck.get("capability") or {}
    capc = ""
    if cap.get("lines"):
        n = cap.get("n") or max(p["n_pass"] for pts in cap["lines"].values() for p in pts)
        capc = _chart(site, cap["lines"], "n_pass", n, cap.get("ref"), "Card capabilities passed", lambda v: f"{int(round(v))}",
                      step=True, xmax=xmax, yticks=list(range(0, int(n) + 1)))
    arrow = {"improve": "↑ improved", "regress": "↓ weaker", "flat": "→ flat"}
    legend = "".join(
        f'<button type="button" class="lg" data-lg="{E(m["name"])}" style="--c:{E(m["colour"])}" aria-pressed="true"><i></i>{E(model_name(m))}'
        f'<small>{E(next((v for k, v in arrow.items() if (ck["verdict"].get(m["name"]) or "").startswith(k)), "~ unclear"))}</small></button>'
        for m in site.models if m["name"] in lines)
    cnt = ck.get("count") or {}
    opp = ", ".join(f'{o["id"]} ({o["tier"]})' for o in ck.get("opponents") or [])
    foot = (f"Frozen programs of every checkpoint replayed with no model calls{' against the fixed practice opponents ' + opp if opp else ''}. "
            f"{cnt.get('ok', 0)} of {cnt.get('planned', 0)} replays done.")
    cap_h = (f'<figure class="cfig"><figcaption><strong>Capability growth</strong><span>Card capabilities passed, of {cap.get("n")}</span></figcaption>{capc}</figure>'
             if capc else "")
    # opponent switch (Chi 11-09): "All (mean)" = the main curve; one view per tested opponent tier, weakest first
    tiers = ck.get("tiers") or []
    fmt2 = lambda v: f"{v:.2f}".rstrip("0").rstrip(".") if v else "0"  # noqa: E731
    views = [("all", "All (mean)", f'<p class="tv-cap">{E(ck["measure"])}</p>{perf}')]
    for tr in tiers:
        tl = {m: v for m, v in tr["lines"].items() if v}
        prog = (f'{tr["ok"]} of {tr["planned"]} replays done' if tr["ok"] < tr["planned"] else f'{tr["ok"]} replays')
        if tl:
            tv = max(p["mean"] for pts in tl.values() for p in pts)
            ch = _chart(site, tl, "mean", 0.5 if tv <= 0.5 else 1.0, None, tr["label"], fmt2, xmax=xmax)
        else:
            ch = '<p class="cr-rule tv-empty">No checkpoint replays against this opponent yet.</p>'
        views.append((tr["id"], tr["short"], f'<p class="tv-cap">Score share against {E(tr["label"])} · {E(prog)}</p>{ch}'))
    if len(views) > 1:
        sw = "".join(f'<button type="button" class="tv-b{" is-on" if k == 0 else ""}" data-tv="{E(v)}" aria-pressed="{"true" if k == 0 else "false"}">{E(lab)}</button>'
                     for k, (v, lab, _) in enumerate(views))
        panes = "".join(f'<div class="tv-p" data-tvp="{E(v)}"{"" if k == 0 else " hidden"}>{body}</div>' for k, (v, _, body) in enumerate(views))
        note = f'<p class="cr-rule tv-note">{E(ck["tier_note"])}</p>' if ck.get("tier_note") else ""
        perf_block = f'<div class="tv-row" role="group" aria-label="Opponent">{sw}</div>{panes}{note}'
        mcap = "Score share (0.5 = even); pick the opponent"
    else:
        perf_block, mcap = perf, ck["measure"]
    return f"""
<div class="ab-c" id="growth"><h3 class="ab-h"><span>C</span>Checkpoint Evaluation</h3>
  <div class="lg-row" data-lgs>{legend}</div>
  <div class="cgrid" data-charts>
    <figure class="cfig"><figcaption><strong>Performance growth</strong><span>{E(mcap)}</span></figcaption>{perf_block}</figure>
    {cap_h}
  </div>
  <p class="cr-rule">{E(foot)}</p>
</div>"""


def agents(site: Site, d: dict) -> str:
    return f"""
<section class="band band--line sp-block" id="agents" data-snav="Agents">
  <div class="wrap">
    {head("04", "Agent performance<br>and growth.")}
    <div class="ab-ab">{achieved(site, d)}{built(site, d)}</div>
    {growth(site, d)}
  </div>
</section>"""


# ---------------------------------------------------------------- page
def render(site: Site, i: int, d: dict):
    s = site.sports[i]
    prev_s, next_s = site.sports[i - 1], site.sports[(i + 1) % len(site.sports)]
    body = (overview(site, s, d) + subnav(site) + records(site, d) + capabilities(site, s, d) + agents(site, d)
            + f"""
<nav class="wrap prevnext" aria-label="More sports">
  <a href="{site.sport_url(prev_s)}"><span>←</span>{icon(prev_s['id'])}<strong>{E(prev_s['name'])}</strong></a>
  <a href="{site.sport_url(next_s)}"><strong>{E(next_s['name'])}</strong>{icon(next_s['id'])}<span>→</span></a>
</nav>
<dialog class="pl" data-player aria-label="Match replay">
  <div class="pl-in">
    <header class="pl-h"><strong data-pl-title></strong>
      <span class="pl-tabs"><button type="button" class="pl-t is-on" data-pl-src="full"></button><button type="button" class="pl-t" data-pl-src="hl" hidden>Highlights</button></span>
      <button type="button" class="pl-x" data-pl-close aria-label="Close">×</button></header>
    <div class="pl-stage" data-pl-stage><video class="pl-v" controls controlslist="nofullscreen nodownload" disablepictureinpicture playsinline preload="metadata" data-pl-video></video>
      <button type="button" class="pl-fs" data-pl-fs aria-label="Full screen (F)" title="Full screen (F)"><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path class="fs-in" d="M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5"/><path class="fs-out" d="M9 4v5H4M15 4v5h5M9 20v-5H4M15 20v-5h5"/></svg></button>
      <p class="pl-rot" data-pl-rot hidden>Turn your phone sideways for a bigger picture</p>
      <div class="sbo" data-sbo hidden aria-live="polite"></div><div class="sbo-toast" data-sbo-toast hidden></div></div>
    <p class="pl-note">{"Provisional results. " if d.get("provisional") else ""}Raw broadcast camera, unedited.</p>
  </div>
</dialog>
<script type="application/json" data-pl-models>{json.dumps({m["name"]: {"short": SHORT.get(m["name"], m["name"]), "colour": m["colour"], "logo": model_logo(site, m, "sbo-logo")} for m in site.models})}</script>
<script src="{site.asset('js/sport.js')}" defer></script>""")
    return f"sports/{slug(s)}/", page(site, path="sports/", title=s["name"], body=body, description=s["pitch"], dark_top=True,
                                      body_class="sp", css=("css/sport.css",))
