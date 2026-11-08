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


def physloop() -> str:
    """Agents in the Physical Loop: two agents, each with its own practice arena, meet in one competition arena.
    Labels state only what the Engineer track's seat instructions say (see handoff/webv3_1108.md, round 7)."""
    def agent(x, name):
        return (f'<g class="pl-agent"><rect x="{x}" y="215" width="230" height="130" rx="16"/>'
                f'<text class="pl-t" x="{x + 115}" y="268">{name}</text>'
                f'<text class="pl-s" x="{x + 115}" y="296">Model · Harness · Workspace</text></g>')

    def practice(x):
        return (f'<g class="pl-prac"><rect x="{x}" y="20" width="230" height="130" rx="16"/>'
                f'<text class="pl-t pl-t--s" x="{x + 115}" y="62">Practice Arena</text>'
                f'<text class="pl-s" x="{x + 115}" y="90">full copy of the match world</text>'
                f'<text class="pl-s" x="{x + 115}" y="112">resettable · unscored</text>'
                f'<text class="pl-s" x="{x + 115}" y="134">open before, during, after play</text></g>')

    def robot(cx, cls):
        return (f'<g class="pl-robot {cls}"><circle cx="{cx}" cy="230" r="13"/><path d="M{cx} 246 v52 M{cx - 26} 262 h52 '
                f'M{cx} 298 l-18 40 M{cx} 298 l18 40"/></g>')
    # flows: agent A at x 20..250, agent B at 950..1180, arena 360..840
    paths = {
        "obsA": "M360 250 H250", "actA": "M250 310 H360", "obsB": "M840 250 H950", "actB": "M950 310 H840",
        "pracA": "M135 150 V215", "pracB": "M1065 150 V215",
        "resA": "M520 440 C520 500 135 500 135 345", "resB": "M680 440 C680 500 1065 500 1065 345",
    }
    lines = "".join(f'<path id="pl-{k}" class="pl-flow{" pl-flow--res" if k.startswith("res") else ""}" d="{d}"/>' for k, d in paths.items())
    heads = "".join(f'<path class="pl-head" d="{d}"/>' for d in (
        "M258 244 L250 250 L258 256", "M352 304 L360 310 L352 316", "M942 244 L950 250 L942 256", "M848 304 L840 310 L848 316",
        "M129 207 L135 215 L141 207", "M1059 207 L1065 215 L1071 207", "M129 353 L135 345 L141 353", "M1059 353 L1065 345 L1071 353"))
    pulses = "".join(f'<circle class="pl-pulse" r="4.5"><animateMotion dur="{d}s" begin="{b}s" repeatCount="indefinite"><mpath href="#pl-{k}"/></animateMotion></circle>'
                     for k, d, b in (("obsA", 3.2, 0), ("actA", 3.2, 1.6), ("obsB", 3.2, .8), ("actB", 3.2, 2.4),
                                     ("pracA", 2.6, .4), ("pracB", 2.6, 1.7), ("resA", 6, 0), ("resB", 6, 3)))
    labels = (
        '<text class="pl-l" x="305" y="238">Observation</text><text class="pl-l" x="305" y="336">Action</text>'
        '<text class="pl-l" x="895" y="238">Observation</text><text class="pl-l" x="895" y="336">Action</text>'
        '<text class="pl-l pl-l--m" x="600" y="492">Score · a review after every scoring unit</text>'
        '<text class="pl-l pl-l--s" x="600" y="520">observation: cameras or vision feed · own state · referee    '
        'action: joint-level commands every 10–20 ms</text>')
    arena = (f'<g class="pl-arena"><rect x="360" y="110" width="480" height="330" rx="20"/>'
             f'<text class="pl-t" x="600" y="160">Competition Arena</text>'
             f'<text class="pl-s" x="600" y="190">shared physical world · runs on its own clock · scored</text>'
             f'{robot(520, "pl-robot--a")}{robot(680, "pl-robot--b")}'
             f'<text class="pl-s pl-vs" x="600" y="300">vs</text>'
             f'<text class="pl-s" x="520" y="372">Robot A</text><text class="pl-s" x="680" y="372">Robot B</text></g>')
    svg = (f'<svg class="pl-svg" viewBox="0 0 1200 535" role="img" aria-label="Two agents, each with its own practice arena, '
           f'observe and act on their robots in one shared competition arena">{lines}{heads}{practice(20)}{practice(950)}'
           f'{agent(20, "Agent A")}{agent(950, "Agent B")}{arena}{labels}<g class="pl-pulses">{pulses}</g></svg>')
    return f"""
<section class="pg pgl" data-inview id="loop">
  <div class="wrap">
    <header class="pl-head-t"><span class="kicker">Agent–environment architecture</span><h2>Agents in the Physical Loop</h2></header>
    <div class="pl-fig"><div class="pl-scroll">{svg}</div><p class="note pl-note">Schematic</p></div>
  </div>
</section>"""


