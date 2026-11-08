"""Project paths and pinned source versions."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC_HTML = ROOT / "src" / "hall-of-realms.src.html"
MANUAL = ROOT / "data" / "manual.json"
CACHE = ROOT / ".cache" / "sources"
BUILD = ROOT / "build"
DIST = ROOT / "dist"

# historical-basemaps by André Ourednik (GPL-3.0), pinned to the commit the published page was built from.
BASEMAPS_COMMIT = "4b5039e50d8d2464b065bd76ad6086cd4597108d"
BASEMAPS_URL = f"https://raw.githubusercontent.com/aourednik/historical-basemaps/{BASEMAPS_COMMIT}/geojson/"
BASEMAPS_FILES = [
    "world_bc3000", "world_bc2000", "world_bc1500", "world_bc1000", "world_bc700", "world_bc500", "world_bc400",
    "world_bc323", "world_bc300", "world_bc200", "world_bc100", "world_bc1", "world_100", "world_200", "world_300",
    "world_400", "world_500", "world_600", "world_700", "world_800", "world_900", "world_1000", "world_1100",
    "world_1200", "world_1279", "world_1300", "world_1400", "world_1492", "world_1500", "world_1530", "world_1600",
    "world_1650", "world_1700", "world_1715", "world_1783", "world_1800", "world_1815", "world_1880", "world_1900",
    "world_1914", "world_1920", "world_1930", "world_1938", "world_1945", "world_1960", "world_1994", "world_2000",
    "world_2010",
]

# Natural Earth (public domain) packaged as TopoJSON by world-atlas (ISC).
WORLD_ATLAS_URL = "https://cdn.jsdelivr.net/npm/world-atlas@2.0.2/"
WORLD_ATLAS_FILES = ["countries-50m.json", "land-110m.json"]

PRESENT_YEAR = 2026
