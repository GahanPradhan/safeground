"""Live Google Earth Engine analysis for regions built on demand (the Chennai snapshot is precomputed offline).

Credentials: on Cloud Run the service's own dedicated account (safeground-run); locally only the owner's SafeGround
gcloud login (CLOUDSDK_CONFIG=~/.config/gcloud-cityguard), never a stray service-account key.
"""
from __future__ import annotations

import os
import threading
import time

import h3

from safeground.config import H3_RES

SCOPES = ["https://www.googleapis.com/auth/earthengine", "https://www.googleapis.com/auth/cloud-platform"]
GFD_URL = "https://developers.google.com/earth-engine/datasets/catalog/GLOBAL_FLOOD_DB_MODIS_EVENTS_V1"
CHIRPS_URL = "https://developers.google.com/earth-engine/datasets/catalog/UCSB-CHG_CHIRPS_DAILY"
ERA5_URL = "https://developers.google.com/earth-engine/datasets/catalog/ECMWF_ERA5_LAND_DAILY_AGGR"
FIRMS_URL = "https://developers.google.com/earth-engine/datasets/catalog/FIRMS"
_lock = threading.Lock()
_ready = False


def init():
    """Initialise Earth Engine once per process with the permitted credential only."""
    global _ready
    with _lock:
        if _ready:
            return
        import ee
        import google.auth
        project = os.getenv("SAFEGROUND_EE_PROJECT") or os.getenv("GOOGLE_CLOUD_PROJECT")
        if not project:
            raise RuntimeError("Set GOOGLE_CLOUD_PROJECT for Earth Engine.")
        if os.getenv("K_SERVICE"):  # running on Cloud Run: the service's dedicated account
            creds, _ = google.auth.default(scopes=SCOPES)
        else:
            if not os.getenv("CLOUDSDK_CONFIG", "").endswith("gcloud-cityguard"):
                raise RuntimeError("Set CLOUDSDK_CONFIG=~/.config/gcloud-cityguard so the SafeGround login is used.")
            if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
                raise RuntimeError("GOOGLE_APPLICATION_CREDENTIALS is set; refusing to use another credential.")
            creds, _ = google.auth.default(scopes=SCOPES)
            if getattr(creds, "service_account_email", None):
                raise RuntimeError("A service-account credential was found; SafeGround only uses the owner's login.")
        ee.Initialize(credentials=creds, project=project)
        ee.data.setDeadline(120_000)  # fail a stuck request after 120 s instead of hanging
        _ready = True


def _hex_feature(ee, cell: str):
    ring = [[lng, lat] for lat, lng in h3.cell_to_boundary(cell)]
    ring.append(ring[0])
    return ee.Feature(ee.Geometry.Polygon([ring]), {"h3": cell})


def _image(ee, aoi):
    pop = ee.ImageCollection("WorldPop/GP/100m/pop").filterBounds(aoi).filter(ee.Filter.eq("year", 2020)).mosaic() \
        .rename("pop")
    dem = ee.ImageCollection("COPERNICUS/DEM/GLO30_2024_1").select("DEM").filterBounds(aoi).mosaic() \
        .setDefaultProjection("EPSG:4326", None, 30).rename("elev")
    # relative elevation: block height minus the median height within ~2 km (computed at 90 m to stay fast)
    dem90 = dem.reproject(ee.Projection("EPSG:4326").atScale(90))
    rel = dem90.subtract(dem90.focalMedian(radius=2000, kernelType="circle", units="meters")).rename("rel_elev")
    gsw = ee.Image("JRC/GSW1_4/GlobalSurfaceWater").select("occurrence").unmask(0).rename("water_occ")
    wet = gsw.gte(50).selfMask()
    water_dist = wet.fastDistanceTransform(256).sqrt().multiply(ee.Image.pixelArea().sqrt()).rename("water_near_m")
    ob = ee.ImageCollection("GOOGLE/Research/open-buildings-temporal/v1").filterBounds(aoi)
    if ob.size().getInfo() > 0:  # Open Buildings covers Africa, South/Southeast Asia, Latin America and the Caribbean
        latest = ob.aggregate_max("inference_time_epoch_s")
        obl = ob.filter(ee.Filter.eq("inference_time_epoch_s", latest)).mosaic()
        presence = obl.select("building_presence")
        height = obl.select("building_height").updateMask(presence.gt(0.5))
    else:  # outside coverage: building layers stay empty (OSM building levels are used instead)
        empty = ee.Image.constant(0).updateMask(ee.Image.constant(0))
        presence, height = empty.rename("building_presence"), empty.rename("building_height")

    def dw_year(year: int):
        col = ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1").filterBounds(aoi) \
            .filterDate(f"{year}-01-01", f"{year}-12-31").select("label")
        mode = col.reduce(ee.Reducer.mode())
        classes = {"water": 0, "trees": 1, "grass": 2, "flooded_vegetation": 3, "built": 6, "bare": 7}
        return ee.Image.cat([mode.eq(v).rename(f"dw_{k}_{year}") for k, v in classes.items()])

    wdpa = ee.FeatureCollection("WCMC/WDPA/current/polygons").filterBounds(aoi)
    protected = ee.Image(0).paint(wdpa, 1).rename("protected")
    return pop, ee.Image.cat([dem.rename("elev_mean"), rel, gsw, water_dist, presence.gt(0.5).rename("bld_frac"),
                              height.rename("bld_h_mean"), dw_year(2016), dw_year(2025), protected]), height


