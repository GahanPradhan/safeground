import yaml

from safeground.agents.validators import numbers_in, unsupported_numbers, validate_safety_plan
from safeground.config import RULEBOOKS
from safeground.models import SafetyPlan, Step

GAS = yaml.safe_load((RULEBOOKS / "gas.yaml").read_text())

FACTS = {
    "hazard": "gas", "tier": "orange", "main_move": "STAY_IN_SEAL", "main_move_text": "Stay inside and seal the room",
    "forbidden_moves": ["GO_DOWN", "MOVE_DOWNWIND"],
    "advice": [{"id": "gas.indoor_room", "text": "x", "source": "ready_chemical"},
               {"id": "gas.indoor_ac", "text": "y", "source": "ready_chemical"}],
    "target": None, "route": None, "zone_basis": {"protective_distance_m": 4184, "isolate_m": 305},
    "data_gaps": [], "valid_while": [], "call": [{"number": "112", "for": "x"}],
}


def plan(**kw):
    base = dict(danger_level="orange", danger_reason="In the protective action zone (4184 m downwind distance).",
                main_move="STAY_IN_SEAL", main_move_text="Stay inside", where_to_go="Stay where you are.",
                do_now=[Step(text="Go to an inside room and close windows.", advice_ids=["gas.indoor_room"]),
                        Step(text="Switch off the AC.", advice_ids=["gas.indoor_ac"])],
                do_not=[Step(text="Do not go to the basement.", advice_ids=["gas.low_areas"])],
                if_you_are=[], call=["112 - emergency"], confidence="high", confidence_reason="ok",
                unknowns=[], valid_while=[])
    base.update(kw)
    return SafetyPlan(**base)


def test_good_plan_passes():
    assert validate_safety_plan(plan(), FACTS, GAS) == []


def test_wrong_tier_and_invented_number_and_basement_rejected():
    bad = plan(danger_level="red", where_to_go="Walk 950 m to the basement shelter.")
    v = validate_safety_plan(bad, FACTS, GAS)
    assert any("danger_level" in x for x in v)
    assert any("950" in x for x in v)
    assert any("unsafe instruction" in x for x in v)


def test_uncited_and_foreign_advice_rejected():
    bad = plan(do_now=[Step(text="Run outside now.", advice_ids=[]),
                       Step(text="Close windows.", advice_ids=["fl.enter_water"])])
    v = validate_safety_plan(bad, FACTS, GAS)
    assert any("cites no advice id" in x for x in v)
    assert any("fl.enter_water" in x for x in v)


def test_number_tolerance():
    allowed = numbers_in({"length_m": 1234, "walk_minutes": 16.5})
    assert unsupported_numbers("about 1.2 km, 16.5 minutes", allowed) == []
    assert unsupported_numbers("about 3.7 km", allowed) == ["3.7"]
