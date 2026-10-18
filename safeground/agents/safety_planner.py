"""SafetyPlanner agent: rewrites computed plan facts into the fixed SafetyPlan format."""
from __future__ import annotations

import json

from google.adk import Agent
from google.genai import types

from safeground.agents.llm import parse_json, run_agent
from safeground.agents.validators import validate_safety_plan
from safeground.config import MODEL
from safeground.engine import data
from safeground.models import SafetyPlan, SituationVariant, Step

INSTRUCTION = """You write emergency safety plans for ONE person at ONE location, for a disaster simulation.
You receive FACTS computed by SafeGround's engine from official guidance and map data, and OTHER_ADVICE.

Produce a SafetyPlan:
- danger_level = FACTS.tier and main_move = FACTS.main_move (never change them). main_move_text = FACTS.main_move_text.
- danger_reason: one sentence using FACTS.tier_meaning and FACTS.zone_basis.
- where_to_go: if FACTS.target exists, name it (use its label or name), give its direction and FACTS.route walking minutes
  and length. If there is no target, write what to do in place (e.g. "Stay where you are and ...").
- do_now: 2-5 short steps for THIS person's situation (FACTS.situation_label). Each step must be based on one or more
  items in FACTS.advice and list their ids in advice_ids. Simplify the wording but never change its meaning.
- do_not: 1-3 short warnings based on FACTS.forbidden_moves and advice items, with advice_ids.
- if_you_are: up to 4 short variants for OTHER situations, using ids from OTHER_ADVICE.
- call: copy FACTS.call as "number - for".
- confidence: "high" when the zone comes from official distance tables and FACTS.data_gaps has at most one item,
  "medium" when estimates (flood susceptibility, building heights) or several data gaps are involved, "low" when tier is
  "unknown". Explain in confidence_reason.
- unknowns: the important items from FACTS.data_gaps and FACTS.caveats.
- valid_while: copy FACTS.valid_while.

Hard rules: use ONLY numbers that appear in FACTS. Do not invent places, streets, distances or advice.
Never tell people to go to basements, underground or low places in a gas leak or flood, never downwind, never toward
the source or the sea, never into flood water. FACTS.nearby_500m lists mapped schools, elderly homes and clinics close by;
mention them only as people who may need help. Plain English, short sentences."""


def make_agent() -> Agent:
    return Agent(name="safety_planner", model=MODEL, instruction=INSTRUCTION, output_schema=SafetyPlan,
                 generate_content_config=types.GenerateContentConfig(temperature=0))


def _prompt(facts: dict, rulebook: dict, feedback: list[str] | None) -> str:
    slim = {k: v for k, v in facts.items() if k not in ("route_coords", "sources")}
    scenario = facts.get("scenario", facts["incident"]["params"].get("scenario"))
    other = [{"id": a["id"], "situations": a["situations"], "text": a["text"]}
             for a in rulebook["advice"] if facts["tier"] in a["tiers"]
             and (not a.get("scenarios") or scenario in a["scenarios"])]
    msg = f"FACTS:\n{json.dumps(slim, ensure_ascii=False)}\n\nOTHER_ADVICE:\n{json.dumps(other, ensure_ascii=False)}"
    if feedback:
        msg += "\n\nYour previous answer was rejected by the validator. Fix ALL of these problems:\n- " + \
               "\n- ".join(feedback)
    return msg


def template_plan(facts: dict) -> SafetyPlan:
    """Deterministic fallback: official advice lines verbatim, no LLM."""
    adv = facts["advice"]
    do_now = [Step(text=a["text"], advice_ids=[a["id"]]) for a in adv[:4]] or \
             [Step(text="Follow official instructions.", advice_ids=[]), Step(text="Stay alert.", advice_ids=[])]
    if len(do_now) < 2:
        do_now.append(Step(text="Follow official instructions and updates.", advice_ids=[adv[0]["id"]] if adv else []))
    t, r = facts.get("target"), facts.get("route")
    where = "Stay where you are and follow official instructions."
    if t and r:
        where = f"{t.get('label') or t['name']}, {t['direction']}, about {r['walk_minutes']} min walk ({r['length_m']} m)."
    return SafetyPlan(
        danger_level=facts["tier"], danger_reason=facts["tier_meaning"], main_move=facts["main_move"],
        main_move_text=facts["main_move_text"], where_to_go=where, do_now=do_now[:5],
        do_not=[Step(text=f"Do not: {m.replace('_', ' ').lower()}", advice_ids=[]) for m in facts["forbidden_moves"][:3]],
        if_you_are=[], call=[f"{c['number']} - {c['for']}" for c in facts["call"]],
        confidence="medium", confidence_reason="Template plan (AI planner unavailable); official advice quoted verbatim.",
        unknowns=facts["data_gaps"][:4], valid_while=facts["valid_while"])


def plan(facts: dict, max_attempts: int = 3) -> dict:
    rulebook = data.load().rulebooks[facts["hazard"]]
    agent = make_agent()
    feedback: list[str] | None = None
    attempts = []
    for _ in range(max_attempts):
        try:
            out = run_agent(agent, _prompt(facts, rulebook, feedback))
            sp = SafetyPlan.model_validate(parse_json(out["text"]))
        except Exception as e:  # model/network/schema failure -> retry, then fall back
            attempts.append({"error": str(e)[:300]})
            feedback = [f"Output was not valid SafetyPlan JSON: {str(e)[:200]}"]
            continue
        violations = validate_safety_plan(sp, facts, rulebook)
        attempts.append({"violations": violations, "cached": out.get("cached"), "latency_s": out.get("latency_s")})
        if not violations:
            return {"plan": sp.model_dump(), "generated_by": "gemini", "attempts": attempts}
        feedback = violations
    return {"plan": template_plan(facts).model_dump(), "generated_by": "template", "attempts": attempts}
