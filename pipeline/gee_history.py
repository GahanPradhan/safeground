"""Dataset-based calamity history for the showcase areas (Earth Engine).

For each area (1.5 km radius) this records:
  - flood events from the Global Flood Database (MODIS, 2000-2018) with flooded pixels in the area
  - the wettest days 2001-2025 from CHIRPS daily rainfall, and the count of days >= 115.6 mm (IMD "very heavy")
  - satellite fire detections (FIRMS, MODIS) per year

Output: data/snapshot/history.json  {area_name: [calamity records]}
Run:    .venv/bin/python -m pipeline.gee_history --project YOUR_GCP_PROJECT
"""
from __future__ import annotations

import argparse
import json
import time

import ee

from pipeline.ee_auth import init_ee

from safeground.config import SHOWCASE_AREAS, SNAPSHOT
from safeground.engine import data

GFD_URL = "https://developers.google.com/earth-engine/datasets/catalog/GLOBAL_FLOOD_DB_MODIS_EVENTS_V1"
CHIRPS_URL = "https://developers.google.com/earth-engine/datasets/catalog/UCSB-CHG_CHIRPS_DAILY"
FIRMS_URL = "https://developers.google.com/earth-engine/datasets/catalog/FIRMS"


def flood_events(geom: ee.Geometry) -> list[dict]:
    col = ee.ImageCollection("GLOBAL_FLOOD_DB/MODIS_EVENTS/V1").filterBounds(geom)

    def flooded(img):
        # flood water only: drop permanent water (rivers, creeks, lakes) using the dataset's own JRC mask
        water = img.select("flooded").updateMask(img.select("jrc_perm_water").eq(0))
        n = water.reduceRegion(ee.Reducer.sum(), geom, 250).get("flooded")
        return ee.Feature(None, {"id": img.get("id"), "began": img.date().format("YYYY-MM-dd"),
                                 "ended": ee.Date(img.get("system:time_end")).format("YYYY-MM-dd"),
                                 "cause": img.get("dfo_main_cause"), "dead": img.get("dfo_dead"),
                                 "displaced": img.get("dfo_displaced"), "pixels": n})

    feats = ee.FeatureCollection(col.map(flooded)).filter(ee.Filter.gte("pixels", 2)).getInfo()["features"]
    out = []
    for f in sorted(feats, key=lambda f: f["properties"]["began"]):
        p = f["properties"]
        out.append({"type": "flood", "date": p["began"],
                    "what_happened": f"Satellite (MODIS) saw flood water on about {round(p['pixels'])} pixels of 250 m "
                                     f"(not counting permanent water) in this area during Global Flood Database event "
                                     f"{p.get('id')} ({p['began']} to {p['ended']}; main cause: {p.get('cause')}; "
                                     f"reported deaths {p.get('dead')}, displaced {p.get('displaced')} for the whole event).",
                    "source_url": GFD_URL, "url": GFD_URL, "evidence_kind": "dataset"})
    return out


def wettest_days(point: ee.Geometry, top: int = 5) -> list[dict]:
    col = ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY").filterDate("2001-01-01", "2026-01-01").select("precipitation")
    rows = col.getRegion(point, 5566).getInfo()
    header, values = rows[0], rows[1:]
    ti, pi = header.index("time"), header.index("precipitation")
    series = [(v[ti], v[pi]) for v in values if v[pi] is not None]
    series.sort(key=lambda t: -t[1])
    very_heavy = sum(1 for _, p in series if p >= 115.6)
    out = []
    for t, p in series[:top]:
        day = time.strftime("%Y-%m-%d", time.gmtime(t / 1000))
        out.append({"type": "extreme rainfall", "date": day,
                    "what_happened": f"{p:.0f} mm of rain in one day at this location (CHIRPS satellite-gauge estimate).",
                    "source_url": CHIRPS_URL, "url": CHIRPS_URL, "evidence_kind": "dataset"})
    out.append({"type": "extreme rainfall (summary)", "date": "2001-2025",
                "what_happened": f"{very_heavy} days with at least 115.6 mm of rain (IMD 'very heavy' threshold) "
                                 f"between 2001 and 2025 (CHIRPS).",
                "source_url": CHIRPS_URL, "url": CHIRPS_URL, "evidence_kind": "dataset"})
    return out


def fires(geom: ee.Geometry) -> list[dict]:
    col = ee.ImageCollection("FIRMS").filterBounds(geom).filterDate("2001-01-01", "2026-01-01").select("T21")

    def count(img):
        n = img.mask().reduceRegion(ee.Reducer.sum(), geom, 1000).get("T21")
        return ee.Feature(None, {"date": img.date().format("YYYY-MM-dd"), "n": n})

    feats = ee.FeatureCollection(col.map(count)).filter(ee.Filter.gt("n", 0)).getInfo()["features"]
    days = sorted({f["properties"]["date"] for f in feats})
    if not days:
        return []
    by_year: dict[str, int] = {}
    for d in days:
        by_year[d[:4]] = by_year.get(d[:4], 0) + 1
    return [{"type": "fire (satellite detection)", "date": f"{days[0][:4]}-{days[-1][:4]}",
             "what_happened": f"Satellite fire detections on {len(days)} days (by year: {by_year}); in a city these are "
                              f"often industrial flares or waste burning, not wildfires (FIRMS, 1 km).",
             "source_url": FIRMS_URL, "url": FIRMS_URL, "evidence_kind": "dataset"}]


def main(project: str) -> None:
    init_ee(project)
    snap = data.load()
    out: dict = {}
    for label, (lat, lon) in SHOWCASE_AREAS.items():
        hit = snap.find_place(label)
        name = hit["name"] if hit else label
        lat, lon = (hit["lat"], hit["lon"]) if hit else (lat, lon)
        pt = ee.Geometry.Point([lon, lat])
        geom = pt.buffer(1500)
        t0 = time.time()
        records = []
        for step in (lambda: flood_events(geom), lambda: wettest_days(pt), lambda: fires(geom)):
            for attempt in range(2):
                try:
                    records += step()
                    break
                except Exception as e:  # EE error or request timeout: keep the other records
                    print(f"  {name}: step failed (attempt {attempt + 1}): {str(e)[:120]}", flush=True)
        out[name] = records
        print(f"{name}: {len(records)} records ({time.time() - t0:.0f}s)", flush=True)
        (SNAPSHOT / "history.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    main(ap.parse_args().project)