def hex_layers(cells: list[str], lat: float, lon: float, radius_m: float) -> dict[str, dict]:
    """Same per-hexagon layers as pipeline/gee_layers.py, for a list of H3 cells."""
    import ee
    init()
    aoi = ee.Geometry.Point([lon, lat]).buffer(radius_m + 2500)
    pop, img, height = _image(ee, aoi)
    out: dict[str, dict] = {}
    for i in range(0, len(cells), 350):
        fc = ee.FeatureCollection([_hex_feature(ee, c) for c in cells[i:i + 350]])
        s = pop.reduceRegions(fc, ee.Reducer.sum().setOutputs(["pop"]), scale=100)
        m = img.reduceRegions(s, ee.Reducer.mean(), scale=30)
        p = height.rename("bld_h_p90").reduceRegions(m, ee.Reducer.percentile([90]).setOutputs(["bld_h_p90"]), scale=10)
        for attempt in range(3):
            try:
                feats = p.getInfo()["features"]
                break
            except Exception:
                if attempt == 2:
                    raise
                time.sleep(3)
        for f in feats:
            props = f["properties"]
            out[props.pop("h3")] = {k: (round(v, 4) if isinstance(v, float) else v) for k, v in props.items()}
    return out


def history(lat: float, lon: float, radius_m: float = 1500) -> tuple[list[dict], list[str]]:
    """Satellite / reanalysis calamity records near a point. Returns (records, notes about failed steps)."""
    import ee
    init()
    pt = ee.Geometry.Point([lon, lat])
    geom = pt.buffer(radius_m)
    records, notes = [], []
    for name, step in (("flood records", lambda: _flood_events(ee, geom)),
                       ("rainfall extremes", lambda: _wettest_days(ee, pt, lat)),
                       ("fire detections", lambda: _fires(ee, geom))):
        try:
            records += step()
        except Exception as e:  # keep the other records
            notes.append(f"{name} unavailable ({type(e).__name__})")
    return records, notes


def _flood_events(ee, geom) -> list[dict]:
    col = ee.ImageCollection("GLOBAL_FLOOD_DB/MODIS_EVENTS/V1").filterBounds(geom)

    def flooded(img):
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


def _wettest_days(ee, pt, lat: float, top: int = 5) -> list[dict]:
    if abs(lat) <= 49.5:  # CHIRPS covers 50S-50N
        col = ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY").filterDate("2001-01-01", "2026-01-01").select("precipitation")
        band, scale, factor, src, label = "precipitation", 5566, 1.0, CHIRPS_URL, "CHIRPS satellite-gauge estimate"
    else:
        col = ee.ImageCollection("ECMWF/ERA5_LAND/DAILY_AGGR").filterDate("2001-01-01", "2026-01-01") \
            .select("total_precipitation_sum")
        band, scale, factor, src, label = "total_precipitation_sum", 11132, 1000.0, ERA5_URL, "ERA5-Land reanalysis"
    series = []
    for y0 in range(2001, 2026, 5):  # 5-year chunks keep each request within Earth Engine's memory limit
        rows = col.filterDate(f"{y0}-01-01", f"{y0 + 5}-01-01").getRegion(pt, scale).getInfo()
        header, values = rows[0], rows[1:]
        ti, pi = header.index("time"), header.index(band)
        series += [(v[ti], v[pi] * factor) for v in values if v[pi] is not None]
    series.sort(key=lambda t: -t[1])
    very_heavy = sum(1 for _, p in series if p >= 115.6)
    out = [{"type": "extreme rainfall", "date": time.strftime("%Y-%m-%d", time.gmtime(t / 1000)),
            "what_happened": f"{p:.0f} mm of rain in one day at this location ({label}).",
            "source_url": src, "url": src, "evidence_kind": "dataset"} for t, p in series[:top]]
    out.append({"type": "extreme rainfall (summary)", "date": "2001-2025",
                "what_happened": f"{very_heavy} days with at least 115.6 mm of rain between 2001 and 2025 ({label}; "
                                 f"115.6 mm is the India Meteorological Department 'very heavy' threshold, used here "
                                 f"as a common marker).", "source_url": src, "url": src, "evidence_kind": "dataset"})
    return out


def _fires(ee, geom) -> list[dict]:
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


def cells_for(lat: float, lon: float, radius_m: float) -> list[str]:
    from safeground.engine.geo import haversine_m
    k = max(1, int(round(radius_m / 300)) + 1)
    return [c for c in h3.grid_disk(h3.latlng_to_cell(lat, lon, H3_RES), k)
            if haversine_m(lat, lon, *h3.cell_to_latlng(c)) <= radius_m + 150]
