"""Validate the entry table and succession chains in the page source. Exits non-zero on any error."""

from __future__ import annotations

import sys
from collections import Counter

from entries import chains, entries, families, read_source, regions
from paths import PRESENT_YEAR

FIRST_YEAR = -3100  # the chart starts here; an earlier start year is allowed and shown in the article


def main() -> int:
    src = read_source()
    items = entries(src)
    fams, regs = families(src), regions(src)
    errors: list[str] = []
    warnings: list[str] = []

    for e in items:
        where = f"line {e.line} ({e.name})"
        if e.start > e.end:
            errors.append(f"{where}: starts after it ends ({e.start} > {e.end})")
        if e.end < FIRST_YEAR or e.end > PRESENT_YEAR:
            errors.append(f"{where}: end year outside {FIRST_YEAR} to {PRESENT_YEAR}")
        if e.family not in fams:
            errors.append(f"{where}: unknown family {e.family!r}")
        bad = [r for r in e.regions if r not in regs]
        if bad or not e.regions:
            errors.append(f"{where}: unknown or missing region {bad}")
        if e.note and "—" in e.note:
            warnings.append(f"{where}: note contains an em dash")

    for name, count in Counter(e.name for e in items).items():
        if count > 1:
            errors.append(f"{name!r} appears {count} times; list a multi-region state once with several regions")

    by_name = {e.name: e for e in items}
    for line, names in chains(src):
        for nm in names:
            if nm not in by_name:
                errors.append(f"chain on line {line}: no entry named {nm!r}")
        for a, b in zip(names, names[1:]):
            ea, eb = by_name.get(a), by_name.get(b)
            if ea and eb and eb.end < ea.start:
                errors.append(f"chain on line {line}: {b!r} ends before {a!r} begins")

    for w in warnings:
        print("warning:", w)
    for err in errors:
        print("error:", err)
    print(f"{len(items)} entries, {sum(len(c) - 1 for _, c in chains(src))} succession links, {len(errors)} errors")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
