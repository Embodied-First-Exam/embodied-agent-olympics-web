/* Home-only interactions. Runs after site.js (which provides window.EO). */
document.addEventListener("DOMContentLoaded", () => {
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const EO = window.EO || { reduced: false, wantHD: () => false, scrollHandlers: {} };
  const reduced = EO.reduced;
  const pad = (n) => String(Math.floor(n)).padStart(2, "0");
  const fmt = (t) => `${pad(t / 60)}:${pad(t % 60)}.${pad((t % 1) * 100)}`;

  /* wordmark: CSS sizes it to the column (story.css). This only fine-tunes, after the fonts are ready, when the text is
     off by more than 2 % (e.g. a scrollbar or an older browser without container units); never before first paint. */
  const fit = () => $$("[data-fit]").forEach((el) => {
    const inner = $(".fit-inner", el);
    el.style.fontSize = "";
    const cur = parseFloat(getComputedStyle(el).fontSize), w = inner.getBoundingClientRect().width;
    if (!w || !cur) return;
    const want = Math.min(cur * el.clientWidth / w, 280);
    if (Math.abs(want - cur) / cur > 0.02) el.style.fontSize = want + "px";
  });
  (document.fonts ? document.fonts.ready : Promise.resolve()).then(fit);
  let rz = 0;
  addEventListener("resize", () => { cancelAnimationFrame(rz); rz = requestAnimationFrame(fit); });

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


/* how medals are won (home): a format tab shows its flow */
document.addEventListener("DOMContentLoaded", () => {
  const root = document.querySelector("[data-mf]"); if (!root) return;
  const tabs = [...root.querySelectorAll("[data-mf-tab]")], pans = [...root.querySelectorAll("[data-mf-pan]")];
  tabs.forEach((b) => b.addEventListener("click", () => {
    tabs.forEach((x) => { x.classList.toggle("is-on", x === b); x.setAttribute("aria-pressed", x === b); });
    pans.forEach((p) => { p.hidden = p.dataset.mfPan !== b.dataset.mfTab; });
  }));
});

/* section nav: appears once the reader passes the intro; shows the four chapters, the current one highlighted */
document.addEventListener("DOMContentLoaded", () => {
  const bar = document.querySelector("[data-snav-bar]");
  const secs = [...document.querySelectorAll("[data-snav]")];
  if (!bar || !secs.length) return;
  secs.forEach((s) => {
    const a = document.createElement("a");
    a.href = "#" + s.id; a.setAttribute("aria-label", s.dataset.snav);
    a.innerHTML = '<i class="snav-t" aria-hidden="true"></i><span></span>';
    a.querySelector("span").textContent = s.dataset.snav;
    bar.appendChild(a);
  });
  const links = [...bar.querySelectorAll("a")];
  const sync = () => {
    const mid = innerHeight * 0.4;
    bar.classList.toggle("on", secs[0].getBoundingClientRect().top < mid);
    let cur = 0;
    secs.forEach((s, k) => { if (s.getBoundingClientRect().top < mid) cur = k; });
    links.forEach((l, k) => l.classList.toggle("is-on", k === cur));
  };
  addEventListener("scroll", sync, { passive: true }); addEventListener("resize", sync); sync();
});

/* in-text links to One season: remember where the reader was, offer a quiet "back" there */
document.addEventListener("DOMContentLoaded", () => {
  const back = document.querySelector("[data-jl-back]");
  let from = null;
  document.querySelectorAll("[data-jl]").forEach((a) => a.addEventListener("click", () => { from = scrollY; if (back) back.hidden = false; }));
  if (back) back.addEventListener("click", (e) => { e.preventDefault(); if (from != null) window.scrollTo({ top: from, behavior: "smooth" }); back.hidden = true; from = null; });
});

/* sports row: real match loops. A card's clip loads and plays only while the card is on screen (posters otherwise, and
   always with reduced motion or Save-Data); the arrows and the format chips scroll the row. */
document.addEventListener("DOMContentLoaded", () => {
  const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const saver = !!(navigator.connection && navigator.connection.saveData);
  const still = reduced || saver;
  const vio = new IntersectionObserver((es) => es.forEach((e) => {
    const v = e.target;
    if (e.isIntersecting && !still) {
      if (!v.src) v.src = v.dataset.loop;
      v.play().then(() => v.closest("[data-sr],.pl-fig")?.classList.add("has-play"), () => {});
    } else if (!v.paused) v.pause();
  }), { threshold: 0.35 });
  document.querySelectorAll("video[data-loop]").forEach((v) => { if (still) v.removeAttribute("autoplay"); vio.observe(v); });

  document.querySelectorAll("[data-sr]").forEach((root) => {
    const track = root.querySelector("[data-sr-track]");
    const cards = [...track.querySelectorAll(".spr-card")];
    const step = () => (cards[1] ? cards[1].offsetLeft - cards[0].offsetLeft : track.clientWidth * 0.8);
    const sync = () => {
      const max = track.scrollWidth - track.clientWidth - 2;
      root.querySelector('[data-sr-step="-1"]').disabled = track.scrollLeft < 2;
      root.querySelector('[data-sr-step="1"]').disabled = track.scrollLeft > max;
      // the chip of the format whose first card is nearest the left edge
      let cur = null;
      root.querySelectorAll("[data-sr-fmt]").forEach((c) => { if (c.offsetLeft - track.offsetLeft <= track.scrollLeft + step() / 2) cur = c.dataset.srFmt; });
      root.querySelectorAll("[data-sr-go]").forEach((b) => b.classList.toggle("is-on", b.dataset.srGo === (cur || "duel")));
    };
    root.querySelectorAll("[data-sr-step]").forEach((b) => b.addEventListener("click", () => {
      const n = Math.max(1, Math.floor(track.clientWidth / step()) - 1);
      track.scrollBy({ left: +b.dataset.srStep * n * step(), behavior: reduced ? "auto" : "smooth" });
    }));
    root.querySelectorAll("[data-sr-go]").forEach((b) => b.addEventListener("click", () => {
      const c = root.querySelector(`[data-sr-fmt="${b.dataset.srGo}"]`);
      if (c) track.scrollTo({ left: c.offsetLeft - track.offsetLeft - parseFloat(getComputedStyle(track).paddingLeft || 0), behavior: reduced ? "auto" : "smooth" });
    }));
    track.addEventListener("scroll", () => requestAnimationFrame(sync), { passive: true });
    addEventListener("resize", sync); sync();
  });

  /* architecture: the arena clip sits under the figure's transparent arena box (kept in place on resize) */
  document.querySelectorAll("[data-arena-vid]").forEach((v) => {
    const host = v.parentElement, box = host.querySelector(".pl-arena > rect"), fig = host.closest(".pl-fig");
    if (!box) return;
    const place = () => {
      const a = box.getBoundingClientRect(), h = host.getBoundingClientRect();
      Object.assign(v.style, { left: a.left - h.left + host.scrollLeft + "px", top: a.top - h.top + "px", width: a.width + "px", height: a.height + "px" });
    };
    place(); addEventListener("resize", place); new ResizeObserver(place).observe(host);
    v.addEventListener("playing", () => fig.classList.add("has-play"), { once: true });
  });

  /* leaderboards: Episodic Learning | Continuous Learning; #episodic, #continuous (or the old #championship) open a tab */
  document.querySelectorAll("[data-lb]").forEach((root) => {
    const tabs = [...root.querySelectorAll("[data-lb-tab]")];
    const pick = (k) => {
      tabs.forEach((t) => { const on = t.dataset.lbTab === k; t.classList.toggle("is-on", on); t.setAttribute("aria-selected", on); t.tabIndex = on ? 0 : -1; });
      root.querySelectorAll("[data-lb-panel]").forEach((p) => { p.hidden = p.dataset.lbPanel !== k; });
    };
    tabs.forEach((t, i) => {
      t.addEventListener("click", () => pick(t.dataset.lbTab));
      t.addEventListener("keydown", (e) => {
        const d = e.key === "ArrowRight" ? 1 : e.key === "ArrowLeft" ? -1 : 0; if (!d) return;
        const n = tabs[(i + d + tabs.length) % tabs.length]; pick(n.dataset.lbTab); n.focus();
      });
    });
    const fromHash = () => {
      const h = location.hash.slice(1);
      if (h === "episodic") pick("episodic");
      if (h === "continuous" || h === "championship") pick("continuous");
    };
    fromHash(); addEventListener("hashchange", fromHash);
  });

  /* head to head: redraw the matrix for a mode and a sport; a tooltip on hover or focus */
  document.querySelectorAll("[data-hh-root]").forEach((root) => {
    const D = JSON.parse(root.querySelector("[data-hh-data]").textContent);
    const tip = root.querySelector("[data-hh-tip]"), sel = root.querySelector("[data-hh-sport]");
    let mode = 0, sport = -1, C = [];
    const fmt = (w, d, l) => (d ? `${w}–${d}–${l}` : `${w}–${l}`);
    const count = () => {
      const n = D.names.length;
      C = Array.from({ length: n }, () => Array.from({ length: n }, () => [0, 0, 0, 0]));
      D.m.forEach(([si, md, a, b, w, lv]) => {
        if ((mode !== -1 && md !== mode) || (sport !== -1 && si !== sport)) return;
        [[a, b], [b, a]].forEach(([x, y]) => { const r = C[x][y]; r[w === x ? 0 : w === -1 ? 1 : 2]++; r[3] += lv; });
      });
    };
    const draw = () => {
      count();
      root.querySelectorAll("td[data-hh]").forEach((td) => {
        const [i, j] = td.dataset.hh.split(",").map(Number), [w, d, l] = C[i][j], n = w + d + l;
        td.classList.toggle("hh-c--0", !n);
        td.tabIndex = n ? 0 : -1;
        if (!n) { td.style.removeProperty("--v"); td.innerHTML = '<span class="hh-p">·</span>'; return; }
        const p = 100 * w / n;
        td.style.setProperty("--v", ((p - 50) / 50).toFixed(3));
        td.innerHTML = `<span class="hh-p">${Math.round(p)}%</span><span class="hh-wl">${fmt(w, d, l)} (${n})</span>`;
      });
      root.querySelectorAll("td[data-hh-t]").forEach((td) => {
        const i = +td.dataset.hhT; let w = 0, d = 0, l = 0;
        C[i].forEach((r, j) => { if (j !== i) { w += r[0]; d += r[1]; l += r[2]; } });
        const n = w + d + l;
        td.innerHTML = n ? `<span class="hh-p">${Math.round(100 * w / n)}%</span><span class="hh-wl">${fmt(w, d, l)} (${n})</span>` : "·";
      });
    };
    root.querySelectorAll("[data-hh-mode]").forEach((b) => b.addEventListener("click", () => {
      mode = +b.dataset.hhMode;
      root.querySelectorAll("[data-hh-mode]").forEach((x) => { x.classList.toggle("is-on", x === b); x.setAttribute("aria-pressed", x === b); });
      draw(); hide();
    }));
    sel.addEventListener("change", () => { sport = +sel.value; draw(); hide(); });
    const hide = () => { tip.hidden = true; };
    const show = (td) => {
      const [i, j] = td.dataset.hh.split(",").map(Number), [w, d, l, lv] = C[i][j], n = w + d + l;
      if (!n) { hide(); return; }
      const scope = `${D.modes[String(mode)]} · ${sport === -1 ? "all " + D.sports.length + " sports" : D.sports[sport]}`;
      tip.innerHTML = `<strong></strong><span class="hh-tip-v"></span><span class="hh-tip-s"></span>`;
      tip.querySelector("strong").textContent = `${D.names[i]} v ${D.names[j]}`;
      tip.querySelector(".hh-tip-v").textContent = `${Math.round(100 * w / n)}% · ${w} won${d ? `, ${d} drawn` : ""}, ${l} lost of ${n}` + (lv ? ` · ${lv} decided at a level score` : "");
      tip.querySelector(".hh-tip-s").textContent = scope;
      tip.hidden = false;
      const r = td.getBoundingClientRect(), h = root.getBoundingClientRect();
      const x = Math.min(Math.max(8, r.left - h.left + r.width / 2 - tip.offsetWidth / 2), h.width - tip.offsetWidth - 8);
      tip.style.left = x + "px"; tip.style.top = r.top - h.top - tip.offsetHeight - 8 + "px";
    };
    root.addEventListener("mouseover", (e) => { const td = e.target.closest("td[data-hh]"); td ? show(td) : hide(); });
    root.addEventListener("mouseleave", hide);
    root.addEventListener("focusin", (e) => { const td = e.target.closest("td[data-hh]"); td ? show(td) : hide(); });
    root.addEventListener("focusout", hide);
    root.querySelector(".hh-scroll").addEventListener("scroll", hide, { passive: true });
    draw();
  });
});
