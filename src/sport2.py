"""Sport page, proposed structure (SPORTPAGE2, 11-10; preview only, for the sports listed in data/sport_pages_v2/).

    01 Overview                    unchanged (sport.overview + athlete view)
    02 Competition & performance   A Competition records (Continual / Episodic Learning boards, medals, replays)
                                   B Performance evolution (Checkpoint Evaluation: score against fixed opponents per saved
                                     version, first v latest version)
    03 What it tests               A Core capabilities (1-3 primary + a few secondary, chosen by match meaning)
                                   B Capability evaluation (measured value v pass line per model; skill tests folded as
                                     supporting evidence; rule checks apart)
                                   C Capability growth (verified primary capabilities per checkpoint: acquired, kept)
    04 Agent development           how they built it, decisions and adaptation

Data: data/sport_pages/<id>.json (eo-sportpage/1, unchanged) + data/sport_pages_v2/<id>.json (eo-sportcaps/0, written by
the coordinator's tools/web/sportpage2_sync.py from the Checkpoint Evaluation capability data and the sport page's skill
tests). A sport without the v2 file keeps the current page (src/sport.py).
"""
from __future__ import annotations

import json

import medals
import sport as sp
from layout import ROOT, E, Site, icon, model_logo, model_name, page, slug

SHOW_03_04 = False   # Chi 11-10: 03 What we measure and 04 Agent development wait for Chi's revision (as PR #27 for src/sport.py)
STATUS = {"verified": ("Verified", "v"), "not_verified": ("Not verified", "n"), "insufficient": ("Insufficient evidence", "i"),
          "not_evaluated": ("Not evaluated", "x"), "no_program": ("Program did not act", "n")}
MARK = {"pass": ("●", "Passed"), "fail": ("○", "Not passed"), "na": ("–", "Not evaluated")}


def load(sport_id: str) -> dict | None:
    p = ROOT / "data" / "sport_pages_v2" / f"{sport_id}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else None


def cp_word(cp: str | None) -> str:
    if not cp:
        return "–"
    return "Start" if cp.startswith("kickoff") else f"after match {cp.split(':')[1]}"


def head(n: str, title: str, lede: str = "", kicker: str = "") -> str:
    k = f'<span class="s2-kick">{E(kicker)}</span>' if kicker else ""
    return (f'<header class="ch-head sp-head"><span class="ch-n">{n}<i>/04</i></span><h2>{k}{title}</h2>'
            f'{f"<p>{E(lede)}</p>" if lede else ""}</header>')


def subnav() -> str:
    items = [("overview", "Overview"), ("competition", "Competition")] + (
        [("capabilities", "Capabilities"), ("development", "Development")] if SHOW_03_04 else [])
    return ('<nav class="sp-sub" aria-label="On this page" data-spnav><div class="wrap">'
            + "".join(f'<a href="#{k}" data-spnav-a="{k}">{v}</a>' for k, v in items) + "</div></nav>")


def sub_h(letter: str, title: str, line: str = "") -> str:
    return (f'<h3 class="s2-h"><span>{letter}</span>{E(title)}</h3>' + (f'<p class="s2-line">{E(line)}</p>' if line else ""))


# ---------------------------------------------------------------- 02 competition & performance
def records_inner(site: Site, d: dict) -> str:
    ch, oa = d.get("championship") or {}, d.get("open_arena")
    if ch.get("races"):
        champ = sp.race_champ(site, ch)
    elif ch.get("series") is not None:
        champ = sp.points_race_champ(site, ch)
    elif ch.get("rows") is not None and ch.get("unit") is not None:
        champ = sp.solo_champ(site, ch)
    elif ch.get("stages"):
        champ = sp.duel_champ(site, ch, d)
    else:
        champ = '<p class="cr-rule">Records at release.</p>'
    champ_sub = "Olympics Championship · medals" if d.get("format") != "solo" else "Medal series · 3 matches"
    tabs = [("champ", medals.CONTINUOUS, champ_sub, champ)]
    if oa:
        tabs.append(("arena", medals.EPISODIC, "Fresh workspace · always open", sp.arena(site, oa)))
    btns = "".join(f'<button type="button" class="tab{" is-on" if k == 0 else ""}" data-sptab="{t}" role="tab">{l}<small>{E(sub)}</small></button>'
                   for k, (t, l, sub, _) in enumerate(tabs))
    panels = "".join(f'<div class="sp-panel{" is-on" if k == 0 else ""}" data-sppanel="{t}">{body}</div>' for k, (t, _, _, body) in enumerate(tabs))
    pod = "" if d.get("format") in ("duel", "team") else sp.podium(site, d)
    return f'{pod}<div class="tabs sp-tabs" role="tablist" data-sptabs>{btns}</div><div class="sp-panels">{panels}</div>'


