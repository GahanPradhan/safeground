"""RESPOND: turn (incident, person's spot, situation) into verified plan facts.

Everything here is deterministic. The SafetyPlanner agent only rewrites these facts
into the fixed SafetyPlan format; it may not add moves, places, numbers or advice.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from safeground.config import WALK_SPEED
from safeground.engine import data, zones
from safeground.engine.geo import bearing_deg, compass, haversine_m
from safeground.engine.routing import router

SITUATIONS = {
    "home_ground": "At home or indoors, ground floor",
    "home_upper": "At home or indoors, upper floor",
    "outdoors": "Outdoors on foot",
    "vehicle": "In a vehicle",
    "institution": "In a school, hospital or other institution",
    "needs_assistance": "With elderly people, children or someone who needs help",
}
INDOOR = {"home_ground", "home_upper", "institution"}
CALL = [{"number": "112", "for": "National emergency number"}, {"number": "108", "for": "Ambulance"},
        {"number": "101", "for": "Fire and rescue"}]
MOVE_TEXT = {
    "STAY_IN_SEAL": "Stay inside and seal the room",
    "MOVE_CROSSWIND_UPWIND": "Move out sideways to the wind, then upwind",
    "MOVE_AWAY": "Move away beyond the safe distance",
    "STAY_INSIDE_AWAY_FROM_WINDOWS": "Shelter inside, away from windows and outer walls",
    "GO_UP": "Go up: upper floor, tall building or higher ground",
    "GO_DOWN_INSIDE": "Go down to underground shelter",
    "STAY_ALERT": "Stay alert and follow official updates",
    "AVOID": "Avoid underpasses, drains and moving water",
    "DROP_COVER_HOLD": "Drop, cover and hold on until the shaking stops",
    "MOVE_TO_OPEN_AREA": "If your building is damaged, get out to an open area",
    "GO_TO_HIGH_GROUND": "Go to high ground, as far inland as possible — now",
    "SHELTER_INTERIOR": "Shelter in an interior room of a sturdy building",
    "EVACUATE_AWAY_FROM_FIRE": "Leave now — away from the fire, never downwind",
    "STAY_COOL": "Get somewhere cool and stay hydrated",
}
NEEDS_INCIDENT = {"gas", "explosion", "wildfire"}


@dataclass
class Incident:
    hazard: str  # a rulebook name: gas, explosion, flood, air_raid, earthquake, tsunami, cyclone, wildfire, heat
    lat: float | None = None
    lon: float | None = None
    params: dict = field(default_factory=dict)


def build_zone(inc: Incident) -> zones.Zone | None:
    snap = data.load()
    rb = snap.rulebooks[inc.hazard]
    p = inc.params
    if inc.hazard == "gas":
        hour = p.get("local_hour", 12)
        return zones.gas_zone(rb, inc.lat, inc.lon, p.get("chemical", "ammonia"), p.get("size", "small"),
                              float(p["wind_from_deg"]), float(p["wind_speed_ms"]), 6 <= hour < 18)
    if inc.hazard == "explosion":
        return zones.explosion_zone(rb, inc.lat, inc.lon, p.get("scenario", "car"))
    if inc.hazard == "flood":
        pts = [tuple(x) for x in p.get("reported_points", [])]
        return zones.flood_zone(rb, snap.hexes, float(p.get("rain_mm_24h", 120)), pts)
    if inc.hazard == "wildfire":
        w = _wind(p, rb)
        return zones.fire_zone(rb, inc.lat, inc.lon, w[0], w[1])
    if inc.hazard == "tsunami":
        return zones.tsunami_zone(rb, snap.hexes)
    if inc.hazard == "cyclone":
        return zones.storm_zone(rb, snap.hexes, p.get("strength", "hurricane"))
    return None  # air_raid, earthquake, heat: the whole area


def _wind(p: dict, rb: dict) -> tuple[float, float]:
    spec = next((x for x in rb.get("params", []) if x["type"] == "wind"), {})
    return float(p.get("wind_from_deg", spec.get("default_from", 90))), \
        float(p.get("wind_speed_ms", spec.get("default_speed", 3)))


def _targets(snap, cats: tuple[str, ...], lat: float, lon: float, radius: float, kind: str, label: str) -> list[dict]:
    out = []
    for c in cats:
        for _, f in snap.features.get(c, data._feature_set([])).near(lat, lon, radius, 25):
            out.append({**f, "kind": kind, "label": f"{f.get('name') or label} ({label.lower()})" if f.get("name")
                        else label})
    return out


def _high_ground(snap, lat: float, lon: float, safe_m: float) -> list[dict]:
    import h3
    out = []
    for cell in h3.grid_disk(snap.hex_of(lat, lon), 14):
        p = snap.hex_props(cell)
        if (p.get("elev_mean") or -1e9) >= safe_m:
            la, lo = h3.cell_to_latlng(cell)
            out.append({"id": cell, "name": None, "lat": la, "lon": lo, "kind": "high_ground",
                        "label": f"Ground about {p['elev_mean']:.0f} m above sea level (DEM estimate)"})
    return out


def _advice(rb: dict, tier: str, situation: str, scenario: str | None) -> list[dict]:
    out = []
    for a in rb["advice"]:
        if tier not in a["tiers"]:
            continue
        if "all" not in a["situations"] and situation not in a["situations"]:
            continue
        if a.get("scenarios") and scenario not in a["scenarios"]:
            continue
        out.append({"id": a["id"], "text": a["text"], "source": a["source"]})
    return out


def _place(f: dict, lat: float, lon: float, kind: str) -> dict:
    d = float(haversine_m(lat, lon, f["lat"], f["lon"]))
    b = bearing_deg(lat, lon, f["lat"], f["lon"])
    return {"kind": kind, "name": f.get("name") or f.get("label") or f"Unnamed {kind.replace('_', ' ')}", "lat": f["lat"],
            "lon": f["lon"], "straight_m": round(d), "direction": compass(b), "id": f.get("id")}


def _flood_refuges(snap, lat, lon, zone) -> list[dict]:
    out = []
    for d, f in snap.features["tall_building_osm"].near(lat, lon, 1200, 15):
        out.append({**f, "kind": "tall_building_osm",
                    "label": f"Building with {int(f['levels']) if f.get('levels') else '?'} floors (OpenStreetMap)"})
    import h3
    for cell in h3.grid_disk(snap.hex_of(lat, lon), 4):
        p = snap.hex_props(cell)
        la, lo = h3.cell_to_latlng(cell)
        bh = p.get("bld_h_p90") or p.get("bld_h_mean") or 0  # Chennai snapshot: p90; global regions: mean
        if bh >= 9:
            out.append({"id": cell, "name": None, "lat": la, "lon": lo, "kind": "multistorey_block",
                        "label": f"Block with buildings ~{bh:.0f} m tall (Open Buildings estimate)"})
        elif (p.get("rel_elev") or 0) >= 3.0:  # below ~3 m the DEM error (several metres) dominates
            out.append({"id": cell, "name": None, "lat": la, "lon": lo, "kind": "high_ground",
                        "label": f"Higher ground (~{p['rel_elev']:.1f} m above surroundings, DEM estimate)"})
    return out


def _nearby(snap, lat: float, lon: float) -> dict:
    """People who may need extra help within 500 m (mapped only)."""
    out = {}
    for c, k in (("school", "schools"), ("elderly_home", "elderly_homes"), ("hospital", "hospitals"),
                 ("clinic", "clinics")):
        n = len(snap.features.get(c, data._feature_set([])).near(lat, lon, 500, 999))
        if n:
            out[k] = n
    return out


def plan_facts(inc: Incident, lat: float, lon: float, situation: str) -> dict:
    snap = data.load()
    rb = snap.rulebooks[inc.hazard]
    p = inc.params
    r = router()
    zone = build_zone(inc)
    cell = snap.hex_of(lat, lon)
    hexp = snap.hex_props(cell)
    speed = WALK_SPEED["assisted" if situation == "needs_assistance" else "default"]
    node, snap_m = r.snap(lat, lon)
    gaps, valid_while = [], []
    scenario = inc.params.get("scenario") or inc.params.get("strength")

    # ---- tier at the spot -------------------------------------------------------------------
    if inc.hazard == "air_raid":
        shelters = [f for c in data.SHELTER_CATEGORIES
                    for _, f in snap.features.get(c, data._feature_set([])).near(lat, lon, 3000, 10)]
        res = r.route_to_nearest(lat, lon, shelters, max_m=3000)
        walk_min = res[0].length_m / speed / 60 if res else None
        tier = "orange" if walk_min is not None and walk_min <= rb["zone_model"]["walk_minutes_poor"] else "red"
        gaps.append("Basements are rarely mapped; a building basement near you may not appear here.")
    elif inc.hazard == "earthquake":
        tier = "red" if p.get("phase", "during") == "during" else "orange"
    elif inc.hazard == "heat":
        hi_f = zones.heat_index_f(float(p.get("temp_c", 40)), float(p.get("humidity", 40)))
        tier = zones.heat_tier(hi_f, rb["zone_model"]["classes_f"])
        valid_while.append(f"Air temperature {p.get('temp_c', 40)} °C and humidity {p.get('humidity', 40)}% "
                           f"(heat index about {hi_f:.0f} °F / {(hi_f - 32) * 5 / 9:.0f} °C)")
    elif zone is None:
        tier = "green"
    else:
        tier = zone.tier_at(lat, lon, cell)
        if inc.hazard in ("flood", "tsunami") and cell not in zone.hex_tiers:
            tier = "unknown"
            gaps.append("No land-height data for this block, so exposure is unknown.")
        if inc.hazard == "cyclone" and cell not in zone.hex_tiers:
            tier = "yellow" if p.get("strength") == "tropical_storm" else "orange"

    allowed = rb["moves"].get(tier, ["STAY_ALERT"])
    forbidden = rb["moves"]["forbidden"]
    move, target, route = "STAY_ALERT", None, None

    # ---- choose the main move and where to go -------------------------------------------
    if inc.hazard == "gas" and tier in ("red", "orange"):
        exit_route = r.exit_zone(lat, lon, zone, downwind_deg=zone.basis["downwind_deg"])
        if situation in INDOOR:
            move = "STAY_IN_SEAL"
        elif situation == "vehicle":
            move = "MOVE_CROSSWIND_UPWIND"
            route = exit_route
        else:  # on foot / needs help: walk out crosswind if short, else nearest building to shelter
            if exit_route and exit_route.length_m <= 600:
                move, route = "MOVE_CROSSWIND_UPWIND", exit_route
            else:
                move = "STAY_IN_SEAL"
                gaps.append("Exit on foot is long; official advice is to find the closest building to shelter in.")
        valid_while.append(f"Wind from {zone.basis['wind_from_deg']}° (±{zone.basis['uncertainty_deg']}°) "
                           f"at {zone.basis['wind_speed_ms']} m/s")
    elif inc.hazard == "gas" and tier == "yellow":
        move = "STAY_ALERT"
        valid_while.append(f"Wind from {zone.basis['wind_from_deg']}° (±{zone.basis['uncertainty_deg']}°)")
    elif inc.hazard == "explosion" and tier == "red":
        move, route = "MOVE_AWAY", r.exit_zone(lat, lon, zone)
    elif inc.hazard == "explosion" and tier == "orange":
        move = "STAY_INSIDE_AWAY_FROM_WINDOWS"
    elif inc.hazard == "flood" and tier in ("red", "orange"):
        move = "GO_UP"
        if situation != "home_upper":
            refuges = _flood_refuges(snap, lat, lon, zone)
            # vertical evacuation: the nearest way up wins; flooded streets cost 8x so drier streets are preferred,
            # underpasses are never used, and the walk is capped at 1 km
            res = r.route_to_nearest(lat, lon, refuges, zone, avoid_underpass=True, max_m=1000)
            if res:
                route, t = res
                target = {**_place(t, lat, lon, t["kind"]), "label": t["label"]}
            else:
                gaps.append("No mapped tall building or higher ground within a 1 km walk that avoids underpasses.")
        valid_while.append(f"Rainfall about {zone.basis['rain_mm_24h']} mm in 24 h ({zone.basis['rain_category']})")
    elif inc.hazard == "flood" and tier == "yellow":
        move = "AVOID"
    elif inc.hazard == "air_raid":
        move = "GO_DOWN_INSIDE"
        if res:
            route, t = res
            kind = "metro_underground" if t in snap.features["metro_underground"].items else "shelter"
            target = _place(t, lat, lon, kind)
        else:
            gaps.append("No mapped underground shelter within a 15-minute walk.")

    elif inc.hazard == "earthquake" and tier == "red":
        move = "DROP_COVER_HOLD"
    elif inc.hazard == "earthquake":
        move = "MOVE_TO_OPEN_AREA"
        opens = _targets(snap, ("open_ground",), lat, lon, 1500, "open_area", "Open area (park or ground)")
        res = r.route_to_nearest(lat, lon, opens, max_m=rb["zone_model"]["open_area_max_walk_m"])
        if res:
            route, t = res
            target = {**_place(t, lat, lon, "open_area"), "label": t["label"]}
        else:
            gaps.append("No mapped park or open ground within a 1 km walk.")
        valid_while.append("Until officials confirm buildings are safe; aftershocks are expected")
    elif inc.hazard == "tsunami" and tier == "red":
        move = "GO_TO_HIGH_GROUND"
        safe = rb["zone_model"]["safe_height_m"]
        res = r.route_to_nearest(lat, lon, _high_ground(snap, lat, lon, safe), zone, avoid_underpass=True,
                                 max_m=rb["zone_model"]["max_walk_m"])
        if res:
            route, t = res
            target = {**_place(t, lat, lon, "high_ground"), "label": t["label"]}
        else:
            gaps.append("No ground 30 m above sea level within a 3 km walk in the loaded area; "
                        "go as high and as far inland as possible.")
        gaps.append("Distance from the coast is not measured; official tsunami evacuation maps override this.")
    elif inc.hazard == "tsunami":
        move = "STAY_ALERT"
    elif inc.hazard == "cyclone" and tier == "red" and situation != "home_upper":
        move = "GO_UP"
        res = r.route_to_nearest(lat, lon, _flood_refuges(snap, lat, lon, zone), zone, avoid_underpass=True,
                                 max_m=1000)
        if res:
            route, t = res
            target = {**_place(t, lat, lon, t["kind"]), "label": t["label"]}
        else:
            move = "SHELTER_INTERIOR"
            gaps.append("No mapped tall building or higher ground within a 1 km walk; shelter on the highest floor.")
        valid_while.append("Until officials lift the storm warning")
    elif inc.hazard == "cyclone":
        move = "SHELTER_INTERIOR"
        valid_while.append("Until officials lift the storm warning")
    elif inc.hazard == "wildfire" and tier in ("red", "orange"):
        move = "EVACUATE_AWAY_FROM_FIRE"
        core = zones.Zone("wildfire", zone.source, {k: v for k, v in zone.polygons.items() if k in ("red", "orange")})
        route = r.exit_zone(lat, lon, core, downwind_deg=zone.basis["downwind_deg"])
        if route is None:
            gaps.append("No exit from the estimated spread zone inside the loaded area; leave crosswind and keep going.")
        valid_while.append(f"Wind from {zone.basis['wind_from_deg']}° (±{zone.basis['uncertainty_deg']}°) at "
                           f"{zone.basis['wind_speed_ms']} m/s")
    elif inc.hazard == "wildfire":
        move = "STAY_ALERT"
        valid_while.append(f"Wind from {zone.basis['wind_from_deg']}° (±{zone.basis['uncertainty_deg']}°)")
    elif inc.hazard == "heat" and tier != "green":
        move = "STAY_COOL"
        if situation in ("outdoors", "needs_assistance") and tier in ("red", "orange"):
            cool = _targets(snap, ("community_centre", "place_of_worship", "library", "mall"), lat, lon, 2000,
                            "public_building", "Public building — may offer shade or cooling (not confirmed)")
            res = r.route_to_nearest(lat, lon, cool, max_m=rb["zone_model"]["cool_place_max_walk_m"])
            if res:
                route, t = res
                target = {**_place(t, lat, lon, "public_building"), "label": t["label"]}
            else:
                gaps.append("No mapped community centre or place of worship within a 1.5 km walk; find shade.")

    if move not in allowed:
        allowed = allowed + [move]  # STAY_ALERT / AVOID are always permitted

    if route is not None and target is None:
        end = route.coords[-1]
        target = {"kind": "safe_point", "name": "Safe point outside the danger zone", "lat": end[0], "lon": end[1],
                  "straight_m": round(float(haversine_m(lat, lon, *end))),
                  "direction": compass(bearing_deg(lat, lon, *end))}

    # ---- context -----------------------------------------------------------------------------
    hosp = []
    for d, f in snap.features.get("hospital_major", data._feature_set([])).near(lat, lon, 6000, 6):
        h = _place(f, lat, lon, "hospital")
        h["in_danger_zone"] = (zone is not None and zone.tier_at(f["lat"], f["lon"], snap.hex_of(f["lat"], f["lon"]))
                               in ("red", "orange"))
        hosp.append(h)
    hosp = [h for h in hosp if not h["in_danger_zone"]][:2] + [h for h in hosp if h["in_danger_zone"]][:1]
    if snap_m > 300:
        gaps.append(f"Nearest mapped path is {round(snap_m)} m away; routes start from there.")
    if not snap.hexes:
        gaps.append("Satellite layers (population, building height, land height) not loaded.")
    gaps.append("Hospitals shown are mapped major hospitals (emergency tag or large campus); their emergency services, "
                "capacity and current status are not verified.")

    source_direction = None
    if inc.lat is not None and inc.hazard in NEEDS_INCIDENT:
        d = float(haversine_m(lat, lon, inc.lat, inc.lon))
        source_direction = {"distance_m": round(d), "direction": compass(bearing_deg(lat, lon, inc.lat, inc.lon))}

    call = CALL
    if snap.region:  # region outside Chennai: that country's numbers (none guessed if unknown)
        em = snap.region.get("emergency") or {}
        call = em.get("call") or []
        if not call:
            gaps.append(em.get("note") or "No checked emergency number for this country; find the local number.")
    return {
        "hazard": inc.hazard, "hazard_title": rb["title"], "situation": situation, "scenario": scenario,
        "situation_label": SITUATIONS[situation],
        "spot": {"lat": lat, "lon": lon, "place": snap.place_name(lat, lon), "hex": cell},
        "incident": {"lat": inc.lat, "lon": inc.lon, "params": inc.params, "source_from_spot": source_direction},
        "zone_basis": zone.basis if zone else {"type": "city-wide alert"},
        "tier": tier, "tier_meaning": rb["tiers"].get(tier, "No data"),
        "allowed_moves": allowed, "forbidden_moves": forbidden,
        "main_move": move, "main_move_text": MOVE_TEXT[move],
        "target": target,
        "route": route.summary(speed) if route else None,
        "route_coords": route.coords if route else None,
        "advice": _advice(rb, tier, situation, scenario),
        "nearest_hospitals": hosp,
        "block_facts": {k: hexp.get(k) for k in ("pop", "bld_h_p90", "bld_frac", "rel_elev", "elev_mean",
                                                 "water_near_m", "dw_trees_2025") if hexp.get(k) is not None},
        "nearby_500m": _nearby(snap, lat, lon),
        "valid_while": valid_while,
        "call": call,
        "data_gaps": gaps,
        "sources": rb["sources"],
        "caveats": rb.get("caveats", []),
    }
