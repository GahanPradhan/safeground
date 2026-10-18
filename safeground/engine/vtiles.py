"""OpenStreetMap data from OpenFreeMap vector tiles (OpenMapTiles schema) — the fallback when Overpass is busy.

Tiles are cached on a CDN, need no key and cover the planet at zoom 14. Roads become a walking graph (vertices are
shared at the exact same tile pixel, pieces cut at tile edges are re-joined); POIs, buildings with heights, land use
and place names become SafeGround features.
"""
from __future__ import annotations

import gzip
import math
import struct
from concurrent.futures import ThreadPoolExecutor

import httpx
import numpy as np
from scipy.spatial import cKDTree

from safeground.engine.osm import WALKABLE, _feature, classify

TILEJSON = "https://tiles.openfreemap.org/planet"
UA = {"User-Agent": "SafeGround/1.0 (disaster readiness prototype; Google Cloud AI Builder Cup)"}
Z = 14
ATTRIBUTION = "OpenFreeMap © OpenMapTiles, data © OpenStreetMap contributors"


# ------------------------------------------------------------------------------------------------ MVT decoding
def _varint(b: bytes, i: int) -> tuple[int, int]:
    shift = result = 0
    while True:
        c = b[i]
        i += 1
        result |= (c & 0x7F) << shift
        if not c & 0x80:
            return result, i
        shift += 7


def _fields(b: bytes):
    i, n = 0, len(b)
    while i < n:
        key, i = _varint(b, i)
        f, wt = key >> 3, key & 7
        if wt == 0:
            v, i = _varint(b, i)
        elif wt == 2:
            ln, i = _varint(b, i)
            v, i = b[i:i + ln], i + ln
        elif wt == 5:
            v, i = b[i:i + 4], i + 4
        elif wt == 1:
            v, i = b[i:i + 8], i + 8
        else:
            raise ValueError("bad wire type")
        yield f, wt, v


def _packed(b: bytes) -> list[int]:
    out, i = [], 0
    while i < len(b):
        v, i = _varint(b, i)
        out.append(v)
    return out


def _value(b: bytes):
    for f, wt, v in _fields(b):
        if f == 1:
            return v.decode("utf-8", "replace")
        if f == 2:
            return struct.unpack("<f", v)[0]
        if f == 3:
            return struct.unpack("<d", v)[0]
        if f in (4, 5):
            return v
        if f == 6:
            return (v >> 1) ^ -(v & 1)
        if f == 7:
            return bool(v)
    return None


def _geometry(cmds: list[int]) -> list[list[tuple[int, int]]]:
    parts, cur, x, y, i = [], [], 0, 0, 0
    while i < len(cmds):
        cmd, count = cmds[i] & 7, cmds[i] >> 3
        i += 1
        if cmd == 7:  # ClosePath
            if cur:
                cur.append(cur[0])
            continue
        for _ in range(count):
            dx, dy = cmds[i], cmds[i + 1]
            i += 2
            x += (dx >> 1) ^ -(dx & 1)
            y += (dy >> 1) ^ -(dy & 1)
            if cmd == 1:  # MoveTo
                if cur:
                    parts.append(cur)
                cur = [(x, y)]
            else:
                cur.append((x, y))
    if cur:
        parts.append(cur)
    return parts


def decode(tile: bytes, want: set[str]) -> dict[str, list[dict]]:
    if tile[:2] == b"\x1f\x8b":
        tile = gzip.decompress(tile)
    layers = {}
    for f, wt, v in _fields(tile):
        if f != 3:
            continue
        name, keys, vals, feats, extent = None, [], [], [], 4096
        for lf, lwt, lv in _fields(v):
            if lf == 1:
                name = lv.decode()
            elif lf == 2:
                feats.append(lv)
            elif lf == 3:
                keys.append(lv.decode())
            elif lf == 4:
                vals.append(_value(lv))
            elif lf == 5:
                extent = lv
        if name not in want:
            continue
        out = []
        for fb in feats:
            tags, gtype, geom = [], 0, []
            for ff, fwt, fv in _fields(fb):
                if ff == 2:
                    tags = _packed(fv)
                elif ff == 3:
                    gtype = fv
                elif ff == 4:
                    geom = _packed(fv)
            props = {keys[tags[k]]: vals[tags[k + 1]] for k in range(0, len(tags) - 1, 2)}
            out.append({"props": props, "type": gtype, "parts": _geometry(geom), "extent": extent})
        layers[name] = out
    return layers