def moments(site: Site, d: dict, idx: list[int], title: str) -> str:
    items = ((d.get("notes") or {}).get("achieved")) or []
    sel = [items[k] for k in idx if k < len(items)]
    if not sel:
        return ""
    li = "".join(f'<li><p>{E(medals.mode_text(x["text"]))}</p><span class="ev">{" ".join(f"<em>{E(medals.mode_text(e))}</em>" for e in x.get("evidence", []))}</span></li>' for x in sel)
    return f'<div class="s2-moments"><h4 class="s2-h4">{E(title)}</h4><ol class="ach">{li}</ol></div>'


# canonical fixed opponents (Chi 11-10: show every one that has readings, say which a sport lacks)
OPP_ORDER = [("L1", "L1 · weak"), ("L2", "L2 · middle"), ("L3", "L3 · strong"), ("PP", "Practice player · strongest")]
OPP_ALIAS = {"TRUTH": "L3", "TWIN": "PP", "Sumatra": "PP"}


def evolution(site: Site, d: dict) -> str:
    """Score per saved version against each fixed opponent: one small chart per opponent, one line per model."""
    ck = (d.get("agents") or {}).get("checkpoint") or {}
    fmt = lambda v: f"{v:.2f}".rstrip("0").rstrip(".") if v else "0"  # noqa: E731
    panels = []                     # (code, title, lines, note)
    for t in ck.get("tiers") or []:
        lines = {k: v for k, v in (t.get("lines") or {}).items() if v}
        code = OPP_ALIAS.get(t["id"], t["id"])
        name = dict(OPP_ORDER).get(code, t.get("short") or t["id"])
        if t["id"] != code:                                   # the sport's own name for that opponent (e.g. TRUTH)
            name = f'{name} ({t["id"]})'
        prog = f'{t.get("ok", 0)} of {t.get("planned", 0)} replays' if t.get("ok", 0) < t.get("planned", 0) else f'{t.get("ok", 0)} replays'
        panels.append((code, name, lines, prog, t.get("label") or ""))
    solo = not panels
    if solo:
        lines = {k: v for k, v in (ck.get("lines") or {}).items() if v}
        if not lines:
            return '<p class="cr-rule">Checkpoint Evaluation at release.</p>'
        panels.append(("REF", ck.get("measure") or "Against the reference program", lines, f'{(ck.get("count") or {}).get("ok", 0)} replays', ""))
    panels.sort(key=lambda p: [c for c, _ in OPP_ORDER].index(p[0]) if p[0] in dict(OPP_ORDER) else 9)
    allpts = [p for _, _, ls, _, _ in panels for pts in ls.values() for p in pts]
    xmax = int(max([p["x"] for p in allpts] or [1]))
    vmax = max([p["mean"] for p in allpts] + [ck.get("ref") or 0, 0.01])
    duel = ck.get("kind") in ("duel", "team") or not solo
    ymax = 0.5 if duel and vmax <= 0.5 else (1.0 if vmax <= 1.0 else round(vmax + 0.25, 1))
    figs = []
    for code, name, ls, prog, label in panels:
        ch = sp._chart(site, ls, "mean", ymax, ck.get("ref") if solo else None, name, fmt, xmax=xmax) if ls else \
            '<p class="cr-rule tv-empty">No replays against this opponent.</p>'
        figs.append(f'<figure class="cfig s2-op"><figcaption><strong>{E(name)}</strong><span>{E(prog)}</span></figcaption>{ch}</figure>')
    have = {c for c, *_ in panels}
    lack = [n for c, n in OPP_ORDER if c not in have]
    seen = {m for _, _, ls, _, _ in panels for m in ls}
    legend = "".join(f'<button type="button" class="lg" data-lg="{E(m["name"])}" style="--c:{E(m["colour"])}" aria-pressed="true"><i></i>{E(model_name(m))}</button>'
                     for m in site.models if m["name"] in seen)
    if solo:
        lack_txt = "Solo event: no opponent. Each saved version runs the course alone; the score is relative to the reference program (1.0 = reference)."
    else:
        lack_txt = ("Every fixed opponent has replays." if not lack else
                    f'No replays against {", ".join(lack)} in this sport.') + " Score share: 0.5 = even with that opponent."
    # first and latest version against each opponent
    codes = [(c, n) for c, n, *_ in panels]
    head_ = "".join(f"<th>{E(n.split(' · ')[0].split(' (')[0])}</th>" for _, n in codes)
    rows = []
    for m in site.models:
        cells, any_ = [], False
        for c, n, ls, *_ in panels:
            pts = sorted(ls.get(m["name"]) or [], key=lambda p: p["x"])
            if pts:
                any_ = True
                a, b = pts[0], pts[-1]
                dv = b["mean"] - a["mean"]
                cells.append(f'<td class="st-n">{fmt(a["mean"])} → <b class="{"is-up" if dv > 0.02 else ("is-dn" if dv < -0.02 else "")}">{fmt(b["mean"])}</b>'
                             f'<small>{E(cp_word(b["cp"]))}</small></td>')
            else:
                cells.append('<td class="st-n">–</td>')
        if any_:
            rows.append(f'<tr><td>{sp.who(site, m["name"])}</td>{"".join(cells)}</tr>')
    vd = ck.get("verdict") or {}
    arrow = {"improve": "↑ stronger", "regress": "↓ weaker", "flat": "→ no clear change"}
    verdicts = " · ".join(f'{SHORT_N(m)} {next((w for k, w in arrow.items() if (vd.get(m) or "").startswith(k)), "~ unclear")}' for m in [x["name"] for x in site.models] if m in vd)
    cnt = ck.get("count") or {}
    return f"""
<div class="lg-row" data-lgs>{legend}</div>
<div class="s2-ops" data-charts style="--np:{len(figs)}">{"".join(figs)}</div>
<p class="cr-rule">{E(lack_txt)}</p>
<div class="s2-evo-t"><h4 class="s2-h4">First → latest version{"" if solo else ", against each opponent"}</h4>
  <div class="tw"><table class="st s2-fl"><thead><tr><th>AI agent</th>{head_}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>
</div>
<p class="cr-rule">Every saved version replayed with no model calls; {cnt.get('ok', 0)} of {cnt.get('planned', 0)} replays. Verdict (all seeds and opponents must agree): {E(verdicts)}. This answers whether the program got stronger; what it can do is measured separately.</p>"""