def chap_head(n: str, title: str, line: str = "", total: str = "04") -> str:
    tot = f"<i>/{total}</i>" if total else ""
    return (f'<header class="ch-head"><span class="ch-n">{n}{tot}</span><h2>{title}</h2>'
            f'{f"<p>{line}</p>" if line else ""}</header>')


CAPS = [  # name, layer, still, card class, one line, skills (shown on hover / click only)
    ("Physical", "sys", "tabletennis_g1", "", "Perceive, predict, and act in the physical world.",
     ["State Estimation", "Prediction", "Execution", "Real-time Interaction"]),
    ("Competitive", "sys", "soccer_hsl_3v3", "mc--crop", "Compete through strategy and interaction.",
     ["Strategy", "Opponent Modeling", "Collaboration"]),
    ("Engineering", "build", "stuntcar_wave_wall", "mc--build", "Develop and validate effective systems.",
     ["Development", "Testing", "Debugging"]),
    ("Adaptive", "build", "drone_race_4", "", "Learn from feedback and improve continuously.",
     ["Feedback", "Continual Improvement"]),
]
MEASURE_GROUPS = [("build", "How the Agent Builds It", ["Engineering", "Adaptive"]),
                  ("sys", "What the System Can Do", ["Physical", "Competitive"])]
MEASURE_FLOW = ("builds and deploys the system", "match results and replays feed back")


