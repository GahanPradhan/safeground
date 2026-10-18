"""Build the OpenStreetMap snapshot for Chennai from the Geofabrik extract.

Outputs (data/snapshot/):
  graph.npz        walkable road/footpath graph (largest connected component)
  features.geojson points for hospitals, schools, shelters, metro stations, industry, parks, ...
  places.json      place-name gazetteer (suburbs, neighbourhoods, localities)
  tagged_buildings.json  OSM buildings with height / building:levels (used to check Open Buildings heights)

Run:  .venv/bin/python -m pipeline.fetch_osm [path/to/extract.osm.pbf]
"""
from __future__ import annotations

import json
import os
import sys
import time
from collections import Counter, defaultdict

import numpy as np
import osmium
from pyproj import Transformer
from shapely.geometry import Polygon
from shapely.ops import transform as shp_transform

from safeground.config import BBOX, DATA_RAW, METRIC_CRS, ROOT, SNAPSHOT

PBF_DEFAULT = DATA_RAW / "geofabrik" / "southern-zone-latest.osm.pbf"

from safeground.engine.osm import (HIGHWAY_CODES, INDUSTRIAL_MAN_MADE, KEEP_TAGS, OPEN_LANDUSE,  # noqa: F401
                                 OPEN_LEISURE, PLACE_TYPES, WALKABLE, _feature, build_graph, classify)

_to_metric = Transformer.from_crs("EPSG:4326", METRIC_CRS, always_xy=True).transform


def in_bbox(lat: float, lon: float) -> bool:
    return BBOX["south"] <= lat <= BBOX["north"] and BBOX["west"] <= lon <= BBOX["east"]


def haversine_m(lat1, lon1, lat2, lon2):
    r = 6371008.8
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dphi, dl = p2 - p1, np.radians(np.asarray(lon2) - np.asarray(lon1))
    a = np.sin(dphi / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * r * np.arcsin(np.sqrt(a))


def scan(pbf: str):
    keys = ["highway", "amenity", "leisure", "landuse", "man_made", "industrial", "railway", "station",
            "emergency", "social_facility", "healthcare", "tourism", "place", "natural", "power",
            "building:levels", "height", "public_transport"]
    fp = (osmium.FileProcessor(pbf, osmium.osm.NODE | osmium.osm.WAY)
          .with_locations()
          .with_filter(osmium.filter.EmptyTagFilter())
          .with_filter(osmium.filter.KeyFilter(*keys)))
    roads, features, places, tagged_buildings = [], [], [], []
    n_seen = 0
    for obj in fp:
        n_seen += 1
        tags = dict(obj.tags)
        if obj.is_node():
            lat, lon = obj.location.lat, obj.location.lon
            if not in_bbox(lat, lon):
                continue
            cats = classify(tags)
            if "place" in cats:
                places.append({"name": tags.get("name:en") or tags["name"], "name_local": tags.get("name"),
                               "type": tags["place"], "lat": lat, "lon": lon, "osm": f"n{obj.id}"})
                cats.remove("place")
            if cats:
                features.append(_feature(f"n{obj.id}", cats, tags, lat, lon, None))
            continue
        # ways
        try:
            coords = [(n.lat, n.lon) for n in obj.nodes]
        except osmium.InvalidLocationError:
            continue
        if not coords or not any(in_bbox(la, lo) for la, lo in coords[:: max(1, len(coords) // 8)] + [coords[-1]]):
            continue
        hw = tags.get("highway")
        if hw in WALKABLE and tags.get("foot") != "no" and tags.get("access") not in ("private", "no") \
                and tags.get("area") != "yes":
            roads.append({"id": obj.id, "refs": [n.ref for n in obj.nodes], "coords": coords, "hw": hw,
                          "name": tags.get("name"), "tunnel": tags.get("tunnel") in ("yes", "building_passage")
                          or (tags.get("layer", "0").lstrip("-").isdigit() and int(tags.get("layer", "0")) < 0),
                          "bridge": tags.get("bridge") == "yes"})
        if ("building:levels" in tags or "height" in tags) and "building" in tags:
            la, lo = np.mean([c[0] for c in coords]), np.mean([c[1] for c in coords])
            tagged_buildings.append({"osm": f"w{obj.id}", "lat": float(la), "lon": float(lo),
                                     "levels": tags.get("building:levels"), "height": tags.get("height"),
                                     "name": tags.get("name")})
        cats = classify(tags)
        if "place" in cats:
            cats.remove("place")
        if cats:
            closed = len(coords) >= 4 and coords[0] == coords[-1]
            area = None
            if closed:
                poly = Polygon([(lo, la) for la, lo in coords])
                if poly.is_valid:
                    area = float(shp_transform(_to_metric, poly).area)
                    c = poly.centroid
                    lat, lon = c.y, c.x
                else:
                    lat, lon = np.mean([c[0] for c in coords]), np.mean([c[1] for c in coords])
            else:
                lat, lon = np.mean([c[0] for c in coords]), np.mean([c[1] for c in coords])
            features.append(_feature(f"w{obj.id}", cats, tags, float(lat), float(lon), area))
    print(f"scanned {n_seen:,} tagged objects; roads={len(roads):,} features={len(features):,} "
          f"places={len(places):,} tagged_buildings={len(tagged_buildings):,}")
    return roads, features, places, tagged_buildings


def main(pbf: str):
    t0 = time.time()
    SNAPSHOT.mkdir(parents=True, exist_ok=True)
    roads, features, places, tagged = scan(pbf)
    g = build_graph(roads)
    np.savez_compressed(SNAPSHOT / "graph.npz", **g)
    (SNAPSHOT / "features.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": features}))
    (SNAPSHOT / "places.json").write_text(json.dumps(places, ensure_ascii=False))
    (SNAPSHOT / "tagged_buildings.json").write_text(json.dumps(tagged))
    counts = Counter(c for f in features for c in f["properties"]["categories"])
    manifest = {"source": os.path.relpath(pbf, ROOT), "built_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "bbox": BBOX,
                "graph_nodes": int(len(g["node_lat"])), "graph_edges": int(len(g["edge_u"])),
                "feature_counts": dict(counts), "places": len(places), "tagged_buildings": len(tagged)}
    (SNAPSHOT / "osm_manifest.json").write_text(json.dumps(manifest, indent=2))
    print(json.dumps(manifest, indent=2))
    print(f"done in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else str(PBF_DEFAULT))
