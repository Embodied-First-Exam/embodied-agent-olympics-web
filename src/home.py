"""Home: broadcast-grade, one idea per screen. Story sections are reused by The Match and Competitions."""
from __future__ import annotations

import json
import re

from layout import E, Site, icon, ink_on, model_logo, model_name, page

# ---------------------------------------------------------------- helpers


def clip_index(site: Site) -> dict:
    """clip id -> {sport, web, hd, poster} for every clip in sports.json."""
    out = {}
    for s in site.sports:
        for c in s["clips"]:
            out[c["id"]] = {"id": c["id"], "sport": s, "web": site.murl(c["web_720p"]["url"]),
                            "hd": site.murl(c["master_1440p"]["url"]), "poster": site.murl(c["poster"]["url"])}
    return out


def tick_ms(s: dict) -> str | None:
    """'every 20 ms' / '100 Hz' in the control line -> '20 ms'."""
    c = s.get("control") or ""
    m = re.search(r"every (\d+) ms", c)
    if m:
        return f"{m.group(1)} ms"
    m = re.search(r"(\d+) Hz", c)
    return f"{1000 // int(m.group(1))} ms" if m else None


def vid(c: dict, cls: str = "", extra: str = "", hd: bool = False) -> str:
    """A lazy, muted, looping video; site.js sets the source (HD on large screens when hd) near the viewport."""
    hd_attr = f' data-hd="{E(c["hd"])}"' if hd and c.get("hd") else ""
    return (f'<video class="{cls}" muted loop playsinline preload="none" poster="{E(c["poster"])}" '
            f'data-lazy data-web="{E(c["web"])}"{hd_attr} {extra}></video>')


# ---------------------------------------------------------------- sections


def hero(site: Site, clips: dict) -> str:
    seq = []
    for h in site.media["home_hero_sequence"]:
        c = clips.get(h["id"])
        if c:
            seq.append({"id": c["id"], "web": c["web"], "hd": c["hd"], "poster": c["poster"],
                        "sport": c["sport"]["id"], "name": c["sport"]["name"]})
    first = seq[0]
    channels = "".join(
        f'<button class="ch{" is-on" if k == 0 else ""}" type="button" data-ch="{k}" aria-label="{E(c["name"])}" '
        f'data-name="{E(c["name"])}">{icon(c["sport"])}<i></i></button>' for k, c in enumerate(seq))
    return f"""
<div class="h2o-media"><div class="h2o-media-in">
  <video class="h2o-v is-on" muted playsinline preload="auto" poster="{E(first['poster'])}"></video>
  <video class="h2o-v" muted playsinline preload="none"></video>
  <div class="h2o-shade"></div>
</div></div>
<section class="h2o">
  <div class="tele" aria-hidden="true"><b><span class="rec"></span>REPLAY</b><span data-t-name>{E(first['name'].upper())}</span><span data-t-clock>00:00.00</span></div>
  <div class="h2o-bottom wrap">
    <h1 class="wordmark" data-fit><span class="fit-inner"><span class="wl">Embodied</span> <span class="wl">Olympics</span></span></h1>
    <div class="h2o-row">
      <div class="h2o-cta">
        <p class="h2o-tag h2o-head">{E(site.cfg['tagline'])}</p>
        <a class="btn btn--light" href="{site.url('watch/')}" data-hero-watch><span class="play"></span>Watch</a>
      </div>
      <div class="channels" role="group" aria-label="Switch sport">{channels}</div>
    </div>
  </div>
</section>
<script type="application/json" data-hero2-clips>{json.dumps(seq)}</script>"""


def reel(site: Site, clips: dict, rows: int = 2) -> str:
    """Two rows of match stills drifting in opposite directions (plain strip: no labels); hover pauses the row and plays that clip."""
    def tile(s, poster, web):
        v = f'<video muted loop playsinline preload="none" data-hover-src="{E(web)}"></video>' if web else ""
        return (f'<a class="rl-t" href="{site.sport_url(s)}" data-hover tabindex="-1">'
                f'<img src="{E(poster)}" alt="" loading="lazy">{v}{icon(s["id"], "pic rl-pic")}'
                f'<span class="rl-name">{E(s["name"])}</span></a>')
    row1, row2 = [], []
    for k, s in enumerate(site.sports):
        c = s["clips"][0] if s["clips"] else None
        poster = site.murl(c["poster"]["url"]) if c else site.murl(s["thumb"]["url"])
        web = site.murl(c["web_720p"]["url"]) if c else None
        (row1 if rows == 1 or k % 2 == 0 else row2).append(tile(s, poster, web))
    tracks = "".join(f'<div class="rl-row rl-row--{d}"><div class="rl-track">{"".join(r) * 2}</div></div>'
                     for d, r in (("l", row1), ("r", row2)) if r)
    return f'<section class="reel" aria-label="The sports in motion">{tracks}</section>'


