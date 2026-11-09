/* Sport page (src/sport.py): record tabs, model selector, chart legend, the on-page nav. Every block reads without JS. */
(() => {
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];

  /* Championship / Open Arena tabs */
  $$("[data-sptabs]").forEach((g) => {
    const box = g.parentElement;
    $$("[data-sptab]", g).forEach((b) => b.addEventListener("click", () => {
      $$("[data-sptab]", g).forEach((x) => { x.classList.toggle("is-on", x === b); x.setAttribute("aria-selected", x === b); });
      $$("[data-sppanel]", box).forEach((p) => p.classList.toggle("is-on", p.dataset.sppanel === b.dataset.sptab));
    }));
  });

  /* model selector (How they built it) */
  $$("[data-msel]").forEach((b) => b.addEventListener("click", () => {
    const k = b.dataset.msel;
    $$("[data-msel]").forEach((x) => { x.classList.toggle("is-on", x === b); x.setAttribute("aria-selected", x === b); });
    $$("[data-mpanel]").forEach((p) => p.classList.toggle("is-on", p.dataset.mpanel === k));
  }));

  /* chart legend: a click hides / shows that model's lines in both charts; a double click shows it alone */
  const charts = $("[data-charts]");
  const apply = () => {
    const off = new Set($$("[data-lg]").filter((b) => b.getAttribute("aria-pressed") === "false").map((b) => b.dataset.lg));
    $$(".cs", charts || document).forEach((g) => g.classList.toggle("is-off", off.has(g.dataset.series)));
  };
  $$("[data-lg]").forEach((b) => {
    b.addEventListener("click", () => { b.setAttribute("aria-pressed", b.getAttribute("aria-pressed") === "false"); apply(); });
    b.addEventListener("dblclick", (e) => {
      e.preventDefault();
      $$("[data-lg]").forEach((x) => x.setAttribute("aria-pressed", x === b));
      apply();
    });
    b.addEventListener("mouseenter", () => $$(".cs", charts || document).forEach((g) => g.classList.toggle("is-dim", g.dataset.series !== b.dataset.lg)));
    b.addEventListener("mouseleave", () => $$(".cs", charts || document).forEach((g) => g.classList.remove("is-dim")));
  });

  /* on-page nav: highlight the block in view */
  const nav = $("[data-spnav]");
  if (nav && "IntersectionObserver" in window) {
    const links = $$("[data-spnav-a]", nav);
    const io = new IntersectionObserver((es) => es.forEach((e) => {
      if (e.isIntersecting) links.forEach((a) => a.classList.toggle("is-on", a.dataset.spnavA === e.target.id));
    }), { rootMargin: "-45% 0px -50% 0px" });
    links.forEach((a) => { const t = document.getElementById(a.dataset.spnavA); if (t) io.observe(t); });
  }
})();

/* in-page player: any [data-play] (cross-table cell, knockout card, replay chip) opens its match in a dialog;
   Esc, the close button or a click outside closes it; a "Highlights" tab appears when the match has a reel */
