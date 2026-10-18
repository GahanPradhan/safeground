"""Hazard zones built only from rulebook numbers (official distances) and measured conditions."""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import h3
from shapely.geometry import Point, Polygon, mapping
from shapely.ops import unary_union

from safeground.engine.geo import to_latlon, to_xy

FT, MI = 0.3048, 1609.344
TIER_ORDER = ["red", "orange", "yellow", "green"]


@dataclass
class Zone:
    hazard: str
    source: tuple[float, float] | None  # (lat, lon) of the incident, None for city-wide hazards
    polygons: dict[str, Polygon] = field(default_factory=dict)  # tier -> polygon (lon/lat)
    hex_tiers: dict[str, str] = field(default_factory=dict)  # h3 cell -> tier (flood)
    basis: dict = field(default_factory=dict)  # numbers + source ids used to build the zone

    def tier_at(self, lat: float, lon: float, cell: str | None = None) -> str:
        if self.hex_tiers:
            return self.hex_tiers.get(cell, "green") if cell else "green"
        p = Point(lon, lat)
        for tier in TIER_ORDER:
            poly = self.polygons.get(tier)
            if poly is not None and poly.contains(p):
                return tier
        return "green"

    def danger_polygon(self) -> Polygon | None:
        polys = [p for t, p in self.polygons.items() if t in ("red", "orange", "yellow")]
        return unary_union(polys) if polys else None

    def geojson(self) -> dict:
        feats = [{"type": "Feature", "properties": {"tier": t}, "geometry": mapping(p)}
                 for t, p in self.polygons.items()]
        return {"type": "FeatureCollection", "features": feats}


def _local_polygon(lat0: float, lon0: float, pts_xy: list[tuple[float, float]]) -> Polygon:
    x0, y0 = to_xy(lat0, lon0)
    coords = []
    for dx, dy in pts_xy:
        la, lo = to_latlon(x0 + dx, y0 + dy)
        coords.append((float(lo), float(la)))
    return Polygon(coords)


def _circle(lat: float, lon: float, r: float, n: int = 72) -> Polygon:
    return _local_polygon(lat, lon, [(r * math.sin(2 * math.pi * i / n), r * math.cos(2 * math.pi * i / n))
                                     for i in range(n)])


def _downwind_square(lat: float, lon: float, bearing: float, length: float) -> Polygon:
    """ERG protective-action zone: square downwind of the source, length = width = protective distance."""
    b = math.radians(bearing)
    ax, ay = math.sin(b), math.cos(b)  # along-wind unit vector
    cx, cy = math.cos(b), -math.sin(b)  # cross-wind unit vector
    h = length / 2
    pts = [(cx * -h, cy * -h), (cx * h, cy * h),
           (ax * length + cx * h, ay * length + cy * h), (ax * length - cx * h, ay * length - cy * h)]
    return _local_polygon(lat, lon, pts)


def wind_class(speed_ms: float, classes: dict) -> int:
    for i, name in enumerate(("low", "moderate", "high")):
        lo, hi = classes[name]
        if lo <= speed_ms < hi:
            return i
    return 2


def gas_zone(rulebook: dict, lat: float, lon: float, chemical: str, size: str,
             wind_from_deg: float, wind_speed_ms: float, is_day: bool) -> Zone:
    zm = rulebook["zone_model"]
    chem = zm["chemicals"][chemical]
    wc = wind_class(wind_speed_ms, zm["wind_classes_ms"])
    if size == "small":
        row = chem["small"]
        pad_mi = row["day_mi"] if is_day else row["night_mi"]
        table = "Table 1 (small spill)"
    else:
        row = chem["large"][size]
        pad_mi = (row["day_mi"] if is_day else row["night_mi"])[wc]
        table = f"Table 3 (large spill, {size.replace('_', ' ')})"
    isolate_m = row["isolate_ft"] * FT
    pad_m = pad_mi * MI
    downwind = (wind_from_deg + 180) % 360
    red = _circle(lat, lon, isolate_m)
    orange = _downwind_square(lat, lon, downwind, pad_m).difference(red)
    u = zm["uncertainty_deg"]
    band = unary_union([_downwind_square(lat, lon, downwind - u, pad_m),
                        _downwind_square(lat, lon, downwind + u, pad_m)])
    yellow = band.difference(orange).difference(red)
    basis = {
        "chemical": chemical, "un": chem["un"], "guide_source": chem["guide"], "table_source": chem["table_source"],
        "erg_table": table, "isolate_m": round(isolate_m), "protective_distance_m": round(pad_m),
        "wind_from_deg": round(wind_from_deg), "downwind_deg": round(downwind), "wind_speed_ms": round(wind_speed_ms, 1),
        "wind_class": ("low", "moderate", "high")[wc], "period": "day" if is_day else "night",
        "uncertainty_deg": u,
    }
    return Zone("gas", (lat, lon), {"red": red, "orange": orange, "yellow": yellow}, basis=basis)