GLANCE_IC = {  # 24x24 line icons, stroke = currentColor
    "sports": '<rect x="3" y="3" width="7.5" height="7.5" rx="1.5"/><rect x="13.5" y="3" width="7.5" height="7.5" rx="1.5"/>'
              '<rect x="3" y="13.5" width="7.5" height="7.5" rx="1.5"/><rect x="13.5" y="13.5" width="7.5" height="7.5" rx="1.5"/>',
    "time": '<circle cx="12" cy="13" r="8"/><path d="M12 9v4.5l3 2M9.5 2.5h5"/>',
    "limits": '<circle cx="12" cy="12" r="3"/><path d="M12 2.5v3M12 18.5v3M2.5 12h3M18.5 12h3M5.3 5.3l2.1 2.1M16.6 16.6l2.1 2.1M5.3 18.7l2.1-2.1M16.6 7.4l2.1-2.1"/>',
    "control": '<circle cx="6" cy="18" r="2.2"/><circle cx="12" cy="10" r="2.2"/><circle cx="19" cy="5" r="1.8"/><path d="M7.3 16.2 10.7 11.8M13.8 8.8 17.4 6"/>',
}
GLANCE = [("sports", "18 Sports", "Diverse physical competition tasks."),
          ("time", "Real-Time Interaction", "The world keeps moving."),
          ("limits", "Real Robot Constraints", "Bodies, joints, actuators and physics."),
          ("control", "Direct Body Control", "Agents control the embodied system through low-level interfaces.")]


def page2(site: Site, clips: dict) -> str:
    """Screen 2: what Embodied Olympics is, a thin strip of all 18 sports, and the benchmark at a glance."""
    c = site.cfg
    mods = "".join(f'<li class="gl-m" data-inview><svg class="gl-ic" viewBox="0 0 24 24" aria-hidden="true">{GLANCE_IC[k]}</svg>'
                   f'<strong>{E(t)}</strong><span>{E(l)}</span></li>' for k, t, l in GLANCE)
    strip = reel(site, clips).replace('class="reel"', 'class="reel reel--plain reel--thin"', 1)
    return f"""
<section class="pg pg2" id="about">
  <div class="wrap pg2-def">
    <span class="kicker pg2-k">{E(c['definition_label'])}</span>
    <h2 class="pg2-h">{E(c['definition'])}</h2>
    <p class="pg2-p">{E(c['definition_line'])}</p>
  </div>
  {strip}
  <div class="wrap gl">
    <h3 class="gl-h">The Benchmark at a Glance</h3>
    <ul class="gl-row">{mods}</ul>
  </div>
</section>"""


def chap_head(n: str, title: str, line: str = "", total: str = "04") -> str:
    tot = f"<i>/{total}</i>" if total else ""
    return (f'<header class="ch-head"><span class="ch-n">{n}{tot}</span><h2>{title}</h2>'
            f'{f"<p>{line}</p>" if line else ""}</header>')


CAPS = [  # name, layer, clip, card class, skills
    ("Physical", "sys", "tabletennis_g1", "", ["State Estimation", "Prediction", "Execution", "Real-time Interaction"]),
    ("Competitive", "sys", "soccer_hsl_3v3", "cap4--crop", ["Strategy", "Opponent Modeling", "Collaboration"]),
    ("Engineering", "build", "stuntcar_replica", "cap4--build", ["Development", "Testing", "Debugging"]),
    ("Adaptive", "build", "drone_race_4", "", ["Feedback", "Continual Improvement"]),
]


def measure(site: Site, clips: dict) -> str:
    """01 What we measure: four core capabilities in two layers, as large video cards.
    The clip plays while the card is on screen; hover, focus or click lists the skills."""
    def card(name, cid, cls, subs):
        c = clips.get(cid)
        media = vid(c, "cover", "data-autoplay") if c else ""
        lis = "".join(f"<li>{E(s)}</li>" for s in subs)
        return (f'<button type="button" class="cap5 {cls}" data-cap aria-expanded="false">{media}<span class="cap4-grid"></span>'
                f'<span class="cap5-face"><strong>{name}</strong></span>'
                f'<span class="cap5-more"><strong>{name}</strong><ul>{lis}</ul></span>'
                f'<i class="cap5-plus" aria-hidden="true"></i></button>')
    layers = [("sys", "What the System Can Do", "The running system, which can change at any time."),
              ("build", "How the Agent Builds It", "Building includes improving, for as long as it competes.")]
    rows = []
    for key, name, sub in layers:
        cards = "".join(card(n, cid, cls, subs) for n, lay, cid, cls, subs in CAPS if lay == key)
        rows.append(f'<div class="lay"><div class="lay-h"><strong>{name}</strong></div><div class="lay-cards">{cards}</div></div>')
    link = ('<div class="lay-link" aria-hidden="true"><span><b>↑</b> develops and deploys new versions</span>'
            '<span><b>↓</b> match statistics and replays</span></div>')
    return f"""
<section class="chap chap--m pg pg3" data-inview id="measure">
  <div class="wrap">
    {chap_head('01', 'What we measure.', 'Four core capabilities in two layers. Results describe the whole agent system: the model, its harness and the code it writes.')}
    <div class="lays lays--big">{rows[0]}{link}{rows[1]}</div>
  </div>
</section>"""


