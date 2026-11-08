"""Read the entry table, succession chains, families and regions out of the page source.

The page source is the single home of the entries, so the map classifier and the page can never drift apart.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from paths import SRC_HTML


@dataclass(frozen=True)
class Entry:
    index: int
    name: str
    start: int
    end: int
    family: str
    regions: tuple[str, ...]
    culture: bool
    note: str
    line: int


def _block(src: str, const: str) -> tuple[str, int]:
    m = re.search(r"const " + const + r" = `(.*?)`;", src, re.S)
    if not m:
        raise SystemExit(f"{const} block not found in {SRC_HTML.name}")
    return m.group(1), src.count("\n", 0, m.start(1)) + 1


def read_source() -> str:
    return SRC_HTML.read_text(encoding="utf-8")


def entries(src: str) -> list[Entry]:
    raw, first_line = _block(src, "RAW")
    out: list[Entry] = []
    for offset, line in enumerate(raw.split("\n")):
        if not line.strip():
            continue
        f = line.split("|")
        if len(f) < 5:
            raise SystemExit(f"line {first_line + offset}: expected name|start|end|family|regions|c[|note]: {line}")
        out.append(Entry(
            index=len(out), name=f[0], start=int(f[1]), end=int(f[2]), family=f[3],
            regions=tuple(f[4].split()), culture=len(f) > 5 and f[5] == "c", note="|".join(f[6:]), line=first_line + offset,
        ))
    return out


def chains(src: str) -> list[tuple[int, list[str]]]:
    raw, first_line = _block(src, "CHAINS")
    return [(first_line + i, [x.strip() for x in line.split(" > ")]) for i, line in enumerate(raw.split("\n")) if line.strip()]


def families(src: str) -> set[str]:
    m = re.search(r"const FAMS = \[(.*?)\];", src, re.S)
    return set(re.findall(r'\["([A-Z]{2})"', m.group(1))) if m else set()


def regions(src: str) -> set[str]:
    m = re.search(r"const REGIONS = \[(.*?)\];", src, re.S)
    return set(re.findall(r'\["([A-Z]{3})"', m.group(1))) if m else set()