def explosion_zone(rulebook: dict, lat: float, lon: float, scenario: str) -> Zone:
    sc = rulebook["zone_model"]["scenarios"][scenario]
    if "building_evacuation_ft" in sc:
        r_red = sc["building_evacuation_ft"] * FT
        r_orange = sc["outdoor_evacuation_ft"] * FT
        red = _circle(lat, lon, r_red)
        polys = {"red": red, "orange": _circle(lat, lon, r_orange).difference(red)}
        basis = {"scenario": scenario, "label": sc["label"], "source": sc["source"],
                 "building_evacuation_m": round(r_red), "outdoor_evacuation_m": round(r_orange)}
    else:
        r = sc["isolate_m"]
        polys = {"red": _circle(lat, lon, r)}
        basis = {"scenario": scenario, "label": sc["label"], "source": sc["source"], "isolate_m": r}
    return Zone("explosion", (lat, lon), polys, basis=basis)


def flood_zone(rulebook: dict, hexes: dict[str, dict], rain_mm_24h: float,
               reported_points: list[tuple[float, float]] | None = None) -> Zone:
    """Susceptibility tiers per hexagon (SafeGround heuristic; thresholds stored in basis)."""
    zm = rulebook["zone_model"]
    levels = zm["rain_levels_mm_24h"]
    rules = {"red_rel_elev": -3.0, "red_water_near_m": 500, "orange_rel_elev": -1.5, "orange_water_occ": 10,
             "yellow_rel_elev": -0.5}
    reported_cells: set[str] = set()
    for la, lo in reported_points or []:
        c = h3.latlng_to_cell(la, lo, 9)
        reported_cells.update(h3.grid_disk(c, 1))  # ~300 m around the report
    tiers: dict[str, str] = {}
    for cell, p in hexes.items():
        rel = p.get("rel_elev")
        wn = p.get("water_near_m")
        wo = p.get("water_occ") or 0
        if cell in reported_cells:
            t = "red"
        elif rel is None:
            continue
        elif rain_mm_24h >= levels["very_heavy"] and rel <= rules["red_rel_elev"] and wn is not None \
                and wn <= rules["red_water_near_m"]:
            t = "red"
        elif rain_mm_24h >= levels["heavy"] and (rel <= rules["orange_rel_elev"] or wo >= rules["orange_water_occ"]):
            t = "orange"
        elif rain_mm_24h >= levels["moderate"] and rel <= rules["yellow_rel_elev"]:
            t = "yellow"
        else:
            t = "green"
        tiers[cell] = t
    basis = {"rain_mm_24h": rain_mm_24h, "rain_category": rain_category(rain_mm_24h, levels),
             "thresholds": rules, "reported_points": len(reported_points or []),
             "method": "SafeGround susceptibility heuristic (relative elevation, surface water, rainfall) — not a forecast"}
    return Zone("flood", None, hex_tiers=tiers, basis=basis)


def rain_category(mm: float, levels: dict) -> str:
    name = "light or none"
    for k in ("moderate", "heavy", "very_heavy", "extremely_heavy"):
        if mm >= levels[k]:
            name = k.replace("_", " ")
    return name


# ------------------------------------------------------------------------------------------------ natural hazards
def _wedge(lat: float, lon: float, bearing: float, half_deg: float, r: float, n: int = 24) -> Polygon:
    pts = [(0.0, 0.0)]
    for i in range(n + 1):
        b = math.radians(bearing - half_deg + 2 * half_deg * i / n)
        pts.append((r * math.sin(b), r * math.cos(b)))
    return _local_polygon(lat, lon, pts)


