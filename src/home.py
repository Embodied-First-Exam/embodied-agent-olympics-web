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


def chap_head(n: str, title: str, line: str = "") -> str:
    return (f'<header class="ch-head"><span class="ch-n">{n}<i>/05</i></span><h2>{title}</h2>'
            f'{f"<p>{line}</p>" if line else ""}</header>')


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
        <p class="h2o-tag">{E(site.cfg['tagline'])}</p>
        <a class="btn btn--light" href="{site.url('watch/')}" data-hero-watch><span class="play"></span>Watch</a>
      </div>
      <div class="channels" role="group" aria-label="Switch sport">{channels}</div>
    </div>
  </div>
</section>
<script type="application/json" data-hero2-clips>{json.dumps(seq)}</script>"""


def question(site: Site, clips: dict) -> str:
    """A short headline in large type; the research question itself, verbatim, as one line beneath it."""
    short = " ".join(f'<span class="ql ql--hi" style="--k:{k}">{E(l)}</span>' for k, l in enumerate(site.cfg["question_short"]))
    return f"""
<section class="qx2" data-inview>
  <div class="wrap qx2-in">
    <h2 class="qx2-text">{short}</h2>
    <p class="ql qx2-full" style="--k:3">{E(site.cfg['question'])}</p>
  </div>
</section>"""


def reel(site: Site, clips: dict) -> str:
    """Two rows of match stills drifting in opposite directions; hover pauses the row and plays that clip."""
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
        (row1 if k % 2 == 0 else row2).append(tile(s, poster, web))
    rows = "".join(f'<div class="rl-row rl-row--{d}"><div class="rl-track">{"".join(r) * 2}</div></div>'
                   for d, r in (("l", row1), ("r", row2)))
    return f'<section class="reel" aria-label="The sports in motion">{rows}</section>'


def numbers(site: Site, clips: dict) -> str:
    """The big numbers sit on top of the drifting reel of all 18 sports (the reel is the '18')."""
    cells = [(len(site.sports), "Sports"), (len(site.models), "AI agents"), (1, "Season"), (0, "Pauses")]
    nums = "".join(f'<div class="num" data-inview><strong data-count="{n}">{n}</strong><span>{E(l)}</span></div>' for n, l in cells)
    return f"""<section class="numreel">
  {reel(site, clips)}
  <div class="numreel-scrim"></div>
  <div class="nums"><div class="wrap nums-grid">{nums}</div></div>
</section>"""


_PY_TOKEN = re.compile(r"""(?P<com>\#.*$)|(?P<str>"[^"]*"|'[^']*')|(?P<kw>\b(?:def|return|if|else|for|in|import|from|class)\b)"""
                       r"""|(?P<num>\b\d+(?:\.\d+)?\b)|(?P<call>\b[A-Za-z_]\w*(?=\())|(?P<attr>(?<=\.)[A-Za-z_]\w*)"""
                       r"""|(?P<kwarg>\b[A-Za-z_]\w*(?==))|(?P<name>\b[A-Za-z_]\w*\b)|(?P<op>[=().,:])""", re.M)


def hl_python(src: str) -> str:
    """Tiny Python highlighter with VS Code Dark+ token classes (enough for the few illustrative lines)."""
    out, pos, after_def = [], 0, False
    for m in _PY_TOKEN.finditer(src):
        out.append(E(src[pos:m.start()]))
        kind, tok = m.lastgroup, m.group()
        if kind == "call" and after_def:
            kind = "fn"
        if kind == "kw" and tok in ("return", "if", "else", "for", "in", "import", "from"):
            kind = "ctl"  # Dark+ colours control-flow keywords purple
        after_def = kind == "kw" and tok == "def" or (after_def and kind not in ("call", "fn", "name"))
        out.append(f'<i class="t-{kind}">{E(tok)}</i>')
        pos = m.end()
    out.append(E(src[pos:]))
    return "".join(out)


