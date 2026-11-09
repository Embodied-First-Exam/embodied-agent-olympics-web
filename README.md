# Embodied Olympics — website

The public site of **Embodied Olympics**, published at <https://olympics.embodied-first-exam.ai/>.

The repository holds the **source**: page templates, styles, data and media. GitHub Actions builds the static site and
publishes it to GitHub Pages; the built HTML is never committed.

## Run it locally

Python 3.10 or newer, standard library only:

```bash
python3 build.py --serve 8000     # build and serve http://localhost:8000/ (rebuilds on every save)
python3 build.py                  # build only, into ./dist
```

## Where things live

| Path | What |
|---|---|
| `site.json` | Site settings: name, tagline, research question, links (Docs / Code / Paper), formats, model logos |
| `data/sports.json`, `data/media.json`, `data/models.json` | The 18 sports, their clips and stills, the six models |
| `data/results.json` | Results (all `null` until release); medal table, podiums and boards fill in from it |
| `src/home.py` | The home page and its story sections |
| `src/pages.py` | Sports, the 18 sport pages, The Match, Competitions, Results, Watch |
| `src/sport.py`, `data/sport_pages/<sport>.json` | The four-block sport page (overview, competition records, capabilities, agents) for every sport with a data file; the data contract is in the module docstring |
| `src/layout.py` | Page frame: head, top bar, footer, URL helpers |
| `assets/css/site.css`, `story.css` | Design tokens (night and day themes) and components |
| `assets/js/site.js`, `home.js` | Interactions; every page also reads fine without JavaScript |
| `assets/media/` | Web clips (720p), posters, stills; `release/full/` holds the 1440p versions used for HD |
| `assets/icons/`, `assets/models/` | Sport pictograms; model logos (see `assets/models/SOURCE.txt`) |
| `tools/fetch_media.py` | Pulls any media file named in `data/` that is not in `assets/media/` yet (campus network or VPN) |

## Making a change

1. Edit the source, run `python3 build.py --serve 8000`, check the page.
2. New footage or stills: add them to `data/*.json`, then `python3 tools/fetch_media.py`.
3. Open a pull request. The **Build and deploy** workflow builds every push; a merge into `main` publishes the site.

## Credits

Text, figures and videos: the Embodied Olympics team. Fonts: Inter Tight and IBM Plex Mono (SIL Open Font License).
Model logos: `@lobehub/icons` (MIT); each logo is a trademark of its owner.
