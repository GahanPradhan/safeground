import yaml
from shapely.geometry import Point

from safeground.config import RULEBOOKS
from safeground.engine import zones
from safeground.engine.geo import offset

GAS = yaml.safe_load((RULEBOOKS / "gas.yaml").read_text())
EXP = yaml.safe_load((RULEBOOKS / "explosion.yaml").read_text())
SRC = (13.2146, 80.3203)


def test_gas_large_ammonia_night_low_wind_matches_erg_table3():
    z = zones.gas_zone(GAS, *SRC, "ammonia", "rail_tank_car", wind_from_deg=90, wind_speed_ms=1.5, is_day=False)
    assert z.basis["isolate_m"] == round(1000 * 0.3048)
    assert z.basis["protective_distance_m"] == round(2.6 * 1609.344)
    # wind from the east -> plume goes west
    west = offset(*SRC, 270, 3000)
    east = offset(*SRC, 90, 3000)
    assert z.tier_at(*west) == "orange"
    assert z.tier_at(*east) == "green"
    assert z.tier_at(*offset(*SRC, 0, 100)) == "red"


def test_gas_wind_class_changes_distance():
    lo = zones.gas_zone(GAS, *SRC, "chlorine", "highway_tank_truck", 0, 1.0, True)
    hi = zones.gas_zone(GAS, *SRC, "chlorine", "highway_tank_truck", 0, 8.0, True)
    assert lo.basis["protective_distance_m"] > hi.basis["protective_distance_m"]
    assert hi.basis["wind_class"] == "high"


def test_gas_yellow_band_is_beside_plume():
    z = zones.gas_zone(GAS, *SRC, "ammonia", "rail_tank_car", 0, 3.0, True)  # wind from north -> plume south
    side = offset(*SRC, 180 + 20, 1200)  # 20 degrees off the plume axis
    assert z.tier_at(*side) in ("orange", "yellow")


def test_explosion_car_bomb_rings():
    z = zones.explosion_zone(EXP, *SRC, "car")
    assert z.basis["building_evacuation_m"] == round(320 * 0.3048)
    assert z.basis["outdoor_evacuation_m"] == round(1500 * 0.3048)
    assert z.tier_at(*offset(*SRC, 45, 50)) == "red"
    assert z.tier_at(*offset(*SRC, 45, 300)) == "orange"
    assert z.tier_at(*offset(*SRC, 45, 600)) == "green"


def test_lpg_fire_isolation():
    z = zones.explosion_zone(EXP, *SRC, "lpg_tanker_fire")
    assert z.tier_at(*offset(*SRC, 200, 1500)) == "red"
    assert z.tier_at(*offset(*SRC, 200, 1700)) == "green"


def test_flood_tiers_follow_rules():
    rb = yaml.safe_load((RULEBOOKS / "flood.yaml").read_text())
    hexes = {"a": {"rel_elev": -4, "water_near_m": 200}, "b": {"rel_elev": -2}, "c": {"rel_elev": -1}, "d": {"rel_elev": 3}}
    z = zones.flood_zone(rb, hexes, rain_mm_24h=150)
    assert z.hex_tiers == {"a": "red", "b": "orange", "c": "yellow", "d": "green"}
    z2 = zones.flood_zone(rb, hexes, rain_mm_24h=20)
    assert z2.hex_tiers["a"] == "yellow" and z2.hex_tiers["b"] == "yellow"