def SHORT_N(m: str) -> str:
    return sp.SHORT.get(m, m)


def competition(site: Site, d: dict, v: dict) -> str:
    status = "Final" if d.get("status") == "final" else "In progress"
    return f"""
<section class="band sp-block" id="competition" data-snav="Competition">
  <div class="wrap">
    {head("02", "Competition &amp;<br>performance.")}
    <div class="s2-part">{sub_h("A", "Competition records", "")}<span class="tag tag--pending s2-st">{status}</span>
      {records_inner(site, d)}
      {moments(site, d, v.get("_moments", []), "What the matches showed")}
    </div>
    <div class="s2-part" id="evolution">{sub_h("B", "Performance evolution", "The same saved versions replayed against the same fixed opponents: did the program get stronger over the season?")}
      {evolution(site, d)}
    </div>
  </div>
</section>"""


# ---------------------------------------------------------------- 03 what it tests
def ops(t: str | None) -> str:
    return (t or "").replace(">=", "≥").replace("<=", "≤")


def fmt_val(vd: dict, val) -> str:
    if val is None:
        return "–"
    r = vd.get("rule") or {}
    if "num" in r:
        return f"{val * 100:.0f} %"
    return f"{val:.2f}".rstrip("0").rstrip(".") if abs(val) < 100 else f"{val:.0f}"


