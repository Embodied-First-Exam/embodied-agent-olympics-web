/* Home-only interactions. Runs after site.js (which provides window.EO). */
document.addEventListener("DOMContentLoaded", () => {
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const EO = window.EO || { reduced: false, wantHD: () => false, scrollHandlers: {} };
  const reduced = EO.reduced;
  const pad = (n) => String(Math.floor(n)).padStart(2, "0");
  const fmt = (t) => `${pad(t / 60)}:${pad(t % 60)}.${pad((t % 1) * 100)}`;

  /* fit the wordmark to the column width */
  const fit = () => $$("[data-fit]").forEach((el) => {
    const inner = $(".fit-inner", el);
    el.style.fontSize = "100px";
    const w = inner.getBoundingClientRect().width;
    if (w) el.style.fontSize = Math.min(100 * el.clientWidth / w, 280) + "px";
  });
  fit();
  (document.fonts ? document.fonts.ready : Promise.resolve()).then(fit);
  addEventListener("resize", fit);

  /* hero: channel switcher + telemetry clock */
  const hero = $("[data-hero2]");
  if (hero) {
    const clips = JSON.parse($("[data-hero2-clips]").textContent);
    const vids = $$(".h2o-v", hero), chs = $$(".ch", hero);
    const tName = $("[data-t-name]"), tClock = $("[data-t-clock]"), watch = $("[data-hero-watch]", hero);
    const SLOT = 7;
    let i = 0, cur = 0, timer = null, pinned = false, hoverT = null;
    const src = (c) => (EO.wantHD() && c.hd ? c.hd : c.web);
    const mark = () => chs.forEach((b, k) => { b.classList.remove("is-on"); void b.offsetWidth; b.classList.toggle("is-on", k === i); b.setAttribute("aria-pressed", k === i); });
    const plan = () => { clearTimeout(timer); if (!pinned && !reduced) timer = setTimeout(() => show(i + 1), SLOT * 1000); };
    const show = (n) => {
      i = (n + clips.length) % clips.length;
      const c = clips[i], next = vids[1 - cur];
      next.poster = c.poster; next.src = src(c); next.loop = true;
      const swap = () => { vids[cur].classList.remove("is-on"); next.classList.add("is-on"); vids[cur].pause(); cur = 1 - cur; };
      next.play().then(swap, swap);
      tName.textContent = c.name.toUpperCase();
      watch.href = watch.href.replace(/#.*$/, "") + "#clip=" + c.id;
      mark(); plan();
    };
    chs.forEach((b, k) => {
      b.style.setProperty("--dur", SLOT + "s");
      b.addEventListener("mouseenter", () => { clearTimeout(hoverT); hoverT = setTimeout(() => k !== i && show(k), 260); });
      b.addEventListener("mouseleave", () => clearTimeout(hoverT));
      // a click pins the channel: auto-advance stops, the visitor is in control
      b.addEventListener("click", () => { clearTimeout(hoverT); pinned = true; hero.classList.add("is-pinned"); if (k !== i) show(k); else plan(); });
    });
    vids[0].loop = true;
    if (!reduced) { vids[0].src = src(clips[0]); vids[0].play().catch(() => {}); }
    mark(); plan();
    const tick = () => { tClock.textContent = "T+" + fmt(vids[cur].currentTime || 0); requestAnimationFrame(tick); };
    requestAnimationFrame(tick);
    document.addEventListener("visibilitychange", () => {
      if (document.hidden) { clearTimeout(timer); vids[cur].pause(); }
      else if (!reduced) { vids[cur].play().catch(() => {}); plan(); }
    });
  }

  /* chapter rail: built from the chapter headings; highlights the chapter in view */
  const rail = $("[data-crail]"), chaps = $$(".chap");
  if (rail && chaps.length) {
    chaps.forEach((c, k) => {
      c.id = c.id || "ch" + (k + 1);
      const h = $(".ch-head h2", c), a = document.createElement("a");
      a.href = "#" + c.id;
      a.innerHTML = `<i></i>${String(k + 1).padStart(2, "0")}<span></span>`;
      a.querySelector("span").textContent = h ? h.textContent.replace(/\s+/g, " ").trim() : "";
      rail.appendChild(a);
    });
    const links = $$("a", rail);
    const sync = () => {
      const mid = innerHeight * 0.45;
      let cur = -1;
      chaps.forEach((c, k) => { const r = c.getBoundingClientRect(); if (r.top < mid && r.bottom > mid) cur = k; });
      const first = chaps[0].getBoundingClientRect(), last = chaps[chaps.length - 1].getBoundingClientRect();
      rail.classList.toggle("on", first.top < mid && last.bottom > mid);
      links.forEach((l, k) => l.classList.toggle("on", k === cur));
    };
    addEventListener("scroll", sync, { passive: true }); addEventListener("resize", sync); sync();
  }

  /* the question: one phrase per screen */
  const qcs = $$(".qc"), qticks = $$(".qx-ticks i");
  if (qcs.length && EO.scrollHandlers) {
    EO.scrollHandlers.chunks = (s, p) => {
      const k = Math.min(qcs.length - 1, Math.floor(p * qcs.length));
      qcs.forEach((c, j) => { c.classList.toggle("on", reduced || j === k); c.classList.toggle("past", !reduced && j < k); });
      qticks.forEach((t, j) => t.classList.toggle("on", j <= k));
    };
    EO.onScroll && EO.onScroll();
  }

  /* terminal: lines type in when the section comes into view, then "deployed" */
  $$("[data-type]").forEach((pre) => {
    const host = pre.closest("[data-inview]") || pre;
    const run = () => {
      const lines = $$(".cl", pre), status = (pre.closest("figure") || pre.parentElement).querySelector(".term-status");
      if (reduced) { lines.forEach((l) => l.classList.add("on")); status.classList.add("on"); return; }
      // a real typewriter: one character at a time, with a little human jitter and a pause at line ends
      lines.forEach((l) => $(".cl-t", l).style.setProperty("--chars", "0ch"));
      let k = 0;
      const line = () => {
        if (k > 0) lines[k - 1].classList.remove("typing");
        if (k === lines.length) { lines[k - 1].classList.add("last"); setTimeout(() => status.classList.add("on"), 300); return; }
        const l = lines[k++], txt = $(".cl-t", l), total = txt.textContent.length;
        l.classList.add("on", "typing");
        let n = 0;
        // leading indentation appears at once, like an editor's auto-indent
        while (n < total && txt.textContent[n] === " ") n++;
        const key = () => {
          txt.style.setProperty("--chars", n + "ch");
          if (n >= total) { txt.style.removeProperty("--chars"); setTimeout(line, 220); return; }
          n++;
          const ch = txt.textContent[n - 1];
          setTimeout(key, (ch === "(" || ch === "," ? 70 : 26) + Math.random() * 34);
        };
        key();
      };
      line();
    };
    host.classList.contains("is-in") ? run() : host.addEventListener("eo:inview", run, { once: true });
  });

});
