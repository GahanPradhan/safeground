"""Global (any place on Earth) helpers: projection, region ids, emergency numbers, plan checks."""
import math

from safeground.engine import emergency, regions
from safeground.engine.geo import _LAT0, haversine_m, set_reference_latitude, to_xy


def test_projection_follows_region_latitude():
    lat, lon = 48.85, 2.35  # Paris: 1 km east must still be ~1 km in the local projection
    tok = set_reference_latitude(lat)
    try:
        dlon = 1000 / (6371008.8 * math.cos(math.radians(lat)) * math.pi / 180)
        x1, _ = to_xy(lat, lon)
        x2, _ = to_xy(lat, lon + dlon)
        assert abs((x2 - x1) - 1000) < 5
        assert abs(haversine_m(lat, lon, lat, lon + dlon) - 1000) < 5
    finally:
        _LAT0.reset(tok)


def test_region_id_is_stable():
    assert regions.region_id(39.4279722, -0.4184254) == regions.region_id(39.42801, -0.41838)
    assert regions.region_id(35.66, 139.70) != regions.region_id(-35.66, 139.70)


def test_emergency_numbers_never_guess():
    assert emergency.numbers("JP")["call"][0]["number"] == "110"
    assert emergency.numbers("es")["call"][0]["number"] == "112"
    unknown = emergency.numbers("ZZ")
    assert unknown["call"] == [] and not unknown["known"]


def test_validator_requires_country_primary_number():
    from safeground.agents.validators import validate_safety_plan
    from safeground.engine import data
    from safeground.engine.respond import Incident, plan_facts
    from safeground.agents.safety_planner import template_plan
    facts = plan_facts(Incident("air_raid", None, None, {}), 13.0358, 80.2280, "home_ground")
    facts["call"] = [{"number": "911", "for": "Emergency"}]
    plan = template_plan(facts)
    assert not any("call list" in v for v in validate_safety_plan(plan, facts, data.load().rulebooks["air_raid"]))
    plan.call = ["112 - Emergency"]
    assert any("911" in v for v in validate_safety_plan(plan, facts, data.load().rulebooks["air_raid"]))
