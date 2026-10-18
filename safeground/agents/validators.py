"""Deterministic checks on agent output. An empty list means the output is accepted."""
from __future__ import annotations

import re

from safeground.models import ReadinessReport, SafetyPlan

NUM = re.compile(r"(?<![\w.])(\d+(?:[.,]\d+)?)(?![\w])")
ALWAYS_OK = {0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 100.0, 101.0, 108.0, 112.0, 2016.0, 2025.0}

FORBIDDEN_PATTERNS = {
    "gas": [(r"\b(basement|cellar|underground|underpass|subway)\b", "sends people low (gas collects in low areas)"),
            (r"\b(go|move|walk|head|run)\b[^.]{0,20}\bdownwind\b", "sends people downwind"),
            (r"\btowards? the (leak|source|plant|factory)\b", "sends people toward the source")],
    "flood": [(r"\b(basement|cellar|underpass|subway)\b", "sends people below ground in a flood"),
              (r"\b(drive|walk|wade)\b[^.]{0,25}\bthrough\b[^.]{0,15}\bwater\b", "suggests crossing flood water")],
    "explosion": [(r"\btowards? the (blast|bomb|device|scene|source)\b", "sends people toward the device"),
                  (r"\b(look|watch|go)\b[^.]{0,15}\b(out of|to|at) the window", "draws people to windows")],
    "air_raid": [(r"\bstay (outside|outdoors)\b", "keeps people outdoors during an air raid")],
    "earthquake": [(r"\b(stand|shelter|wait|go)\b[^.]{0,15}\bdoorways?\b", "sends people to doorways (Ready.gov: avoid)"),
                   (r"\b(use|take)\b[^.]{0,12}\b(lifts?|elevators?)\b", "suggests using a lift"),
                   (r"\b(enter|go back into|return to)\b[^.]{0,20}\bdamaged\b", "sends people into damaged buildings")],
    "tsunami": [(r"\b(go|walk|head|run|drive)\b[^.]{0,20}\b(beach|shore|shoreline|sea ?front|harbou?r)\b",
                 "sends people toward the sea"),
                (r"\bwait\b[^.]{0,25}\b(warning|order|siren)s?\b", "tells people to wait for a warning")],
    "cyclone": [(r"\bclimb\b[^.]{0,15}\battic\b", "sends people into a closed attic"),
                (r"\b(drive|walk|wade|swim)\b[^.]{0,25}\bthrough\b[^.]{0,15}\bwater\b", "suggests crossing flood water")],
    "wildfire": [(r"\b(go|move|walk|head|run|drive)\b[^.]{0,20}\bdownwind\b", "sends people downwind of the fire"),
                 (r"\btowards? the (fire|flames|smoke)\b", "sends people toward the fire")],
    "heat": [(r"\b(stay|wait|leave)\b[^.]{0,25}\b(car|vehicle)\b[^.]{0,15}\b(closed|windows up)\b",
              "leaves people in a closed car")],
}
NEGATION = re.compile(r"\b(never|not|don't|do not|avoid|no)\b[^.]{0,30}$", re.I)


def numbers_in(obj, out: set[float] | None = None) -> set[float]:
    """Every number appearing anywhere in a nested structure (plus simple unit conversions)."""
    out = set() if out is None else out
    if isinstance(obj, bool):
        return out
    if isinstance(obj, (int, float)):
        v = float(obj)
        out.update({v, round(v), round(v, 1), round(v / 1000, 1), round(v / 1000, 2), round(v * 100, 1)})
        return out
    if isinstance(obj, str):
        for m in NUM.findall(obj):
            numbers_in(float(m.replace(",", "")), out)
        return out
    if isinstance(obj, dict):
        for v in obj.values():
            numbers_in(v, out)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            numbers_in(v, out)
    return out


def unsupported_numbers(text: str, allowed: set[float]) -> list[str]:
    bad = []
    for m in NUM.findall(text):
        v = float(m.replace(",", ""))
        if v in ALWAYS_OK or v in allowed:
            continue
        if any(abs(v - a) <= max(1.0, 0.02 * abs(a)) for a in allowed):
            continue
        bad.append(m)
    return bad


