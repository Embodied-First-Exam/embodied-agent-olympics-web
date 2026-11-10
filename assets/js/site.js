/* Embodied Olympics — shared enhancements. Every page reads fine without this file or with reduced motion. */
(() => {
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const conn = navigator.connection || {};
  // HD masters (2560x1440) only where they show: large screens, no data saver.
  const wantHD = () => !conn.saveData && innerWidth * (devicePixelRatio || 1) >= 1800;
  window.EO = { reduced, wantHD };

  /* top bar: solid once the page scrolls off a dark hero */
  const top = $("[data-top]");
  if (top && top.classList.contains("top--over")) {
    const onScroll = () => top.classList.toggle("is-solid", scrollY > 40);
    addEventListener("scroll", onScroll, { passive: true });
    onScroll();
  }

  /* day / night: remembered per visitor; a short cross-fade while the colours change */
  const tbtn = $("[data-theme-toggle]");
  if (tbtn) {
    const root = document.documentElement, meta = $('meta[name="theme-color"]');
    const sync = () => {
      const light = root.dataset.theme === "light";
      tbtn.setAttribute("aria-label", light ? "Switch to night mode" : "Switch to day mode");
      if (meta) meta.content = light ? "#F4F3EF" : "#08090B";
    };
    tbtn.addEventListener("click", () => {
      const next = root.dataset.theme === "light" ? "dark" : "light";
      if (!reduced) { root.classList.add("theme-anim"); setTimeout(() => root.classList.remove("theme-anim"), 500); }
      if (next === "dark") delete root.dataset.theme; else root.dataset.theme = next;
      try { localStorage.setItem("eo-theme", next); } catch (e) {}
      sync();
    });
    sync();
  }

  /* mobile menu */
  const menu = $("[data-menu]");
  if (menu) menu.addEventListener("click", () => {
    const open = document.body.classList.toggle("menu-open");
    menu.setAttribute("aria-expanded", open);
  });

  /* lazy videos: load near the viewport, play only while visible */
  const io = new IntersectionObserver((es) => es.forEach((e) => {
    const v = e.target;
    if (e.isIntersecting) {
      if (!v.src) v.src = wantHD() && v.dataset.hd ? v.dataset.hd : v.dataset.web;
      if (v.hasAttribute("data-autoplay") && !reduced) v.play().catch(() => {});
    } else if (!v.paused) v.pause();
  }), { rootMargin: "200px 0px" });
  $$("video[data-lazy]").forEach((v) => io.observe(v));

  /* hover / focus plays a tile's clip */
  $$("[data-hover]").forEach((t) => {
    const v = $("video[data-hover-src]", t); if (!v) return;
    const on = () => { if (!v.src) v.src = v.dataset.hoverSrc; if (!reduced) v.play().then(() => t.classList.add("is-playing"), () => {}); };
    const off = () => { v.pause(); t.classList.remove("is-playing"); };
    t.addEventListener("mouseenter", on); t.addEventListener("focus", on);
    t.addEventListener("mouseleave", off); t.addEventListener("blur", off);
  });

  /* in-view entrances (once), with count-up numbers */
  const count = (el) => {
    const n = +el.dataset.count; if (reduced || !n) return;
    const t0 = performance.now(), d = 1100;
    const f = (t) => { const p = Math.min(1, (t - t0) / d); el.textContent = Math.round(n * (1 - Math.pow(1 - p, 3))); if (p < 1) requestAnimationFrame(f); };
    el.textContent = "0"; requestAnimationFrame(f);
  };
  const seen = new IntersectionObserver((es) => es.forEach((e) => {
    if (!e.isIntersecting) return;
    e.target.classList.add("is-in"); seen.unobserve(e.target);
    $$("[data-count]", e.target).forEach(count);
    e.target.dispatchEvent(new CustomEvent("eo:inview"));
  }), { threshold: 0.25 });
  $$("[data-inview]").forEach((el) => seen.observe(el));

  /* scroll-driven sections: --p is 0..1 across each [data-scrolly] */
  const scrollies = $$("[data-scrolly]");
  const handlers = {
  };
  window.EO.scrollHandlers = handlers;
  const onScroll = () => scrollies.forEach((s) => {
    const r = s.getBoundingClientRect(), span = r.height - innerHeight;
    const p = Math.max(0, Math.min(1, span > 0 ? -r.top / span : 0));
    s.style.setProperty("--p", p.toFixed(4));
    const h = handlers[s.dataset.scrolly]; if (h) h(s, p);
  });
  window.EO.onScroll = onScroll;
  addEventListener("scroll", onScroll, { passive: true });
  addEventListener("resize", onScroll);
  onScroll();

  /* one match: a playhead runs across the timeline while in view; clicking a segment jumps there and pauses */
  $$("[data-match]").forEach((root) => {
    const steps = JSON.parse($("[data-match-steps]", root).textContent);
    const total = steps.reduce((a, s) => a + s.w, 0), starts = [];
    steps.reduce((acc, s) => { starts.push(acc / total); return acc + s.w; }, 0);
    const segs = $$(".tl3-seg", root), head = $(".tl3-head", root), btn = $("[data-match-btn]", root);
    const vid = $("video", root), T = 20000;
    const el = (k) => $(`[data-now-${k}]`, root);
    let p = 0, last = null, raf = null, playing = !reduced, visible = false, cur = -1;
    const stepAt = (x) => starts.reduce((k, s, i) => (x >= s ? i : k), 0);
    const swap = (node, text) => { if (node.textContent === text) return; node.classList.add("out"); setTimeout(() => { node.textContent = text; node.classList.remove("out"); }, 180); };
    const show = (k) => {
      if (k === cur) return; cur = k; const s = steps[k];
      root.dataset.phase = s.key;
      segs.forEach((g, i) => { g.classList.toggle("past", i < k); g.classList.toggle("on", i === k); });
      swap(el("title"), s.title); swap(el("agent"), s.agent); swap(el("field"), s.field);
      el("tag").textContent = s.tag;
      if (s.score) { $("[data-s0]", root).textContent = s.score[0]; $("[data-s1]", root).textContent = s.score[1]; }
      $$("[data-v]", root).forEach((v) => v.classList.toggle("on", +v.dataset.v <= s.v));
      if (vid) vid.playbackRate = s.key === "rev" ? 0.35 : 1;
    };
    // per-phase details: the practice log counts up; the live clock runs during play
    let resets = 1, tests = 1, mclock = 0, lastTick = 0;
    const R = $("[data-resets]", root), Tt = $("[data-tests]", root), MC = $("[data-mclock]", root);
    const detail = (t) => {
      if (t - lastTick < 140) return; lastTick = t;
      const ph = root.dataset.phase;
      if (ph === "prep") { tests = tests % 20 + 1; if (tests === 1) resets++; R.textContent = "#" + resets; Tt.textContent = tests + "/20"; }
      if (ph === "play" || ph === "play2") { mclock += 7; MC.textContent = `${String(Math.floor(mclock / 60) % 100).padStart(2, "0")}:${String(mclock % 60).padStart(2, "0")}`; }
      if (ph === "prep" && mclock) mclock = 0;
    };
    const place = () => { head.style.left = (p * 100).toFixed(3) + "%"; show(stepAt(p)); };
    const frame = (t) => { if (last !== null) p = (p + (t - last) / T) % 1; last = t; place(); detail(t); raf = requestAnimationFrame(frame); };
    const start = () => { if (raf || !playing || !visible) return; last = null; raf = requestAnimationFrame(frame); };
    const stop = () => { cancelAnimationFrame(raf); raf = null; };
    const setBtn = () => { btn.classList.toggle("is-paused", !playing); btn.setAttribute("aria-label", playing ? "Pause" : "Play"); };
    segs.forEach((g, i) => g.addEventListener("click", () => { playing = false; stop(); p = starts[i] + 0.001; place(); setBtn(); }));
    btn.addEventListener("click", () => { playing = !playing; playing ? start() : stop(); setBtn(); });
    new IntersectionObserver(([e]) => { visible = e.isIntersecting; visible ? start() : stop(); }, { threshold: 0.3 }).observe(root);
    place(); setBtn();
  });

  /* charts that draw themselves: start only when the chart itself is mostly on screen */
  const drawIO = new IntersectionObserver((es) => es.forEach((e) => {
    if (e.isIntersecting) { e.target.classList.add("is-drawn"); drawIO.unobserve(e.target); }
  }), { threshold: 0, rootMargin: "0px 0px -30% 0px" });
  $$("[data-draw]").forEach((el) => drawIO.observe(el));

  /* two growths, one control: auto-advances while in view; a click on a checkpoint takes over */
  $$("[data-g2]").forEach((root) => {
    const data = JSON.parse($("[data-g2-data]", root).textContent);
    const stops = $$("[data-g2-stop]", root), nodes = $$(".g2-node, .g2-cap", root), edges = $$(".g2-edge", root);
    const ev = $("[data-g2-event]", root), sc = $("[data-g2-score]", root), sk = $("[data-g2-skills]", root);
    let k = -1, timer = null, pinned = false, shownScore = data[0].score;
    const tween = (to) => {
      const from = shownScore, t0 = performance.now();
      const f = (t) => { const q = Math.min(1, (t - t0) / 600); shownScore = from + (to - from) * (1 - Math.pow(1 - q, 3)); sc.textContent = shownScore.toFixed(2); if (q < 1) requestAnimationFrame(f); };
      if (!sc) return;
      reduced ? (sc.textContent = to.toFixed(2), shownScore = to) : requestAnimationFrame(f);
    };
    const set = (n) => {
      if (n === k) return; k = n; const d = data[k];
      root.dataset.k = k;
      root.style.setProperty("--g2x", d.x + "%"); root.style.setProperty("--g2y", d.y + "%");
      if (d.cy != null) root.style.setProperty("--g2cy", d.cy + "%");
      root.style.setProperty("--g2p", (k / (data.length - 1) * 100) + "%");
      stops.forEach((s, i) => { s.classList.toggle("past", i < k); s.classList.toggle("on", i === k); });
      $$(".sw-m", root).forEach((m) => { m.classList.toggle("done", +m.dataset.done < k); m.classList.toggle("cur", +m.dataset.done === k); });
      const pin = stops[k], row = pin && pin.parentElement;
      if (pin && row) root.style.setProperty("--g2p", ((pin.offsetLeft + pin.offsetWidth / 2) / row.offsetWidth * 100).toFixed(2) + "%");
      nodes.forEach((nd) => { const on = +nd.dataset.at <= k; if (on && !nd.classList.contains("on")) { nd.classList.add("new"); setTimeout(() => nd.classList.remove("new"), 700); } nd.classList.toggle("on", on); });
      edges.forEach((e) => e.classList.toggle("on", +e.dataset.at <= k));
      ev.classList.add("out"); setTimeout(() => { ev.textContent = d.event; ev.classList.remove("out"); }, 180);
      if (sk) sk.textContent = d.skills; tween(d.score);
    };
    const run = () => {
      clearTimeout(timer); if (pinned || reduced) return;
      timer = setTimeout(() => { if (k < data.length - 1) { set(k + 1); run(); } else { timer = setTimeout(() => { set(0); run(); }, 3200); } }, k < 0 ? 300 : 1800);
    };
    stops.forEach((s) => s.addEventListener("click", () => { pinned = true; clearTimeout(timer); set(+s.dataset.g2Stop); }));
    $$("[data-g2-goto]", root).forEach((m) => m.addEventListener("click", () => { pinned = true; clearTimeout(timer); set(+m.dataset.g2Goto); }));
    set(reduced ? data.length - 1 : 0);
    new IntersectionObserver(([e]) => { if (e.isIntersecting) run(); else clearTimeout(timer); }, { threshold: 0, rootMargin: "0px 0px -30% 0px" }).observe(root);
  });

  /* how medals are won: round robin -> knockout -> medals, looping while on screen */
  $$("[data-tm]").forEach((root) => {
    const cells = $$(".tm-c", root).sort((a, b) => a.style.getPropertyValue("--k") - b.style.getPropertyValue("--k"));
    const byK = {}; cells.forEach((c) => (byK[c.style.getPropertyValue("--k")] ??= []).push(c));
    const ks = Object.keys(byK).sort((a, b) => a - b);
    // the Episodic fold's round-robin widget has no knockout: keep only the parts this widget has
    const ko = [1, 2, 3, 4].map((n) => $(`[data-ko="${n}"]`, root)).filter(Boolean), medals = [".s", ".g", ".b"].map((s) => $(`.tm-medal.${s.slice(1)}`, root)).filter(Boolean);
    let timers = [], on = false;
    const at = (ms, f) => timers.push(setTimeout(f, ms));
    const reset = () => { cells.forEach((c) => c.classList.remove("on", "cur")); ko.forEach((e) => e.classList.remove("on")); medals.forEach((m) => m.classList.remove("on")); };
    // the other formats: elements tagged data-g="rr" | "ko" | "md" light up in order, stage by stage
    const panel = (f) => $(`[data-fmt-panel="${f}"]`, root);
    const playGen = (f) => {
      timers.forEach(clearTimeout); timers = [];
      const p = panel(f), group = (g) => $$(`[data-g="${g}"]`, p);
      $$("[data-g]", p).forEach((e) => e.classList.remove("on"));
      const gap = { rr: f === "racing" ? 950 : f === "solo" ? 420 : 170, ko: f === "racing" ? 160 : f === "solo" ? 300 : 220, md: 260 };
      let t = 300;
      ["rr", "ko", "md"].forEach((g) => {
        at(t, () => { root.dataset.step = g; }); t += 200;
        group(g).forEach((e) => { at(t, () => e.classList.add("on")); t += gap[g]; });
        t += 350;
      });
      at(t + 2600, () => on && root.dataset.fmt === f && playGen(f));
    };
    const run = () => (root.dataset.fmt === "h2h" ? play() : playGen(root.dataset.fmt));
    // format tabs: the buttons below switch the panel and start that format's own animation
    const tabs = $$("[data-fmt]", root).filter((b) => b.tagName === "BUTTON");
    tabs.forEach((b) => b.addEventListener("click", () => {
      const f = b.dataset.fmt; root.dataset.fmt = f;
      tabs.forEach((x) => { x.classList.toggle("is-on", x === b); x.setAttribute("aria-pressed", x === b); });
      $$("[data-fmt-panel]", root).forEach((p) => { p.hidden = p.dataset.fmtPanel !== f; });
      timers.forEach(clearTimeout); timers = [];
      if (reduced || !on) final(); else run();
    }));
    const final = () => { root.dataset.step = "md"; cells.forEach((c) => c.classList.add("on")); ko.forEach((e) => e.classList.add("on")); medals.forEach((m) => m.classList.add("on"));
      $$("[data-g]", root).forEach((e) => e.classList.add("on")); };
    const play = () => {
      timers.forEach(clearTimeout); timers = []; reset(); root.dataset.step = "rr";
      let t = 300;
      ks.forEach((k) => { at(t, () => { cells.forEach((c) => c.classList.remove("cur")); byK[k].forEach((c) => c.classList.add("on", "cur")); }); t += 170; });
      at(t, () => { cells.forEach((c) => c.classList.remove("cur")); root.dataset.step = "ko"; }); t += 400;
      ko.forEach((e) => { at(t, () => e.classList.add("on")); t += 450; });
      at(t, () => { root.dataset.step = "md"; }); t += 250;
      medals.forEach((m) => { at(t, () => m.classList.add("on")); t += 220; });
      at(t + 2600, () => on && root.dataset.fmt === "h2h" && play());
    };
    if (reduced) { final(); return; }
    new IntersectionObserver(([e]) => {
      if (e.isIntersecting && !on) { on = true; run(); }
      else if (!e.isIntersecting && on) { on = false; timers.forEach(clearTimeout); final(); }
    }, { threshold: 0, rootMargin: "0px 0px -30% 0px" }).observe(root);
  });

  /* sports filter */
  const grid = $("[data-grid]");
  if (grid) $$("[data-filter]").forEach((b) => b.addEventListener("click", () => {
    $$("[data-filter]").forEach((x) => x.classList.toggle("is-on", x === b));
    const f = b.dataset.filter;
    $$(".sc", grid).forEach((c) => c.classList.toggle("is-hidden", f !== "all" && c.dataset.cat !== f));
  }));

  /* results tabs (remembered in the URL hash); #fmt-<format> opens that panel of the format diagram */
  const tabs = $$("[data-tab]");
  const fromHash = () => {
    const h = location.hash.slice(1);
    const fb = h.startsWith("fmt-") && $(`.tm-o[data-fmt="${h.slice(4)}"]`);
    if (fb) { fb.click(); $("#formats") && $("#formats").scrollIntoView(); return; }
    if (tabs.some((t) => t.dataset.tab === h)) { pick(h); const s = $("#tables"); if (s) s.scrollIntoView(); }
  };
  const pick = (id) => {
    if (!tabs.some((t) => t.dataset.tab === id)) id = tabs[0].dataset.tab;
    tabs.forEach((t) => { t.classList.toggle("is-on", t.dataset.tab === id); t.setAttribute("aria-selected", t.dataset.tab === id); });
    $$("[data-panel]").forEach((p) => p.classList.toggle("is-on", p.dataset.panel === id));
  };
  if (tabs.length) {
    tabs.forEach((t) => t.addEventListener("click", () => { pick(t.dataset.tab); history.replaceState(null, "", "#" + t.dataset.tab); }));
    pick(location.hash.slice(1));
  }
  if (location.hash) fromHash();
  addEventListener("hashchange", fromHash);

  /* how medals are won (home): a chip opens its one-paragraph detail; without JS it links to the full diagram */
  const mchips = $$("[data-mchip]");
  mchips.forEach((c) => c.addEventListener("click", (e) => {
    e.preventDefault();
    const k = c.dataset.mchip, open = !c.classList.contains("is-on");
    mchips.forEach((x) => { x.classList.toggle("is-on", open && x === c); x.setAttribute("aria-expanded", open && x === c); });
    $$("[data-mchip-d]").forEach((d) => { d.hidden = !(open && d.dataset.mchipD === k); });
  }));

  /* watch: one player, a grid of clips, #clip=<id> deep links */
  const wv = $("[data-wvideo]");
  if (wv) {
    const clips = JSON.parse($("[data-wclips]").textContent);
    const load = (id, play) => {
      const c = clips[id]; if (!c) return;
      wv.poster = c.poster; wv.src = c.src;
      $("[data-wtitle]").textContent = c.sport;
      const mk = $("[data-wmaster]"); mk.hidden = !c.master; if (c.master) mk.href = c.master;
      $$(".wtile").forEach((t) => t.classList.toggle("is-on", t.dataset.clip === id));
      if (play) wv.play().catch(() => {});
    };
    $$(".wtile").forEach((t) => t.addEventListener("click", () => {
      load(t.dataset.clip, true);
      history.replaceState(null, "", "#clip=" + t.dataset.clip);
      wv.scrollIntoView({ behavior: reduced ? "auto" : "smooth", block: "center" });
    }));
    const m = location.hash.match(/clip=([\w-]+)/);
    if (m) load(m[1], false);
  }
})();