MATCH_STEPS = [
    {"key": "prep", "kind": "prep", "label": "Prepare", "w": 24, "title": "Prepare", "v": 0, "score": None,
     "tag": "Practice arena · unscored", "agent": "Writes the controller and tests it in the practice arena.",
     "field": "Empty. The match has not started."},
    {"key": "play", "kind": "play", "label": "Play", "w": 26, "title": "Play", "v": 1, "score": [0, 1],
     "tag": "Official match · v1", "agent": "Watches through its robots’ cameras. It can keep coding.",
     "field": "v1 on the field. The clock runs at 1×."},
    {"key": "rev", "kind": "rev", "label": "Review", "w": 14, "title": "Review", "v": 1, "score": [0, 1],
     "tag": "Review window", "agent": "Replays the first half, finds what failed and patches it.",
     "field": "Paused for review."},
    {"key": "play2", "kind": "play", "label": "Play", "w": 26, "title": "Improve", "v": 2, "score": [2, 1],
     "tag": "Official match · v2", "agent": "Swaps in the new version and keeps watching.",
     "field": "v2 on the field."},
    {"key": "end", "kind": "end", "label": "Whistle", "w": 10, "title": "Final whistle", "v": 2, "score": [2, 1],
     "tag": "Full time", "agent": "Every version it fielded is saved for re-testing.", "field": "Full time."},
]


def match_block(site: Site, clips: dict) -> str:
    """One match as a broadcast timeline: footage + "now" panel; a playhead runs Prepare -> Play -> Review -> Play."""
    c = clips.get("basketball_3x3") or next(iter(clips.values()))
    steps = MATCH_STEPS
    total = sum(s["w"] for s in steps)
    starts, acc = [], 0
    for s in steps:
        starts.append(acc / total * 100)
        acc += s["w"]
    segs = "".join(f'<button type="button" class="tl3-seg tl3-{s["kind"]}" style="flex:{s["w"]}" data-seg="{k}">'
                   f'<span class="tl3-bar"></span><span class="tl3-lab">{s["label"]}</span></button>' for k, s in enumerate(steps))
    marks = (f'<span class="tl3-mark" style="left:{starts[1]:.2f}%">v1</span>'
             f'<span class="tl3-mark" style="left:{starts[3]:.2f}%">v2</span>')
    s0 = steps[0]
    return f"""<div class="mt3" data-match data-phase="prep">
      <div class="mt3-top">
        <figure class="stage-vid">{vid(c, 'cover', 'data-autoplay')}
          <div class="ov ov-grid"></div>
          <div class="ov ov-tag"><span data-now-tag>{s0['tag']}</span></div>
          <div class="ov ov-bug"><span>HOME</span><b data-s0>0</b><b data-s1>0</b><span>AWAY</span></div>
          <div class="ov ov-ft"><strong>Full time</strong><span class="ov-ft-score">2 – 1</span>
            <span class="ov-saved"><i>v1 saved</i><i>v2 saved</i></span></div>
          <div class="ov ov-log" aria-hidden="true"><span>reset <b data-resets>#1</b></span><span>test <b data-tests>1/20</b> <em>✓</em></span></div>
          <div class="ov ov-live" aria-hidden="true"><i class="rec"></i>LIVE <b data-mclock>00:00</b></div>
          <div class="ov ov-rev" aria-hidden="true">
            <span class="ov-mark"><i></i><em>lost the ball</em></span>
            <span class="ov-diff"><b>controller.py</b><del>- pass(ball)</del><ins>+ dribble(ball, safe=True)</ins></span>
            <span class="ov-scrub"><i></i></span>
          </div>
          <div class="ov ov-swap" aria-hidden="true"><span>v1</span><b>→</b><span>v2</span></div>
        </figure>
        <div class="now">
          <span class="kicker">Now</span>
          <strong data-now-title>{s0['title']}</strong>
          <dl>
            <div><dt>The agent</dt><dd data-now-agent>{s0['agent']}</dd></div>
            <div><dt>The field</dt><dd data-now-field>{s0['field']}</dd></div>
          </dl>
          <div class="vers"><span data-v="1">v1</span><span data-v="2">v2</span></div>
        </div>
      </div>
      <div class="tl3">
        <button type="button" class="tl3-btn" data-match-btn aria-label="Pause"><span></span></button>
        <div class="tl3-track">{segs}{marks}<span class="tl3-head" aria-hidden="true"></span></div>
      </div>
      <p class="note tl3-note">Illustration</p>
      <script type="application/json" data-match-steps>{json.dumps(steps)}</script>
    </div>"""


