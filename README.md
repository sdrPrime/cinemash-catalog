# CINEMASH Catalog — free hosting via GitHub

One static `catalog.json` (~100-300 KB) that the CINEMASH game fetches directly.
No server, no cost: GitHub Pages hosts it, GitHub Actions rebuilds it quarterly.

## Criteria (baked into build_catalog.py)
- Bollywood: original language `hi`, origin country `IN` · Hollywood: `en` / `US`
- Rolling 50-year window at quarter granularity: current quarter minus 200 quarters → today.
  Each quarterly run drops the oldest quarter automatically — no manual dumping.
- IMDb title type `movie` only (excludes series, episodes, shorts, TV movies, miniseries,
  specials, videos, games) · runtime ≥ 60 min · IMDb rating ≥ 6.0 · votes ≥ 1,000
- Includes theatrical, streaming, animated, independent, direct-to-video standalone films
- Per movie: title, year, genres, tier (E/M/H from vote count), lead actor, lead actress,
  director, famous dialogue (from your curated `dialogues.json`), IMDb id

## Data sources
- **TMDB** (`/discover/movie`) — candidate list per industry + credits (director, leads).
  Free API key: https://www.themoviedb.org/settings/api
- **IMDb datasets** (title.basics + title.ratings, auto-downloaded ~190 MB gz) —
  authoritative type/runtime/rating/votes filter. Free, no key.

## One-time setup (~10 minutes, all free)
1. Create a **public** GitHub repository, e.g. `cinemash-catalog`.
2. Push everything in this folder to it (including the hidden `.github/` folder).
3. Repo → Settings → Secrets and variables → Actions → **New repository secret**:
   name `TMDB_API_KEY`, value = your TMDB key.
4. Repo → Settings → Pages → Source: **Deploy from a branch** → `main` / root → Save.
5. Repo → Actions → "Refresh catalog" → **Run workflow** (first build, ~15-25 min).

Your catalog URL (test it in a browser once the run finishes):
```
https://YOURNAME.github.io/cinemash-catalog/catalog.json
```

## Quarterly refresh — automatic
`.github/workflows/refresh.yml` runs at 03:00 UTC on the 1st of Jan/Apr/Jul/Oct:
rebuilds with the slid window and commits the new `catalog.json`. Pages redeploys itself.
You can also trigger it manually anytime from the Actions tab.

## Point the game at it
In the game, once:
```js
localStorage.setItem('bh_catalog_url', 'https://YOURNAME.github.io/cinemash-catalog/catalog.json')
```
The game falls back to its built-in list when offline.

## Famous dialogues
`dialogues.json` maps IMDb id → dialogue line; the builder merges it in. Curate over time —
there is no reliable free bulk source for famous dialogues. Edits to it take effect on the
next workflow run (manual or quarterly).
