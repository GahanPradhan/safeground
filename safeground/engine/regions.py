"""Regions built on demand for any place on Earth: OpenStreetMap (Overpass) + Earth Engine + open hazard APIs.

A region is a circle (default 3 km) around a chosen point, stored under data/cache/regions/<id>/ with the same files
as the Chennai snapshot, so the engine, agents and validators work unchanged.
"""
from __future__ import annotations

import json
import threading
import time

import httpx
import numpy as np

from safeground.config import ROOT
from safeground.engine import data, earth, emergency, hazard_history, vtiles
from safeground.engine.geo import haversine_m, set_reference_latitude, to_xy
from safeground.engine.osm import WALKABLE, _feature, build_graph, classify

REGIONS = ROOT / "data" / "cache" / "regions"
OVERPASS = ["https://overpass-api.de/api/interpreter", "https://overpass.private.coffee/api/interpreter",
            "https://maps.mail.ru/osm/tools/overpass/api/interpreter"]
UA = {"User-Agent": "SafeGround/1.0 (disaster readiness prototype; Google Cloud AI Builder Cup)"}
DEFAULT_RADIUS_M = 3000
_snaps: dict[str, data.Snapshot] = {}
_building: dict[str, threading.Lock] = {}
_status: dict[str, dict] = {}


def region_id(lat: float, lon: float, radius_m: float = DEFAULT_RADIUS_M) -> str:
    return f"r{lat:+.3f}{lon:+.3f}_{int(radius_m)}".replace("+", "p").replace("-", "m").replace(".", "")


def meta(rid: str) -> dict:
    return json.loads((REGIONS / rid / "region.json").read_text())


def exists(rid: str) -> bool:
    return (REGIONS / rid / "region.json").exists()


def status(rid: str) -> dict:
    if exists(rid):
        return {"state": "ready", **meta(rid)}
    return _status.get(rid, {"state": "unknown"})


def snapshot(rid: str) -> data.Snapshot:
    if rid not in _snaps:
        if not exists(rid):
            raise KeyError(f"Region {rid} has not been built")
        _snaps[rid] = data.build_snapshot(REGIONS / rid, curated_metro=False, region=meta(rid))
    return _snaps[rid]


def list_regions() -> list[dict]:
    return [json.loads(p.read_text()) for p in sorted(REGIONS.glob("*/region.json"))] if REGIONS.exists() else []


# ------------------------------------------------------------------------------------------------ build
def build(lat: float, lon: float, name: str, country: str | None, country_code: str | None,
          radius_m: float = DEFAULT_RADIUS_M, admin: str | None = None) -> dict:
    """Build (or return) a region. Safe to call concurrently: one build per region id."""
    rid = region_id(lat, lon, radius_m)
    if exists(rid):
        return meta(rid)
    lock = _building.setdefault(rid, threading.Lock())
    with lock:
        if exists(rid):
            return meta(rid)
        t0 = time.time()
        folder = REGIONS / rid
        folder.mkdir(parents=True, exist_ok=True)
        tok = set_reference_latitude(lat)
        try:
            _step(rid, "Fetching roads and facilities from OpenStreetMap")
            try:
                osm = _overpass(lat, lon, radius_m, quick=True)
                roads, feats, places, tagged = _parse(osm, lat, lon, radius_m)
                source, osm_ts = "OpenStreetMap via the Overpass API", osm.get("osm3s", {}).get("timestamp_osm_base")
            except Exception:  # Overpass busy: the same OpenStreetMap data from OpenFreeMap vector tiles
                tiles = vtiles.fetch(lat, lon, radius_m + 300)
                roads, feats, places, tagged = vtiles.parse(tiles, lat, lon, radius_m)
                source, osm_ts = vtiles.ATTRIBUTION, None
            if len(roads) < 20:
                raise RuntimeError("Too few mapped roads here (OpenStreetMap) to plan routes.")
            graph = build_graph(roads)
            np.savez_compressed(folder / "graph.npz", **graph)
            (folder / "features.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": feats}))
            (folder / "places.json").write_text(json.dumps(places))
            (folder / "tagged_buildings.json").write_text(json.dumps(tagged))
            _step(rid, "Measuring population, buildings, land and water with Google Earth Engine")
            cells = earth.cells_for(lat, lon, radius_m)
            gee_note = None
            try:
                hexes = earth.hex_layers(cells, lat, lon, radius_m)
            except Exception as e:  # keep the region usable without satellite layers
                hexes, gee_note = {}, f"Earth Engine layers unavailable ({type(e).__name__}: {str(e)[:120]})"
            (folder / "hexes.json").write_text(json.dumps(hexes))
            _step(rid, "Collecting past disasters (Earth Engine, USGS, GDACS)")
            hist, notes = [], []
            try:
                h, n = earth.history(lat, lon, 1500)
                hist += h
                notes += n
            except Exception as e:
                notes.append(f"Earth Engine history unavailable ({type(e).__name__})")
            for label, fn in (("USGS earthquakes", lambda: hazard_history.earthquakes(lat, lon)),
                              ("GDACS alerts", lambda: hazard_history.gdacs_events(lat, lon, country))):
                try:
                    hist += fn()
                except Exception as e:
                    notes.append(f"{label} unavailable ({type(e).__name__})")
            (folder / "history.json").write_text(json.dumps(hist, indent=1))
            m = {"id": rid, "name": name, "admin": admin, "country": country, "country_code": (country_code or "").upper() or None,
                 "lat": lat, "lon": lon, "radius_m": radius_m, "built_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                 "build_seconds": round(time.time() - t0, 1), "roads": len(roads), "graph_nodes": int(len(graph["node_lat"])),
                 "features": len(feats), "blocks": len(cells), "blocks_with_satellite_data": len(hexes),
                 "history_records": len(hist), "notes": [x for x in [gee_note, *notes] if x],
                 "emergency": emergency.numbers(country_code),
                 "map_data_source": source, "osm_timestamp": osm_ts}
            (folder / "region.json").write_text(json.dumps(m, indent=1))  # written last: marks the region ready
            _status.pop(rid, None)
            return m
        except Exception as e:
            _status[rid] = {"state": "error", "error": f"{type(e).__name__}: {str(e)[:200]}"}
            raise
        finally:
            from safeground.engine import geo
            geo._LAT0.reset(tok)


