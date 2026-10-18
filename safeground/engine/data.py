"""Loads the data snapshot once and exposes fast spatial lookups."""
from __future__ import annotations

import contextvars
import json
from contextlib import contextmanager
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import h3
import numpy as np
import yaml
from scipy.spatial import cKDTree

from safeground.config import H3_RES, RULEBOOKS, SHOWCASE_AREAS, SNAPSHOT

CURATED = RULEBOOKS.parent / "curated"
PLACE_ALIASES = {"t nagar": "Thiyagaraya Nagar", "t. nagar": "Thiyagaraya Nagar", "tnagar": "Thiyagaraya Nagar",
                 "thyagaraya nagar": "Thiyagaraya Nagar"}
from safeground.engine.geo import haversine_m, set_reference_latitude, to_xy

# The region a request works on: "chennai" (precomputed snapshot) or a region built on demand (engine/regions.py)
DEFAULT_REGION = "chennai"
_REGION = contextvars.ContextVar("safeground_region", default=DEFAULT_REGION)


def current_region() -> str:
    return _REGION.get()


@contextmanager
def use_region(region_id: str | None):
    """Run engine code against one region: its snapshot, road graph and local projection."""
    rid = region_id or DEFAULT_REGION
    tok = _REGION.set(rid)
    lat0 = 13.07 if rid == DEFAULT_REGION else _region_lat(rid)
    tok2 = set_reference_latitude(lat0)
    try:
        yield
    finally:
        from safeground.engine import geo
        geo._LAT0.reset(tok2)
        _REGION.reset(tok)


def _region_lat(rid: str) -> float:
    from safeground.engine import regions
    return regions.meta(rid)["lat"]

# Air-raid shelters: OSM amenity=shelter is almost always a bus or rain shelter, so it is NOT used.
SHELTER_CATEGORIES = ("metro_underground", "parking_underground", "assembly_point")


@dataclass
class FeatureSet:
    items: list[dict]
    xy: np.ndarray
    tree: cKDTree | None

    def near(self, lat: float, lon: float, radius_m: float, limit: int = 10) -> list[tuple[float, dict]]:
        if self.tree is None or not self.items:
            return []
        x, y = to_xy(lat, lon)
        idx = self.tree.query_ball_point([float(x), float(y)], r=radius_m)
        out = []
        for i in idx:
            f = self.items[i]
            out.append((float(haversine_m(lat, lon, f["lat"], f["lon"])), f))
        return sorted(out, key=lambda t: t[0])[:limit]

    def nearest(self, lat: float, lon: float, k: int = 1) -> list[tuple[float, dict]]:
        if self.tree is None or not self.items:
            return []
        x, y = to_xy(lat, lon)
        k = min(k, len(self.items))
        d, idx = self.tree.query([float(x), float(y)], k=k)
        idx = np.atleast_1d(idx)
        return [(float(haversine_m(lat, lon, self.items[i]["lat"], self.items[i]["lon"])), self.items[i]) for i in idx]


def _feature_set(items: list[dict]) -> FeatureSet:
    if not items:
        return FeatureSet([], np.zeros((0, 2)), None)
    x, y = to_xy(np.array([f["lat"] for f in items]), np.array([f["lon"] for f in items]))
    xy = np.column_stack([x, y])
    return FeatureSet(items, xy, cKDTree(xy))


@dataclass
class Snapshot:
    graph: dict
    features: dict[str, FeatureSet]
    places: list[dict]
    hexes: dict[str, dict]
    rulebooks: dict[str, dict]
    manifests: dict[str, dict] = field(default_factory=dict)
    region: dict = field(default_factory=dict)

    def hex_of(self, lat: float, lon: float) -> str:
        return h3.latlng_to_cell(lat, lon, H3_RES)

    def hex_props(self, cell: str) -> dict:
        return self.hexes.get(cell, {})

    def place_name(self, lat: float, lon: float) -> str | None:
        fs = self.features.get("_places")
        hit = fs.nearest(lat, lon, 1) if fs else []
        return hit[0][1]["name"] if hit and hit[0][0] < 2500 else None

    def find_place(self, query: str) -> dict | None:
        from rapidfuzz import fuzz, process
        if query in SHOWCASE_AREAS:
            lat, lon = SHOWCASE_AREAS[query]
            return {"name": query, "lat": lat, "lon": lon, "type": "showcase", "match_score": 100.0}
        query = PLACE_ALIASES.get(query.lower().strip(), query)
        names = [p["name"] for p in self.places]
        if not names:
            return None
        exact = [p for p in self.places if p["name"].lower() == query.lower()]
        if exact:
            return {**exact[0], "match_score": 100.0}
        match = process.extractOne(query, names, scorer=fuzz.WRatio)
        if match and match[1] >= 80:
            return {**self.places[match[2]], "match_score": match[1]}
        return None