def chap1(site: Site, clips: dict) -> str:
    c = clips.get("badminton_g1") or next(iter(clips.values()))
    code = ["# written by the agent", "def step(obs):", "    shuttle = track(obs.head_depth)",
            "    hit = predict_contact(shuttle)", "    pose = reach(hit, racket=\"right\")",
            "    return joint_targets(pose)"]
    lines = "".join(f'<span class="cl"><b>{n + 1}</b><span class="cl-t">{hl_python(t)}</span><i class="cl-cur"></i></span>'
                    for n, t in enumerate(code))
    return f"""
<section class="chap chap--1" data-inview>
  <div class="wrap">
    {chap_head('01', 'AI agents build<br>robot athletes.')}
    <figure class="codevid build">
      {vid(c, 'cover', 'data-autoplay', hd=True)}
      <div class="codevid-shade"></div>
      <div class="codevid-ed"><span class="codevid-tab"><i></i>controller.py</span><pre class="codevid-code" data-type>{lines}</pre></div>
      <div class="term-status"><span class="ok">●</span> v7 on the field</div>
      <span class="note codevid-note">Illustrative code</span>
    </figure>
  </div>
</section>"""


def chap2(site: Site, clips: dict) -> str:
    panels = [("beach_volleyball", "Real motor limits."), ("drone_race_4", "Only its own cameras."),
              ("f1_night_race", "The clock never stops.")]
    tri = "".join(f'<figure class="tri-p">{vid(clips[cid], "cover", "data-autoplay")}<figcaption>{line}</figcaption></figure>'
                  for cid, line in panels if cid in clips)
    return f"""
<section class="chap chap--2" data-inview>
  <div class="wrap">
    {chap_head('02', 'Real bodies.<br>Real time.')}
    <div class="tri">{tri}</div>
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


def chap3(site: Site, clips: dict, n: str = "03", title: str = "Prepare. Play.<br>Review. Improve.",
          line: str = "") -> str:
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
    return f"""
<section class="chap chap--3" data-inview>
  <div class="wrap">
    {chap_head(n, title, line)}
    <div class="mt3" data-match data-phase="prep">
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
    </div>
  </div>
