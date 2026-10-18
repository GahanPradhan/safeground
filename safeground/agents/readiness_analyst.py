"""ReadinessAnalyst: decides which readiness checks matter for an area's own calamities, runs them, reports."""
from __future__ import annotations

import functools
import json
import os

import yaml
from google.adk import Agent
from google.genai import types

from safeground.agents import news_researcher
from safeground.agents.llm import parse_json, run_agent
from safeground.agents.validators import validate_readiness
from safeground.config import MODEL, ROOT, SNAPSHOT
from safeground.engine import data, prepare
from safeground.models import ReadinessReport

INVESTIGATE = """You are SafeGround's disaster-readiness investigator for one area of Chennai.
You get the area's KNOWN CALAMITIES (curated news with checked links and satellite records).
1. Decide which calamities matter most here (most frequent, most recent, most severe). Use only the given calamities.
2. Call the tools that are relevant to those calamities to measure readiness BEFORE (avoid/reduce), DURING (protect)
   and AFTER (recover) for PEOPLE, ANIMALS and NATURE. Choose by context, for example: floods -> get_flood_exposure,
   get_nature_change, get_access('flood_refuge'); gas leaks or industry -> get_industrial_exposure, get_access('hospital');
   any calamity -> get_access('hospital'), get_animal_facilities. Do not call tools that are irrelevant here.
3. Finish with 2-4 sentences: which calamities you prioritised and why, and which checks you ran for each."""

WRITE = """You write SafeGround's disaster-readiness report for one area of Chennai, for residents and local officials.
Inputs: KNOWN CALAMITIES, the INVESTIGATOR's note, and TOOL RESULTS (measured data).
Write the ReadinessReport:
- calamities: the given calamities you rely on (type, date, what_happened, source_url = the given url, evidence_kind).
- readiness: for the 1-3 most important calamities, a matrix of cells (phase before/during/after x group
  people/animals/nature). Each finding quotes TOOL RESULTS numbers exactly and names the evidence (tool name).
  Use level "unknown" when there is no data - never guess.
- recommendations: 3-6, ranked by people protected and severity: what, where (place names / features from the tool
  results), why (with tool numbers), who/what it protects, calamity, phase, evidence, confidence, map_hexes
  (only hex ids copied from TOOL RESULTS, e.g. gap_hexes or worst_blocks).
- data_gaps: what could not be measured.
Hard rules: every number must come from TOOL RESULTS or the calamity list. No invented facts, places or URLs."""

TIMEOUT_MS = 150_000
INVESTIGATE_GLOBAL = INVESTIGATE.replace("one area of Chennai", "one place")
WRITE_GLOBAL = WRITE.replace("one area of Chennai", "one place") + """
- Data covers only the loaded area (3 km around the place). When a tool says a facility is not mapped within the loaded
  area, write exactly that (e.g. "no major hospital is mapped within 3 km") - never claim residents have no access or
  are isolated, because the nearest one may be just outside the area."""


def _in_region(rid: str | None):
    """Run a tool against the analysed region (tools may run on another thread or task)."""
    def deco(fn):
        @functools.wraps(fn)
        def wrapper(*a, **kw):
            with data.use_region(rid):
                return fn(*a, **kw)
        return wrapper
    return deco


def _tools(area: dict):
    def get_area_profile() -> dict:
        """Residents, land cover (2016 vs 2025), low-lying share, water nearby, building heights and counts of
        hospitals, schools, elderly homes, shelters, metro stations, vets, industrial sites in the area."""
        return prepare.area_profile(area)

    def get_access(kind: str) -> dict:
        """Walking access from every block to the nearest facility. kind is one of: hospital, fire_station, police,
        underground_shelter, open_ground, vet, flood_refuge. Returns shares of residents within 500 m/1 km/2 km and
        the worst-served blocks."""
        if kind not in prepare.ACCESS_TARGETS:
            return {"error": f"kind must be one of {sorted(prepare.ACCESS_TARGETS)}"}
        return prepare.access(area, kind)

    def get_flood_exposure() -> dict:
        """Low-lying blocks, residents there, blocks with no flood refuge (tall building) within 300 m,
        underpasses, and schools / elderly homes / hospitals in low-lying blocks."""
        return prepare.flood_exposure(area)

    def get_industrial_exposure() -> dict:
        """Industrial and storage sites within 4.2 km (worst-case ERG ammonia protective distance)."""
        return prepare.industrial_exposure(area)

    def get_nature_change() -> dict:
        """Tree, water, built-up, grass and wetland cover in 2016 vs 2025 (Google Dynamic World), protected areas,
        named lakes and wetlands."""
        return prepare.nature(area)

    def get_animal_facilities() -> dict:
        """Veterinary clinics, animal shelters, zoos nearby, walking access to vets, and animal data gaps."""
        return prepare.animals(area)

    wrap = _in_region(area.get("region"))
    return [wrap(f) for f in (get_area_profile, get_access, get_flood_exposure, get_industrial_exposure,
                              get_nature_change, get_animal_facilities)]