def _step(rid: str, text: str) -> None:
    _status[rid] = {"state": "building", "step": text}


def _overpass(lat: float, lon: float, radius_m: float, quick: bool = False) -> dict:
    hw = "|".join(sorted(WALKABLE - {"service", "track"}))
    r, r2 = int(radius_m + 300), int(radius_m * 3)
    q = f"""[out:json][timeout:120];
(way["highway"~"^({hw})$"](around:{r},{lat},{lon}););
out body geom;
(nwr["amenity"~"^(hospital|clinic|doctors|school|college|university|kindergarten|police|fire_station|veterinary|animal_shelter|shelter|parking|fuel|social_facility|nursing_home|community_centre)$"](around:{r},{lat},{lon});
 nwr["healthcare"~"^(hospital|clinic|centre)$"](around:{r},{lat},{lon});
 nwr["emergency"="assembly_point"](around:{r},{lat},{lon});
 nwr["railway"~"^(station|halt|subway_entrance)$"](around:{r},{lat},{lon});
 nwr["public_transport"="station"](around:{r},{lat},{lon});
 nwr["landuse"~"^(industrial|recreation_ground|grass|meadow|village_green)$"](around:{r},{lat},{lon});
 nwr["man_made"~"^(works|storage_tank|gasometer|silo)$"](around:{r},{lat},{lon});
 nwr["power"="plant"](around:{r},{lat},{lon});
 nwr["leisure"~"^(park|pitch|playground|stadium|recreation_ground|garden|common)$"](around:{r},{lat},{lon});
 nwr["tourism"="zoo"](around:{r},{lat},{lon});
 nwr["natural"~"^(water|wetland)$"]["name"](around:{r},{lat},{lon});
 node["place"~"^(city|town|suburb|neighbourhood|quarter|locality|village|hamlet)$"](around:{r2},{lat},{lon});
);
out tags center 6000;
way["building"]["building:levels"~"^([3-9]|[1-9][0-9])"](around:{r},{lat},{lon});
out tags center 4000;"""
    last = None
    # the main server asks clients to back off when busy; then try the mirrors once each
    plan = [(OVERPASS[0], 0)] if quick else \
        [(OVERPASS[0], 0), (OVERPASS[0], 6), (OVERPASS[0], 15), (OVERPASS[0], 30)] + [(u, 0) for u in OVERPASS[1:]]
    for url, wait in plan:
        time.sleep(wait)
        try:
            resp = httpx.post(url, data={"data": q}, headers=UA, timeout=60 if quick else 150)
            if resp.status_code == 200 and resp.text.lstrip().startswith("{"):
                return resp.json()
            last = f"HTTP {resp.status_code} from {url.split('/')[2]}"
        except Exception as e:
            last = f"{type(e).__name__} from {url.split('/')[2]}"
    raise RuntimeError(f"The OpenStreetMap server is busy right now ({last}). Try again in a few minutes, "
                       f"or open one of the ready places.")