(() => {
  const dlg = document.querySelector("[data-player]");
  if (!dlg) return;
  const vid = dlg.querySelector("[data-pl-video]"), ttl = dlg.querySelector("[data-pl-title]");
  const tFull = dlg.querySelector('[data-pl-src="full"]'), tHl = dlg.querySelector('[data-pl-src="hl"]');
  let src = {}, opener = null;
  /* live scoreboard overlay: a match timeline (data/timelines/<FIXTURE>.json, eo-timeline/1) synced to currentTime */
  const sbo = dlg.querySelector("[data-sbo]"), toastEl = dlg.querySelector("[data-sbo-toast]");
  const mdl = JSON.parse((document.querySelector("[data-pl-models]") || {}).textContent || "{}");
  let tl = null, lastToast = -1, toastTimer = 0, mode = "full";
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const names = () => Object.fromEntries((tl.sides || []).map((s) => [s.seat, (mdl[s.model] || {}).short || s.model]));
  const fill = (txt) => { const n = names(); return String(txt).replace(/\{([A-Z])\}/g, (_, k) => n[k] || k); };
  const latest = (t, f) => { let v; for (const e of tl.events) { if (e.t > t) break; if (e[f] !== undefined) v = e; } return v; };
  const mmss = (s) => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, "0")}`;
  let curT = 0;
  const kitOf = (seat) => {  // baseball: the colour follows the role (batting / fielding) of the current half-inning
    const k = (tl.kit || {})[seat];
    if (k && tl.kit_from != null && curT < tl.kit_from) return { name: "open table", hex: null, what: "no ball group yet" };
    if (k && k.batting && k.fielding) {
      const tu = latest(curT, "turn");
      if (tu) return { ...(tu.turn === seat ? k.batting : k.fielding), what: tu.turn === seat ? "batting" : "fielding" };
    }
    return k;
  };
  // robots now wear their model's colour (Chi 11-09): the swatch is the model colour; a word only for non-colour cues
  // (court end, billiards ball group, baseball role)
  const sw = (k) => (k && k.hex ? `<i class="sbo-kit" title="${esc(k.what || "")}"></i>` : "");
  const kitWord = (k) => (k && !k.hex ? esc(k.name) : "");
  const side = (s, cls, mark) => {
    const m = mdl[s.model] || {}, k = kitOf(s.seat);
    const kitTxt = k ? `${sw(k)}${kitWord(k)}` : "";
    const sub = [kitTxt, s.agents ? `${s.agents} agents` : ""].filter(Boolean).join(" · ");
    return `<span class="sbo-side ${cls}" style="--c:${m.colour || "#888"}">${cls === "sbo-b" ? "" : mark}<i class="sbo-flag"></i>${m.logo || ""}`
      + `<span class="sbo-nm">${esc(m.short || s.model)}${sub ? `<small>${sub}</small>` : ""}</span>${cls === "sbo-b" ? mark : ""}</span>`;
  };
  const legend = () => {  // more than two entrants (drone, racing heats): a compact kit legend
    if (!tl.kit || (tl.sides || []).length === 2) return "";
    const items = tl.sides.filter((s) => kitOf(s.seat)).map((s) => `<span style="--c:${(mdl[s.model] || {}).colour || "#888"}">${sw(kitOf(s.seat))}${esc((mdl[s.model] || {}).short || s.model)}${kitWord(kitOf(s.seat)) ? ` <em>${kitWord(kitOf(s.seat))}</em>` : ""}</span>`);
    return items.length ? `<div class="sbo-leg">${items.join("")}</div>` : "";
  };
  const render = () => {
    if (!tl || mode !== "full") return;
    const t = vid.currentTime || 0, two = (tl.sides || []).length === 2;
    curT = t;
    const sc = latest(t, "score"), pe = latest(t, "period"), inf = latest(t, "info");
    const who = latest(t, "serve") || latest(t, "possession") || latest(t, "turn");
    const whoSeat = who ? (who.serve || who.possession || who.turn) : null;
    const whoWord = who ? (who.serve ? "serve" : who.possession ? "ball" : "turn") : "";
    let clock = "";
    if (pe && pe.clock_start) clock = mmss(Math.max(0, t - pe.t));
    const mark = (seat) => (whoSeat === seat ? `<b class="sbo-who" title="${whoWord}">●</b>` : `<b class="sbo-who is-off">●</b>`);
    let html = "";
    if (two) {
      const [a, b] = tl.sides;
      const s = (sc && sc.score) || {};
      html += `<div class="sbo-bar">${side(a, "sbo-a", mark(a.seat))}<span class="sbo-sc"><b>${s[a.seat] ?? 0}</b><i>:</i><b>${s[b.seat] ?? 0}</b></span>${side(b, "sbo-b", mark(b.seat))}</div>`;
    }
    const kind = two && tl.score_kind && !["points", "goals", "runs"].includes(tl.score_kind) ? tl.score_kind : "";
    const sub = [tl.label, kind, pe ? pe.period : "", clock, inf ? fill(inf.info) : "", whoSeat && !two ? `${names()[whoSeat] || whoSeat} · ${whoWord}` : ""].filter(Boolean);
    if (!two) html += legend();
    html += `<div class="sbo-sub">${sub.map((x, i) => (i === 0 ? `<span class="sbo-lab">${esc(x)}${sub.length > 1 ? " · " : ""}</span>` : esc(x) + (i < sub.length - 1 ? " · " : ""))).join("")}${whoSeat && two ? ` <em>● ${whoWord}</em>` : ""}</div>`;
    if (sbo.innerHTML !== html) sbo.innerHTML = html;
    // toast: the latest toast event within the last 2.5 s
    let ti = -1;
    tl.events.forEach((e, i) => { if (e.toast && e.t <= t && t - e.t < 2.5) ti = i; });
    if (ti !== lastToast) {
      lastToast = ti;
      if (ti >= 0) { toastEl.textContent = fill(tl.events[ti].toast); toastEl.hidden = false; } else toastEl.hidden = true;
    }
  };
  let raf = 0;
  const loop = () => { render(); raf = vid.paused ? 0 : requestAnimationFrame(loop); };
  vid.addEventListener("play", () => { if (!raf) raf = requestAnimationFrame(loop); });
  vid.addEventListener("seeked", render);
  vid.addEventListener("timeupdate", render);
  const show = (k) => {
    mode = k;
    vid.src = src[k]; vid.play().catch(() => {});
    tFull.classList.toggle("is-on", k === "full"); tHl.classList.toggle("is-on", k === "hl");
    sbo.hidden = !(tl && k === "full"); toastEl.hidden = true; lastToast = -1;
    if (tl && k === "full") render();
  };
  const open = (el) => {
    opener = el;
    src = { full: el.dataset.play, hl: el.dataset.hl };
    ttl.textContent = el.dataset.title || el.dataset.kind || "Replay";
    tFull.textContent = el.dataset.kind || "Full match replay";
    tHl.hidden = !src.hl;
    tl = null; sbo.hidden = true; sbo.innerHTML = ""; toastEl.hidden = true;
    if (dlg.showModal) dlg.showModal(); else dlg.setAttribute("open", "");
    show("full");
    if (el.dataset.tl) fetch(el.dataset.tl).then((r) => (r.ok ? r.json() : null)).then((j) => {
      if (!j || src.full !== el.dataset.play) return;
      tl = j; tl.events.sort((x, y) => x.t - y.t); sbo.hidden = mode !== "full"; render();
    }).catch(() => {});
  };
  /* full screen: the stage (video + scoreboard) goes full screen together; native video full screen is off.
     Without the element Fullscreen API (iPhone Safari) the stage fills the viewport with CSS instead. */
  const stage = dlg.querySelector("[data-pl-stage]"), fsBtn = dlg.querySelector("[data-pl-fs]"), rot = dlg.querySelector("[data-pl-rot]");
  const fsEl = () => document.fullscreenElement || document.webkitFullscreenElement;
  const canFs = !!(stage.requestFullscreen || stage.webkitRequestFullscreen);
  const isFill = () => stage.classList.contains("is-fill");
  const portrait = () => matchMedia("(orientation: portrait)").matches;
  const setFill = (on) => {
    stage.classList.toggle("is-fill", on); document.documentElement.classList.toggle("pl-fill-on", on);
    rot.hidden = !(on && portrait());
    fsBtn.classList.toggle("is-on", on);
    fit();
  };
  const toggleFs = () => {
    if (fsEl()) { (document.exitFullscreen || document.webkitExitFullscreen).call(document); return; }
    if (isFill()) { setFill(false); return; }
    if (canFs) {
      const req = stage.requestFullscreen || stage.webkitRequestFullscreen;
      const p = req.call(stage);
      if (p && p.catch) p.catch(() => setFill(true));
    } else setFill(true);
  };
  /* the picture's own rect inside the stage (object-fit: contain leaves black bands in full screen / odd window
     shapes): --px --py --pw --ph on the stage, so the scoreboard, toast and full-screen button sit on the picture */
  const fit = () => {
    const s = stage.getBoundingClientRect(), v = vid.getBoundingClientRect();
    if (!s.width || !v.width) return;
    let w = v.width, h = v.height;
    if (vid.videoWidth && vid.videoHeight) {
      const k = Math.min(v.width / vid.videoWidth, v.height / vid.videoHeight);
      w = vid.videoWidth * k; h = vid.videoHeight * k;
    }
    const x = v.left - s.left - stage.clientLeft + (v.width - w) / 2, y = v.top - s.top - stage.clientTop + (v.height - h) / 2;
    const st = stage.style;
    st.setProperty("--px", `${x.toFixed(1)}px`); st.setProperty("--py", `${y.toFixed(1)}px`);
    st.setProperty("--pw", `${w.toFixed(1)}px`); st.setProperty("--ph", `${h.toFixed(1)}px`);
  };
  vid.addEventListener("loadedmetadata", fit);
  if (window.ResizeObserver) new ResizeObserver(fit).observe(vid);
  addEventListener("resize", fit);
  const onFs = () => { const on = fsEl() === stage; stage.classList.toggle("is-fs", on); fsBtn.classList.toggle("is-on", on); fit(); render(); };
  document.addEventListener("fullscreenchange", onFs);
  document.addEventListener("webkitfullscreenchange", onFs);
  addEventListener("orientationchange", () => { if (isFill()) rot.hidden = !portrait(); });
  addEventListener("resize", () => { if (isFill()) rot.hidden = !portrait(); });
  fsBtn.addEventListener("click", (e) => { e.stopPropagation(); toggleFs(); });
  vid.addEventListener("dblclick", (e) => { e.preventDefault(); toggleFs(); });
  dlg.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && fsEl()) { (document.exitFullscreen || document.webkitExitFullscreen).call(document); return; }
    if ((e.key === "f" || e.key === "F") && !e.metaKey && !e.ctrlKey && !e.altKey && !/input|textarea/i.test(e.target.tagName)) { e.preventDefault(); toggleFs(); }
  });
  const close = () => { if (fsEl()) (document.exitFullscreen || document.webkitExitFullscreen).call(document); setFill(false); vid.pause(); vid.removeAttribute("src"); vid.load(); if (dlg.open) dlg.close(); if (opener) opener.focus(); };
  document.addEventListener("click", (e) => {
    const el = e.target.closest("[data-play]");
    if (!el || dlg.contains(el)) return;
    e.preventDefault(); e.stopPropagation(); open(el);
  });
  document.addEventListener("keydown", (e) => {
    const el = e.target.closest && e.target.closest("article[data-play]");
    if (el && (e.key === "Enter" || e.key === " ")) { e.preventDefault(); open(el); }
  });
  tFull.addEventListener("click", () => show("full"));
  tHl.addEventListener("click", () => show("hl"));
  dlg.querySelector("[data-pl-close]").addEventListener("click", close);
  dlg.addEventListener("click", (e) => { if (e.target === dlg) close(); });
  dlg.addEventListener("cancel", (e) => { e.preventDefault(); if (isFill()) setFill(false); else if (!fsEl()) close(); });
})();

/* Checkpoint Evaluation: opponent switch (All (mean) | L1 | L2 | L3 | practice player) */
(() => {
  document.querySelectorAll(".tv-row").forEach((row) => {
    const fig = row.closest(".cfig");
    row.querySelectorAll("[data-tv]").forEach((b) => b.addEventListener("click", () => {
      row.querySelectorAll("[data-tv]").forEach((x) => { x.classList.toggle("is-on", x === b); x.setAttribute("aria-pressed", x === b); });
      fig.querySelectorAll("[data-tvp]").forEach((p) => { p.hidden = p.dataset.tvp !== b.dataset.tv; });
    }));
  });
})();