# ------------------------------------------------------------------------------------------------ tiles
def _tile_xy(lat: float, lon: float) -> tuple[float, float]:
    n = 2 ** Z
    x = (lon + 180) / 360 * n
    y = (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n
    return x, y


def _to_latlon(wx: float, wy: float) -> tuple[float, float]:
    n = 2 ** Z
    lon = wx / n * 360 - 180
    lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * wy / n))))
    return lat, lon


def _tile_url() -> str:
    r = httpx.get(TILEJSON, headers=UA, timeout=20)
    r.raise_for_status()
    return r.json()["tiles"][0]


def fetch(lat: float, lon: float, radius_m: float) -> list[tuple[int, int, bytes]]:
    url = _tile_url()
    dlat = radius_m / 111_320
    dlon = radius_m / (111_320 * math.cos(math.radians(lat)))
    x0, y1 = _tile_xy(lat - dlat, lon - dlon)
    x1, y0 = _tile_xy(lat + dlat, lon + dlon)
    tiles = [(x, y) for x in range(int(x0), int(x1) + 1) for y in range(int(y0), int(y1) + 1)]

    def get(t):
        r = httpx.get(url.format(z=Z, x=t[0], y=t[1]), headers=UA, timeout=30)
        r.raise_for_status()
        return t[0], t[1], r.content

    with ThreadPoolExecutor(8) as ex:
        return list(ex.map(get, tiles))


# ------------------------------------------------------------------------------------------------ OpenMapTiles -> SafeGround
POI_TAGS = {  # (class, subclass) -> OSM-like tags understood by osm.classify
    "hospital": {"amenity": "hospital"}, "clinic": {"amenity": "clinic"}, "doctors": {"amenity": "doctors"},
    "school": {"amenity": "school"}, "kindergarten": {"amenity": "kindergarten"}, "college": {"amenity": "college"},
    "university": {"amenity": "university"}, "police": {"amenity": "police"},
    "fire_station": {"amenity": "fire_station"}, "veterinary": {"amenity": "veterinary"},
    "animal_shelter": {"amenity": "animal_shelter"}, "fuel": {"amenity": "fuel"}, "zoo": {"tourism": "zoo"},
    "nursing_home": {"amenity": "social_facility", "social_facility": "nursing_home"},
    "social_facility": {"amenity": "social_facility"}, "community_centre": {"amenity": "community_centre"},
    "subway_entrance": {"railway": "subway_entrance"}, "park": {"leisure": "park"}, "pitch": {"leisure": "pitch"},
    "playground": {"leisure": "playground"}, "stadium": {"leisure": "stadium"}, "garden": {"leisure": "garden"},
}
PATH_SUB = {"footway", "steps", "pedestrian", "path", "cycleway", "corridor"}
PLACE_CLASSES = {"city", "town", "suburb", "neighbourhood", "quarter", "locality", "village", "hamlet"}


def _hw(props: dict) -> str | None:
    c, sub = props.get("class"), props.get("subclass")
    if c in ("trunk", "primary", "secondary", "tertiary"):
        return f"{c}_link" if props.get("ramp") == 1 else c
    if c == "minor":
        return "residential"
    if c == "path":
        return sub if sub in PATH_SUB else "path"
    if c == "service":
        return "service"
    return None  # motorway, rail, ferry, track, etc.