/* medal table: Medals | Win rate, and the win-rate scope (Both | Championship only | Open Arena only) */
(() => {
  document.querySelectorAll("[data-mw]").forEach((mw) => {
    mw.querySelectorAll("[data-mw-v]").forEach((b) => b.addEventListener("click", () => {
      mw.querySelectorAll("[data-mw-v]").forEach((x) => { x.classList.toggle("is-on", x === b); x.setAttribute("aria-pressed", x === b); });
      mw.querySelectorAll("[data-mw-p]").forEach((p) => { p.hidden = p.dataset.mwP !== b.dataset.mwV; });
    }));
    mw.querySelectorAll("[data-wr]").forEach((b) => b.addEventListener("click", () => {
      mw.querySelectorAll("[data-wr]").forEach((x) => { x.classList.toggle("is-on", x === b); x.setAttribute("aria-pressed", x === b); });
      mw.querySelectorAll("[data-wr-p]").forEach((p) => { p.hidden = p.dataset.wrP !== b.dataset.wr; });
    }));
  });
})();

/* a link to something inside a closed fold (e.g. #formats) opens the fold first */
(() => {
  const open = () => {
    const id = location.hash.slice(1); if (!id) return;
    const el = document.getElementById(id), d = el && el.closest("details");
    if (d && !d.open) { d.open = true; el.scrollIntoView(); }
  };
  open(); addEventListener("hashchange", open);
})();