def measure(site: Site, clips: dict, variant: str = "a") -> str:
    """01 What we measure: four equal capabilities in two light groups, joined by a loop.
    A: 2 x 2 (agent group left, system group right) with the two flow arrows between the columns.
    B: one row of four, a thin bracket above each pair and the loop drawn under the row."""
    by = {c[0]: c for c in CAPS}

    def card(name):
        _, _, cid, cls, line, subs = by[name]
        c = clips.get(cid)
        img = f'<img src="{E(c["poster"])}" alt="" loading="lazy">' if c else ""
        skills = "".join(f"<li>{E(s)}</li>" for s in subs)
        return (f'<button type="button" class="mc {cls}" data-cap aria-expanded="false">'
                f'<span class="mc-img">{img}<span class="mc-grid"></span><ul class="mc-skills">{skills}</ul>'
                f'<i class="mc-plus" aria-hidden="true"></i></span>'
                f'<strong class="mc-name">{name}</strong><span class="mc-line">{E(line)}</span></button>')
    fwd, back = MEASURE_FLOW
    if variant == "b":
        groups = "".join(f'<div class="mb-g"><span class="mb-br kicker">{E(g)}</span><div class="mb-cards">{card(n1)}{card(n2)}</div></div>'
                         for _, g, (n1, n2) in MEASURE_GROUPS)
        body = (f'<div class="mb">{groups}</div>'
                f'<div class="mb-loop" aria-label="Loop: the agent {fwd}; {back}">'
                f'<p class="mb-fwd"><span>{E(fwd)}</span></p><p class="mb-back"><span>{E(back)}</span></p>'
                f'<i class="flow-dot flow-dot--a"></i><i class="flow-dot flow-dot--b"></i></div>')
    else:
        (k1, g1, (a1, a2)), (k2, g2, (b1, b2)) = MEASURE_GROUPS
        body = f"""<div class="ma">
      <span class="kicker ma-tag ma-tag--l">{E(g1)}</span><span class="kicker ma-tag ma-tag--r">{E(g2)}</span>
      <div class="ma-c ma-l1">{card(a1)}</div><div class="ma-c ma-l2">{card(a2)}</div>
      <div class="ma-c ma-r1">{card(b1)}</div><div class="ma-c ma-r2">{card(b2)}</div>
      <div class="ma-arrow ma-fwd"><span class="ma-lab">{E(fwd)}</span><span class="ma-line"><i class="flow-dot flow-dot--a"></i></span></div>
      <div class="ma-arrow ma-back"><span class="ma-line"><i class="flow-dot flow-dot--b"></i></span><span class="ma-lab">{E(back)}</span></div>
    </div>"""
    return f"""
<section class="chap chap--m pg pg3 pg3--{variant}" data-inview id="measure">
  <div class="wrap">
    {chap_head('01', 'What we measure.', 'We evaluate both the capabilities of the embodied system and the agent&rsquo;s ability to build and improve it.')}
    {body}
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
    <div class="sw-foot"><span class="sw-carry-lab">Carried to the next match<b>programs · weights · notes</b></span>
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


def match_loop() -> str:
    """One match in time: preparation, then a loop the agent runs as it decides, then the end of the match."""
    import math
    cx, cy, r = 600, 205, 128
    nodes = [("Play", "the world never waits", -90), ("Review", "the world freezes|after each scoring unit", 0),
             ("Improve & Test", "in the practice arena", 90), ("Deploy", "start or replace programs", 180)]
    pos = [(cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))) for _, _, a in nodes]
    arcs = ""
    for k in range(4):
        a0, a1 = math.radians(nodes[k][2] + 22), math.radians(nodes[k][2] + 68)
        x0, y0, x1, y1 = cx + r * math.cos(a0), cy + r * math.sin(a0), cx + r * math.cos(a1), cy + r * math.sin(a1)
        arcs += f'<path class="ml-arc" d="M{x0:.1f} {y0:.1f} A{r} {r} 0 0 1 {x1:.1f} {y1:.1f}"/>'
        hx, hy = x1, y1
        ang = nodes[k][2] + 68 + 90
        arcs += (f'<path class="ml-head" transform="translate({hx:.1f} {hy:.1f}) rotate({ang:.1f})" d="M-6 -6 L0 0 L-6 6"/>')
    def node(k):
        (name, sub, a), (x, y) = nodes[k], pos[k]
        tx = {0: (x, y - 52), 1: (x + 38, y - 66), 2: (x, y + 58), 3: (x - 38, y - 50)}[k]
        anchor = {0: "middle", 1: "start", 2: "middle", 3: "end"}[k]
        return (f'<g class="ml-node"><circle cx="{x:.1f}" cy="{y:.1f}" r="30"/>'
                f'<text class="ml-n" x="{tx[0]:.1f}" y="{tx[1]:.1f}" text-anchor="{anchor}">{name}</text>'
                + "".join(f'<text class="ml-s" x="{tx[0]:.1f}" y="{tx[1] + 20 + 17 * j:.1f}" text-anchor="{anchor}">{s}</text>'
                          for j, s in enumerate(sub.split("|"))) + '</g>')
    nodes_svg = "".join(node(k) for k in range(4))
    ring = f'<circle id="ml-ring" class="ml-ring" cx="{cx}" cy="{cy}" r="{r}"/>'
    pulse = ('<circle class="pl-pulse" r="5"><animateMotion dur="9s" repeatCount="indefinite" '
             f'path="M{cx} {cy - r} A{r} {r} 0 1 1 {cx - .1} {cy - r}"/></circle>')
    box = lambda x, t1, t2, cls: (f'<g class="ml-box {cls}"><rect x="{x}" y="150" width="230" height="110" rx="16"/>'  # noqa: E731
                                  f'<text class="pl-t pl-t--s" x="{x + 115}" y="196">{t1}</text>'
                                  f'<text class="pl-s" x="{x + 115}" y="224">{t2}</text></g>')
    links = ('<path class="pl-flow" d="M250 205 H420"/><path class="pl-head" d="M412 199 L420 205 L412 211"/>'
             '<path class="pl-flow" d="M780 205 H950"/><path class="pl-head" d="M942 199 L950 205 L942 211"/>')
    center = (f'<text class="pl-t pl-t--s" x="{cx}" y="{cy - 4}">Competition</text>'
              f'<text class="pl-s" x="{cx}" y="{cy + 22}">as often as the agent decides</text>')
    svg = (f'<svg class="ml-svg" viewBox="0 0 1200 420" role="img" aria-label="Preparation, then a loop of play, review, improve and test, '
           f'deploy, then the match ends">{links}{ring}{arcs}{box(20, "Preparation", "develop · test · deploy", "ml-prep")}'
           f'{center}{nodes_svg}{box(950, "Match ends", "programs and records saved", "ml-end")}<g class="pl-pulses">{pulse}</g></svg>')
    return svg


def match_screen() -> str:
    return f"""