def parse(tiles: list[tuple[int, int, bytes]], lat0: float, lon0: float, radius_m: float):
    from safeground.engine.geo import haversine_m
    want = {"transportation", "poi", "building", "place", "landuse", "park", "water_name"}
    node_id: dict[tuple[int, int], int] = {}
    roads, feats, places, tagged = [], [], [], []
    seen_poi = set()

    def nid(key):
        if key not in node_id:
            node_id[key] = len(node_id)
        return node_id[key]

    for tx, ty, raw in tiles:
        layers = decode(raw, want)
        for f in layers.get("transportation", []):
            hw = _hw(f["props"])
            if hw not in WALKABLE or f["type"] != 2:
                continue
            ext = f["extent"]
            for part in f["parts"]:
                keys = [(tx * ext + px, ty * ext + py) for px, py in part]
                coords = [_to_latlon(k[0] / ext, k[1] / ext) for k in keys]
                if len(coords) < 2:
                    continue
                roads.append({"id": len(roads), "refs": [nid(k) for k in keys], "coords": coords, "hw": hw,
                              "name": None, "tunnel": f["props"].get("brunnel") == "tunnel",
                              "bridge": f["props"].get("brunnel") == "bridge"})
        for layer, kind in (("poi", "poi"), ("place", "place"), ("landuse", "landuse"), ("park", "park"),
                            ("water_name", "water"), ("building", "building")):
            for f in layers.get(layer, []):
                ext = f["extent"]
                pts = [p for part in f["parts"] for p in part]
                if not pts:
                    continue
                if layer == "building":
                    h = f["props"].get("render_height")
                    if not isinstance(h, (int, float)) or h < 9:
                        continue
                px, py = np.mean([p[0] for p in pts]), np.mean([p[1] for p in pts])
                la, lo = _to_latlon(tx + px / ext, ty + py / ext)
                if haversine_m(lat0, lon0, la, lo) > radius_m + 300:
                    continue
                p = f["props"]
                name = p.get("name:en") or p.get("name_en") or p.get("name")
                if layer == "building":
                    tagged.append({"osm": f"t{tx}_{ty}_{len(tagged)}", "lat": la, "lon": lo,
                                   "levels": None, "height": str(round(p["render_height"])), "name": name})
                    continue
                if layer == "place":
                    if p.get("class") in PLACE_CLASSES and name:
                        places.append({"name": name, "name_local": p.get("name"), "type": p.get("class"),
                                       "lat": la, "lon": lo, "osm": f"t{tx}_{ty}"})
                    continue
                if layer == "landuse":
                    tags = {"landuse": p.get("class")} if p.get("class") in ("industrial",) else {}
                elif layer == "park":
                    tags = {"leisure": "park"}
                elif layer == "water_name":
                    tags = {"natural": "water", "name": name} if name else {}
                else:
                    tags = dict(POI_TAGS.get(p.get("subclass")) or POI_TAGS.get(p.get("class")) or {})
                    if p.get("class") == "railway" and p.get("subclass") in ("station", "halt", "subway"):
                        tags = {"railway": "station", **({"station": "subway"} if p.get("subclass") == "subway" else {})}
                    if p.get("level") is not None:
                        tags["level"] = str(p.get("level"))
                if not tags:
                    continue
                if name:
                    tags["name"] = name
                cats = [c for c in classify(tags) if c != "place"]
                key = (layer, name, round(la, 4), round(lo, 4))
                if not cats or key in seen_poi:
                    continue
                seen_poi.add(key)
                feats.append(_feature(f"t{len(feats)}", cats, {**tags, "source": "openmaptiles"}, la, lo, None))
    _join_tile_edges(roads)
    return roads, feats, places, tagged


def _join_tile_edges(roads: list[dict], max_m: float = 40.0) -> None:
    """Pieces of a road cut at a tile edge overlap but may share no vertex: link each dangling end to the nearest
    vertex of another piece within max_m (the tile buffer), as a short connector."""
    from collections import Counter

    from safeground.engine.geo import haversine_m
    deg = Counter()
    coord_of: dict[int, tuple[float, float]] = {}
    piece_of: dict[int, set[int]] = {}
    for i, r in enumerate(roads):
        deg[r["refs"][0]] += 1
        deg[r["refs"][-1]] += 1
        for ref, c in zip(r["refs"], r["coords"]):
            coord_of[ref] = c
            piece_of.setdefault(ref, set()).add(i)
            deg[ref] += 0
    ids = list(coord_of)
    xy = np.array([[c[1] * math.cos(math.radians(c[0])) * 111_320, c[0] * 110_574] for c in (coord_of[i] for i in ids)])
    tree = cKDTree(xy)
    ends = [r for r in ids if deg[r] == 1]
    for e in ends:
        c = coord_of[e]
        q = [c[1] * math.cos(math.radians(c[0])) * 111_320, c[0] * 110_574]
        best, bd = None, max_m
        for j in tree.query_ball_point(q, r=max_m):
            other = ids[j]
            if other == e or piece_of[other] & piece_of[e]:
                continue
            d = float(haversine_m(c[0], c[1], *coord_of[other]))
            if d < bd:
                best, bd = other, d
        if best is not None:
            src = roads[next(iter(piece_of[e]))]
            roads.append({"id": len(roads), "refs": [e, best], "coords": [c, coord_of[best]], "hw": src["hw"],
                          "name": None, "tunnel": src["tunnel"], "bridge": src["bridge"]})