</section>"""


G2_STEPS = [  # checkpoint (re-test after every match), score share vs fixed opponents, newly unlocked skills, what changed
    ("Start", 0.18, ["walk"], "Its first program walks."),
    ("Match 1", 0.27, ["getup"], "Gets up after falls."),
    ("Match 2", 0.34, [], "Steadier: falls half as often."),
    ("Match 3", 0.45, ["vision"], "Finds the ball with its own camera."),
    ("Match 4", 0.53, ["react"], "Reacts to the ball in time."),
    ("Match 5", 0.61, ["pass"], "Passes instead of dribbling into traffic."),
    ("Final", 0.71, ["team"], "Plays as a team."),
]
G2_TREE = {  # skill -> (label, x %, y %)
    "walk": ("Walking", 52, 86), "getup": ("Get-up", 32, 60), "vision": ("Vision", 72, 60),
    "pass": ("Passing", 32, 34), "react": ("Reaction", 72, 34), "team": ("Team play", 52, 9),
}
G2_ICONS = {  # 24x24 line icons, stroke = currentColor
    "walk": '<path d="M8.5 3.5c1.4 0 2.3 1.5 2.3 3.6s-1 4.2-2.3 4.2-2.3-2-2.3-4.2.9-3.6 2.3-3.6zM15.5 9c1.4 0 2.3 1.5 2.3 3.6s-1 4.2-2.3 4.2-2.3-2-2.3-4.2.9-3.6 2.3-3.6zM7 14.5h3M14 20h3"/>',
    "getup": '<path d="M12 21V9M6.5 14.5 12 9l5.5 5.5M6 4h12"/>',
    "vision": '<path d="M2 12s3.6-6.5 10-6.5S22 12 22 12s-3.6 6.5-10 6.5S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',
    "react": '<path d="M13 2 4.5 13.5H11L10 22l8.5-11.5H12z"/>',
    "pass": '<circle cx="5" cy="12" r="2.2"/><path d="M8.5 12H19M15 8l4 4-4 4"/>',
    "team": '<circle cx="6" cy="9" r="2.3"/><circle cx="12" cy="7" r="2.6"/><circle cx="18" cy="9" r="2.3"/><path d="M2.5 19c0-2.8 1.6-4.8 3.6-4.8M21.5 19c0-2.8-1.6-4.8-3.6-4.8M7 20c0-3.3 2.2-6 5-6s5 2.7 5 6"/>',
}
G2_LOCK = '<rect x="6" y="11" width="12" height="9" rx="2"/><path d="M9 11V8.5a3 3 0 0 1 6 0V11"/>'
G2_TIERS = [("Team", 9), ("Play", 34), ("Senses", 60), ("Body", 86)]
G2_EDGES = [("walk", "getup"), ("walk", "vision"), ("getup", "pass"), ("vision", "pass"), ("vision", "react"),
            ("pass", "team"), ("react", "team")]


def growth2() -> str:
    """Two growths driven by one checkpoint track: score vs fixed opponents, and the skill tree.
    Linked views: one control, both panels follow it. Illustration (humanoid soccer)."""
    n = len(G2_STEPS)
    W, H, pad = 400, 200, 12
    X = lambda i: pad + i * (W - 2 * pad) / (n - 1)  # noqa: E731
    Y = lambda v: H - pad - v * (H - 2 * pad)  # noqa: E731
    pts = [(X(i), Y(v)) for i, (_, v, _, _) in enumerate(G2_STEPS)]
    line = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    area = line + f" L{pts[-1][0]:.1f},{H - pad} L{pts[0][0]:.1f},{H - pad} Z"
    chart = f"""<svg viewBox="0 0 {W} {H}" preserveAspectRatio="none" aria-hidden="true">
        <line class="g2-level" x1="{pad}" x2="{W - pad}" y1="{Y(.5):.1f}" y2="{Y(.5):.1f}"/>
        <path class="g2-ghost" d="{line}"/>
        <g class="g2-reveal"><path class="g2-area" d="{area}"/><path class="g2-line" d="{line}"/></g></svg>"""
    # the season workflow: six matches (each a miniature of section 03's timeline), checkpoints saved where the
    # research saves them (M1 opening; end of M1, M3, M5, Final), each dropping into the re-test
    # the season: match tiles (each a miniature of section 03), with the saved checkpoints sitting in the gaps
    # between them where the research saves them (M1 opening; end of M1, M3, M5, Final)
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
    pins = ""
    stops = ""
    unlock = {sk: i for i, (_, _, sks, _) in enumerate(G2_STEPS) for sk in sks}
    def branch(a, b):  # right-angled branch from the lower skill up to the higher one
        (_, x1, y1), (_, x2, y2) = G2_TREE[a], G2_TREE[b]
        mid = (y1 + y2) / 2
        return (f'<path class="g2-edge" data-at="{max(unlock[a], unlock[b])}" '
                f'd="M{x1} {y1} V{mid:.1f} H{x2} V{y2}"/>')
    edges = "".join(branch(a, b) for a, b in G2_EDGES)
    svg_icon = lambda body, cls: f'<svg class="{cls}" viewBox="0 0 24 24" aria-hidden="true">{body}</svg>'  # noqa: E731
    nodes = "".join(
        f'<span class="g2-node" data-at="{unlock[k]}" style="left:{x}%;top:{y}%">'
        f'<b class="g2-badge">{svg_icon(G2_ICONS[k], "g2-ic")}{svg_icon(G2_LOCK, "g2-lock")}</b><em>{lab}</em></span>'
        for k, (lab, x, y) in G2_TREE.items())
    tiers = ""
    data = [{"x": round(X(i) / W * 100, 2), "y": round(Y(v) / H * 100, 2), "score": v, "skills": sum(len(s[2]) for s in G2_STEPS[:i + 1]),
             "event": ev} for i, (_, v, _, ev) in enumerate(G2_STEPS)]
    return f"""<figure class="g2" data-g2>
  <div class="g2-top"><div class="g2-ex">{icon("soccer_hsl", "pic")}<span><em>Example</em>Humanoid Soccer</span></div>
    <p class="g2-event" data-g2-event>{G2_STEPS[0][3]}</p></div>
  <div class="sw">
    <div class="sw-matches">{tiles}</div>
    <div class="sw-carry"><span class="sw-carry-line"><i></i></span></div>
  </div>
  <div class="g2-panels">
    <div class="g2-p">
      <span class="kicker">Growth curve</span>
      <div class="g2-big"><strong data-g2-score>0.18</strong><span>score share vs the same fixed opponents</span></div>
      <div class="g2-chart">{chart}<span class="g2-dot"></span><span class="g2-lv">0.5 = level</span></div>
    </div>
    <div class="g2-p">
      <span class="kicker">Capability growth</span>
      <div class="g2-big"><strong data-g2-skills>1</strong><span>of {len(G2_TREE)} skills on its sport card</span></div>
      <div class="g2-tree">{tiers}<svg viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">{edges}</svg>{nodes}</div>
    </div>
  </div>
  
  <script type="application/json" data-g2-data>{json.dumps(data)}</script>
