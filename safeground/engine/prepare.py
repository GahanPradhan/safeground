"""PREPARE: deterministic readiness indicators for an area (the agent's tools call these)."""
from __future__ import annotations

from functools import lru_cache

import h3
import numpy as np

from safeground.config import ROOT
from safeground.engine import data
from safeground.engine.geo import haversine_m
from safeground.engine.routing import router

ACCESS_TARGETS = {
    "hospital": ("hospital_major",),
    "fire_station": ("fire_station",),
    "police": ("police",),
    "underground_shelter": ("metro_underground", "parking_underground", "assembly_point"),
    "open_ground": ("open_ground",),
    "vet": ("vet", "animal_shelter"),
    "flood_refuge": ("tall_building_osm",),
}
DW_CLASSES = ("trees", "water", "built", "grass", "flooded_vegetation", "bare")
COUNT_CATEGORIES = ("hospital", "clinic", "school", "elderly_home", "police", "fire_station", "metro_underground",
                    "parking_underground", "shelter", "open_ground", "vet", "animal_shelter", "zoo", "industrial",
                    "fuel", "water_named")


def area_cells(lat: float, lon: float, radius_m: float = 1500) -> list[str]:
    snap = data.load()
    k = max(1, int(round(radius_m / 300)))
    cells = h3.grid_disk(snap.hex_of(lat, lon), k)
    return [c for c in cells if haversine_m(lat, lon, *h3.cell_to_latlng(c)) <= radius_m + 150]


def resolve_area(name: str, radius_m: float = 1500) -> dict:
    snap = data.load()
    hit = snap.find_place(name)
    if not hit:
        raise ValueError(f"Area '{name}' not found in the OpenStreetMap place list")
    return {"name": hit["name"], "lat": hit["lat"], "lon": hit["lon"], "radius_m": radius_m,
            "match_score": hit.get("match_score"), "cells": area_cells(hit["lat"], hit["lon"], radius_m)}


def _features_in(cat: str, lat: float, lon: float, radius_m: float) -> list[dict]:
    fs = data.load().features.get(cat)
    return [f for _, f in fs.near(lat, lon, radius_m, 100_000)] if fs else []


def area_profile(area: dict) -> dict:
    snap = data.load()
    rows = [snap.hex_props(c) for c in area["cells"]]
    have = [r for r in rows if r]
    out: dict = {"area": area["name"], "centre": [area["lat"], area["lon"]], "radius_m": area["radius_m"],
                 "blocks": len(area["cells"]), "blocks_with_satellite_data": len(have)}
    if have:
        pops = np.array([r.get("pop") or 0 for r in have])
        out["residents_estimate"] = int(pops.sum())
        out["residents_source"] = "WorldPop 2020 (modelled estimate)"
        for cls in DW_CLASSES:
            a = [r.get(f"dw_{cls}_2016") for r in have if r.get(f"dw_{cls}_2016") is not None]
            b = [r.get(f"dw_{cls}_2025") for r in have if r.get(f"dw_{cls}_2025") is not None]
            if a and b:
                out[f"{cls}_share_2016_pct"] = round(100 * float(np.mean(a)), 1)
                out[f"{cls}_share_2025_pct"] = round(100 * float(np.mean(b)), 1)
        rel = [r.get("rel_elev") for r in have if r.get("rel_elev") is not None]
        if rel:
            out["low_lying_blocks_pct"] = round(100 * float(np.mean(np.array(rel) <= -1.5)), 1)
        wn = [r.get("water_near_m") for r in have]
        out["blocks_within_500m_of_water_pct"] = round(100 * float(np.mean([w is not None and w <= 500 for w in wn])), 1)
        h = [r.get("bld_h_p90") for r in have if r.get("bld_h_p90")]
        if h:
            out["typical_tall_building_m"] = round(float(np.median(h)), 1)
        out["protected_area_blocks"] = int(sum(1 for r in have if (r.get("protected") or 0) > 0.5))
    else:
        out["note"] = "Satellite layers not loaded for this area"
    out["counts"] = {c: len(_features_in(c, area["lat"], area["lon"], area["radius_m"])) for c in COUNT_CATEGORIES}
    out["named_water_bodies"] = sorted({f["name"] for f in _features_in("water_named", area["lat"], area["lon"],
                                                                       area["radius_m"] + 1000) if f["name"]})[:10]
    return out


