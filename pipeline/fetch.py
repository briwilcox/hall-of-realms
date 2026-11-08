"""Download the border sources into .cache/sources. Files already present and valid are skipped."""

from __future__ import annotations

import json
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from paths import BASEMAPS_FILES, BASEMAPS_URL, CACHE, WORLD_ATLAS_FILES, WORLD_ATLAS_URL

USER_AGENT = "hall-of-realms-build/1.0"


def valid(path: Path) -> bool:
    try:
        with path.open(encoding="utf-8", errors="replace") as f:
            json.load(f)
        return True
    except (OSError, ValueError):
        return False


def download(url: str, dest: Path, attempts: int = 4) -> None:
    if dest.exists() and valid(dest):
        return
    tmp = dest.with_suffix(dest.suffix + ".part")
    for n in range(attempts):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=120) as r:
                tmp.write_bytes(r.read())
            if valid(tmp):
                tmp.replace(dest)
                print("fetched", dest.name)
                return
        except OSError as e:
            print(f"retry {dest.name}: {e}", file=sys.stderr)
        time.sleep(2 ** (n + 1))
    raise SystemExit(f"could not download {url}")


def main() -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    jobs = [(BASEMAPS_URL + f + ".geojson", CACHE / (f + ".geojson")) for f in BASEMAPS_FILES]
    jobs += [(WORLD_ATLAS_URL + f, CACHE / f) for f in WORLD_ATLAS_FILES]
    with ThreadPoolExecutor(max_workers=3) as pool:
        list(pool.map(lambda j: download(*j), jobs))
    print(f"{len(jobs)} source files in {CACHE}")


if __name__ == "__main__":
    main()
