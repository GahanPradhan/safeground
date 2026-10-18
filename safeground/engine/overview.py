"""Place overview: which hazards this place has a record of, and what is exposed. Computed only from loaded data."""
from __future__ import annotations

import json
import re

from safeground import config
from safeground.engine import data, earth, prepare, regions

REPORTS = config.ROOT / "data" / "cache" / "reports"
HISTORY_TYPES = {  # history record type -> hazard
    "earthquake": "earthquake", "flood": "flood", "extreme rainfall": "flood", "tropical cyclone": "cyclone",
    "fire (satellite detection)": "wildfire", "wildfire": "wildfire", "drought": "heat", "tsunami": "tsunami",
}
NEWS_WORDS = [  # report calamity type keywords -> hazard
    (r"explosion|blast|bomb", "explosion"), (r"gas|chemical|ammonia|chlorine|toxic", "gas"),
    (r"tsunami", "tsunami"), (r"earthquake|quake", "earthquake"), (r"cyclone|hurricane|typhoon|storm", "cyclone"),
    (r"wildfire|bushfire|forest fire", "wildfire"), (r"heat", "heat"), (r"flood|rain", "flood"),
    (r"air.?raid|missile|drone|strike|shelling|bombard", "air_raid"),
]


def _report(rid: str) -> dict | None:
    p = REPORTS / f"{rid}.json"
    return json.loads(p.read_text()) if p.exists() else None


def overview(rid: str) -> dict:
    m = regions.meta(rid)
    with data.use_region(rid):
        snap = data.load()
        area = {"name": m["name"], "lat": m["lat"], "lon": m["lon"], "radius_m": m["radius_m"],
                "cells": earth.cells_for(m["lat"], m["lon"], m["radius_m"])}
        prof = prepare.area_profile(area)
        hist = snap.manifests.get("history.json") or []
        hexes = [snap.hex_props(c) for c in area["cells"] if snap.hex_props(c)]
        counts = dict(prof.get("counts", {}))
        counts["underground_shelter"] = sum(len(snap.features[c].items) for c in data.SHELTER_CATEGORIES
                                            if c in snap.features)
        counts["open_area"] = len(snap.features.get("open_ground", data._feature_set([])).items)
        counts["fuel"] = len(snap.features.get("fuel", data._feature_set([])).items)

    ev: dict[str, list[dict]] = {}
    for h in hist:
        t = h.get("type", "")
        hz = HISTORY_TYPES.get(t.replace(" (summary)", ""))
        if hz:
            summary = "summary" in t or t == "fire (satellite detection)"  # FIRMS hits in cities are often flares
            if t == "extreme rainfall":  # the wettest days are always listed; only very heavy days count as events
                mm = re.search(r"(\d+(?:\.\d+)?) mm", h.get("what_happened", ""))
                summary = not (mm and float(mm.group(1)) >= 115.6)
            ev.setdefault(hz, []).append({"date": h.get("date"), "text": h.get("what_happened"), "summary": summary,
                                          "source": h.get("source_url") or h.get("url"), "kind": "dataset"})
    rep = _report(rid)
    if rep and rep.get("report"):
        checked = rep.get("sources_checked") or {}
        for c in rep["report"]["calamities"]:
            if c.get("evidence_kind") != "news" or not (checked.get(c["source_url"]) or {}).get("verified"):
                continue
            for pat, hz in NEWS_WORDS:
                if re.search(pat, c["type"] + " " + c["what_happened"], re.I):
                    ev.setdefault(hz, []).insert(0, {"date": c["date"], "text": c["what_happened"], "summary": False,
                                                     "source": c["source_url"], "kind": "news"})
                    break

    def n_events(hz):
        return sum(1 for e in ev.get(hz, []) if not e["summary"])

    elev = [p["elev_mean"] for p in hexes if p.get("elev_mean") is not None]
    low_ground = sum(1 for e in elev if e < 30.5)
    signals = {
        "gas": f"{counts.get('industrial', 0)} industrial sites and {counts['fuel']} fuel stations mapped",
        "explosion": f"{counts.get('industrial', 0)} industrial sites and {counts['fuel']} fuel stations mapped",
        "air_raid": f"{counts['underground_shelter']} underground shelters mapped (metro, car parks)",
        "tsunami": (f"{low_ground} of {len(elev)} blocks are below 30 m above sea level" if elev else None),
        "heat": (f"Tree cover {prof['trees_share_2025_pct']}% in 2025" if "trees_share_2025_pct" in prof else None),
        "cyclone": None, "earthquake": None, "flood": (f"{prof['low_lying_blocks_pct']}% of blocks low-lying"
                                                       if "low_lying_blocks_pct" in prof else None),
        "wildfire": (f"Trees {prof.get('trees_share_2025_pct', 0)}% · grass {prof.get('grass_share_2025_pct', 0)}% of land"
                     if "trees_share_2025_pct" in prof else None),
    }
    hazards = []
    for hz, rb in snap.rulebooks.items():
        n = n_events(hz)
        news = any(e["kind"] == "news" for e in ev.get(hz, []))
        level = "high" if news or n >= 3 else "medium" if n >= 1 else "low"
        if hz == "tsunami" and level == "low" and low_ground and n_events("earthquake"):
            level = "medium"
        if hz in ("gas", "explosion") and level == "low" and counts.get("industrial", 0) >= 5:
            level = "medium"
        hazards.append({"id": hz, "title": rb["title"], "group": rb.get("group", "natural"), "level": level,
                        "events": n, "evidence": ev.get(hz, [])[:4], "signal": signals.get(hz)})
    order = {"high": 0, "medium": 1, "low": 2}
    for h in hazards:
        h["evidence"] = sorted(h["evidence"], key=lambda e: (e["kind"] != "news", e["summary"]))
    hazards.sort(key=lambda h: (order[h["level"]], -h["events"]))
    timeline = [{**e, "hazard": hz} for hz, es in ev.items() for e in es if not e["summary"]]
    timeline.sort(key=lambda e: str(e.get("date") or ""), reverse=True)
    return {"region": {k: m.get(k) for k in ("id", "name", "admin", "country", "country_code", "lat", "lon",
                                              "radius_m", "map_data_source", "emergency", "built_at", "osm_timestamp")},
            "timeline": timeline[:25],
            "profile": {k: v for k, v in prof.items() if k not in ("centre", "named_water_bodies")},
            "counts": counts, "elevation_m": ({"min": round(min(elev)), "max": round(max(elev))} if elev else None),
            "hazards": hazards, "report_ready": bool(rep and rep.get("report"))}