def bar(vd: dict, sk: dict) -> str:
    """Measured value against the pass line: a track, the value, a tick at the line."""
    r = vd.get("rule") or {}
    val, thr = sk.get("value"), (vd["line_value"] if vd.get("line_value") is not None else r.get("value"))
    if val is None or thr is None:
        rd = sk.get("reading")
        if sk.get("src") == "skill test":
            word = {"pass": "passed", "fail": "not passed"}.get(sk.get("status"), "not run")
            rd = f'skill test {word}{(" · " + rd) if rd else ""}{(" · " + cp_word(sk["checkpoint"])) if sk.get("checkpoint") else ""}'
        return f'<span class="s2-bar is-none{" is-ok" if sk.get("status") == "pass" else ""}"><em>{E(rd) if rd else "no reading"}</em></span>'
    scale = 1.0 if "num" in r and thr <= 1 else max(thr * 2, val * 1.1, 1e-6)
    w = max(0.0, min(1.0, val / scale)) * 100
    t = max(0.0, min(1.0, thr / scale)) * 100
    ok = sk.get("status") == "pass"
    nn = f' · n {int(sk["n"])}' if sk.get("n") else ""
    src = f' {vd["line_src"]}' if vd.get("line_src") in ("L1", "L2") else (" reference" if vd.get("line_src") else "")
    tip = f'{vd["name"]}: {fmt_val(vd, val)} (line{src} {ops(r.get("op", ""))} {fmt_val(vd, thr)}){nn}'
    return (f'<span class="s2-bar{" is-ok" if ok else ""}" title="{E(tip)}"><span class="s2-tr"><i style="width:{w:.1f}%"></i>'
            f'<b style="left:{t:.1f}%"></b></span><em>{fmt_val(vd, val)}</em></span>')


def chip(st: str) -> str:
    w, k = STATUS.get(st, ("Not evaluated", "x"))
    return f'<span class="s2-chip s2-chip--{k}">{E(w)}</span>'


def cap_cards(v: dict) -> str:
    cards = []
    for c in v["capabilities"]:
        def vli(x):
            if x.get("line_value") is not None:
                src = x["line_src"] if x["line_src"] in ("L1", "L2") else "reference program"
                return f'<li>{E(x["name"])}: {E(ops(x.get("op") or ""))} {E(fmt_val(x, x["line_value"]))}, the {E(src)} reading, pooled over 2 opponents × 2 seeds</li>'
            return f'<li>{E(x["name"])}{(": " + E(ops(x["line"]))) if x.get("line") else ""}</li>'
        ver = "".join(vli(x) for x in c["verify"])
        cards.append(f'<article class="s2-cap s2-cap--{c["role"][0]}"><header><span class="s2-role">{"Primary" if c["role"] == "primary" else "Secondary"}</span>'
                     f'<span class="s2-layer">{E(c["layer"])}</span></header><h4>{E(c["name"])}</h4><p>{E(c["meaning"])}</p>'
                     f'<div class="s2-ver"><span class="kicker">Verified when</span><ul>{ver}</ul></div></article>')
    return f'<div class="s2-caps">{"".join(cards)}</div>'


def ev_rows(site: Site, v: dict, ids: list[str]) -> str:
    models = [m["name"] for m in site.models]
    hdr = "".join(f'<span class="sk-m" title="{E(model_name(sp._m(site, m)))}">{model_logo(site, sp._m(site, m))}<em>{E(sp.SHORT.get(m, m))}</em></span>' for m in models)
    out = []
    for pid in ids:
        e = v["evidence"].get(pid)
        if not e:
            continue
        cells, reads = [], []
        for m in models:
            r = e["marks"].get(m) or {}
            st = r.get("status", "na")
            sym, word = MARK.get(st, MARK["na"])
            rd = r.get("reading") or ""
            cells.append(f'<span class="sk-c sk-c--{st}" title="{E(model_name(sp._m(site, m)))}: {word}{(" · " + E(rd)) if rd else ""}{(" · " + E(cp_word(r.get("checkpoint")))) if r.get("checkpoint") else ""}">{sym}</span>')
            if rd:
                reads.append(f'<span>{E(sp.SHORT.get(m, m))} {E(rd)}</span>')
        out.append(f'<div class="s2-ev"><div class="s2-ev-n"><strong>{E(e["name"])}</strong>'
                   f'<small>Pass line: {E(ops(e.get("line")) or "at release")}</small>'
                   f'{f"<small class=s2-rd>{chr(32).join(reads)}</small>" if reads else ""}</div>'
                   f'<span class="sk-cells">{"".join(cells)}</span></div>')
    if not out:
        return ""
    return f'<div class="s2-evs"><div class="s2-ev s2-ev--h"><span></span><span class="sk-cells sk-cells--h">{hdr}</span></div>{"".join(out)}</div>'


