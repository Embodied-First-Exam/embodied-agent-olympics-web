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
  const show = (k) => {
    vid.src = src[k]; vid.play().catch(() => {});
    tFull.classList.toggle("is-on", k === "full"); tHl.classList.toggle("is-on", k === "hl");
  };
  const open = (el) => {
    opener = el;
    src = { full: el.dataset.play, hl: el.dataset.hl };
    ttl.textContent = el.dataset.title || el.dataset.kind || "Replay";
    tFull.textContent = el.dataset.kind || "Full match replay";
    tHl.hidden = !src.hl;
    if (dlg.showModal) dlg.showModal(); else dlg.setAttribute("open", "");
    show("full");
  };
  const close = () => { vid.pause(); vid.removeAttribute("src"); vid.load(); if (dlg.open) dlg.close(); if (opener) opener.focus(); };
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
  dlg.addEventListener("cancel", (e) => { e.preventDefault(); close(); });
})();
