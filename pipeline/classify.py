"""Link every territory in every snapshot to a timeline entry or a language family; write build/mapdata.json.

Order of rules for each territory: an alias in data/manual.json, a timeline entry alive within 60 years
(exact name, then core-word match), the polity it belongs to, the manual family table, a colonial suffix
such as "(UK)", keyword patterns, and finally a continent fallback. Anything left is grey ("XX").
"""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from typing import Any

from entries import Entry, entries, read_source
from geo import EncPoly, decode_area, encode_polygons, topojson_features
from paths import BUILD, CACHE, MANUAL

WINDOW = 60  # years a territory may sit outside an entry's dates and still link to it
LAND_EPS = 0.12

GENERIC = set(
    "empire kingdom kingdoms of the dynasty caliphate sultanate khanate khaganate khanates state states emirate "
    "emirates republic confederation confederacy principality grand duchy city chiefdoms chiefdom and tsardom realm "
    "period culture cultures great imperial federal democratic peoples people s rep united".split()
)
COLONIAL = [
    (r"\((uk|gb|france|fr|portugal|spain|belgium|it|italy|netherlands|nl|germany|usa|us|denmark|dk|britain|british|russia|ru|south africa|sa|australia|new zealand|nz)\)", "IE"),
    (r"\(japan\)", "OT"),
]
KEYWORDS = [
    (r"bantu|west african cereal|mande|yoruba|igbo|akan|hausa|fulani|nilot|zulu|luba|lunda|kongo", "NC"),
    (r"khoisan|khoi|san people|aborigin|australian|tasmania|papua|ainu|paleo siberian|siberian|chukchi|samoy|finno|ugric|saami|sami|permian|uralic|korea|japan|jomon|yayoi|koguryo|goguryeo|silla|baekje|sumer|elam|hurri|minoan|etrusc|basque|georgia", "OT"),
    (r"turk|turcik|mongol|tungus|manchu|altaic|khagan|khanate|horde|kipchak|cuman|oghuz|uyghur|uighur|kazakh|quazaq|uzbek|tatar|bulgar|karluk|kimek|oirat|dzungar|jurchen|khitan|xiongnu|xianbei|rouran|ruanruan|avar|khazar|pechen|peshemeg|seljuk|timurid|ottoman", "TM"),
    (r"semit|arab|bedouin|berber|tuareg|touareg|sahara|cushit|oromo|somali|ethiopia|hejaz|nejd|egypt|yemen|hadram|ibadi|phoenic|carthag|amazigh|beja|amhar|tigr|assyr|babylon|akkad|canaan|israel|juda", "AA"),
    (r"dravid|tamil|telugu|kannad|chola|pandya|chera|pallava", "DR"),
    (r"austrones|polynes|melanes|micrones|malay|maori|austro asiatic|thai|tai|mon|khmer|cham|java|sumatra|filipin|taiwanese tribes|lapita|viet|lao", "AU"),
    (r"tibet|sinic|chinese|han|zhou|qiang|burm|shan|tangut|xixia|yi|bai|nan chao|nanzhao|pyu", "ST"),
    (r"celt|german|slav|urnfield|hallstatt|scyth|sarmat|cimmer|cimer|iranian|aryan|vedic|indo|persia|greek|hellen|roman|latin|illyr|thrac|dacian|baltic|balt|corded|yamna|afanas|andronovo|saka|sogd|bactr|tochar|kurd|pashtun|rajput|hindu|maratha|sikh|bengal|norse|viking|frank|goth|anglo|saxon|lombard|rus", "IE"),
    (r"amerind|amazon|andean|pampas|patagon|maize|manioc|bison|plateau|inuit|inupiaq|yup|thule|dorset|arctic|athaba|dene|denendeh|cree|innu|naskapi|montagnais|ojibw|anishin|shoshon|ute|apache|navajo|sioux|ochethi|assiniboin|iroquo|haudeno|cherokee|creek|choctaw|comanch|tupi|guarani|arawak|carib|taino|maya|aztec|mexica|olmec|zapotec|mixtec|toltec|inca|chimu|moche|mapuche|muisca|anasazi|pueblo|hohokam|mogollon|hopewell|adena|mississip|woodland|laurel|point peninsula|eyaq|chorrera|valdivia|metis|michif|shellfish|caloosa|calusa|beothuk|boethuk|tekoha|aleut|tlingit|haida", "AM"),
]
# Short tokens match whole words only ("ute" must not match "Utetera"), except these prefixes.
PREFIX_OK = {"turk", "celt", "slav", "balt", "goth", "kurd", "arab", "tupi", "sumer", "beja", "tamil", "khmer", "sinic"}
KEYWORD_RX = [
    (re.compile(r"\b(?:" + "|".join(t if (len(t) >= 5 or t in PREFIX_OK) else t + r"\b" for t in rx.split("|")) + ")"), fam)
    for rx, fam in KEYWORDS
]
CULTURE_RX = re.compile(
    r"hunter|gatherer|farmer|pastoral|nomad|tribe|peoples|culture|herder|fisher|fichers|forag|neolithic|bronze age|"
    r"pottery|complex|burials|shellfish|marine mammal|aboriginal|^celts$|^slav|^arabs$|^bedouin|^berber|^semites|"
    r"^tibetans$|^tungus$|^mongols$|^uyghurs$|^siberians$|^dravidians$|^austronesians$|^papuans$|^polynesians$|"
    r"^malays?$|^bantu|^tuareg|^touareg|^inuit|^thule$|^dorset$|^cree$|^innu$|^ainu$|^saami$|^sámi$|^samis$",
    re.I,
)


