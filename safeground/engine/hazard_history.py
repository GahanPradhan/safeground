"""Global disaster history from open APIs: USGS earthquakes and GDACS disaster alerts."""
from __future__ import annotations

import httpx

from safeground.engine.geo import haversine_m

UA = {"User-Agent": "SafeGround/1.0 (disaster readiness prototype; Google Cloud AI Builder Cup)"}
USGS = "https://earthquake.usgs.gov/fdsnws/event/1/query"
GDACS = "https://www.gdacs.org/gdacsapi/api/events/geteventlist/SEARCH"
GDACS_TYPES = {"EQ": "earthquake", "TC": "tropical cyclone", "FL": "flood", "VO": "volcano", "DR": "drought",
               "WF": "wildfire"}
# how close a GDACS event's reference point must be to count for this place
GDACS_RADIUS_KM = {"EQ": 200, "TC": 300, "FL": 60, "VO": 100, "DR": 600, "WF": 60}


def earthquakes(lat: float, lon: float, radius_km: float = 200, min_mag: float = 5.5, top: int = 5) -> list[dict]:
    """Strongest earthquakes within radius_km since 1970 (USGS ComCat) plus a count summary."""
    params = {"format": "geojson", "starttime": "1970-01-01", "minmagnitude": min_mag, "latitude": lat,
              "longitude": lon, "maxradiuskm": radius_km, "orderby": "magnitude", "limit": 200}
    r = httpx.get(USGS, params=params, headers=UA, timeout=30)
    r.raise_for_status()
    feats = r.json().get("features", [])
    out = []
    for f in feats[:top]:
        p, (qlon, qlat, depth) = f["properties"], f["geometry"]["coordinates"]
        dist = haversine_m(lat, lon, qlat, qlon) / 1000
        out.append({"type": "earthquake", "date": _iso(p["time"]),
                    "what_happened": f"Magnitude {p['mag']} earthquake, {dist:.0f} km from this place ({p.get('place')}); "
                                     f"depth {depth:.0f} km.",
                    "source_url": p.get("url"), "url": p.get("url"), "evidence_kind": "dataset"})
    if feats:
        out.append({"type": "earthquake (summary)", "date": "1970-2026",
                    "what_happened": f"{len(feats)}{'+' if len(feats) == 200 else ''} earthquakes of magnitude "
                                     f"{min_mag} or more within {radius_km} km since 1970 (USGS catalogue).",
                    "source_url": "https://earthquake.usgs.gov/earthquakes/search/",
                    "url": "https://earthquake.usgs.gov/earthquakes/search/", "evidence_kind": "dataset"})
    return out


def gdacs_events(lat: float, lon: float, country: str | None, top: int = 8) -> list[dict]:
    """GDACS orange/red alerts (and green floods/cyclones) since 2000 whose reference point is near this place."""
    if not country:
        return []
    found = []
    for code, label in GDACS_TYPES.items():
        params = {"eventlist": code, "fromDate": "2000-01-01", "toDate": "2026-10-18",
                  "alertlevel": "Orange;Red" if code in ("DR", "EQ") else "Green;Orange;Red", "country": country}
        try:
            r = httpx.get(GDACS, params=params, headers=UA, timeout=30)
            if r.status_code != 200 or not r.text.strip():
                continue
            feats = r.json().get("features", [])
        except Exception:
            continue
        for f in feats:
            p = f["properties"]
            elon, elat = f["geometry"]["coordinates"][:2]
            dist = haversine_m(lat, lon, elat, elon) / 1000
            if dist > GDACS_RADIUS_KM[code]:
                continue
            url = (p.get("url") or {}).get("report") or "https://www.gdacs.org/"
            found.append({"type": label, "date": str(p.get("fromdate", ""))[:10],
                          "what_happened": f"{p.get('name')} — GDACS {p.get('alertlevel', '').lower()} alert"
                                           f"{_sev(p)} (event reference point {dist:.0f} km away).",
                          "source_url": url, "url": url, "evidence_kind": "dataset",
                          "_rank": {"Red": 0, "Orange": 1, "Green": 2}.get(p.get("alertlevel"), 3)})
    found.sort(key=lambda e: (e["_rank"], e["date"]), reverse=False)
    best = sorted(found, key=lambda e: (e["_rank"], -int(e["date"][:4] or 0)))[:top]
    for e in best:
        e.pop("_rank", None)
    return best


def _sev(p: dict) -> str:
    t = ((p.get("severitydata") or {}).get("severitytext") or "").strip()
    return "" if not t or t.startswith("Magnitude 0") else f"; {t}"


def _iso(ms: int) -> str:
    import time
    return time.strftime("%Y-%m-%d", time.gmtime(ms / 1000))