def _underground_names() -> dict[str, str]:
    cur = yaml.safe_load((CURATED / "metro_underground.yaml").read_text())
    return {v.lower(): official for official, variants in cur["stations"].items() for v in variants}


def load() -> Snapshot:
    rid = _REGION.get()
    if rid == DEFAULT_REGION:
        return _load_chennai()
    from safeground.engine import regions
    return regions.snapshot(rid)


@lru_cache(maxsize=1)
def _load_chennai() -> Snapshot:
    return build_snapshot(SNAPSHOT, curated_metro=True)


def build_snapshot(folder: Path, curated_metro: bool = False, region: dict | None = None) -> Snapshot:
    graph = dict(np.load(folder / "graph.npz", allow_pickle=True)) if (folder / "graph.npz").exists() else {}
    raw = json.loads((folder / "features.geojson").read_text())["features"] \
        if (folder / "features.geojson").exists() else []
    by_cat: dict[str, list[dict]] = {}
    for f in raw:
        p = f["properties"]
        lon, lat = f["geometry"]["coordinates"]
        item = {"id": p["id"], "name": p.get("name:en") or p.get("name"), "lat": lat, "lon": lon,
                "area_m2": p.get("area_m2"), "tags": {k: v for k, v in p.items() if k not in ("id", "categories")}}
        for c in p["categories"]:
            by_cat.setdefault(c, []).append(item)
    features = {c: _feature_set(v) for c, v in by_cat.items()}
    underground = []
    if curated_metro:  # Chennai: the official list of underground stations (OSM tags there are unreliable)
        names = _underground_names()
        for s in by_cat.get("metro_station", []):
            official = names.get((s["name"] or "").lower())
            if official:
                underground.append({**s, "name": f"{official} Metro (underground)"})
    else:  # elsewhere: only subway entrances and stations explicitly tagged underground (many metros are elevated)
        for s in by_cat.get("subway_entrance", []):
            underground.append({**s, "name": f"{s['name'] or 'Subway'} entrance (underground station)"})
        for s in by_cat.get("metro_station", []):
            t = s["tags"]
            if t.get("location") == "underground" or str(t.get("level", "")).startswith("-") \
                    or str(t.get("layer", "")).startswith("-"):
                underground.append({**s, "name": f"{s['name'] or 'Metro'} (underground station)"})
    features["metro_underground"] = _feature_set(underground)
    # Emergency-capable hospitals: OSM emergency=yes or a large campus, minus specialty-only places.
    specialty = ("eye", "dental", "physio", "ayurved", "siddha", "homoeo", "homeo", "veterinar", "rehabilitation",
                 "nethralaya", "indian medicine", "traditional", "impcops", "unani", "yoga", "naturopathy", "fertility",
                 "skin", "hair", "scan", "diagnostic")
    major = [h for h in by_cat.get("hospital", [])
             if (str(h["tags"].get("emergency", "")).lower() == "yes" or (h["area_m2"] or 0) >= 3000
                 or h["tags"].get("source") == "openmaptiles")  # tile POIs carry no size: every hospital counts
             and not any(w in (h["name"] or "").lower() for w in specialty)]
    features["hospital_major"] = _feature_set(major)
    features["assembly_point"] = _feature_set([f for f in by_cat.get("shelter", [])
                                               if f["tags"].get("emergency") == "assembly_point"])
    tagged = json.loads((folder / "tagged_buildings.json").read_text()) \
        if (folder / "tagged_buildings.json").exists() else []
    tall = []
    for b in tagged:
        levels = _num(b.get("levels"))
        height = _num(b.get("height"))
        if (levels and levels >= 3) or (height and height >= 9):
            tall.append({"id": b["osm"], "name": b.get("name"), "lat": b["lat"], "lon": b["lon"],
                         "levels": levels, "height_m": height, "tags": {}})
    features["tall_building_osm"] = _feature_set(tall)
    places = json.loads((folder / "places.json").read_text()) if (folder / "places.json").exists() else []
    features["_places"] = _feature_set(places)
    hexes = json.loads((folder / "hexes.json").read_text()) if (folder / "hexes.json").exists() else {}
    rulebooks = {p.stem: yaml.safe_load(p.read_text()) for p in sorted(RULEBOOKS.glob("*.yaml"))}
    manifests = {}
    for name in ("osm_manifest.json", "gee_manifest.json", "history.json"):
        if (folder / name).exists():
            manifests[name] = json.loads((folder / name).read_text())
    return Snapshot(graph, features, places, hexes, rulebooks, manifests, region or {})


def _num(v) -> float | None:
    if v is None:
        return None
    try:
        return float(str(v).split(";")[0].replace("m", "").strip())
    except ValueError:
        return None
