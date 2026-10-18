"""New hazards: official thresholds, zone shapes, moves and validator rules."""
import pytest

from safeground.agents.safety_planner import template_plan
from safeground.agents.validators import FORBIDDEN_PATTERNS, NEGATION
from safeground.engine import data, zones
from safeground.engine.respond import Incident, plan_facts

ANTAKYA, LAHAINA = "rp36204p36164_3000", "rp20887m156675_3000"


def test_heat_index_matches_nws_examples():
    # NWS chart: 90 °F and 40% RH -> about 91 °F; 104 °F and 40% -> about 119 °F
    assert zones.heat_index_f(32.2, 40) == pytest.approx(91, abs=1.5)
    assert zones.heat_index_f(40, 40) == pytest.approx(119, abs=2)
    classes = {"caution": 80, "extreme_caution": 90, "danger": 103, "extreme_danger": 125}
    assert [zones.heat_tier(v, classes) for v in (79, 85, 95, 110)] == ["green", "yellow", "orange", "red"]


def test_fire_zone_points_downwind():
    rb = data.load().rulebooks["wildfire"]
    z = zones.fire_zone(rb, 20.88, -156.67, wind_from_deg=0, wind_speed_ms=5)  # wind from north -> spreads south
    assert z.basis["spread_m_per_hour"] == 1800  # 10% of 5 m/s
    assert z.tier_at(20.88 - 0.012, -156.67) == "red"      # ~1.3 km downwind, within 1 h
    assert z.tier_at(20.88 + 0.012, -156.67) == "green"    # upwind


@pytest.mark.parametrize("hazard,params,move", [
    ("earthquake", {"phase": "during"}, "DROP_COVER_HOLD"),
    ("earthquake", {"phase": "after"}, "MOVE_TO_OPEN_AREA"),
    ("heat", {"temp_c": 40, "humidity": 40}, "STAY_COOL"),
    ("tsunami", {}, "STAY_ALERT"),  # Antakya is ~70 m+ above sea level
])
def test_new_hazard_moves_in_antakya(hazard, params, move):
    with data.use_region(ANTAKYA):
        f = plan_facts(Incident(hazard, None, None, params), 36.2036, 36.1638, "outdoors")
    assert f["main_move"] == move
    assert f["call"][0]["number"] == "112"
    template_plan(f)  # the fallback always builds


def test_tsunami_routes_low_coast_to_30m_ground():
    with data.use_region(LAHAINA):
        f = plan_facts(Incident("tsunami", None, None, {}), 20.8790, -156.6800, "outdoors")
    assert f["tier"] == "red" and f["main_move"] == "GO_TO_HIGH_GROUND"
    assert f["target"] and "above sea level" in f["target"]["label"]


def test_validator_patterns_respect_negation():
    import re
    pat, _ = FORBIDDEN_PATTERNS["wildfire"][0]
    bad, ok = "Walk downwind to the beach.", "Do not walk downwind."
    assert re.search(pat, bad, re.I) and not NEGATION.search(bad[:re.search(pat, bad, re.I).start()] + " ")
    m = re.search(pat, ok, re.I)
    assert m and NEGATION.search(ok[:m.start()] + " ")
