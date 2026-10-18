"""Output schemas the agents must produce (validated by Pydantic and by safeground.agents.validators)."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Tier = Literal["red", "orange", "yellow", "green", "unknown"]
Move = Literal["STAY_IN_SEAL", "MOVE_CROSSWIND_UPWIND", "MOVE_AWAY", "STAY_INSIDE_AWAY_FROM_WINDOWS", "GO_UP",
               "GO_DOWN_INSIDE", "STAY_ALERT", "AVOID", "DROP_COVER_HOLD", "MOVE_TO_OPEN_AREA", "GO_TO_HIGH_GROUND",
               "SHELTER_INTERIOR", "EVACUATE_AWAY_FROM_FIRE", "STAY_COOL"]


# ---------------------------------------------------------------- RESPOND
class Step(BaseModel):
    text: str = Field(description="One short instruction in plain English")
    advice_ids: list[str] = Field(description="Rulebook advice ids this step is based on (at least one)")


class SituationVariant(BaseModel):
    situation: str
    text: str
    advice_ids: list[str]


class SafetyPlan(BaseModel):
    danger_level: Tier
    danger_reason: str = Field(description="One line explaining the danger level using the given facts only")
    main_move: Move
    main_move_text: str
    where_to_go: str = Field(description="Named place, distance, direction and walking time from the facts, "
                                         "or 'Stay where you are' if there is no target")
    do_now: list[Step] = Field(min_length=2, max_length=5)
    do_not: list[Step] = Field(min_length=1, max_length=3)
    if_you_are: list[SituationVariant] = Field(max_length=5)
    call: list[str]
    confidence: Literal["high", "medium", "low"]
    confidence_reason: str
    unknowns: list[str]
    valid_while: list[str]


# ---------------------------------------------------------------- PREPARE
class Calamity(BaseModel):
    type: str = Field(description="flood, cyclone, gas leak, industrial accident, fire, heatwave, oil spill, ...")
    date: str = Field(description="YYYY-MM-DD or YYYY-MM or YYYY")
    what_happened: str
    source_url: str
    evidence_kind: Literal["news", "dataset"]


class ReadinessCell(BaseModel):
    phase: Literal["before", "during", "after"]
    group: Literal["people", "animals", "nature"]
    level: Literal["good", "fair", "poor", "unknown"]
    finding: str = Field(description="What the tools show, quoting their numbers exactly")
    evidence: list[str] = Field(description="Tool names / dataset ids the finding comes from")


class Recommendation(BaseModel):
    rank: int
    what: str
    where: str = Field(description="Named places, streets or blocks from the tool outputs")
    why: str = Field(description="Reason with the exact numbers from the tools")
    protects: str = Field(description="Who or what it protects: people, animals, nature, with counts if known")
    calamity: str
    phase: Literal["before", "during", "after"]
    evidence: list[str]
    confidence: Literal["high", "medium", "low"]
    map_hexes: list[str] = Field(default_factory=list, description="H3 ids to highlight, copied from tool outputs")


class CalamityReadiness(BaseModel):
    calamity: str
    why_it_matters_here: str
    overall: Literal["good", "fair", "poor", "unknown"]
    matrix: list[ReadinessCell]


class ReadinessReport(BaseModel):
    area: str
    summary: str = Field(description="3 sentences for a resident: main risks, readiness, top action")
    calamities: list[Calamity]
    readiness: list[CalamityReadiness]
    recommendations: list[Recommendation] = Field(min_length=3, max_length=8)
    data_gaps: list[str]