/* Episodic fold: the ranking emerges from the results. Two tabs (Duel · Team duel, Solo) like the old widget. Served in
   its final state (no-JS / reduced motion); with motion a panel starts from zero: rows in entrant order, results fill in
   (round robin: each match lights its two cells and adds its points; solo: each first match lights and sets its score),
   then the rows slide into rank order with ranks and medal colours, then the podium. Loops while on screen. */
(() => {
  document.querySelectorAll("[data-tm-ep]").forEach((root) => {
    const D = JSON.parse(root.querySelector("[data-ep-data]").textContent);
    const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
    const tabs = [...root.querySelectorAll("[data-ep-tab]")], panels = [...root.querySelectorAll("[data-ep-panel]")];
    root.classList.add("is-js");
    let cur = "h2h", timers = [], on = false;
    const at = (ms, f) => timers.push(setTimeout(f, ms));
    const P = () => root.querySelector(`[data-ep-panel="${cur}"]`);
    const fmt = (v, d) => (d ? v.toFixed(d) : String(v));
    const setRow = (rows, k, v, d) => { const r = rows[k]; const mx = D[cur].max; r.querySelector("i").style.setProperty("--w", (v ? Math.max(4, Math.round(100 * v / mx)) : 0) + "%"); r.querySelector("b").textContent = fmt(v, d); };
    const parts = () => { const p = P(); return { p, table: p.querySelector(".tm-pts--ep"), rows: [...p.querySelectorAll("[data-ep-row]")], marks: [...p.querySelectorAll("[data-ep-c]")], medals: [...p.querySelectorAll(".tm-medal")] }; };
    const start = () => {
      timers.forEach(clearTimeout); timers = [];
      const { table, rows, marks, medals } = parts(), d = D[cur];
      root.dataset.step = "rr"; table.classList.remove("is-sorted");
      marks.forEach((c) => c.classList.remove("on", "ep-hit"));
      rows.forEach((r, k) => setRow(rows, k, 0, d.dec)); medals.forEach((m) => m.classList.remove("on"));
    };
    const end = () => {
      timers.forEach(clearTimeout); timers = [];
      panels.forEach((p) => {
        const d = D[p.dataset.epPanel], rows = [...p.querySelectorAll("[data-ep-row]")], keep = cur; cur = p.dataset.epPanel;
        p.querySelector(".tm-pts--ep").classList.add("is-sorted");
        p.querySelectorAll("[data-ep-c]").forEach((c) => { c.classList.add("on"); c.classList.remove("ep-hit"); });
        rows.forEach((r, k) => setRow(rows, k, d.final[k], d.dec)); p.querySelectorAll(".tm-medal").forEach((m) => m.classList.add("on"));
        cur = keep;
      });
      root.dataset.step = "md";
    };
    const play = () => {
      start();
      const { p, table, rows, medals } = parts(), d = D[cur], hit = (els) => { p.querySelectorAll(".ep-hit").forEach((c) => c.classList.remove("ep-hit")); els.forEach((c) => c && c.classList.add("on", "ep-hit")); };
      let t = 500;
      if (d.kind === "rr") {
        const pts = d.final.map(() => 0);
        d.games.forEach(([a, b, pa, pb]) => { at(t, () => { hit([p.querySelector(`[data-ep-c="${a}-${b}"]`), p.querySelector(`[data-ep-c="${b}-${a}"]`)]); pts[a] += pa; pts[b] += pb; setRow(rows, a, pts[a], d.dec); setRow(rows, b, pts[b], d.dec); }); t += 320; });
      } else {
        d.seq.forEach(([k, v]) => { at(t, () => { hit([p.querySelector(`[data-ep-c="${k}"]`)]); setRow(rows, k, v, d.dec); }); t += 650; });
      }
      at(t, () => p.querySelectorAll(".ep-hit").forEach((c) => c.classList.remove("ep-hit")));
      at(t + 400, () => { root.dataset.step = "ko"; table.classList.add("is-sorted"); });
      t += 1500;
      at(t, () => { root.dataset.step = "md"; });
      medals.slice().sort((x, y) => +x.textContent - +y.textContent).forEach((m, k) => at(t + 250 + k * 260, () => m.classList.add("on")));
      at(t + 5200, () => on && play());
    };
    const pick = (key) => {
      cur = key;
      tabs.forEach((b) => { const o = b.dataset.epTab === key; b.classList.toggle("is-on", o); b.setAttribute("aria-pressed", o); });
      panels.forEach((p) => p.classList.toggle("is-on", p.dataset.epPanel === key));
      if (reduced) { end(); return; }
      on ? play() : start();
    };
    tabs.forEach((b) => b.addEventListener("click", () => pick(b.dataset.epTab)));
    panels.forEach((p) => p.classList.toggle("is-on", p.dataset.epPanel === cur));
    if (reduced) return;
    ["solo", "h2h"].forEach((k) => { cur = k; start(); });  // the first frame a reader sees is the start, never the result
    cur = "h2h"; root.dataset.step = "rr";
    new IntersectionObserver(([e]) => {
      if (e.isIntersecting && !on) { on = true; play(); }
      else if (!e.isIntersecting && on) { on = false; end(); }
    }, { threshold: 0, rootMargin: "0px 0px -30% 0px" }).observe(root);
  });
})();