<section class="chap pg pgm" data-inview id="match">
  <div class="wrap">
    {chap_head('02', 'One match.', 'The agent prepares before the match, stays in the loop through competition, and decides when and how to improve its system.')}
    <div class="ml-fig">{match_loop()}</div>
  </div>
</section>"""


def season_screen() -> str:
    return f"""
<section class="chap pg pgs" data-inview id="season">
  <div class="wrap">
    <header class="ch-head"><span class="ch-n"></span><h2>One season.</h2>
      <p>Programs, weights and notes carry over; the world and the seed reset. Saved programs are re-tested after every match.</p></header>
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
    """03 The competition: the 18 sports in one six-column grid, grouped by format (Solo and Race share the first row).
    Each tile: pictogram, name, body; hover or focus plays the clip and shows what the sport mainly stresses."""
    tags = site.cfg.get("sport_tags", {})
    fmts = {f["id"]: f for f in site.cfg["formats"]}

    def tiles(f):
        out = []
        for sid in f["sports"]:
            s = site.sport_by_id.get(sid)
            if not s:
                continue
            c = clips.get(s["clips"][0]["id"]) if s["clips"] else None
            media = (f'<video muted loop playsinline preload="none" data-hover-src="{E(c["web"])}" poster="{E(c["poster"])}"></video>'
                     if c else f'<img src="{E(site.murl(s["thumb"]["url"]))}" alt="" loading="lazy">')
            meta, labs = (tags.get(sid) or ["", []])
            chips = "".join(f"<i>{E(l)}</i>" for l in labs)
            out.append(f'<a class="wt wt3" href="{site.sport_url(s)}" data-hover><span class="wt-media">{media}</span>'
                       f'{icon(s["id"], "pic wt-pic")}<span class="wt3-txt"><span class="wt-name">{E(s["name"])}</span>'
                       f'<span class="wt3-meta">{E(meta)}</span><span class="wt3-labs">{chips}</span></span></a>')
        return out

    def head(f, span):
        n = len([x for x in f["sports"] if x in site.sport_by_id])
        return (f'<header class="fg2-h" style="grid-column:span {span}"><h3>{E(f["name"])}<b>{n}</b></h3>'
                f'<p>{E(f["line"])}</p></header>')
    rows = [[("solo", 4), ("race", 2)], [("duel", 6)], [("team", 6)]]
    cells = []
    for row in rows:
        cells += [head(fmts[k], span) for k, span in row]
        for k, _ in row:
            cells += tiles(fmts[k])
    return f"""
<section class="chap chap--c pg pgc" data-inview id="competition">
  <div class="wrap">
    <header class="ch-head"><span class="ch-n">03<i>/04</i></span><h2>{len(site.sports)} sports. Four formats.</h2>
      <p>Real rules on real robot bodies. Hover a sport for what it mainly stresses. <a class="link" href="{site.url('sports/')}">All sports <span class="arr">→</span></a></p></header>
    <div class="fg2">{''.join(cells)}</div>
  </div>
</section>"""


