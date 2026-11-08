"""Simplify every border snapshot into build/borders.json.

Output: [[year, [[name, part_of, [encoded polygons]], ...]], ...] sorted by year, plus build/names.json
(every territory name with its total area and count, largest first) for writing aliases.
"""

from __future__ import annotations

import json
import sys
from typing import Any

from geo import GeoFeature, decode_area, encode_polygons, geojson_polygons, topojson_features
from paths import BASEMAPS_FILES, BUILD, CACHE, PRESENT_YEAR

EPS = 0.07  # degrees; about 8 km at the equator

# The source files carry a few names with a broken accented character.
NAME_FIXES = {"Teotihuac�n": "Teotihuacán", "Monte Alb�n": "Monte Albán", "Arag�n": "Aragón"}


def snapshot_year(stem: str) -> int:
    key = stem.removeprefix("world_")
    return -int(key[2:]) if key.startswith("bc") else int(key)


def load_basemap(stem: str) -> list[GeoFeature]:
    data: dict[str, Any] = json.loads((CACHE / f"{stem}.geojson").read_text(encoding="utf-8", errors="replace"))
    out: list[GeoFeature] = []
    for ft in data["features"]:
        props: dict[str, Any] = ft.get("properties") or {}
        geom: dict[str, Any] | None = ft.get("geometry")
        name = str(props.get("NAME") or "").strip()
        if not geom or not name:
            continue
        name = NAME_FIXES.get(name, name)
        part = str(props.get("PARTOF") or props.get("SUBJECTO") or "").strip()
        part = NAME_FIXES.get(part, part)
        out.append(GeoFeature(name=name, part_of=part if part != name else "", polygons=geojson_polygons(geom)))
    return out


def main() -> None:
    snaps: dict[int, list[GeoFeature]] = {snapshot_year(s): load_basemap(s) for s in BASEMAPS_FILES}
    snaps[PRESENT_YEAR] = topojson_features(json.loads((CACHE / "countries-50m.json").read_text(encoding="utf-8")), "countries")
    result: list[list[Any]] = []
    names: dict[str, list[float]] = {}
    for year in sorted(snaps):
        feats: list[list[Any]] = []
        for f in snaps[year]:
            polys = encode_polygons(f.polygons, EPS)
            if not polys:
                continue
            feats.append([f.name, f.part_of, polys])
            stat = names.setdefault(f.name, [0.0, 0.0])
            stat[0] += sum(decode_area(p[0]) for p in polys)
            stat[1] += 1
        result.append([year, feats])
    leftover = [n for _, fs in result for f in fs for n in f[:2] if "�" in n]
    if leftover:
        sys.exit(f"names with broken characters, add them to NAME_FIXES: {sorted(set(leftover))}")
    BUILD.mkdir(exist_ok=True)
    (BUILD / "borders.json").write_text(json.dumps(result, separators=(",", ":"), ensure_ascii=False), encoding="utf-8")
    ranked = sorted(names.items(), key=lambda kv: -kv[1][0])
    (BUILD / "names.json").write_text(json.dumps(ranked, ensure_ascii=False), encoding="utf-8")
    print(f"{len(result)} snapshots, {len(names)} territory names")


if __name__ == "__main__":
    main()
