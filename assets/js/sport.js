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

/* cross-table cells link to their match row inside the folded list: open it, scroll, highlight */
(() => {
  const go = (id) => {
    const row = document.getElementById(id);
    if (!row) return;
    const d = row.closest("details"); if (d) d.open = true;
    const panel = row.closest("[data-sppanel]");
    if (panel && !panel.classList.contains("is-on")) { const b = document.querySelector(`[data-sptab="${panel.dataset.sppanel}"]`); if (b) b.click(); }
    document.querySelectorAll(".mx.is-hl").forEach((x) => x.classList.remove("is-hl"));
    row.classList.add("is-hl");
    row.scrollIntoView({ block: "center", behavior: "smooth" });
  };
  document.addEventListener("click", (e) => {
    const a = e.target.closest("a.xt-c[href^='#']");
    if (!a) return;
    e.preventDefault(); history.replaceState(null, "", a.getAttribute("href")); go(a.getAttribute("href").slice(1));
  });
  if (/^#(cm|am)-/.test(location.hash)) go(location.hash.slice(1));
})();