def _distance_field(kind: str) -> np.ndarray:
    return _distance_field_in(kind, data.current_region())


@lru_cache(maxsize=None)
def _distance_field_in(kind: str, region: str) -> np.ndarray:
    snap = data.load()
    sources = [f for c in ACCESS_TARGETS[kind] for f in snap.features.get(c, data._feature_set([])).items]
    return router().distance_field(sources)


def _cell_node(cell: str) -> int:
    return _cell_node_in(cell, data.current_region())


@lru_cache(maxsize=None)
def _cell_node_in(cell: str, region: str) -> int:
    la, lo = h3.cell_to_latlng(cell)
    return router().snap(la, lo)[0]


def access(area: dict, kind: str) -> dict:
    """Walking distance from each block to the nearest target of this kind, weighted by residents."""
    snap = data.load()
    field = _distance_field(kind)
    rows = []
    for c in area["cells"]:
        d = float(field[_cell_node(c)])
        pop = (snap.hex_props(c).get("pop") or 0)
        la, lo = h3.cell_to_latlng(c)
        rows.append((c, d, pop, la, lo))
    pops = np.array([r[2] for r in rows])
    dists = np.array([r[1] for r in rows])
    total = pops.sum()
    w = pops / total if total > 0 else np.full(len(rows), 1 / max(1, len(rows)))
    res = {"kind": kind, "targets": list(ACCESS_TARGETS[kind]), "blocks": len(rows),
           "weighting": "residents (WorldPop 2020)" if total > 0 else "equal per block (no population data)"}
    for lim in (500, 1000, 2000):
        res[f"share_within_{lim}m_pct"] = round(100 * float(w[dists <= lim].sum()), 1)
    finite = dists[np.isfinite(dists)]
    res["median_walk_m"] = round(float(np.median(finite))) if len(finite) else None
    if not len(finite) and data.current_region() != data.DEFAULT_REGION:
        res["note"] = (f"No {kind.replace('_', ' ')} is mapped in OpenStreetMap within the loaded area (3 km around "
                       f"the place); the nearest one may be further away.")
    worst = sorted(rows, key=lambda r: (-(r[1] if np.isfinite(r[1]) else 1e9), -r[2]))[:3]
    unreachable = "over 20 km" if data.current_region() == data.DEFAULT_REGION else \
        "none within the loaded area (3 km around the place); may exist further away"
    res["worst_blocks"] = [{"hex": c, "walk_m": (round(d) if np.isfinite(d) else unreachable), "residents": int(p),
                            "place": snap.place_name(la, lo)} for c, d, p, la, lo in worst]
    return res


def _reported_flood_cells(area_cells: set[str]) -> tuple[list[str], list[dict]]:
    """Blocks within ~500 m of a locality reported underwater (safeground/curated/flood_reports.yaml)."""
    import h3
    import yaml
    reports = yaml.safe_load((ROOT / "safeground" / "curated" / "flood_reports.yaml").read_text())
    cells, used = set(), []
    for rep in reports.values():
        for pt in rep["points"]:
            near = set(h3.grid_disk(h3.latlng_to_cell(pt["lat"], pt["lon"], 9), 2)) & area_cells
            if near:
                cells |= near
                used.append({"locality": pt["name"], "report": rep["label"], "source_url": rep["url"]})
    return sorted(cells), used