</figure>"""


def growth_panels(draw: bool = False) -> str:
    return growth2()


def chap4(n: str = "04", title: str = "Agents keep learning<br>across the season.", line: str = "") -> str:
    return f"""
<section class="chap chap--4" data-inview>
  <div class="wrap">
    {chap_head(n, title, line)}
    {growth2()}
  </div>
</section>"""


def chap5(site: Site, clips: dict) -> str:
    caps = [
        ("Physical", "tabletennis_g1", "", "State estimation · Prediction · Execution · Real-time"),
        ("Competitive", "soccer_hsl_3v3", "cap4--crop", "Strategy · Opponent modeling · Teamwork"),
        ("Engineering", "stuntcar_replica", "cap4--build", "Development · Testing · Reliability"),
        ("Adaptive", "drone_race_4", "cap4--grow", "Feedback · Continual improvement"),
    ]
    grow = ('<svg class="cap4-grow" viewBox="0 0 100 60" preserveAspectRatio="none" aria-hidden="true">'
            '<path d="M4 52 L18 48 L30 50 L42 38 L56 34 L68 24 L82 20 L96 8" pathLength="1"/></svg>')
    cards = "".join(
        f'<figure class="cap4 {cls}">{vid(clips[cid], "cover", "data-autoplay") if cid in clips else ""}'
        f'<span class="cap4-grid"></span>{grow if cls == "cap4--grow" else ""}'
        f'<figcaption><strong>{name}</strong><span>{skills}</span></figcaption></figure>'
        for name, cid, cls, skills in caps)
    return f"""
<section class="chap chap--5" data-inview>
  <div class="wrap">
    {chap_head('05', 'Four core capabilities.')}
    <div class="caps4-layers"><span>What the system can do</span><span>How the agent builds it</span></div>
    <div class="caps4">{cards}</div>
  </div>
</section>"""


def parade(site: Site) -> str:
    cards = "".join(f"""<li class="plc" style="--c:{E(m['colour'])};--k:{k};--on:{ink_on(m['colour'])}">
  <div class="plc-card"><div class="plc-flag">{model_logo(site, m)}</div><div class="plc-name"><strong>{E(model_name(m))}</strong><span>{E(m['maker'])}</span></div></div>
  <div class="plc-pole"></div>
</li>""" for k, m in enumerate(site.models))
    return f"""
<section class="parade" data-inview>
  <div class="wrap">
    <header class="sec-head"><h2>Each model enters<br>like a nation.</h2><span class="tag tag--pending">Medals at release</span></header>
    <ol class="placards">{cards}</ol>
    {tournament(site)}
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
    btns = [("h2h", h2h_sports, "Head-to-head", "12 sports"), ("drone", ["drone"], "Drone racing", "Alone → groups → final"),
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


def wall(site: Site, clips: dict) -> str:
    tiles = []
    for s in site.sports:
        c = clips.get(s["clips"][0]["id"]) if s["clips"] else None
        media = (f'<video muted loop playsinline preload="none" data-hover-src="{E(c["web"])}" poster="{E(c["poster"])}"></video>'
                 if c else f'<img src="{E(site.murl(s["thumb"]["url"]))}" alt="" loading="lazy">')
        tiles.append(f'<a class="wt" href="{site.sport_url(s)}" data-hover><span class="wt-media">{media}</span>'
                     f'{icon(s["id"], "pic wt-pic")}<span class="wt-name">{E(s["name"])}</span></a>')
    return f"""
<section class="wall">
  <div class="wrap">
    <header class="sec-head"><h2>{len(site.sports)} sports.<br>Real rules.</h2>
      <a class="link" href="{site.url('sports/')}">All sports <span class="arr">→</span></a></header>
    <div class="wall-grid">{''.join(tiles)}</div>
  </div>
</section>"""


# ---------------------------------------------------------------- page


def home(site: Site):
    clips = clip_index(site)
    body = ('<div class="stagebg" data-hero2>' + hero(site, clips) + question(site, clips) + numbers(site, clips) + '</div>' + chap1(site, clips) + chap2(site, clips)
            + chap3(site, clips) + chap4() + chap5(site, clips) + parade(site) + wall(site, clips)
            + '<nav class="crail" aria-label="Chapters" data-crail></nav>'
            + f'<script src="{site.asset("js/home.js")}" defer></script>')
    return "", page(site, path="", title=None, body=body, dark_top=True)
