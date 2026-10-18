"""NewsResearcher: finds past calamities for an area with Google Search grounding, then checks every link."""
from __future__ import annotations

import re

import httpx
from google.adk import Agent
from google.adk.tools import google_search
from google.genai import types

from safeground.agents.llm import parse_json, run_agent
from safeground.config import MODEL

INSTRUCTION = """You research the disaster history of one area of Chennai, India, using Google Search.
Find specific past events (2005 onwards) that affected the area or its immediate surroundings: floods and
waterlogging, cyclones, gas leaks, industrial accidents, oil or chemical spills, fires, heatwaves, building
collapses, drought or water scarcity, disease outbreaks after floods.

Return ONLY a JSON array (no prose). Each item:
{"type": "...", "date": "YYYY-MM-DD or YYYY-MM or YYYY", "place": "...", "what_happened": "one sentence",
 "url": "the exact URL of the news or official page you used"}
Rules: only events you found in search results with a real URL; one item per event; at most 12 items;
prefer official sources and established newspapers; never invent URLs."""

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/605.1.15 (KHTML, like Gecko) "
                    "Version/17.0 Safari/605.1.15"}


GLOBAL_INSTRUCTION = INSTRUCTION.replace("one area of Chennai, India", "one place (a town, city or city district)") \
    .replace("2005 onwards", "2000 onwards").replace("disease outbreaks after floods.",
                                                    "disease outbreaks after floods, earthquakes, storms, landslides.")


def make_agent(global_: bool = False) -> Agent:
    return Agent(name="news_researcher", model=MODEL, instruction=GLOBAL_INSTRUCTION if global_ else INSTRUCTION,
                 tools=[google_search],
                 generate_content_config=types.GenerateContentConfig(
                     temperature=0, thinking_config=types.ThinkingConfig(thinking_level="low")))


def _resolve(uri: str, client: httpx.Client) -> str:
    try:
        r = client.head(uri, follow_redirects=True, timeout=8)
        return str(r.url)
    except Exception:
        return uri


def verify_url(url: str, area: str, year: str, client: httpx.Client, city: str | None = "chennai") -> dict:
    """Fetch the page and check it mentions the area (or Chennai) and the year."""
    try:
        r = client.get(url, follow_redirects=True, timeout=10)
    except Exception as e:
        return {"verified": False, "reason": f"unreachable ({type(e).__name__})"}
    via = None
    if r.status_code in (401, 403, 429, 451, 503):  # site blocks automated checks: check the Internet Archive copy
        try:
            a = client.get(f"https://web.archive.org/web/2026/{url}", follow_redirects=True, timeout=25)
            if a.status_code == 200 and "/web/" in str(a.url):
                r, via = a, "Internet Archive copy (the site blocks automated checks)"
        except Exception:
            pass
    if r.status_code != 200:
        return {"verified": False, "reason": f"HTTP {r.status_code} (site may block automated checks)"}
    final_url = url if via else str(r.url)
    text = re.sub(r"<[^>]+>", " ", r.text[:400000]).lower()
    place_ok = area.lower().split()[0] in text or bool(city and city in text)
    year_ok = year in text
    return {"verified": place_ok and year_ok, "final_url": final_url,
            "reason": (f"page mentions the place and year{' — checked via ' + via if via else ''}") if place_ok and year_ok else
            f"page {'lacks the place' if not place_ok else ''}{' and ' if not place_ok and not year_ok else ''}"
            f"{'lacks the year' if not year_ok else ''}".strip()}


def research(area: str, context: str | None = None) -> dict:
    """context: e.g. 'Valencian Community, Spain' for places outside Chennai (None keeps the Chennai prompt)."""
    out = None
    prompt = f"Area: {area}, {context}." if context else f"Area: {area}, Chennai, Tamil Nadu, India."
    for attempt in range(2):  # one retry; on failure fall back to curated + dataset records
        try:
            out = run_agent(make_agent(global_=bool(context)), prompt)
            break
        except Exception as e:  # timeout, quota, network
            err = f"{type(e).__name__}: {str(e)[:150]}"
    if out is None:
        return {"events": [], "grounding_sources": [], "error": err,
                "note": "Live news search failed; curated and dataset records only."}
    try:
        events = parse_json(out["text"])
        events = events if isinstance(events, list) else []
    except Exception:
        events = []
    checked = []
    with httpx.Client(headers=UA) as client:
        grounding = [{**g, "resolved": _resolve(g["uri"], client)} for g in out.get("grounding", [])[:20]]
        for e in events[:12]:
            url = str(e.get("url") or "")
            if not url.startswith("http"):
                continue
            year = str(e.get("date", ""))[:4]
            v = verify_url(url, area, year, client, "chennai" if not context else None)
            final = v.pop("final_url", None)
            if final and "grounding-api-redirect" not in final:
                e = {**e, "url": final}  # keep the publisher's address, not Google's temporary redirect
            checked.append({**e, **v, "evidence_kind": "news"})
    return {"events": checked, "grounding_sources": grounding, "cached": out.get("cached"),
            "latency_s": out.get("latency_s")}
