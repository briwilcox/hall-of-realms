# Third-party sources

| Source | Used for | License | Notes |
|---|---|---|---|
| [historical-basemaps](https://github.com/aourednik/historical-basemaps) by André Ourednik | 48 border snapshots, 3000 BCE to 2010 | GPL-3.0 | Pinned to commit `4b5039e`. Simplified and reclassified for this project; the derived data in `build/` and `dist/` is distributed under GPL-3.0. |
| [Natural Earth](https://www.naturalearthdata.com/) | Present-day borders (1:50m) and land outline (1:110m) | Public domain | Version 4.1.0, released May 2018. De facto lines as Natural Earth drew them in 2018. |
| [world-atlas](https://github.com/topojson/world-atlas) by Mike Bostock | TopoJSON packaging of Natural Earth | ISC | Version 2.0.2. Copyright 2013-2019 Michael Bostock. |
| [Wikipedia](https://en.wikipedia.org/) and [Wikidata](https://www.wikidata.org/) | November 2026 check of dates, language families and successions | Facts only; no text copied. Wikidata is CC0. | Each change and the article it rests on is listed in [docs/fact-check-2026-11.md](docs/fact-check-2026-11.md). |
| [d3](https://d3js.org/) | Map projections and drawing | ISC | Version 7.9.0, loaded from cdnjs at runtime, not bundled. |
| [Playfair Display](https://fonts.google.com/specimen/Playfair+Display), [DM Sans](https://fonts.google.com/specimen/DM+Sans), [JetBrains Mono](https://fonts.google.com/specimen/JetBrains+Mono) | Light and Dark typefaces | SIL Open Font License 1.1 | Loaded from Google Fonts at runtime, not bundled. The Retro look uses fonts already on the reader's system. |

The entry table, succession chains, article notes, page code and pipeline are original to this project. The table was compiled for this project rather than taken from a single reference work; the names and dates in it are historical facts.
