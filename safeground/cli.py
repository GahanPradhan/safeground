"""Terminal entry points.

  python -m safeground.cli respond --hazard gas --at "Ennore" --incident "Ennore" --situation outdoors
  python -m safeground.cli prepare Velachery
"""
from __future__ import annotations

import argparse
import json

from safeground.engine import data
from safeground.engine.respond import Incident, plan_facts


def _point(name: str) -> tuple[float, float]:
    if "," in name:
        a, b = name.split(",")
        return float(a), float(b)
    hit = data.load().find_place(name)
    if not hit:
        raise SystemExit(f"place not found: {name}")
    return hit["lat"], hit["lon"]


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("respond")
    r.add_argument("--hazard", required=True, choices=["gas", "explosion", "flood", "air_raid"])
    r.add_argument("--at", required=True, help="place name or 'lat,lon' of the person")
    r.add_argument("--incident", help="place name or 'lat,lon' of the incident (gas / explosion)")
    r.add_argument("--situation", default="home_ground")
    r.add_argument("--params", default="{}", help="JSON params, e.g. '{\"wind_from_deg\": 90, \"wind_speed_ms\": 2}'")
    r.add_argument("--ai", action="store_true", help="also run the Gemini SafetyPlanner")
    p = sub.add_parser("prepare")
    p.add_argument("area")
    a = ap.parse_args()
    if a.cmd == "respond":
        lat, lon = _point(a.at)
        ilat, ilon = _point(a.incident) if a.incident else (None, None)
        params = {"wind_from_deg": 90, "wind_speed_ms": 2, **json.loads(a.params)}
        facts = plan_facts(Incident(a.hazard, ilat, ilon, params), lat, lon, a.situation)
        slim = {k: v for k, v in facts.items() if k not in ("route_coords", "sources", "caveats")}
        print(json.dumps(slim, indent=1, ensure_ascii=False))
        if a.ai:
            from safeground.agents import safety_planner
            print(json.dumps(safety_planner.plan(facts), indent=1, ensure_ascii=False))
    else:
        from safeground.agents import readiness_analyst
        print(json.dumps(readiness_analyst.analyse(a.area), indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