def chap3(site: Site, clips: dict, n: str = "02", title: str = "Prepare. Play.<br>Review. Improve.",
          line: str = "") -> str:
    """The match timeline as a chapter of its own (The Match page)."""
    return f"""
<section class="chap chap--3" data-inview>
  <div class="wrap">
    {chap_head(n, title, line)}
    {match_block(site, clips)}
  </div>
</section>"""


def arenas() -> str:
    """Practice arena · agent workspace · competition arena: two separate worlds, joined only through the agent's work."""
    return """<figure class="three">
  <div class="th-box th-prac"><span class="kicker">Practice arena</span><strong>Open at all hours.<br>Resettable.<br>Never scored.</strong></div>
  <div class="th-wire"><span>change &amp; test →</span><span>← results</span></div>
  <div class="th-box th-ws"><span class="kicker">Agent workspace</span><strong>Code · weights · notes</strong></div>
  <div class="th-wire"><span>deploy →</span><span>← replay</span></div>
  <div class="th-box th-arena"><span class="kicker">Competition arena</span><strong>Real time.<br>Official opponents.<br>Scored.</strong></div>
</figure>"""


G2_STEPS = [  # checkpoint (re-test after every match), score share vs fixed opponents, newly shown capabilities, what changed
    ("Start", 0.18, ["walk"], "Its first program walks."),
    ("Match 1", 0.27, ["getup"], "Gets up after falls."),
    ("Match 2", 0.34, [], "Steadier: falls half as often."),
    ("Match 3", 0.45, ["vision"], "Finds the ball with its own camera."),
    ("Match 4", 0.53, ["react"], "Reacts to the ball in time."),
    ("Match 5", 0.61, ["pass"], "Passes to a teammate in space."),
    ("Final", 0.71, ["team"], "Plays as a team."),
]
G2_CAPS = {"walk": "Walking", "getup": "Get-up", "vision": "Vision", "react": "Reaction", "pass": "Passing", "team": "Team play"}


