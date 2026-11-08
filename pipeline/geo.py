"""Geometry helpers shared by the pipeline: simplification, ring winding, delta encoding, TopoJSON decoding."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, TypeAlias

Point: TypeAlias = tuple[float, float]
Ring: TypeAlias = list[Point]
EncRing: TypeAlias = list[int]
EncPoly: TypeAlias = list[EncRing]


@dataclass(frozen=True)
class GeoFeature:
    """One named territory: its name, the polity it belongs to (if any) and its polygons."""

    name: str
    part_of: str
    polygons: list[list[Ring]]


def douglas_peucker(pts: Ring, eps: float) -> Ring:
    """Drop points closer than eps (degrees) to the line between their kept neighbours."""
    if len(pts) < 3:
        return pts
    keep = [False] * len(pts)
    keep[0] = keep[-1] = True
    stack: list[tuple[int, int]] = [(0, len(pts) - 1)]
    while stack:
        a, b = stack.pop()
        ax, ay = pts[a]
        bx, by = pts[b]
        dx, dy = bx - ax, by - ay
        length = math.hypot(dx, dy)
        best, best_i = -1.0, -1
        for i in range(a + 1, b):
            px, py = pts[i]
            d = abs(dy * px - dx * py + bx * ay - by * ax) / length if length else math.hypot(px - ax, py - ay)
            if d > best:
                best, best_i = d, i
        if best > eps:
            keep[best_i] = True
            stack += [(a, best_i), (best_i, b)]
    return [p for p, k in zip(pts, keep) if k]


def signed_area(r: Ring) -> float:
    return sum(r[i][0] * r[i + 1][1] - r[i + 1][0] * r[i][1] for i in range(len(r) - 1)) / 2


def clean_ring(r: Ring, exterior: bool, eps: float) -> Ring | None:
    """Round, close, simplify and orient a ring (d3 wants exteriors clockwise). None if it collapses."""
    pts: Ring = [(round(x, 2), round(y, 2)) for x, y in r]
    if pts[0] != pts[-1]:
        pts.append(pts[0])
    s = douglas_peucker(pts, eps)
    if len(s) < 4:
        return None
    a = signed_area(s)
    if abs(a) < 0.04:
        return None
    if (exterior and a > 0) or (not exterior and a < 0):
        s = s[::-1]
    return s


def encode_ring(r: Ring) -> EncRing:
    """Delta-encode a closed ring as integers in hundredths of a degree, dropping the closing point."""
    out: EncRing = []
    px = py = 0
    for x, y in r[:-1]:
        ix, iy = int(round(x * 100)), int(round(y * 100))
        out += [ix - px, iy - py]
        px, py = ix, iy
    return out


def decode_area(r: EncRing) -> float:
    """Absolute area in square degrees of an encoded ring."""
    x = y = 0
    pts: Ring = []
    for k in range(0, len(r), 2):
        x += r[k]
        y += r[k + 1]
        pts.append((x / 100, y / 100))
    if len(pts) < 3:
        return 0.0
    pts.append(pts[0])
    return abs(signed_area(pts))


def encode_polygons(polygons: list[list[Ring]], eps: float) -> list[EncPoly]:
    out: list[EncPoly] = []
    for poly in polygons:
        ext = clean_ring(poly[0], True, eps)
        if not ext:
            continue
        holes = [clean_ring(h, False, eps) for h in poly[1:]]
        out.append([encode_ring(ext)] + [encode_ring(h) for h in holes if h])
    return out


def geojson_polygons(geometry: dict[str, Any]) -> list[list[Ring]]:
    kind = geometry.get("type")
    coords: Any = geometry.get("coordinates", [])
    raw: list[Any] = [coords] if kind == "Polygon" else coords if kind == "MultiPolygon" else []
    return [[[(float(p[0]), float(p[1])) for p in ring] for ring in poly] for poly in raw]


def topojson_features(topo: dict[str, Any], object_name: str) -> list[GeoFeature]:
    """Decode one object of a quantized or plain TopoJSON file into features."""
    transform: dict[str, list[float]] | None = topo.get("transform")
    arcs: list[Ring] = []
    for arc in topo["arcs"]:
        x = y = 0.0
        pts: Ring = []
        for p in arc:
            if transform:
                x += p[0]
                y += p[1]
                pts.append((x * transform["scale"][0] + transform["translate"][0], y * transform["scale"][1] + transform["translate"][1]))
            else:
                pts.append((float(p[0]), float(p[1])))
        arcs.append(pts)

    def ring(indices: list[int]) -> Ring:
        pts: Ring = []
        for i in indices:
            a = arcs[i] if i >= 0 else arcs[~i][::-1]
            pts += a if not pts else a[1:]
        return pts

    feats: list[GeoFeature] = []
    for g in topo["objects"][object_name]["geometries"]:
        if g["type"] == "Polygon":
            polys = [[ring(r) for r in g["arcs"]]]
        elif g["type"] == "MultiPolygon":
            polys = [[ring(r) for r in p] for p in g["arcs"]]
        else:
            continue
        name = str((g.get("properties") or {}).get("name") or "")
        feats.append(GeoFeature(name=name, part_of="", polygons=polys))
    return feats
