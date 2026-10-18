"""OpenStreetMap helpers shared by the offline pipeline and the live region builder (no GDAL / osmium needed)."""
from __future__ import annotations

from collections import Counter

import numpy as np

from safeground.engine.geo import haversine_m

WALKABLE = {
    "trunk", "trunk_link", "primary", "primary_link", "secondary", "secondary_link",
    "tertiary", "tertiary_link", "unclassified", "residential", "living_street", "service",
    "pedestrian", "footway", "path", "steps", "track", "cycleway", "road", "corridor",
}
HIGHWAY_CODES = {h: i for i, h in enumerate(sorted(WALKABLE))}
PLACE_TYPES = {"city", "town", "suburb", "neighbourhood", "quarter", "locality", "village", "hamlet"}
OPEN_LEISURE = {"park", "pitch", "playground", "stadium", "recreation_ground", "garden", "common"}
OPEN_LANDUSE = {"recreation_ground", "grass", "meadow", "village_green"}
INDUSTRIAL_MAN_MADE = {"works", "storage_tank", "petroleum_well", "gasometer", "silo"}

def classify(tags: dict) -> list[str]:
    """Map OSM tags to SafeGround feature categories (an object may have several)."""
    a = tags.get("amenity")
    cats: list[str] = []
    if a == "hospital" or tags.get("healthcare") == "hospital":
        cats.append("hospital")
    elif a in ("clinic", "doctors") or tags.get("healthcare") in ("clinic", "centre"):
        cats.append("clinic")
    if a in ("school", "college", "university", "kindergarten"):
        cats.append("school")
    if (a == "social_facility" and tags.get("social_facility") in ("nursing_home", "assisted_living", "group_home")) \
            or a == "nursing_home" or tags.get("social_facility:for") in ("senior", "elderly"):
        cats.append("elderly_home")
    for key, cat in (("police", "police"), ("fire_station", "fire_station"), ("veterinary", "vet"),
                     ("animal_shelter", "animal_shelter"), ("fuel", "fuel"), ("community_centre", "community_centre"),
                     ("place_of_worship", "place_of_worship")):
        if a == key:
            cats.append(cat)
    if tags.get("tourism") == "zoo":
        cats.append("zoo")
    if a == "shelter" or tags.get("emergency") == "assembly_point" or tags.get("social_facility") == "shelter":
        cats.append("shelter")
    if a == "parking" and tags.get("parking") in ("underground", "multi-storey"):
        cats.append("parking_underground" if tags.get("parking") == "underground" else "parking_multistorey")
    rw = tags.get("railway")
    if rw in ("station", "halt") or tags.get("public_transport") == "station":
        name = (tags.get("name") or "") + " " + (tags.get("network") or "")
        if tags.get("station") == "subway" or tags.get("subway") == "yes" or "metro" in name.lower():
            cats.append("metro_station")
        elif rw in ("station", "halt"):
            cats.append("rail_station")
    if rw == "subway_entrance":
        cats.append("subway_entrance")
    if tags.get("leisure") in OPEN_LEISURE or tags.get("landuse") in OPEN_LANDUSE:
        cats.append("open_ground")
    if tags.get("landuse") == "industrial" or "industrial" in tags or tags.get("man_made") in INDUSTRIAL_MAN_MADE \
            or tags.get("power") == "plant":
        cats.append("industrial")
    if tags.get("natural") in ("water", "wetland") and tags.get("name"):
        cats.append("water_named")
    if tags.get("place") in PLACE_TYPES and tags.get("name"):
        cats.append("place")
    return cats


KEEP_TAGS = ("name", "name:en", "amenity", "healthcare", "emergency", "beds", "operator", "railway", "station",
             "location", "layer", "level", "subway", "parking", "leisure", "landuse", "man_made", "industrial",
             "product", "substance", "content", "power", "natural", "place", "social_facility", "tourism", "network")


