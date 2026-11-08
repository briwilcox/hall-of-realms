# Corrections and additions

Most fixes are a one-line change in `src/hall-of-realms.src.html` or `data/manual.json`.

## Wrong dates, family or hall

Edit the entry's line in the `RAW` block (`name|start|end|family|regions|c|note`). Years are integers, negative for BCE. Family is the language family of the ruling group, not of the population. Give a reference work or other source for the change in the pull request.

## Missing or wrong succession

Edit the `CHAINS` block. Every name must match an entry exactly. `make check` reports names that do not match and successors that end before their predecessor begins.

## A territory on the map is grey or the wrong color

1. Run `make classify` and look up the territory's name in `build/unclassified.json` (grey ones) or `build/names.json` (all of them).
2. If the territory is one of the timeline's entries under another name, add `"Border name": "Entry name"` to `alias` in `data/manual.json`.
3. Otherwise add `"Border name": "XX"` to `family`, where `XX` is a family code from `FAMS` in the page source.

Wrong borders themselves come from historical-basemaps; report those upstream at https://github.com/aourednik/historical-basemaps.

## Before opening a pull request

```bash
make check
make page
make typecheck   # only if you changed the pipeline
```

Open `dist/hall-of-realms.html` and look at the entry or year you changed.

Contributions are accepted under the project's GPL-3.0 license.