def growth2() -> str:
    """One season: match tiles with re-test checkpoints between them drive two sketched curves,
    the growth curve (score vs the same fixed opponents) and the capability growth curve (Voyager-style count of
    distinct capabilities). Illustration only (humanoid soccer); no data."""
    n = len(G2_STEPS)
    W, H, pad = 400, 200, 14
    X = lambda i: pad + i * (W - 2 * pad) / (n - 1)  # noqa: E731
    Y = lambda v: H - pad - v * (H - 2 * pad)  # noqa: E731
    pts = [(X(i), Y(v)) for i, (_, v, _, _) in enumerate(G2_STEPS)]
    line = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    area = line + f" L{pts[-1][0]:.1f},{H - pad} L{pts[0][0]:.1f},{H - pad} Z"
    axes = f'<path class="g2-axis" d="M{pad},{pad - 6} V{H - pad} H{W - pad + 6}"/>'
    chart = f"""<svg viewBox="0 0 {W} {H}" preserveAspectRatio="none" aria-hidden="true">{axes}
        <line class="g2-level" x1="{pad}" x2="{W - pad}" y1="{Y(.5):.1f}" y2="{Y(.5):.1f}"/>
        <path class="g2-ghost" d="{line}"/>
        <g class="g2-reveal"><path class="g2-area" d="{area}"/><path class="g2-line" d="{line}"/></g></svg>"""
    # capability growth: a step up for every capability the re-test shows for the first time
    total = len(G2_CAPS)
    counts, acc = [], 0
    for _, _, caps, _ in G2_STEPS:
        acc += len(caps)
        counts.append(acc)
    YC = lambda c: H - pad - c / total * (H - 2 * pad) * 0.92  # noqa: E731
    step = f"M{X(0):.1f},{YC(counts[0]):.1f}" + "".join(f" H{X(i):.1f} V{YC(c):.1f}" for i, c in enumerate(counts) if i)
    step_svg = f"""<svg viewBox="0 0 {W} {H}" preserveAspectRatio="none" aria-hidden="true">{axes}
        <path class="g2-ghost" d="{step}"/><g class="g2-reveal"><path class="g2-line" d="{step}"/></g></svg>"""
    caps = "".join(f'<span class="g2-cap" data-at="{i}" style="left:{X(i) / W * 100:.2f}%;top:{YC(counts[i]) / H * 100:.2f}%">'
                   f'<i></i><em>{G2_CAPS[k]}</em></span>'
                   for i, (_, _, ks, _) in enumerate(G2_STEPS) for k in ks)
    loop = '<span class="sw-loop"><i class="p"></i><i class="g"></i><i class="r"></i><i class="g"></i></span>'

    def tile(lab, done):
        short = "F" if lab == "Final" else "M" + lab.split()[-1]
        return (f'<button type="button" class="sw-m" data-done="{done}" data-g2-goto="{done}">{loop}'
                f'<b><span class="sw-full">{lab}</span><span class="sw-short">{short}</span></b></button>')

    def ck(i):
        return (f'<button type="button" class="sw-ck" data-g2-stop="{i}" aria-label="Checkpoint {i + 1}: re-test">'
                f'<i></i><span>Re-test</span></button>')
    crown = ('<span class="sw-crown" aria-label="Season ends"><svg viewBox="0 0 24 24" aria-hidden="true">'
             '<path d="M3 8.5 7.5 12 12 5l4.5 7L21 8.5 19 18H5z"/><path d="M5 20.5h14"/></svg><span>Season ends</span></span>')
    labs = ["Match 1", "Match 2", "Match 3", "Match 4", "Match 5", "Final"]
    tiles = ck(0) + "".join(tile(l, i + 1) + ck(i + 1) for i, l in enumerate(labs)) + crown
    data = [{"x": round(X(i) / W * 100, 2), "y": round(Y(v) / H * 100, 2), "cy": round(YC(counts[i]) / H * 100, 2),
             "score": v, "skills": counts[i], "event": ev} for i, (_, v, _, ev) in enumerate(G2_STEPS)]
    return f"""<figure class="g2" data-g2>
  <div class="g2-top"><div class="g2-ex">{icon("soccer_hsl", "pic")}<span><em>Example</em>Humanoid Soccer</span></div>
    <p class="g2-event" data-g2-event>{G2_STEPS[0][3]}</p></div>
  <div class="sw">
    <div class="sw-matches">{tiles}</div>
    <div class="sw-carry"><span class="sw-carry-line"><i></i></span></div>
    <div class="sw-foot"><span class="sw-carry-lab">Carried to the next match<b>code · weights · replays · notes</b></span>
      <span class="sw-key">The world resets every match.</span></div>
  </div>
  <div class="g2-panels">
    <div class="g2-p">
      <span class="kicker">Growth curve</span>
      <div class="g2-q"><strong>Getting stronger?</strong><span>Score share against the same fixed opponents at each checkpoint</span></div>
      <div class="g2-chart">{chart}<span class="g2-dot"></span><span class="g2-lv">level</span><span class="g2-xl">checkpoint</span></div>
    </div>
    <div class="g2-p">
      <span class="kicker">Capability growth curve</span>
      <div class="g2-q"><strong>What has it learned?</strong><span>Distinct capabilities its program shows in the re-test, counted as they first appear</span></div>
      <div class="g2-chart g2-steps">{step_svg}{caps}<span class="g2-dot g2-dot--c"></span><span class="g2-xl">checkpoint</span></div>
    </div>
  </div>
  <p class="note g2-note">Sketches without data. Both curves come from the post-match re-test: frozen programs, no model calls.</p>
  <script type="application/json" data-g2-data>{json.dumps(data)}</script>
</figure>"""


def growth_panels(draw: bool = False) -> str:
    return growth2()


def season(site: Site, clips: dict) -> str:
    """02 One match · one season: the match loop, the two arenas, and what a season carries and produces."""
    sub = lambda k, t, line: (f'<header class="sub-h"><span class="kicker">{k}</span><h3>{t}</h3>'  # noqa: E731
                              f'<p>{line}</p></header>')
    return f"""
<section class="chap chap--s" data-inview id="season">
  <div class="wrap">
    {chap_head('02', 'One match.<br>One season.', 'Prepare, play, review, improve. The agent stays in the loop the whole time and decides when to do what.')}
    {sub('One match', 'Prepare → Play → Review → Improve', 'The clock runs in real time. The agent can keep coding while its program plays, and swap in a new version when it is ready.')}
    {match_block(site, clips)}
    {sub('Two arenas', 'Practise freely. Compete for real.', 'The practice arena and the competition arena are separate worlds. The agent decides when to use which; only its programs and weights cross over.')}
    {arenas()}
    {sub('One season', 'The work carries over. The world resets.', 'After every match the saved program is re-tested against the same fixed opponents. The re-tests give two curves.')}
    {growth2()}
  </div>
</section>"""


def _podium(seq: bool = False) -> str:
    g = ' data-g="md"' if seq else ""
    return (f'<div class="tm-pod"><div class="tm-step tm-step--2"><i class="tm-medal s"{g}>2</i><span></span></div>'
            f'<div class="tm-step tm-step--1"><i class="tm-medal g"{g}>1</i><span></span></div>'
            f'<div class="tm-step tm-step--3"><i class="tm-medal b"{g}>3</i><span></span></div></div>')