def evaluation(site: Site, v: dict) -> str:
    blocks = []
    for c in v["capabilities"]:
        rows = []
        for m in site.models:
            ev = v["eval"].get(m["name"]) or {}
            ce = (ev.get("caps") or {}).get(c["id"]) or {"status": "not_evaluated", "skills": {}}
            one = len(c["verify"]) == 1
            bars = "".join('<span class="s2-sk">' + ("" if one else f'<small>{E(x["name"])}</small>')
                           + bar(x, ce["skills"].get(x["id"], {})) + "</span>" for x in c["verify"])
            rows.append(f'<li class="s2-row"><span class="s2-who">{sp.who(site, m["name"])}<small>{E(cp_word(ev.get("cp")))}</small></span>'
                        f'<span class="s2-bars">{bars}</span>{chip(ce["status"])}</li>')
        n_ev = len(c["evidence"])
        evid = (f'<details class="s2-more"><summary>Supporting evidence · {n_ev} skill test{"s" if n_ev != 1 else ""} '
                f'<span class="arr">▾</span></summary>{ev_rows(site, v, c["evidence"])}</details>') if n_ev else ""
        def mline(x):
            if x.get("line_value") is not None:
                src = x["line_src"] if x["line_src"] in ("L1", "L2") else "the reference program"
                return f'{x["name"]}; line = {src} {fmt_val(x, x["line_value"])}'
            return f'{x["name"]} ({ops(x.get("line")) or "pass line at release"})'
        meas = " · ".join(mline(x) for x in c["verify"])
        blocks.append(f'<div class="s2-eb"><div class="s2-eb-h"><h4>{E(c["name"])}</h4><span class="s2-role s2-role--{c["role"][0]}">{"Primary" if c["role"] == "primary" else "Secondary"}</span></div>'
                      f'<p class="s2-meas">Measured: {E(meas)}</p>'
                      f'<ol class="s2-rows">{"".join(rows)}</ol>{evid}</div>')
    extra = []
    if v.get("rules"):
        extra.append(f'<details class="s2-more s2-rules"><summary>Rules and prerequisites · {len(v["rules"])} <span class="arr">▾</span></summary>'
                     f'<p class="cr-rule">Playing within the rules and keeping the control loop running are conditions for scoring, checked on their own and outside the capability count.</p>{ev_rows(site, v, v["rules"])}</details>')
    if v.get("health"):
        extra.append(f'<details class="s2-more s2-rules"><summary>Control-loop checks · {len(v["health"])} <span class="arr">▾</span></summary>'
                     f'<p class="cr-rule">How the agent engineers its controller; read with Agent development (04).</p>{ev_rows(site, v, v["health"])}</details>')
    if v.get("not_shown"):
        li = "".join(f'<li><strong>{E(x["name"])}</strong> {E(x["why"])}</li>' for x in v["not_shown"])
        extra.append(f'<details class="s2-more s2-rules"><summary>Shown once there is evidence · {len(v["not_shown"])} <span class="arr">▾</span></summary><ul class="s2-ns">{li}</ul></details>')
    legend = "".join(chip(k) for k in ("verified", "not_verified", "insufficient", "not_evaluated"))
    return (f'<div class="s2-legend">{legend}<span class="s2-lg-bar"><span class="s2-tr"><i style="width:60%"></i><b style="left:40%"></b></span>'
            f'measured value · tick = pass line</span></div>{"".join(blocks)}{"".join(extra)}'
            f'<p class="cr-rule">Each model\'s latest saved version, replayed against the fixed opponents (Checkpoint Evaluation, no model calls). '
            f'Not evaluated = no measurement; insufficient evidence = measured, but too few events to judge.</p>')


