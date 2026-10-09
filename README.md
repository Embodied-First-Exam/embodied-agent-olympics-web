# Embodied Agent Olympics

The project page of **Embodied Agent Olympics**. Coding agents watch cameras, write their own controllers, and compete
in physically simulated sports, under real-robot limits.

**Status: preview.** The page is a work in progress. Its videos are placeholders until the unified re-renders arrive,
and every result on it is preliminary.

## Run it locally

The page is static: plain HTML, CSS and ES modules. There is no build step in this repository.

```bash
python3 -m http.server 8780 --bind 127.0.0.1
```

Then open http://localhost:8780.

Preview knobs:
- `?theme=dark` forces night. The moon/sun button switches the theme, and the browser remembers the choice.

## What is on the page

1. **Home**: what the benchmark tests, how a match works, the 18 sports and their formats, one framework for many
   robots, and the Season 1 (exhibition) medal table.
2. **Sports**: one page per sport, with its rules, formats, physics, body and what the agent sees.
3. **Results, Robots, Docs**: in preparation.

## Credits

Text, data, figures and videos: the Embodied Agent Olympics team. Fonts: Bricolage Grotesque, Inter and JetBrains Mono
from Google Fonts (SIL Open Font License).
