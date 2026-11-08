"""Assemble the page.

Default: dist/hall-of-realms.html, one self-contained file with the map data inline.
--split: dist/site/ with index.html, app.js and mapdata.js. The two scripts load deferred, so the text
of the page shows while the ~3.6 MB of border data downloads, and hosts can cache and compress it.
"""

from __future__ import annotations

import argparse
import re
import shutil

from paths import BUILD, DIST, SRC_HTML

MARKER = "/*MAPDATA*/"
DATA_TAG = f'<script id="mapdata" type="application/json">{MARKER}</script>'
SOURCE_ARCHIVE = "hall-of-realms-source.tar.gz"
SITE_FOOTER = (
    f'<p>Hall of Realms is free software under the GPL-3.0. <a href="{SOURCE_ARCHIVE}">Download the complete source</a> '
    "(page, build pipeline and border-processing code) to rebuild or modify it.</p>"
)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--split", action="store_true", help="write a static site folder with separate scripts")
    args = ap.parse_args()

    src = SRC_HTML.read_text(encoding="utf-8")
    data = (BUILD / "mapdata.json").read_text(encoding="utf-8")
    if "�" in data:
        raise SystemExit("map data has broken characters; see NAME_FIXES in pipeline/borders.py")
    if src.count(DATA_TAG) != 1:
        raise SystemExit("map data placeholder not found in the page source")
    DIST.mkdir(exist_ok=True)

    if not args.split:
        page = src.replace(MARKER, data.replace("</", "<\\/"))
        out = DIST / "hall-of-realms.html"
        out.write_text(page, encoding="utf-8")
        print(f"wrote {out.relative_to(DIST.parent)} ({out.stat().st_size // 1024} KB)")
        return

    scripts = list(re.finditer(r"<script>(.*?)</script>", src, re.S))
    app = scripts[-1]
    site = DIST / "site"
    shutil.rmtree(site, ignore_errors=True)
    site.mkdir(parents=True)
    (site / "app.js").write_text(app.group(1), encoding="utf-8")
    (site / "mapdata.js").write_text(f"window.HALL_OF_REALMS_MAPDATA = {data};\n", encoding="utf-8")
    loader = '<script defer src="mapdata.js"></script>\n<script defer src="app.js"></script>'
    page = src[: app.start()] + loader + src[app.end():]
    page = page.replace("<!--SITE-FOOTER-->", SITE_FOOTER)
    page = page.replace(DATA_TAG, "").replace(
        '<script src="https://cdnjs.cloudflare.com/', '<script defer src="https://cdnjs.cloudflare.com/'
    )
    (site / "index.html").write_text(page, encoding="utf-8")
    sizes = ", ".join(f"{p.name} {p.stat().st_size // 1024} KB" for p in sorted(site.iterdir()))
    print(f"wrote {site.relative_to(DIST.parent)}/: {sizes}")


if __name__ == "__main__":
    main()
