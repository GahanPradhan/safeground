"""SafeGround web API + static frontend."""
from __future__ import annotations

import json
import time
from pathlib import Path

import h3
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from safeground import config
from safeground.engine import data, prepare, regions
from safeground.engine.respond import SITUATIONS, Incident, build_zone, plan_facts

WEB = config.ROOT / "web"
REPORTS = config.ROOT / "data" / "cache" / "reports"
app = FastAPI(title="SafeGround")


@app.on_event("startup")
def _warm() -> None:
    data.load()


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    html = (WEB / "index.html").read_text()
    return html.replace("__MAPS_KEY__", config.MAPS_BROWSER_KEY)


@app.get("/health")
def health() -> dict:
    snap = data.load()
    return {"ok": True, "rulebooks": sorted(snap.rulebooks)}


HAZARD_ORDER = ["flood", "earthquake", "cyclone", "tsunami", "wildfire", "heat", "gas", "explosion", "air_raid"]
GROUPS = {"natural": "Natural hazards", "industrial": "Industrial accidents", "security": "Security threats"}


def _params(rb: dict) -> list[dict]:
    out = []
    for p in rb.get("params", []):
        p = dict(p)
        if p.get("from") == "scenarios":
            p["options"] = [[k, v["label"]] for k, v in rb["zone_model"]["scenarios"].items()]
        out.append(p)
    return out


@app.get("/api/meta")
def meta() -> dict:
    """Hazard catalog: every rulebook with its conditions (params), danger levels and sources."""
    from safeground.engine.respond import NEEDS_INCIDENT
    rb = data.load().rulebooks
    hazards = [{"id": h, "title": rb[h]["title"], "group": rb[h].get("group", "natural"),
                "needs_incident": h in NEEDS_INCIDENT, "params": _params(rb[h]), "tiers": rb[h]["tiers"],
                "sources": rb[h]["sources"], "zone_type": rb[h]["zone_model"]["type"]}
               for h in HAZARD_ORDER if h in rb]
    return {"situations": SITUATIONS, "hazards": hazards, "groups": GROUPS}


@app.get("/api/region/{rid}/overview")
def region_overview(rid: str) -> dict:
    if not regions.exists(rid):
        raise HTTPException(404, "Region not loaded yet")
    from safeground.engine.overview import overview
    return overview(rid)


@app.get("/api/reverse")
def reverse(lat: float, lon: float) -> dict:
    try:
        hit = regions.reverse(lat, lon)
    except Exception as e:
        raise HTTPException(502, f"Place lookup unavailable: {type(e).__name__}")
    return {"place": hit}


LAYER_FIELDS = {"population": "pop", "building_height": "bld_h_p90", "low_lying": "rel_elev", "elevation": "elev_mean",
                "tree_cover": "dw_trees_2025", "tree_change": None, "water_near": "water_near_m"}


@app.get("/api/layers/{name}")
def layer(name: str, region: str | None = None) -> dict:
    if name not in LAYER_FIELDS:
        raise HTTPException(404, "unknown layer")
    with _region(region):
        snap = data.load()
        rows = []
        for cell, p in snap.hexes.items():
            if name == "tree_change":
                a, b = p.get("dw_trees_2016"), p.get("dw_trees_2025")
                v = None if a is None or b is None else round((b - a) * 100, 1)
            elif name == "building_height":
                v = p.get("bld_h_p90") or p.get("bld_h_mean")
            else:
                v = p.get(LAYER_FIELDS[name])
            if v is not None:
                rows.append({"h": cell, "v": v})
    return {"layer": name, "cells": rows}


@app.get("/api/features/{category}")
def features(category: str, region: str | None = None) -> dict:
    with _region(region):
        fs = data.load().features.get(category)
    if fs is None:
        raise HTTPException(404, "unknown category")
    return {"category": category, "items": [{"name": f["name"], "lat": f["lat"], "lon": f["lon"]} for f in fs.items]}


class RespondIn(BaseModel):
    hazard: str
    lat: float
    lon: float
    situation: str = "home_ground"
    incident_lat: float | None = None
    incident_lon: float | None = None
    params: dict = {}
    use_ai: bool = True
    region: str | None = None