def _stepper(names: list, static: bool = False) -> str:
    keys = ["rr", "ko", "md"]
    return (f'<ol class="tm-steps{" tm-steps--all" if static else ""}">'
            + "".join(f'<li data-st="{keys[i]}"><b>{i + 1:02d}</b><strong>{n}</strong></li>' for i, n in enumerate(names)) + "</ol>")


def tournament(site: Site, head: bool = True) -> str:
    """The four formats of the edition (research page, section 03), one panel each, chosen with the buttons below.
    Head-to-head (12 sports): round robin -> semifinals -> final + bronze. Drone: time trials -> heats -> final.
    Full-size racing: 3 races, F1 points. Solo (4 sports): 3 runs, ranked by the mean. Cells never show invented results."""
    ms = site.models
    pairs = [(i, j) for i in range(len(ms)) for j in range(i + 1, len(ms))]
    order = {p: k for k, p in enumerate(sorted(pairs, key=lambda p: ((p[1] - p[0]) % 3, p)))}
    hdr = "".join(f'<span class="tm-h" title="{E(model_name(m))}" style="--c:{E(m["colour"])}">{model_logo(site, m)}</span>' for m in ms)
    rows = ""
    for i, mi in enumerate(ms):
        cells = "".join('<i class="tm-x"></i>' if i == j else f'<i class="tm-c" style="--k:{order[(min(i, j), max(i, j))]}"></i>'
                        for j in range(len(ms)))
        rows += f'<span class="tm-h" title="{E(model_name(mi))}" style="--c:{E(mi["colour"])}">{model_logo(site, mi)}</span>{cells}'
    tag = lambda m: f'<span class="tm-h tm-h--s" style="--c:{E(m["colour"])}">{model_logo(site, m)}</span>'  # noqa: E731

    h2h = f"""<div class="tm-pan" data-fmt-panel="h2h">
    {_stepper(["Round robin", "Knockout", "Medals"])}
    <div class="tm-body">
      <div class="tm-col" data-st="rr"><div class="tm-grid" style="--n:{len(ms)}"><span></span>{hdr}{rows}</div></div>
      <div class="tm-col" data-st="ko">
        <div class="tm-br">
          <div class="tm-bc">
            <span class="tm-bl" style="top:18px">Semifinal 1</span>
            <div class="tm-card1 tm-sf" data-ko="1" style="top:36px"><b>1st</b><em>v</em><b>4th</b></div>
            <span class="tm-bl" style="top:126px">Semifinal 2</span>
            <div class="tm-card1 tm-sf" data-ko="2" style="top:144px"><b>2nd</b><em>v</em><b>3rd</b></div>
          </div>
          <svg class="tm-wires" data-ko="3" viewBox="0 0 48 220" width="48" height="220" aria-hidden="true">
            <path d="M0 58 H24 V83 H44"/><path d="M0 166 H24 V119 H44"/><circle cx="44" cy="83" r="3"/><circle cx="44" cy="119" r="3"/></svg>
          <div class="tm-bc" data-ko="4">
            <span class="tm-bl tm-bl--gold" style="top:46px">Final</span>
            <div class="tm-card2 tm-fin" style="top:64px"><b>Winner SF 1</b><b>Winner SF 2</b></div>
            <span class="tm-bl tm-bl--bronze" style="top:156px">Bronze</span>
            <div class="tm-card1 tm-brz" style="top:174px"><b>SF 1 &amp; 2 losers</b></div>
          </div>
        </div>
      </div>
      <div class="tm-col" data-st="md">{_podium()}</div>
    </div>
    <p class="tm-rule">Win 3 · draw 1 · top four reach the semifinals</p>
  </div>"""

    trial = "".join(f'<div class="tm-run" data-g="rr">{tag(m)}' + "".join(f'<i style="--w:{w}%"{" class=best" if b else ""}></i>'
                    for w, b in zip([60, 72, 66], [False, True, False])) + '</div>'
                    for k, m in enumerate(ms))
    heat = lambda name, seats: (f'<div class="tm-heat"><span class="tm-bl2">{name}</span>'  # noqa: E731
                                + "".join(f'<b data-g="ko">{s}</b>' for s in seats) + '</div>')
    drone = f"""<div class="tm-pan" data-fmt-panel="drone" hidden>
    {_stepper(["Fly alone", "Race in 2 groups", "Final"])}
    <div class="tm-body">
      <div class="tm-col"><div class="tm-runs">{trial}</div></div>
      <div class="tm-col"><div class="tm-heats">{heat("Group A · 3 drones together", ["#1", "#4", "#5"])}{heat("Group B · 3 drones together", ["#2", "#3", "#6"])}</div></div>
      <div class="tm-col"><div class="tm-final4"><span class="tm-bl2">Final · 4 drones</span><b data-g="md">Group A top 2</b><b data-g="md">Group B top 2</b></div>{_podium(seq=True)}</div>
    </div>
    <p class="tm-rule">Fastest of 3 solo laps sets #1–#6 · top 2 of each group reach the final</p>
  </div>"""

    races = "".join(f'<div class="tm-race" data-g="rr"><b>Race {k}</b><span>10 laps · 6 cars</span><i></i></div>' for k in (1, 2, 3))
    pts = "".join(f'<div class="tm-pt" data-g="ko"><span>{p}</span><i style="--w:{v * 4}%"></i><b>{v}</b></div>'
                  for p, v in zip(["1st", "2nd", "3rd", "4th", "5th", "6th"], [25, 18, 15, 12, 10, 8]))
    racing = f"""<div class="tm-pan" data-fmt-panel="racing" hidden>
    {_stepper(["3 races", "F1 points", "Medals"])}
    <div class="tm-body">
      <div class="tm-col"><div class="tm-races">{races}</div></div>
      <div class="tm-col"><div class="tm-pts">{pts}</div></div>
      <div class="tm-col">{_podium(seq=True)}</div>
    </div>
    <p class="tm-rule">All six models on one track · points summed over the three races</p>
  </div>"""

    wrench = ('<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M14.5 6.5a4 4 0 0 0 5 5L12 19a2.1 2.1 0 0 1-3-3l7.5-7.5'
              'a4 4 0 0 0-2-2z"/></svg>')
    runs_w = [46, 64, 82]
    sr = lambda n, w: f'<div class="tm-sr" data-g="rr"><b>Run {n}</b><span><i style="--w:{w}%"></i></span></div>'  # noqa: E731
    fix = lambda a, b: f'<div class="tm-fix" data-g="rr" aria-label="new version of its code"><span>v{a} → v{b}</span></div>'  # noqa: E731
    journey = sr(1, runs_w[0]) + fix(1, 2) + sr(2, runs_w[1]) + fix(2, 3) + sr(3, runs_w[2])
    ghosts = "".join(f'<i data-g="ko" style="--w:{w}%"></i>' for w in runs_w)
    mean_w = round(sum(runs_w) / 3)
    solo = f"""<div class="tm-pan" data-fmt-panel="solo" hidden>
    {_stepper(["Three runs", "Average", "Medals"])}
    <div class="tm-body">
      <div class="tm-col"><div class="tm-solo"><span class="tm-bl2">One entry</span>{journey}</div></div>
      <div class="tm-col"><div class="tm-avg"><span class="tm-bl2">Average</span>
        <div class="tm-avg-bars">{ghosts}</div>
        <div class="tm-avg-eq" data-g="ko"><b>=</b><span><i style="--w:{mean_w}%"></i></span></div></div></div>
      <div class="tm-col">{_podium(seq=True)}</div>
    </div>
    <p class="tm-rule">Same hidden course for everyone · fix the code between runs · ranked by the average</p>
  </div>"""

    h2h_sports = ["soccer_hsl", "badminton", "tennis", "basketball"]
    btns = [("h2h", h2h_sports, "Duel · Team duel", "12 sports"), ("drone", ["drone"], "Drone racing", "Alone → groups → final"),
            ("racing", ["racing"], "Full-size racing", "3 races · F1 points"),
            ("solo", ["stuntcar", "sprint", "hurdles", "javelin"], "Solo events", "3 runs · averaged")]
    oth = "".join(f'<button type="button" class="tm-o{" is-on" if k == "h2h" else ""}" data-fmt="{k}" aria-pressed="{str(k == "h2h").lower()}">'
                  f'<span class="tm-o-ic">{"".join(icon(s) for s in ids)}</span><strong>{n}</strong><span>{d}</span></button>'
                  for k, ids, n, d in btns)
    title = '<header class="sec-head"><h2>How medals<br>are won.</h2></header>' if head else ""
    return f"""<div class="tm" data-tm data-fmt="h2h">
  {title}
  <div class="tm-card">{h2h}{drone}{racing}{solo}</div>
  <div class="tm-others" role="tablist" aria-label="Formats">{oth}</div>
</div>"""