def _feature(fid, cats, tags, lat, lon, area):
    props = {k: tags[k] for k in KEEP_TAGS if k in tags}
    props.update({"id": fid, "categories": cats, "area_m2": round(area, 1) if area else None})
    return {"type": "Feature", "geometry": {"type": "Point", "coordinates": [round(lon, 6), round(lat, 6)]},
            "properties": props}


def build_graph(roads):
    """Split ways at intersections; keep the largest connected component."""
    use = Counter()
    for r in roads:
        use.update(r["refs"])
        use[r["refs"][0]] += 1
        use[r["refs"][-1]] += 1
    node_index: dict[int, int] = {}
    node_lat, node_lon = [], []

    def idx(ref, lat, lon):
        i = node_index.get(ref)
        if i is None:
            i = node_index[ref] = len(node_lat)
            node_lat.append(lat)
            node_lon.append(lon)
        return i

    eu, ev, elen, ehw, eflag, ename = [], [], [], [], [], []
    geom_offsets, geom_lat, geom_lon = [0], [], []
    names: dict[str, int] = {}
    for r in roads:
        refs, coords = r["refs"], r["coords"]
        start = 0
        for k in range(1, len(refs)):
            if use[refs[k]] >= 2 or k == len(refs) - 1:
                seg = coords[start:k + 1]
                lat = np.array([c[0] for c in seg])
                lon = np.array([c[1] for c in seg])
                length = float(haversine_m(lat[:-1], lon[:-1], lat[1:], lon[1:]).sum()) if len(seg) > 1 else 0.0
                u = idx(refs[start], *coords[start])
                v = idx(refs[k], *coords[k])
                if u != v:
                    eu.append(u); ev.append(v); elen.append(length)
                    ehw.append(HIGHWAY_CODES[r["hw"]])
                    eflag.append((1 if r["tunnel"] else 0) | (2 if r["bridge"] else 0))
                    nm = r["name"] or ""
                    ename.append(names.setdefault(nm, len(names)))
                    geom_lat.extend(lat.tolist()); geom_lon.extend(lon.tolist())
                    geom_offsets.append(len(geom_lat))
                start = k
    eu, ev = np.array(eu), np.array(ev)
    # Largest connected component (undirected)
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components
    n = len(node_lat)
    m = coo_matrix((np.ones(len(eu)), (eu, ev)), shape=(n, n))
    ncomp, labels = connected_components(m, directed=False)
    keep_label = np.bincount(labels).argmax()
    keep_nodes = labels == keep_label
    new_id = -np.ones(n, dtype=np.int64)
    new_id[keep_nodes] = np.arange(keep_nodes.sum())
    keep_edges = keep_nodes[eu]
    offs = np.array(geom_offsets)
    starts, ends = offs[:-1][keep_edges], offs[1:][keep_edges]
    glat, glon = np.array(geom_lat), np.array(geom_lon)
    seg_lens = ends - starts
    new_offsets = np.concatenate([[0], np.cumsum(seg_lens)])
    sel = np.concatenate([np.arange(s, e) for s, e in zip(starts, ends)])
    print(f"graph: {n:,} nodes / {len(eu):,} edges -> largest component {keep_nodes.sum():,} nodes / "
          f"{keep_edges.sum():,} edges ({ncomp:,} components)")
    return {
        "node_lat": np.array(node_lat)[keep_nodes], "node_lon": np.array(node_lon)[keep_nodes],
        "edge_u": new_id[eu[keep_edges]], "edge_v": new_id[ev[keep_edges]],
        "edge_len": np.array(elen)[keep_edges], "edge_hw": np.array(ehw, dtype=np.int16)[keep_edges],
        "edge_flag": np.array(eflag, dtype=np.int8)[keep_edges], "edge_name": np.array(ename)[keep_edges],
        "geom_offsets": new_offsets, "geom_lat": glat[sel].astype(np.float32), "geom_lon": glon[sel].astype(np.float32),
        "names": np.array(list(names.keys()), dtype=object),
        "highway_codes": np.array(sorted(WALKABLE), dtype=object),
    }