def words(s: str) -> list[str]:
    ascii_ = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9 ]", " ", ascii_).split()


def core(s: str) -> str:
    return " ".join(w for w in words(s) if w not in GENERIC)


@dataclass(frozen=True)
class Linkable:
    entry: Entry
    norm: str
    core: str


class Linker:
    def __init__(self, items: list[Entry], aliases: dict[str, str]) -> None:
        self.items = [Linkable(e, " ".join(words(e.name)), core(e.name)) for e in items]
        self.aliases = aliases

    def link(self, name: str, year: int) -> Entry | None:
        def alive(it: Linkable) -> bool:
            return it.entry.start - WINDOW <= year <= it.entry.end + WINDOW

        if name in self.aliases:
            cands = [it for it in self.items if it.entry.name == self.aliases[name]]
            if cands:
                return min(cands, key=lambda it: 0 if alive(it) else 1).entry
        live = [it for it in self.items if alive(it)]
        n, c = " ".join(words(name)), core(name)
        for it in live:
            if it.norm == n:
                return it.entry
        if len(c) >= 3:
            for it in live:
                if it.core == c:
                    return it.entry
            for it in live:
                if it.entry.culture or len(it.core) < 4:
                    continue
                if re.search(r"\b" + re.escape(it.core) + r"\b", c) or re.search(r"\b" + re.escape(c) + r"\b", it.core):
                    return it.entry
        return None


def centroid(polys: list[EncPoly]) -> tuple[float, float]:
    xs = ys = 0.0
    n = 0
    for poly in polys[:3]:
        x = y = 0
        for k in range(0, len(poly[0]), 2):
            x += poly[0][k]
            y += poly[0][k + 1]
            xs += x
            ys += y
            n += 1
    return (xs / n / 100, ys / n / 100) if n else (0.0, 0.0)


def continent(lon: float, lat: float) -> str | None:
    if lon < -30:
        return "AM"
    if lon > 110 and lat < -10:
        return "AUS"
    if -20 < lon < 52 and lat < 15:
        return "SSA"
    return None


def main() -> None:
    manual: dict[str, dict[str, str]] = json.loads(MANUAL.read_text(encoding="utf-8"))
    families = manual.get("family", {})
    linker = Linker(entries(read_source()), manual.get("alias", {}))
    snaps: list[list[Any]] = json.loads((BUILD / "borders.json").read_text(encoding="utf-8"))

    names: dict[str, int] = {}

    def name_id(s: str) -> int:
        return names.setdefault(s, len(names))

    out_snaps: list[list[Any]] = []
    extent: dict[tuple[int, int], float] = {}
    missing: dict[str, int] = {}
    total = covered = 0
    for year, feats in snaps:
        out: list[list[Any]] = []
        for name, part, polys in feats:
            fam: str | None = None
            cult = False
            it = linker.link(name, year) or (linker.link(part, year) if part else None)
            if it:
                fam, cult = it.family, it.culture
            fam = fam or families.get(name) or (families.get(part) if part else None)
            if not fam:
                fam = next((f for rx, f in COLONIAL if re.search(rx, name.lower())), None)
            if not fam:
                low = " ".join(words(name))
                fam = next((f for rx, f in KEYWORD_RX if rx.search(low)), None)
            looks_cultural = bool(CULTURE_RX.search(name))
            if not it:
                cult = looks_cultural
            if not fam:
                c = continent(*centroid(polys))
                if c == "AM":
                    fam = "AM"
                elif c == "AUS":
                    fam, cult = "OT", True
                elif c == "SSA" and looks_cultural:
                    fam = "NC"
            weight = sum(len(p[0]) for p in polys)
            total += weight
            if fam:
                covered += weight
            else:
                missing[name] = missing.get(name, 0) + weight
            if it:
                key = (it.index, len(out_snaps))
                extent[key] = extent.get(key, 0.0) + sum(decode_area(p[0]) for p in polys)
            out.append([name_id(name), name_id(part) if part else -1, fam or "XX", 1 if cult else 0, it.index if it else -1, polys])
        out_snaps.append([year, out])

    best: dict[int, tuple[int, float]] = {}
    for (i, si), area in extent.items():
        if i not in best or area > best[i][1]:
            best[i] = (si, area)

    land_topo = json.loads((CACHE / "land-110m.json").read_text(encoding="utf-8"))
    land_topo["objects"] = {"land": {"geometries": land_topo["objects"]["land"]["geometries"]}}
    land = [p for f in topojson_features(land_topo, "land") for p in encode_polygons(f.polygons, LAND_EPS)]

    name_list = [""] * len(names)
    for k, v in names.items():
        name_list[v] = k
    data = {"names": name_list, "snaps": out_snaps, "ext": {str(i): v[0] for i, v in best.items()}, "land": land}
    (BUILD / "mapdata.json").write_text(json.dumps(data, separators=(",", ":"), ensure_ascii=False), encoding="utf-8")
    ranked = sorted(missing.items(), key=lambda kv: -kv[1])
    (BUILD / "unclassified.json").write_text(json.dumps(ranked, ensure_ascii=False, indent=0), encoding="utf-8")
    print(f"classified {100 * covered / total:.1f}% of border detail; {len(best)} entries have a locator map; "
          f"top unclassified: {', '.join(n for n, _ in ranked[:5])}")


if __name__ == "__main__":
    main()