def growth(site: Site, v: dict) -> str:
    prim = [c for c in v["capabilities"] if c["role"] == "primary"]
    cps = sorted({g["cp"] for gl in v["growth"].values() for g in gl}, key=lambda c: (0 if c.startswith("kickoff") else int(c.split(":")[1])))
    hdr = "".join(f'<span class="s2-gh">{"Start" if c.startswith("kickoff") else c.split(":")[1]}</span>' for c in cps)
    cls = {"verified": "v", "not_verified": "n", "insufficient": "i", "no_program": "n"}
    rows = []
    for m in site.models:
        gl = {g["cp"]: g for g in v["growth"].get(m["name"]) or []}
        cells = []
        for c in cps:
            g = gl.get(c)
            if not g:
                cells.append('<span class="s2-gc is-none" title="No saved version">·</span>')
                continue
            sq = "".join(f'<i class="s2-sq s2-sq--{cls.get(g["caps"].get(p["id"]), "x")}" title="{E(p["name"])}: {E(STATUS.get(g["caps"].get(p["id"]), ("Not evaluated",))[0])}"></i>' for p in prim)
            k = sum(1 for p in prim if g["caps"].get(p["id"]) == "verified")
            cells.append(f'<span class="s2-gc" title="{E(model_name(m))} · {E(cp_word(c))}: {k} of {len(prim)} verified">{sq}<b>{k}</b></span>')
        # acquired / kept per primary
        cl = (v.get("claims") or {}).get(m["name"]) or {}
        notes = [cl[p["id"]]["text"] for p in prim if (cl.get(p["id"]) or {}).get("text")]
        rows.append(f'<div class="s2-gr"><span class="s2-gw">{sp.who(site, m["name"])}</span><span class="s2-gcs" style="--n:{len(cps)}">{"".join(cells)}</span>'
                    f'<small class="s2-gn">{"<br>".join(E(x) for x in notes) if notes else "No primary capability acquired yet (two passing versions in a row)"}</small></div>')
    key = "".join(f'<span><i class="s2-sq s2-sq--{k}"></i>{w}</span>' for k, w in (("v", "Verified"), ("n", "Not verified"), ("i", "Insufficient evidence"), ("x", "Not evaluated")))
    order = " · ".join(f"{k + 1} {p['name']}" for k, p in enumerate(prim))
    cnt = {m["name"]: [{"cp": g["cp"], "x": g["x"], "n_pass": sum(1 for p in prim if g["caps"].get(p["id"]) == "verified")}
                       for g in v["growth"].get(m["name"]) or [] if any(g["caps"].get(p["id"]) in ("verified", "not_verified") for p in prim)]
           for m in site.models}
    cnt = {k: x for k, x in cnt.items() if x}
    chart = ""
    if cnt:
        xmax = int(max(p["x"] for pts in cnt.values() for p in pts)) or 1
        legend = "".join(f'<button type="button" class="lg" data-lg="{E(mm["name"])}" style="--c:{E(mm["colour"])}" aria-pressed="true"><i></i>{E(model_name(mm))}</button>'
                         for mm in site.models if mm["name"] in cnt)
        chart = (f'<figure class="cfig s2-cc"><figcaption><strong>Verified primary capabilities per saved version</strong><span>of {len(prim)}; versions without a verdict are left out</span></figcaption>'
                 f'<div class="lg-row" data-lgs>{legend}</div><div data-charts>{sp._chart(site, cnt, "n_pass", max(len(prim), 1), None, "Verified primary capabilities", lambda q: f"{int(round(q))}", step=True, xmax=xmax, yticks=list(range(0, len(prim) + 1)))}</div></figure>')
    return chart + f"""
<div class="s2-grow">
  <div class="s2-gr s2-gr--h"><span class="s2-gw kicker">Saved version</span><span class="s2-gcs" style="--n:{len(cps)}">{hdr}</span><small class="s2-gn kicker">Primary capabilities</small></div>
  {"".join(rows)}
</div>
<p class="s2-key">{key}<span>Squares in order: {E(order)}</span></p>
<p class="cr-rule">A saved version passes a primary capability when its headline reading, pooled over the Checkpoint Evaluation runs (2 fixed opponents × 2 seeds), reaches the line. Acquired = two passing versions in a row; lost = two failing versions in a row. Too few events = insufficient evidence; no reading = not evaluated. Skill tests are evidence and are never added up; counts are not compared across sports.</p>"""


