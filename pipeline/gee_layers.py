"""Compute per-hexagon layers for Chennai with Google Earth Engine.

For every H3 res-9 hexagon in the study area this computes:
  pop               residents (WorldPop 2020, sum)
  elev_mean         mean surface elevation, m (Copernicus GLO-30)
  rel_elev          hex elevation minus the median hex elevation within ~2 km (negative = lower than surroundings),
                    computed locally from elev_mean after download
  water_occ         mean surface-water occurrence %, 0-100 (JRC GSW 1.4) within the hex
  water_near_m      distance from hex centre to frequently-wet pixels (occurrence >= 50 %), m (capped 3000)
  bld_frac          fraction of area covered by buildings (Open Buildings 2.5D Temporal, latest year)
  bld_h_mean / bld_h_p90   building height mean / 90th percentile in m (built pixels only)
  dw_<class>_<year> Dynamic World share of trees / water / built / grass / flooded_vegetation / bare, for 2016 and 2025
  protected         1 if the hex centre lies in a WDPA protected area

Output: data/snapshot/hexes.json  (list of dicts keyed by H3 id) + gee_manifest.json

Run:  .venv/bin/python -m pipeline.gee_layers --project YOUR_GCP_PROJECT
"""
from __future__ import annotations

import argparse
import json
import time

import ee

from pipeline.ee_auth import init_ee
import h3

from safeground.config import BBOX, H3_RES, SNAPSHOT

BATCH = 400  # hexes per getInfo call (keeps each request well under the 5-minute limit)


def hex_cells() -> list[str]:
    poly = h3.LatLngPoly([(BBOX["south"], BBOX["west"]), (BBOX["south"], BBOX["east"]),
                          (BBOX["north"], BBOX["east"]), (BBOX["north"], BBOX["west"])])
    return sorted(h3.polygon_to_cells(poly, H3_RES))


def hex_feature(cell: str) -> ee.Feature:
    ring = [[lng, lat] for lat, lng in h3.cell_to_boundary(cell)]
    ring.append(ring[0])
    return ee.Feature(ee.Geometry.Polygon([ring]), {"h3": cell})


def build_image(aoi: ee.Geometry) -> ee.Image:
    pop = ee.ImageCollection("WorldPop/GP/100m/pop").filter(ee.Filter.eq("country", "IND")) \
        .filter(ee.Filter.eq("year", 2020)).mosaic().rename("pop")
    dem = ee.ImageCollection("COPERNICUS/DEM/GLO30_2024_1").select("DEM").filterBounds(aoi).mosaic() \
        .setDefaultProjection("EPSG:4326", None, 30).rename("elev")
    gsw = ee.Image("JRC/GSW1_4/GlobalSurfaceWater").select("occurrence").unmask(0).rename("water_occ")
    wet = gsw.gte(50).selfMask()
    water_dist = wet.fastDistanceTransform(256).sqrt().multiply(ee.Image.pixelArea().sqrt()) \
        .rename("water_near_m")
    ob = ee.ImageCollection("GOOGLE/Research/open-buildings-temporal/v1").filterBounds(aoi)
    latest_year = ob.aggregate_max("inference_time_epoch_s")
    ob_latest = ob.filter(ee.Filter.eq("inference_time_epoch_s", latest_year)).mosaic()
    presence = ob_latest.select("building_presence")
    height = ob_latest.select("building_height").updateMask(presence.gt(0.5))
    bld_frac = presence.gt(0.5).rename("bld_frac")

    def dw_year(year: int) -> ee.Image:
        col = ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1").filterBounds(aoi) \
            .filterDate(f"{year}-01-01", f"{year}-12-31").select("label")
        mode = col.reduce(ee.Reducer.mode())
        classes = {"water": 0, "trees": 1, "grass": 2, "flooded_vegetation": 3, "built": 6, "bare": 7}
        return ee.Image.cat([mode.eq(v).rename(f"dw_{k}_{year}") for k, v in classes.items()])

    wdpa = ee.FeatureCollection("WCMC/WDPA/current/polygons").filterBounds(aoi)
    protected = ee.Image(0).paint(wdpa, 1).rename("protected")

    return ee.Image.cat([
        pop, dem.rename("elev_mean"), gsw, water_dist,
        bld_frac, height.rename("bld_h_mean"), height.rename("bld_h_p90"),
        dw_year(2016), dw_year(2025), protected,
    ])


def add_relative_elevation(results: dict[str, dict], k: int = 7) -> None:
    """rel_elev = hex elevation minus median elevation of hexes within k rings (~2 km at res 9)."""
    import statistics
    for cell, row in results.items():
        e = row.get("elev_mean")
        if e is None:
            row["rel_elev"] = None
            continue
        ring = [results[c]["elev_mean"] for c in h3.grid_disk(cell, k)
                if c in results and results[c].get("elev_mean") is not None]
        row["rel_elev"] = round(e - statistics.median(ring), 2) if ring else None


def main(project: str) -> None:
    init_ee(project)
    cells = hex_cells()
    print(f"{len(cells):,} hexagons at res {H3_RES}")
    aoi = ee.Geometry.Rectangle([BBOX["west"], BBOX["south"], BBOX["east"], BBOX["north"]])
    img = build_image(aoi)
    sum_bands = ["pop"]
    mean_bands = [b for b in img.bandNames().getInfo() if b not in ("pop", "bld_h_p90")]
    reducer_mean = ee.Reducer.mean()
    results: dict[str, dict] = {}
    t0 = time.time()
    for i in range(0, len(cells), BATCH):
        fc = ee.FeatureCollection([hex_feature(c) for c in cells[i:i + BATCH]])
        s = img.select(sum_bands).reduceRegions(fc, ee.Reducer.sum().setOutputs(["pop"]), scale=100)
        m = img.select(mean_bands).reduceRegions(s, reducer_mean, scale=30)
        p = img.select(["bld_h_p90"]).reduceRegions(m, ee.Reducer.percentile([90]).setOutputs(["bld_h_p90"]), scale=10)
        for attempt in range(3):
            try:
                feats = p.getInfo()["features"]
                break
            except Exception as e:  # EE error or request timeout
                print(f"  batch {i // BATCH + 1} attempt {attempt + 1} failed: {e}")
                time.sleep(5)
        else:
            raise RuntimeError(f"batch starting at {i} failed 3 times")
        for f in feats:
            props = f["properties"]
            results[props.pop("h3")] = {k: (round(v, 4) if isinstance(v, float) else v) for k, v in props.items()}
        print(f"  batch {i // BATCH + 1}: {len(results):,} done ({time.time() - t0:.0f}s)")
    add_relative_elevation(results)
    SNAPSHOT.mkdir(parents=True, exist_ok=True)
    (SNAPSHOT / "hexes.json").write_text(json.dumps(results))
    manifest = {"built_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "project": project, "h3_res": H3_RES,
                "hexes": len(results), "bands": sorted({k for v in results.values() for k in v})}
    (SNAPSHOT / "gee_manifest.json").write_text(json.dumps(manifest, indent=2))
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    main(ap.parse_args().project)
