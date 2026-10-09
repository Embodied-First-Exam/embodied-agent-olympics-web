# Embodied Agent Olympics

The project page of **Embodied Agent Olympics**. Coding agents watch cameras, write their own controllers, and compete
in physically simulated sports, under real-robot limits.

**Status: preview.** The page is a work in progress. Some videos are still placeholders, and every result on it is
preliminary.

## Run it locally

The page is static: plain HTML, CSS and ES modules, with three.js vendored under `assets/vendor/`. There is no build
step in this repository.

```bash
python3 -m http.server 8780 --bind 127.0.0.1
```

Then open http://localhost:8780.

Preview knobs:
- `?theme=dark` forces night. The moon/sun button switches the theme, and the browser remembers the choice.
- `?hero=0.6` freezes the opening at that scroll fraction; `?overview=1` gives a short, static opening.

## What is on the page

1. **The opening** (scroll-driven, real-time WebGL): a recorded table-tennis rally between two Franka Panda arms,
   replayed from the match record. Every pose comes from the replay; nothing is simulated in the browser.
2. **Home**: what the benchmark tests, how a match works, the 18 sports in a control room, one framework for many
   robots, and the Season 1 (exhibition) medal table with its match replays.
3. **Sports**: one page per sport, with its rules, formats, physics, body and what the agent sees.
4. **Results**: Season 1 (exhibition) and the pilot findings, all preliminary, every number with its n.
5. **Robots** and **Docs**: the robot library, the renderers, the match loop, the formats and the framework.

## Credits and licences

Text, data, figures and videos: the Embodied Agent Olympics team.
- three.js: MIT License, `assets/vendor/three/LICENSE`.
- Franka Emika Panda visual meshes: MuJoCo Menagerie, Apache License 2.0, `assets/opening/LICENSE.franka_emika_panda`.
- Fonts: Bricolage Grotesque, Inter and JetBrains Mono from Google Fonts (SIL Open Font License).