def competition(site: Site, clips: dict) -> str:
    """03 The competition: the 18 sports grouped by format; body and stressed capabilities as labels.
    Same grid interaction as before: hover or focus plays the sport's clip."""
    tags = site.cfg.get("sport_tags", {})
    groups = []
    for f in site.cfg["formats"]:
        tiles = []
        for sid in f["sports"]:
            s = site.sport_by_id.get(sid)
            if not s:
                continue
            c = clips.get(s["clips"][0]["id"]) if s["clips"] else None
            media = (f'<video muted loop playsinline preload="none" data-hover-src="{E(c["web"])}" poster="{E(c["poster"])}"></video>'
                     if c else f'<img src="{E(site.murl(s["thumb"]["url"]))}" alt="" loading="lazy">')
            meta, labs = (tags.get(sid) or ["", []])
            chips = "".join(f"<i>{E(l)}</i>" for l in labs)
            tiles.append(f'<a class="wt wt3" href="{site.sport_url(s)}" data-hover><span class="wt-media">{media}</span>'
                         f'{icon(s["id"], "pic wt-pic")}<span class="wt3-txt"><span class="wt-name">{E(s["name"])}</span>'
                         f'<span class="wt3-meta">{E(meta)}</span><span class="wt3-labs">{chips}</span></span></a>')
        groups.append(f'<div class="fg" data-n="{len(tiles)}"><header class="fg-h"><h3>{E(f["name"])}<b>{len(tiles)}</b></h3>'
                      f'<p>{E(f["line"])}</p></header><div class="fg-tiles">{"".join(tiles)}</div></div>')
    return f"""
<section class="chap chap--c" data-inview id="competition">
  <div class="wrap">
    {chap_head('03', f'{len(site.sports)} sports.<br>Four formats.', 'Real rules on real robot bodies. Labels say what each sport mainly stresses; Engineering and Adaptive run through all of them.')}
    <div class="fgs">{''.join(groups)}</div>
    <p class="fgs-foot"><a class="link" href="{site.url('sports/')}">All sports <span class="arr">→</span></a></p>
  </div>
</section>"""


