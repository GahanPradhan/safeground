"""Walking routes on the OpenStreetMap graph that avoid hazard zones (scipy shortest paths)."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import shapely
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra
from scipy.spatial import cKDTree

from safeground.engine import data
from safeground.engine.geo import to_xy
from safeground.engine.zones import Zone

TIER_COST = {"red": 8.0, "orange": 4.0, "yellow": 2.0, "green": 1.0}


@dataclass
class Route:
    length_m: float
    nodes: list[int]
    coords: list[tuple[float, float]]  # (lat, lon)
    street_names: list[str]
    passes_tiers: list[str]  # tiers crossed along the route (from edge midpoints)
    uses_underpass: bool

    def summary(self, speed_ms: float) -> dict:
        return {"length_m": round(self.length_m), "walk_minutes": round(self.length_m / speed_ms / 60, 1),
                "via": [n for n in dict.fromkeys(self.street_names) if n][:5],
                "passes_tiers": sorted(set(self.passes_tiers)), "uses_underpass": self.uses_underpass}


class Router:
    def __init__(self, g: dict):
        self.lat = g["node_lat"].astype(float)
        self.lon = g["node_lon"].astype(float)
        u, v, length = g["edge_u"], g["edge_v"], np.maximum(g["edge_len"].astype(float), 0.1)
        a, b = np.minimum(u, v), np.maximum(u, v)
        order = np.lexsort((length, b, a))
        a, b = a[order], b[order]
        first = np.ones(len(a), dtype=bool)
        first[1:] = (a[1:] != a[:-1]) | (b[1:] != b[:-1])
        keep = order[first]  # shortest edge per unordered node pair
        self.eidx = keep
        self.u, self.v, self.len = u[keep], v[keep], length[keep]
        self.flag = g["edge_flag"][keep]
        self.name_idx = g["edge_name"][keep]
        self.names = g["names"]
        self.geom_offsets, self.geom_lat, self.geom_lon = g["geom_offsets"], g["geom_lat"], g["geom_lon"]
        self.n = len(self.lat)
        x, y = to_xy(self.lat, self.lon)
        self.x, self.y = x, y
        self.tree = cKDTree(np.column_stack([x, y]))
        self.mid_lat = (self.lat[self.u] + self.lat[self.v]) / 2
        self.mid_lon = (self.lon[self.u] + self.lon[self.v]) / 2
        self.pair = {(int(p), int(q)): i for i, (p, q) in enumerate(zip(np.minimum(self.u, self.v),
                                                                          np.maximum(self.u, self.v)))}

    # ---- helpers -------------------------------------------------------------------------
    def snap_surface(self, lat: float, lon: float) -> tuple[int, float]:
        """Nearest junction with at least one street-level (non-underpass) edge."""
        if not hasattr(self, "_surface_tree"):
            ok = np.zeros(self.n, dtype=bool)
            surf = (self.flag & 1) == 0
            ok[self.u[surf]] = True
            ok[self.v[surf]] = True
            self._surface_idx = np.where(ok)[0]
            self._surface_tree = cKDTree(np.column_stack([self.x[self._surface_idx], self.y[self._surface_idx]]))
        x, y = to_xy(lat, lon)
        d, i = self._surface_tree.query([float(x), float(y)])
        return int(self._surface_idx[i]), float(d)

    def snap(self, lat: float, lon: float) -> tuple[int, float]:
        x, y = to_xy(lat, lon)
        d, i = self.tree.query([float(x), float(y)])
        return int(i), float(d)

    def edge_tiers(self, zone: Zone | None) -> np.ndarray:
        tiers = np.full(len(self.u), "green", dtype=object)
        if zone is None:
            return tiers
        if zone.hex_tiers:
            import h3
            cells = [h3.latlng_to_cell(la, lo, 9) for la, lo in zip(self.mid_lat, self.mid_lon)]
            return np.array([zone.hex_tiers.get(c, "green") for c in cells], dtype=object)
        for tier in ("yellow", "orange", "red"):  # later tiers overwrite earlier ones
            poly = zone.polygons.get(tier)
            if poly is not None:
                inside = shapely.contains_xy(poly, self.mid_lon, self.mid_lat)
                tiers[inside] = tier
        return tiers

    def _graph(self, weights: np.ndarray) -> csr_matrix:
        ok = np.isfinite(weights)
        return csr_matrix((weights[ok], (self.u[ok], self.v[ok])), shape=(self.n, self.n))

    def _path(self, pred: np.ndarray, src: int, dst: int, tiers: np.ndarray) -> Route | None:
        if dst != src and pred[dst] < 0:
            return None
        nodes = [dst]
        while nodes[-1] != src:
            nodes.append(int(pred[nodes[-1]]))
        nodes.reverse()
        coords, names, crossed, length, underpass = [], [], [], 0.0, False
        for p, q in zip(nodes[:-1], nodes[1:]):
            e = self.pair[(min(p, q), max(p, q))]
            length += float(self.len[e])
            names.append(str(self.names[self.name_idx[e]]))
            crossed.append(str(tiers[e]))
            underpass |= bool(self.flag[e] & 1)
            gi = int(self.eidx[e])
            s, t = int(self.geom_offsets[gi]), int(self.geom_offsets[gi + 1])
            seg = list(zip(self.geom_lat[s:t].astype(float), self.geom_lon[s:t].astype(float)))
            if seg and (abs(seg[0][0] - self.lat[p]) + abs(seg[0][1] - self.lon[p])) > 1e-6:
                seg.reverse()
            coords.extend(seg if not coords else seg[1:])
        if not coords:
            coords = [(float(self.lat[src]), float(self.lon[src]))]
        return Route(length, nodes, coords, names, crossed, underpass)

    # ---- queries -------------------------------------------------------------------------
    def exit_zone(self, lat: float, lon: float, zone: Zone, avoid_underpass: bool = False,
                  max_m: float = 12000, downwind_deg: float | None = None) -> Route | None:
        """Cheapest walk from the spot to the nearest node outside every danger tier.
        With downwind_deg (gas), exits that lie downwind of the person are penalised (up to 3x for straight
        downwind) so the route heads crosswind or upwind, as ERG advises."""
        tiers = self.edge_tiers(zone)
        w = self.len * np.vectorize(TIER_COST.get)(tiers)
        if avoid_underpass:
            w = np.where(self.flag & 1, np.inf, w)
        src, _ = self.snap(lat, lon)
        dist, pred = dijkstra(self._graph(w), directed=False, indices=src, return_predecessors=True,
                              limit=max_m * 8)
        node_tier = np.full(self.n, "green", dtype=object)
        for tier in ("yellow", "orange", "red"):
            np.put(node_tier, self.u[tiers == tier], tier)
            np.put(node_tier, self.v[tiers == tier], tier)
        if zone.hex_tiers:
            node_tier = node_tier  # edge-based tiers already cover hexes
        candidates = np.where((node_tier == "green") & np.isfinite(dist))[0]
        if len(candidates) == 0:
            return None
        score = dist[candidates]
        if downwind_deg is not None:
            bearing = np.degrees(np.arctan2(self.x[candidates] - self.x[src], self.y[candidates] - self.y[src]))
            score = score * (1 + 2 * np.maximum(0, np.cos(np.radians(bearing - downwind_deg))))
        dst = int(candidates[np.argmin(score)])
        return self._path(pred, src, dst, tiers)

    def route_to_nearest(self, lat: float, lon: float, targets: list[dict], zone: Zone | None = None,
                         forbid_tiers: tuple[str, ...] = (), avoid_underpass: bool = False,
                         max_m: float = 6000) -> tuple[Route, dict] | None:
        """Shortest safe walk to the closest reachable target (targets are dicts with lat/lon)."""
        if not targets:
            return None
        tiers = self.edge_tiers(zone)
        w = self.len * np.vectorize(TIER_COST.get)(tiers)
        for t in forbid_tiers:
            w = np.where(tiers == t, np.inf, w)
        if avoid_underpass:
            w = np.where(self.flag & 1, np.inf, w)
        snap = self.snap_surface if avoid_underpass else self.snap
        src, _ = snap(lat, lon)
        dist, pred = dijkstra(self._graph(w), directed=False, indices=src, return_predecessors=True,
                              limit=max_m * 8)
        best = None
        for t in targets:
            node, snap_d = snap(t["lat"], t["lon"])
            if snap_d > 250 or not np.isfinite(dist[node]):
                continue
            if best is None or dist[node] < best[0]:
                best = (dist[node], node, t)
        if best is None:
            return None
        route = self._path(pred, src, best[1], tiers)
        return (route, best[2]) if route else None

    def distance_field(self, sources: list[dict]) -> np.ndarray:
        """Walking distance (m) from every graph node to the nearest source (inf if unreachable)."""
        idx = sorted({self.snap(s["lat"], s["lon"])[0] for s in sources})
        if not idx:
            return np.full(self.n, np.inf)
        return dijkstra(self._graph(self.len), directed=False, indices=idx, min_only=True, limit=20000)


_ROUTERS: dict[str, Router] = {}


def router() -> Router:
    """Router for the active region (built once per region)."""
    rid = data.current_region()
    if rid not in _ROUTERS:
        _ROUTERS[rid] = Router(data.load().graph)
    return _ROUTERS[rid]
