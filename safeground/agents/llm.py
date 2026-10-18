"""Run ADK agents with a record/replay cache so demos are reproducible.

SAFEGROUND_LLM_MODE:
  cached (default)  use a cached response when one exists, otherwise call Gemini and store the result
  live              always call Gemini (and refresh the cache)
  replay            never call Gemini; fail if no cached response exists
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
import time
import uuid

from google.adk import Agent, Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from safeground.config import ROOT

CACHE_DIR = ROOT / "data" / "cache" / "llm"


def _key(agent: Agent, prompt: str) -> str:
    h = hashlib.sha256()
    h.update(f"{agent.name}|{agent.model}|{agent.instruction}|{prompt}".encode())
    return h.hexdigest()[:24]


LIVE_CALLS_PER_HOUR = int(os.getenv("SAFEGROUND_LIVE_CALLS_PER_HOUR", "60"))
_live_calls: list[float] = []


def _rate_guard() -> None:
    """Budget protection: cap fresh Gemini calls per hour for the whole service (cached answers are free)."""
    now = time.time()
    _live_calls[:] = [t for t in _live_calls if now - t < 3600]
    if len(_live_calls) >= LIVE_CALLS_PER_HOUR:
        raise RuntimeError("Live AI limit reached for this hour; showing saved or official-text results instead.")
    _live_calls.append(now)


def ensure_permitted_credentials() -> None:
    """Only ever use the Gemini key the owner put in .env — never fall back to machine credentials (ADC)."""
    if not os.getenv("GOOGLE_API_KEY"):
        raise RuntimeError("No Gemini API key in .env (GOOGLE_API_KEY). SafeGround will not use any other credential.")
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "FALSE"  # AI Studio key path; never Vertex via ADC


async def _run(agent: Agent, prompt: str) -> dict:
    session_service = InMemorySessionService()
    runner = Runner(app_name="safeground", agent=agent, session_service=session_service)
    session = await session_service.create_session(app_name="safeground", user_id="safeground")
    final_text, tool_calls, grounding = "", [], []
    msg = types.Content(role="user", parts=[types.Part(text=prompt)])
    debug = os.getenv("SAFEGROUND_DEBUG") == "1"
    t0 = time.time()
    async for event in runner.run_async(user_id="safeground", session_id=session.id, new_message=msg):
        if debug:
            calls = [c.name for c in (event.get_function_calls() or [])]
            resps = [r.name for r in (event.get_function_responses() or [])]
            txt = "".join(p.text or "" for p in (event.content.parts if event.content and event.content.parts else [])
                          if getattr(p, "text", None))[:120].replace("\n", " ")
            print(f"[{time.time() - t0:6.1f}s] {agent.name} calls={calls} responses={resps} "
                  f"final={event.is_final_response()} text={txt!r}", flush=True)
        for call in event.get_function_calls() or []:
            tool_calls.append({"name": call.name, "args": dict(call.args or {})})
        for resp in event.get_function_responses() or []:
            tool_calls.append({"name": resp.name, "response": resp.response})
        gm = getattr(event, "grounding_metadata", None)
        if gm and getattr(gm, "grounding_chunks", None):
            for ch in gm.grounding_chunks:
                if ch.web:
                    grounding.append({"uri": ch.web.uri, "title": ch.web.title})
        if event.is_final_response() and event.content and event.content.parts:
            text = "".join(p.text or "" for p in event.content.parts if not getattr(p, "thought", False))
            if text.strip():
                final_text = text
    return {"text": final_text, "tool_calls": tool_calls, "grounding": grounding}


def run_agent(agent: Agent, prompt: str, mode: str | None = None) -> dict:
    mode = mode or os.getenv("SAFEGROUND_LLM_MODE", "cached")
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = CACHE_DIR / f"{agent.name}_{_key(agent, prompt)}.json"
    if mode in ("cached", "replay") and path.exists():
        out = json.loads(path.read_text())
        out["cached"] = True
        return out
    if mode == "replay":
        raise RuntimeError(f"No cached response for {agent.name}")
    ensure_permitted_credentials()
    _rate_guard()
    t0 = time.time()
    out = asyncio.run(_with_timeout(agent, prompt)) if not _in_loop() else _run_in_thread(agent, prompt)
    out.update({"cached": False, "latency_s": round(time.time() - t0, 1), "model": agent.model,
                "run_id": uuid.uuid4().hex[:8], "at": time.strftime("%Y-%m-%dT%H:%M:%S%z")})
    path.write_text(json.dumps(out, default=str))
    return out


RUN_TIMEOUT_S = float(os.getenv("SAFEGROUND_RUN_TIMEOUT_S", "240"))


async def _with_timeout(agent: Agent, prompt: str) -> dict:
    return await asyncio.wait_for(_run(agent, prompt), timeout=RUN_TIMEOUT_S)


def _in_loop() -> bool:
    try:
        asyncio.get_running_loop()
        return True
    except RuntimeError:
        return False


def _run_in_thread(agent: Agent, prompt: str) -> dict:
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(1) as ex:
        return ex.submit(lambda: asyncio.run(_with_timeout(agent, prompt))).result()


def parse_json(text: str) -> dict | list:
    t = text.strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[1].rsplit("```", 1)[0]
    return json.loads(t)