MEDAL_FORMATS = [  # id (results page tab), name, sports covered, the path in one line, detail
    ("solo", "Solo", "4 sports", "3 runs → average",
     "Sprint, hurdles, javelin and stunt car. Every entry runs the same hidden course three times and may fix its code "
     "between runs. Ranked by the average of the three runs."),
    ("h2h", "Duel · Team duel", "12 sports", "Round robin → semifinals → final",
     "Every entrant plays every other once: win 3, draw 1. The top four reach the semifinals, then a final and a bronze match."),
    ("drone", "Drone racing", "1 sport", "Time trial → heats → final",
     "The fastest of three solo laps sets the seeding. Two heats of three drones; the top two of each heat fly the final."),
    ("racing", "Full-size racing", "1 sport", "3 races → points",
     "Every car on one track for three races. F1-style points, summed over the three races, decide the medals."),
]


def results_compact(site: Site) -> str:
    """04 Results, home version: how medals are won (four chips), a provisional medal table, links to /results/."""
    chips = "".join(
        f'<a class="mchip" href="{site.url("results/")}#fmt-{k}" data-mchip="{k}" aria-expanded="false">'
        f'<span class="mchip-top"><strong>{E(name)}</strong><em>{E(n)}</em></span><span class="mchip-path">{E(path)}</span></a>'
        for k, name, n, path, _ in MEDAL_FORMATS)
    details = "".join(
        f'<div class="mchip-d" data-mchip-d="{k}" hidden><p>{E(d)}</p>'
        f'<a class="link" href="{site.url("results/")}#fmt-{k}">Full format diagram <span class="arr">→</span></a></div>'
        for k, _, _, _, d in MEDAL_FORMATS)
    links = [("results/#arena", "Open Arena", "Every agent against every other, from scratch"),
             ("results/#by-sport", "By sport", "Podiums for all 18 sports"),
             ("results/#replays", "Replays", "Watch the matches")]
    row = "".join(f'<a class="rlink" href="{site.url(h)}"><strong>{E(n)}</strong><span>{E(l)}</span><b class="arr">→</b></a>'
                  for h, n, l in links)
    return f"""
<section class="chap chap--r" data-inview id="results">
  <div class="wrap">
    {chap_head('04', 'Results.', 'Medals are decided sport by sport. The medal table fills in at release.')}
    <div class="rx">
      <div class="rx-medals">
        <h3 class="rx-h">How medals are won</h3>
        <div class="mchips">{chips}</div>
        {details}
      </div>
      <div class="rx-table">
        <h3 class="rx-h">Medal table</h3>
        <div class="rx-ph"><i class="medal medal--g"></i><i class="medal medal--s"></i><i class="medal medal--b"></i><strong>Medal table at release</strong></div>
      </div>
    </div>
    <nav class="rlinks" aria-label="Full results">{row}</nav>
  </div>
</section>"""


# ---------------------------------------------------------------- page


def home(site: Site):
    clips = clip_index(site)
    body = ('<div class="stagebg" data-hero2>' + hero(site, clips) + '</div>' + page2(site, clips)
            + measure(site, clips) + season(site, clips) + competition(site, clips) + results_compact(site)
            + '<nav class="crail" aria-label="Chapters" data-crail></nav>'
            + f'<script src="{site.asset("js/home.js")}" defer></script>')
    return "", page(site, path="", title=None, body=body, dark_top=True)