MEDAL_FLOWS = [  # id, name, sports, steps, one line
    ("solo", "Solo", "4 sports", ["Run 1", "Run 2", "Run 3", "Average", "Medals"],
     "Same hidden course for every entry; the agent may fix its code between runs."),
    ("h2h", "Duel · Team duel", "12 sports", ["Round robin", "Semifinals", "Final + bronze", "Medals"],
     "Win 3 · draw 1 · the top four reach the semifinals (1st v 4th, 2nd v 3rd)."),
    ("drone", "Drone racing", "1 sport", ["Time trial", "Heats · 2 × 3", "Final · 4", "Medals"],
     "The fastest of three solo laps sets the seeding; the top two of each heat fly the final."),
    ("racing", "Full-size racing", "1 sport", ["Race 1", "Race 2", "Race 3", "Points", "Medals"],
     "Every car on one track; F1-style points summed over the three races."),
]


def results_compact(site: Site) -> str:
    """04 Results, home version: how medals are won (click a format for its flow), the medal table placeholder, links."""
    tabs = "".join(f'<button type="button" class="mf-tab{" is-on" if k == 0 else ""}" data-mf-tab="{fid}" aria-pressed="{str(k == 0).lower()}">'
                   f'<strong>{E(n)}</strong><em>{E(c)}</em></button>' for k, (fid, n, c, _, _) in enumerate(MEDAL_FLOWS))
    def flow(steps):
        out = []
        for k, s in enumerate(steps):
            last = k == len(steps) - 1
            out.append(f'<li class="mf-step{" mf-step--m" if last else ""}" style="--k:{k}">{E(s)}</li>')
            if not last:
                out.append(f'<li class="mf-arr" aria-hidden="true" style="--k:{k}">→</li>')
        return "".join(out)
    panels = "".join(f'<div class="mf-pan" data-mf-pan="{fid}"{"" if k == 0 else " hidden"}><ol class="mf-flow">{flow(st)}</ol>'
                     f'<p class="mf-note">{E(line)}</p></div>' for k, (fid, _, _, st, line) in enumerate(MEDAL_FLOWS))
    links = [("results/#arena", "Open Arena", "Every agent against every other, from scratch"),
             ("results/#by-sport", "By sport", "Podiums for all 18 sports"),
             ("results/#replays", "Replays", "Watch the matches")]
    row = "".join(f'<a class="rlink" href="{site.url(h)}"><strong>{E(n)}</strong><span>{E(l)}</span><b class="arr">→</b></a>'
                  for h, n, l in links)
    return f"""
<section class="chap pg pgr" data-inview id="results">
  <div class="wrap">
    {chap_head('04', 'Results.', 'Medals are decided sport by sport.')}
    <div class="mf" data-mf>
      <h3 class="kicker mf-k">How medals are won</h3>
      <div class="mf-tabs" role="group" aria-label="Formats">{tabs}</div>
      <div class="mf-panels">{panels}</div>
      <a class="link mf-full" href="{site.url('results/')}#formats">Full format diagram <span class="arr">→</span></a>
    </div>
    <div class="rx-ph"><i class="medal medal--g"></i><i class="medal medal--s"></i><i class="medal medal--b"></i><strong>Medal table at release</strong></div>
    <nav class="rlinks" aria-label="Full results">{row}</nav>
  </div>
</section>"""


# ---------------------------------------------------------------- page


def home(site: Site, measure_variant: str = "a"):
    clips = clip_index(site)
    body = ('<div class="stagebg" data-hero2>' + hero(site, clips) + '</div>' + page2(site, clips) + physloop()
            + measure(site, clips, measure_variant) + match_screen() + season_screen() + competition(site, clips) + results_compact(site)
            + '<nav class="crail" aria-label="Chapters" data-crail></nav>'
            + f'<script src="{site.asset("js/home.js")}" defer></script>')
    return "", page(site, path="", title=None, body=body, dark_top=True)