def tests(site: Site, s: dict, d: dict, v: dict) -> str:
    lede = (d.get("notes") or {}).get("challenge") or s.get("pitch")
    np_ = sum(1 for c in v["capabilities"] if c["role"] == "primary")
    ns = len(v["capabilities"]) - np_
    return f"""
<section class="band band--line sp-block" id="capabilities" data-snav="Capabilities">
  <div class="wrap">
    {head("03", "What we measure.", lede, "What the system can do")}
    <div class="s2-part">{sub_h("A", "Core capabilities", f"{np_} primary capabilit{'y' if np_ == 1 else 'ies'} decide matches in this sport; {ns} secondary add to them.")}
      {cap_cards(v)}</div>
    <div class="s2-part">{sub_h("B", "Capability evaluation", "The measured value for each model, against the pass line.")}
      {evaluation(site, v)}</div>
    <div class="s2-part" id="growth">{sub_h("C", "Capability growth", "Which primary capabilities each saved version verifies, from the start of the season to the latest version.")}
      {growth(site, v)}</div>
  </div>
</section>"""


# ---------------------------------------------------------------- 04 agent development
def development(site: Site, d: dict, v: dict) -> str:
    dev = moments(site, d, v.get("_dev", []), "Decisions and adaptation")
    return f"""
<section class="band band--line sp-block" id="development" data-snav="Development">
  <div class="wrap">
    {head("04", "Agent<br>development.", "How each agent built, trained, tested and changed its system over the season.", "How the agent builds it")}
    <div class="ab-ab s2-dev">{sp.built(site, d)}{dev or '<div class="ab-a"></div>'}</div>
  </div>
</section>"""


def render(site: Site, i: int, d: dict, v: dict):
    s = site.sports[i]
    prev_s, next_s = site.sports[i - 1], site.sports[(i + 1) % len(site.sports)]
    split = (v.get("notes_split") or {})
    if not split:   # no hand split: findings about building / adapting go to 04, the rest to 02
        items = ((d.get("notes") or {}).get("achieved")) or []
        dev_words = ("practice", "rehears", "patch", "train", "replayed", "noticed", "changed", "review", "rewrote", "version", "studied", "tuned")
        dev = [k for k, x in enumerate(items) if any(w in x["text"].lower() for w in dev_words)]
        split = {"records": [k for k in range(len(items)) if k not in dev], "development": dev}
    if not SHOW_03_04:   # 04 hidden: every finding stays with the records
        split = {"records": sorted(split.get("records", []) + split.get("development", [])), "development": []}
    v = {**v, "_moments": split.get("records", []), "_dev": split.get("development", [])}
    base_html = sp.render(site, i, d)[1]
    # reuse the current page's player dialog + model JSON (everything after the prev/next nav)
    k = base_html.find('<dialog class="pl"')
    tail = base_html[k:base_html.find('<script src="', k)] if k >= 0 else ""
    note_fn = getattr(medals, "exhibition_notice", None)   # PR #22: exhibition sports carry one notice above the records
    note = note_fn(site, s["id"]) if note_fn else ""
    body = (sp.overview(site, s, d) + subnav() + (note or "") + competition(site, d, v)
            + ((tests(site, s, d, v) + development(site, d, v)) if SHOW_03_04 else "")
            + f"""
<nav class="wrap prevnext" aria-label="More sports">
  <a href="{site.sport_url(prev_s)}"><span>←</span>{icon(prev_s['id'])}<strong>{E(prev_s['name'])}</strong></a>
  <a href="{site.sport_url(next_s)}"><strong>{E(next_s['name'])}</strong>{icon(next_s['id'])}<span>→</span></a>
</nav>
{tail}
<script src="{site.asset('js/sport.js')}" defer></script>""")
    return f"sports/{slug(s)}/", page(site, path="sports/", title=s["name"], body=body, description=s["pitch"], dark_top=True,
                                      body_class="sp sp2", css=("css/sport.css", "css/sport2.css"))
