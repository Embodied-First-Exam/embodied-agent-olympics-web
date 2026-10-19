# Embodied Olympics

The project page of **Embodied Olympics**: physical sports for coding agents. Published at
<https://olympics.embodied-first-exam.ai/> by GitHub Pages from `main` (`CNAME`).

**Status (2026-10-19): First Exam release.** Two Embodied Olympics suites are part of the
[Embodied First Exam](https://www.embodied-first-exam.ai/): RoboOlympics-Fun and RoboOlympics-Match. The home page
shows them; the full benchmark is not released yet. Pages of the earlier preview (sports, results, robots, docs, film)
keep their URLs and show a short "returns with the full release" page. Earlier versions are in the git history.

## Run it locally

Static HTML and CSS, no build step:

```bash
python3 -m http.server 8780 --bind 127.0.0.1
```

Then open http://localhost:8780. `?theme=dark` forces the dark theme.

## Files

- `index.html`: the release page. `404.html`: not found.
- `sports/`, `results/`, `robots/`, `docs/`, `film/`: placeholders for the full release.
- `assets/css/site.css`, `responsive.css`: the site's look; `release.css`: the release page.
- `assets/media/release/`: web clips (H.264, muted) and posters of RoboOlympics-Match and RoboOlympics-Fun tasks.

## Credits

Text, figures and videos: the Embodied Olympics team. Fonts: Bricolage Grotesque, Inter and JetBrains Mono from Google
Fonts (SIL Open Font License).
