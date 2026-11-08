# Corrections and additions

Most fixes are a one-line change to `src/hall-of-realms.src.html` or `data/manual.json`. Issues are welcome too, especially with a source attached.

## Dates, family or hall

Each entry is one line of the `RAW` block: `name|start|end|family|regions|c|note`. Years are integers, negative for BCE. The family is the language family of the ruling group, which can differ from the population's. A pull request that changes a date or family names its source: a reference work, a scholarly article or an encyclopedia entry.

## Successions

The `CHAINS` block holds successions, and every name in it has to match an entry exactly. `make check` reports names that match nothing and successors that end before their predecessor begins.

## A grey or miscolored territory

`make classify` writes `build/unclassified.json` (grey territories) and `build/names.json` (every territory name). The fix goes in `data/manual.json`:

- a territory that is one of the timeline's entries under another name gets an `alias` line, `"Border name": "Entry name"`;
- any other territory gets a `family` line, `"Border name": "XX"`, where `XX` is a family code from `FAMS` in the page source.

The borders themselves come from historical-basemaps, and errors in them belong [upstream](https://github.com/aourednik/historical-basemaps/issues).

## Checks before a pull request

```bash
make check
make page
make typecheck   # only after pipeline changes
```

After the build, `dist/hall-of-realms.html` shows the changed entry or year.

Contributions are accepted under the project's GPL-3.0 license.