def fire_zone(rulebook: dict, lat: float, lon: float, wind_from_deg: float, wind_speed_ms: float) -> Zone:
    """Wildfire spread estimate: forward rate ~10% of the open wind speed (Cruz & Alexander 2019)."""
    zm = rulebook["zone_model"]
    rate_m_h = zm["spread_fraction_of_wind"] * max(wind_speed_ms, 0.5) * 3600
    downwind = (wind_from_deg + 180) % 360
    r1 = max(zm["min_radius_m"], rate_m_h * zm["red_hours"])
    r3 = max(zm["min_radius_m"] * 2, rate_m_h * zm["orange_hours"])
    half, u = zm["half_angle_deg"], zm["uncertainty_deg"]
    red = unary_union([_wedge(lat, lon, downwind, half, r1), _circle(lat, lon, zm["min_radius_m"])])
    orange = _wedge(lat, lon, downwind, half, r3).difference(red)
    yellow = _wedge(lat, lon, downwind, half + u, r3).difference(orange).difference(red)
    basis = {"rule": "forward spread ≈ 10% of open wind speed (forests and shrublands)", "rule_source": "cruz_2019",
             "wind_from_deg": round(wind_from_deg), "downwind_deg": round(downwind),
             "wind_speed_ms": round(wind_speed_ms, 1), "spread_m_per_hour": round(rate_m_h),
             "reach_1h_m": round(r1), "reach_3h_m": round(r3), "uncertainty_deg": u}
    return Zone("wildfire", (lat, lon), {"red": red, "orange": orange, "yellow": yellow}, basis=basis)


def tsunami_zone(rulebook: dict, hexes: dict[str, dict]) -> Zone:
    safe = rulebook["zone_model"]["safe_height_m"]
    tiers = {c: ("red" if p["elev_mean"] < safe else "green") for c, p in hexes.items()
             if p.get("elev_mean") is not None}
    basis = {"safe_height_m": safe, "safe_height_source": "Ready.gov: shelters 100 feet or more above sea level",
             "method": "block-average height above sea level (Copernicus DEM); distance inland not measured"}
    return Zone("tsunami", None, hex_tiers=tiers, basis=basis)


def storm_zone(rulebook: dict, hexes: dict[str, dict], strength: str) -> Zone:
    zm = rulebook["zone_model"]
    hurricane = strength in ("hurricane", "major")
    wind_tier = "yellow" if strength == "tropical_storm" else "orange"
    tiers = {}
    for c, p in hexes.items():
        rel, ab, wo = p.get("rel_elev"), p.get("elev_mean"), p.get("water_occ") or 0
        low = (rel is not None and rel <= zm["low_rel_elev_m"]) or (ab is not None and ab <= zm["low_abs_elev_m"]) \
            or wo >= zm["water_occ_pct"]
        tiers[c] = ("red" if hurricane else "orange") if low else wind_tier
    basis = {"strength": strength, "scale_source": "nhc_sshws",
             "low_lying_rule": f"relative height ≤ {zm['low_rel_elev_m']} m, height ≤ {zm['low_abs_elev_m']} m above "
                               f"sea level, or surface water ≥ {zm['water_occ_pct']}% of the time",
             "method": "SafeGround exposure estimate — not an official evacuation zone"}
    return Zone("cyclone", None, hex_tiers=tiers, basis=basis)


def heat_index_f(temp_c: float, rh: float) -> float:
    """NWS heat index (Rothfusz regression with NWS adjustments), in °F."""
    t = temp_c * 9 / 5 + 32
    simple = 0.5 * (t + 61.0 + (t - 68.0) * 1.2 + rh * 0.094)
    if (simple + t) / 2 < 80:
        return simple
    hi = (-42.379 + 2.04901523 * t + 10.14333127 * rh - .22475541 * t * rh - .00683783 * t * t
          - .05481717 * rh * rh + .00122874 * t * t * rh + .00085282 * t * rh * rh - .00000199 * t * t * rh * rh)
    if rh < 13 and 80 <= t <= 112:
        hi -= ((13 - rh) / 4) * math.sqrt((17 - abs(t - 95.)) / 17)
    elif rh > 85 and 80 <= t <= 87:
        hi += ((rh - 85) / 10) * ((87 - t) / 5)
    return hi


def heat_tier(hi_f: float, classes: dict) -> str:
    if hi_f >= classes["danger"]:
        return "red"
    if hi_f >= classes["extreme_caution"]:
        return "orange"
    if hi_f >= classes["caution"]:
        return "yellow"
    return "green"