def validate_safety_plan(plan: SafetyPlan, facts: dict, rulebook: dict) -> list[str]:
    v: list[str] = []
    if plan.danger_level != facts["tier"]:
        v.append(f"danger_level must be '{facts['tier']}' (computed), got '{plan.danger_level}'")
    if plan.main_move != facts["main_move"]:
        v.append(f"main_move must be '{facts['main_move']}' (computed), got '{plan.main_move}'")
    if plan.main_move in facts["forbidden_moves"]:
        v.append(f"main_move {plan.main_move} is forbidden for this hazard")
    spot_ids = {a["id"] for a in facts["advice"]}
    scenario = facts.get("scenario", facts.get("incident", {}).get("params", {}).get("scenario"))
    tier_ids = {a["id"] for a in rulebook["advice"] if facts["tier"] in a["tiers"]
                and (not a.get("scenarios") or scenario in a["scenarios"])}
    for label, steps, allowed_ids in (("do_now", plan.do_now, spot_ids), ("do_not", plan.do_not, tier_ids)):
        for s in steps:
            if not s.advice_ids:
                v.append(f"{label} step '{s.text[:50]}' cites no advice id")
            for a in s.advice_ids:
                if a not in allowed_ids:
                    v.append(f"{label} step cites '{a}', which is not an allowed advice id for this tier/situation")
    for s in plan.if_you_are:
        for a in s.advice_ids:
            if a not in tier_ids:
                v.append(f"if_you_are '{s.situation}' cites unknown advice id '{a}'")
    allowed_nums = numbers_in(facts)
    for field_name, text in [("where_to_go", plan.where_to_go), ("danger_reason", plan.danger_reason)] + \
            [("do_now", s.text) for s in plan.do_now] + [("if_you_are", s.text) for s in plan.if_you_are]:
        bad = unsupported_numbers(text, allowed_nums)
        if bad:
            v.append(f"{field_name} contains numbers not in the computed facts: {bad}")
    for pattern, why in FORBIDDEN_PATTERNS.get(facts["hazard"], []):
        for s in plan.do_now + [type("S", (), {"text": plan.where_to_go})()]:
            m = re.search(pattern, s.text, flags=re.I)
            if m and not NEGATION.search(s.text[:m.start()] + " "):
                v.append(f"unsafe instruction ({why}): '{s.text[:80]}'")
    primary = (facts.get("call") or [{}])[0].get("number")
    if primary and not any(primary in c for c in plan.call):
        v.append(f"call list must include {primary} (from FACTS.call)")
    return v


def validate_readiness(report: ReadinessReport, tool_outputs: list, allowed_urls: set[str],
                       area_cells: set[str]) -> list[str]:
    v: list[str] = []
    for c in report.calamities:
        if not c.source_url.startswith("http"):
            v.append(f"calamity '{c.type} {c.date}' has no source URL")
        elif c.evidence_kind == "news" and allowed_urls and c.source_url not in allowed_urls:
            v.append(f"calamity '{c.type} {c.date}' cites a URL not returned by the news search: {c.source_url}")
        if not c.date.strip():
            v.append(f"calamity '{c.type}' has no date")
    allowed_nums = numbers_in(tool_outputs) | numbers_in([c.date for c in report.calamities])
    texts = [("summary", report.summary)]
    for r in report.readiness:
        texts += [(f"readiness {r.calamity}/{m.phase}/{m.group}", m.finding) for m in r.matrix]
    for r in report.recommendations:
        texts += [(f"recommendation {r.rank} why", r.why), (f"recommendation {r.rank} protects", r.protects),
                  (f"recommendation {r.rank} where", r.where)]
        bad_hex = [h for h in r.map_hexes if h not in area_cells]
        if bad_hex:
            v.append(f"recommendation {r.rank} highlights hexes outside the area: {bad_hex[:3]}")
    for label, text in texts:
        bad = unsupported_numbers(text, allowed_nums)
        if bad:
            v.append(f"{label}: numbers not found in tool outputs: {bad}")
    ranks = sorted(r.rank for r in report.recommendations)
    if ranks != list(range(1, len(ranks) + 1)):
        v.append(f"recommendation ranks must be 1..{len(ranks)}, got {ranks}")
    return v