def _parse(osm: dict, lat0: float, lon0: float, radius_m: float):
    roads, feats, places, tagged = [], [], [], []
    seen = set()
    for el in osm.get("elements", []):
        tags = el.get("tags", {})
        key = (el["type"], el["id"])
        if el["type"] == "way" and "geometry" in el and tags.get("highway") in WALKABLE:
            if tags.get("foot") == "no" or tags.get("access") in ("private", "no") or tags.get("area") == "yes":
                continue
            coords = [(g["lat"], g["lon"]) for g in el["geometry"]]
            refs = el.get("nodes") or []
            if len(coords) < 2 or len(refs) != len(coords):
                continue
            layer = tags.get("layer", "0")
            roads.append({"id": el["id"], "refs": refs, "coords": coords, "hw": tags["highway"], "name": tags.get("name"),
                          "tunnel": tags.get("tunnel") in ("yes", "building_passage")
                          or (layer.lstrip("-").isdigit() and int(layer) < 0), "bridge": tags.get("bridge") == "yes"})
            continue
        if key in seen:
            continue
        seen.add(key)
        if el["type"] == "node":
            la, lo = el["lat"], el["lon"]
        elif "center" in el:
            la, lo = el["center"]["lat"], el["center"]["lon"]
        else:
            continue
        if "building" in tags and "building:levels" in tags and not classify(tags):
            tagged.append({"osm": f"w{el['id']}", "lat": la, "lon": lo, "levels": tags.get("building:levels"),
                           "height": tags.get("height"), "name": tags.get("name")})
            continue
        cats = classify(tags)
        if "place" in cats:
            places.append({"name": tags.get("name:en") or tags["name"], "name_local": tags.get("name"),
                           "type": tags["place"], "lat": la, "lon": lo, "osm": f"{el['type'][0]}{el['id']}"})
            cats.remove("place")
        if cats:
            area = _area_m2(el.get("bounds")) if el["type"] != "node" else None
            feats.append(_feature(f"{el['type'][0]}{el['id']}", cats, tags, float(la), float(lo), area))
    return roads, feats, places, tagged


def _area_m2(bounds: dict | None) -> float | None:
    """Rough footprint from the bounding box (Overpass 'center' output has no full geometry)."""
    if not bounds:
        return None
    x1, y1 = to_xy(bounds["minlat"], bounds["minlon"])
    x2, y2 = to_xy(bounds["maxlat"], bounds["maxlon"])
    return float(abs(x2 - x1) * abs(y2 - y1) * 0.6)  # 0.6: typical fill of a bounding box


def geocode(q: str, limit: int = 6) -> list[dict]:
    r = httpx.get("https://photon.komoot.io/api/", params={"q": q, "limit": limit, "lang": "en"}, headers=UA, timeout=15)
    r.raise_for_status()
    return _photon(r.json())


def reverse(lat: float, lon: float) -> dict | None:
    """Name of the place at a map point (Photon reverse geocoding); the region centre stays at the clicked point."""
    r = httpx.get("https://photon.komoot.io/reverse", params={"lat": lat, "lon": lon, "lang": "en", "limit": 1},
                  headers=UA, timeout=15)
    r.raise_for_status()
    js = r.json()
    for f in js.get("features", []):  # name the area, not the nearest shop or street
        p = f["properties"]
        if p.get("osm_key") not in ("place", "boundary"):
            p["name"] = p.get("district") or p.get("locality") or p.get("city") or p.get("county") or p.get("name")
    hits = _photon(js)
    if not hits:
        return None
    h = hits[0]
    return {**h, "lat": lat, "lon": lon, "region_id": region_id(lat, lon)}


def _photon(js: dict) -> list[dict]:
    out = []
    for f in js.get("features", []):
        p, (lo, la) = f["properties"], f["geometry"]["coordinates"]
        if not p.get("name"):
            p["name"] = p.get("district") or p.get("locality") or p.get("city") or p.get("county") or p.get("state")
        parts = [p.get("name"), p.get("district") or p.get("city"), p.get("state"), p.get("country")]
        label = ", ".join(dict.fromkeys(x for x in parts if x))
        out.append({"name": p.get("name"), "label": label, "lat": la, "lon": lo, "admin": p.get("state"),
                    "country": p.get("country"), "country_code": (p.get("countrycode") or "").upper(),
                    "type": p.get("osm_value"), "region_id": region_id(la, lo)})
    return out


def area_for(rid: str, radius_m: float = 1500) -> dict:
    """PREPARE area for a region: the centre circle used by the readiness analyst."""
    m = meta(rid)
    return {"name": m["name"], "lat": m["lat"], "lon": m["lon"], "radius_m": radius_m, "match_score": 100.0,
            "cells": earth.cells_for(m["lat"], m["lon"], radius_m), "region": rid, "country": m.get("country")}


def inside(rid: str, lat: float, lon: float) -> bool:
    m = meta(rid)
    return haversine_m(m["lat"], m["lon"], lat, lon) <= m["radius_m"]