def make_investigator(area: dict) -> Agent:
    return Agent(name="readiness_investigator", model=MODEL,
                 instruction=INVESTIGATE_GLOBAL if area.get("region") else INVESTIGATE, tools=_tools(area),
                 generate_content_config=types.GenerateContentConfig(
                     temperature=0, http_options=types.HttpOptions(timeout=TIMEOUT_MS)))


def make_writer(global_: bool = False) -> Agent:
    return Agent(name="readiness_writer", model=MODEL, instruction=WRITE_GLOBAL if global_ else WRITE,
                 output_schema=ReadinessReport,
                 generate_content_config=types.GenerateContentConfig(
                     temperature=0, http_options=types.HttpOptions(timeout=TIMEOUT_MS),
                     thinking_config=types.ThinkingConfig(thinking_level="low")))


def dataset_calamities(area: dict) -> list[dict]:
    """Calamities from satellite / dataset records precomputed for the area (pipeline/gee_history.py)."""
    if area.get("region"):  # regions built on demand store a plain list for their centre
        with data.use_region(area["region"]):
            return list(data.load().manifests.get("history.json") or [])
    path = SNAPSHOT / "history.json"
    if not path.exists():
        return []
    hist = json.loads(path.read_text())
    return hist.get(area["name"], [])


def curated_calamities(area: dict) -> list[dict]:
    """Hand-checked past events with public sources (safeground/curated/events.yaml)."""
    cur = ROOT / "safeground" / "curated"
    events = (yaml.safe_load((cur / "events.yaml").read_text()) or {}).get(area["name"], [])
    checks = json.loads((cur / "events_verification.json").read_text())
    return [{**e, "date": str(e["date"]), "source_url": e["url"], "evidence_kind": "news", "curated": True,
             **checks.get(e["url"], {"verified": False, "reason": "not checked"})} for e in events]


def analyse(area_name: str, radius_m: float = 1500, max_attempts: int = 3, region: str | None = None) -> dict:
    if region:
        from safeground.engine import regions
        area = regions.area_for(region, radius_m)
        m = regions.meta(region)
        context = ", ".join(x for x in [m.get("admin"), m.get("country")] if x) or None
    else:
        area, context = prepare.resolve_area(area_name, radius_m), None
    # Live Google Search grounding is used only when the owner switches it on (SAFEGROUND_NEWS_SEARCH=1).
    if os.getenv("SAFEGROUND_NEWS_SEARCH") == "1":
        news = news_researcher.research(area["name"], context) if region else news_researcher.research(area["name"])
    else:
        news = {"events": [], "note": "Live news search is switched off; curated and dataset records only."}
    curated = [] if region else curated_calamities(area)
    # only news events whose link opened and mentions the place and year; the rest stay visible in "news"
    known = curated + [e for e in news["events"] if e.get("verified")] + dataset_calamities(area)
    allowed_urls = {e["url"] for e in known if e.get("url")}
    sources_checked = {e["url"]: {"verified": e.get("verified"), "reason": e.get("reason")}
                       for e in curated + news["events"]}
    where = f"{area['name']}, {context}" if region and context else area["name"]
    head = (f"AREA: {where} (centre {area['lat']:.4f}, {area['lon']:.4f}, radius {radius_m:.0f} m, "
            f"{len(area['cells'])} blocks)\nKNOWN CALAMITIES:\n{json.dumps(known, ensure_ascii=False)}")
    inv = run_agent(make_investigator(area), head)
    tool_results = [{"tool": c["name"], "args": c.get("args")} for c in inv["tool_calls"] if "args" in c]
    responses = [c["response"] for c in inv["tool_calls"] if "response" in c]
    for tr, resp in zip(tool_results, responses):
        tr["result"] = resp
    writer, feedback, attempts = make_writer(global_=bool(region)), None, []
    report = None
    for _ in range(max_attempts):
        p = (head + f"\nINVESTIGATOR NOTE:\n{inv['text']}\nTOOL RESULTS:\n{json.dumps(tool_results, default=str)}"
             + ("\n\nYour previous report was rejected. Fix ALL of these:\n- " + "\n- ".join(feedback) if feedback else ""))
        try:
            out = run_agent(writer, p)
            report = ReadinessReport.model_validate(parse_json(out["text"]))
        except Exception as e:
            attempts.append({"error": str(e)[:300]})
            feedback = [f"Output was not valid ReadinessReport JSON: {str(e)[:200]}"]
            continue
        violations = validate_readiness(report, responses + [known], allowed_urls, set(area["cells"]))
        attempts.append({"violations": violations, "cached": out.get("cached"), "latency_s": out.get("latency_s")})
        if not violations:
            break
        feedback = violations
    base = {"area": {k: v for k, v in area.items() if k != "cells"}, "cells": area["cells"], "region": region,
            "investigator": {"note": inv["text"], "tools_called": [t["tool"] + (f"({t['args'].get('kind')})"
                             if t.get("args", {}).get("kind") else "") for t in tool_results]},
            "news": news, "sources_checked": sources_checked, "attempts": attempts}
    if report is not None and attempts and not attempts[-1].get("violations") and "error" not in attempts[-1]:
        return {**base, "report": report.model_dump(), "validated": True}
    return {**base, "report": report.model_dump() if report else None, "validated": False}