@app.post("/api/zone")
def zone(body: RespondIn) -> dict:
    inc = Incident(body.hazard, body.incident_lat, body.incident_lon, body.params)
    with _region(body.region):
        z = build_zone(inc)
    if z is None:
        return {"type": "citywide"}
    if z.hex_tiers:
        return {"type": "hex", "cells": [{"h": c, "t": t} for c, t in z.hex_tiers.items() if t != "green"],
                "basis": z.basis}
    return {"type": "polygons", "geojson": z.geojson(), "basis": z.basis}


@app.post("/api/respond")
def respond(body: RespondIn) -> dict:
    if body.situation not in SITUATIONS:
        raise HTTPException(400, "unknown situation")
    t0 = time.time()
    if body.region and not regions.inside(body.region, body.lat, body.lon):
        raise HTTPException(400, "This spot is outside the loaded area. Search for the place to load it first.")
    inc = Incident(body.hazard, body.incident_lat, body.incident_lon, body.params)
    with _region(body.region):
        facts = plan_facts(inc, body.lat, body.lon, body.situation)
        out = {"facts": facts}
        if body.use_ai:
            from safeground.agents import safety_planner
            out.update(safety_planner.plan(facts))
        else:
            from safeground.agents.safety_planner import template_plan
            out.update({"plan": template_plan(facts).model_dump(), "generated_by": "template"})
    out["latency_s"] = round(time.time() - t0, 2)
    return out


@app.get("/api/prepare/{area}")
def prepare_area(area: str, fresh: bool = False, region: str | None = None) -> dict:
    REPORTS.mkdir(parents=True, exist_ok=True)
    key = region or area.lower().replace(' ', '_').replace('.', '')
    path = REPORTS / f"{key}.json"
    if path.exists() and not fresh:
        return json.loads(path.read_text())
    from safeground.agents import readiness_analyst
    try:
        with _region(region):
            res = readiness_analyst.analyse(area, region=region)
    except ValueError as e:
        raise HTTPException(404, str(e))
    res["generated_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    path.write_text(json.dumps(res, default=str))
    return res


@app.get("/api/area/{area}/indicators")
def area_indicators(area: str, region: str | None = None) -> dict:
    with _region(region):
        a = regions.area_for(region) if region else prepare.resolve_area(area)
        return {"area": {k: v for k, v in a.items() if k != "cells"}, "cells": a["cells"],
                "profile": prepare.area_profile(a), "flood": prepare.flood_exposure(a),
                "hospital_access": prepare.access(a, "hospital"),
                "shelter_access": prepare.access(a, "underground_shelter")}


@app.get("/api/hex/{cell}")
def hex_info(cell: str, region: str | None = None) -> dict:
    with _region(region):
        snap = data.load()
        la, lo = h3.cell_to_latlng(cell)
        return {"hex": cell, "lat": la, "lon": lo, "place": snap.place_name(la, lo), "props": snap.hex_props(cell)}


# ------------------------------------------------------------------------------------------------ global regions
def _region(region: str | None):
    if region and not regions.exists(region):
        raise HTTPException(404, "Region not loaded yet")
    return data.use_region(region)


@app.get("/api/geocode")
def geocode(q: str) -> dict:
    if len(q.strip()) < 2:
        return {"results": []}
    try:
        return {"results": regions.geocode(q.strip())}
    except Exception as e:
        raise HTTPException(502, f"Place search unavailable: {type(e).__name__}")


class RegionIn(BaseModel):
    lat: float
    lon: float
    name: str
    country: str | None = None
    country_code: str | None = None
    admin: str | None = None


@app.post("/api/region")
def build_region(body: RegionIn) -> dict:
    """Builds the region synchronously (about 1-2 minutes the first time); poll /api/region/{id} for progress."""
    try:
        return regions.build(body.lat, body.lon, body.name, body.country, body.country_code, admin=body.admin)
    except Exception as e:
        raise HTTPException(502, f"Could not load this place: {str(e)[:240]}")


@app.get("/api/region/{rid}")
def region_status(rid: str) -> dict:
    return regions.status(rid)


@app.get("/api/regions")
def list_regions() -> dict:
    return {"regions": [{k: r.get(k) for k in ("id", "name", "country", "country_code", "lat", "lon")}
                        for r in regions.list_regions()]}


if WEB.exists():
    app.mount("/static", StaticFiles(directory=WEB), name="static")