def flood_exposure(area: dict) -> dict:
    snap = data.load()
    low = [c for c in area["cells"] if (snap.hex_props(c).get("rel_elev") or 0) <= -1.5]
    reported, reports_used = _reported_flood_cells(set(area["cells"]))
    prone = sorted(set(low) | set(reported))
    refuge_field = _distance_field("flood_refuge")
    no_refuge = []
    for c in prone:
        p = snap.hex_props(c)
        has_multistorey = (p.get("bld_h_p90") or 0) >= 9
        if not has_multistorey and float(refuge_field[_cell_node(c)]) > 300:
            no_refuge.append(c)
    pop = lambda cells: int(sum(snap.hex_props(c).get("pop") or 0 for c in cells))  # noqa: E731
    r = router()
    near = haversine_m(area["lat"], area["lon"], r.mid_lat, r.mid_lon) <= area["radius_m"]
    tunnel = near & ((r.flag & 1) == 1)
    underpasses = sorted({str(r.names[i]) for i in r.name_idx[tunnel] if str(r.names[i])})
    vulnerable = []
    for cat in ("school", "elderly_home", "hospital"):
        for f in _features_in(cat, area["lat"], area["lon"], area["radius_m"]):
            if snap.hex_of(f["lat"], f["lon"]) in set(prone):
                vulnerable.append({"category": cat, "name": f["name"], "lat": f["lat"], "lon": f["lon"]})
    return {"low_lying_blocks": len(low), "residents_in_low_lying_blocks": pop(low),
            "blocks_near_reported_flooding": len(reported), "residents_near_reported_flooding": pop(reported),
            "reported_flooding_used": reports_used,
            "flood_prone_blocks": len(prone), "residents_in_flood_prone_blocks": pop(prone),
            "flood_prone_blocks_without_refuge_within_300m": len(no_refuge),
            "residents_without_refuge_within_300m": pop(no_refuge), "gap_hexes": no_refuge[:40],
            "underpass_segments": int(tunnel.sum()), "underpass_names": underpasses[:10],
            "vulnerable_sites_in_flood_prone_blocks": vulnerable[:15],
            "method": "flood-prone = low-lying block (at least 1.5 m below the median of blocks within ~2 km, "
                      "Copernicus DEM estimate) OR block within ~500 m of a locality reported underwater "
                      "(Sphere India SitRep, 9 Dec 2023); the DEM misses most drain and lake flooding in Chennai. "
                      "Refuge = OSM building with 3+ floors within 300 m walk or block with Open Buildings "
                      "90th-percentile height >= 9 m"}


def industrial_exposure(area: dict, radius_m: float = 4200) -> dict:
    """Industrial / storage sites near the area. 4.2 km = largest ERG ammonia night-time protective distance."""
    snap = data.load()
    sites = []
    fs = snap.features.get("industrial", data._feature_set([]))
    for d, f in fs.near(area["lat"], area["lon"], radius_m, 100_000):  # count every site, not the first N
        sites.append({"name": f["name"], "distance_m": round(d), "lat": f["lat"], "lon": f["lon"],
                      "tags": {k: v for k, v in f["tags"].items() if k in ("landuse", "man_made", "industrial",
                                                                           "product", "substance", "content",
                                                                           "operator", "area_m2")}})
    named = [s for s in sites if s["name"]]
    return {"sites_within_m": radius_m, "site_count": len(sites), "named_sites": named[:12],
            "what_is_stored": "unknown for most sites (rarely mapped)",
            "basis": "4.2 km is the ERG 2024 night-time, low-wind protective distance for a large ammonia release "
                     "(rail tank car) — a worst-case screening radius"}


def nature(area: dict) -> dict:
    prof = area_profile(area)
    keys = [k for k in prof if k.endswith("_pct") and k.split("_share_")[0] in DW_CLASSES]
    change = {}
    for cls in DW_CLASSES:
        a, b = prof.get(f"{cls}_share_2016_pct"), prof.get(f"{cls}_share_2025_pct")
        if a is not None and b is not None:
            change[cls] = {"2016_pct": a, "2025_pct": b, "change_pct_points": round(b - a, 1)}
    return {"land_cover_change": change, "source": "Google Dynamic World V1 (10 m), yearly mode of class",
            "protected_area_blocks": prof.get("protected_area_blocks"),
            "named_water_bodies": prof.get("named_water_bodies"), "_keys": keys}


def animals(area: dict) -> dict:
    out = {}
    for cat in ("vet", "animal_shelter", "zoo"):
        out[cat] = [{"name": f["name"], "lat": f["lat"], "lon": f["lon"]}
                    for f in _features_in(cat, area["lat"], area["lon"], area["radius_m"] + 1500)][:8]
    out["access_to_vet"] = access(area, "vet")
    out["data_gaps"] = ["Stray and pet animal numbers are not mapped.", "Livestock locations in the city are not mapped.",
                        "Animal shelter capacity is not public."]
    return out
