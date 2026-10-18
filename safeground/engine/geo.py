"""Small geodesy helpers. All coordinates are (lat, lon) in degrees unless stated."""
from __future__ import annotations

import contextvars
import math

import numpy as np

R = 6371008.8
LAT0 = 13.07  # Chennai reference latitude for the local metric projection
_KY = R * math.pi / 180  # metres per degree of latitude
# Reference latitude of the region being worked on (Chennai by default; set per request for other regions)
_LAT0 = contextvars.ContextVar("safeground_lat0", default=LAT0)


def set_reference_latitude(lat: float) -> contextvars.Token:
    return _LAT0.set(float(lat))


def _kx() -> float:
    return R * math.cos(math.radians(_LAT0.get())) * math.pi / 180  # metres per degree of longitude

COMPASS = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]


def to_xy(lat, lon):
    """Local equirectangular projection around the active region's latitude (metres); error < 0.5 % within ~50 km."""
    return np.asarray(lon) * _kx(), np.asarray(lat) * _KY


def to_latlon(x, y):
    return np.asarray(y) / _KY, np.asarray(x) / _kx()


def haversine_m(lat1, lon1, lat2, lon2):
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dphi, dl = p2 - p1, np.radians(np.asarray(lon2) - np.asarray(lon1))
    a = np.sin(dphi / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * R * np.arcsin(np.sqrt(a))


def bearing_deg(lat1, lon1, lat2, lon2) -> float:
    """Initial bearing from point 1 to point 2, degrees clockwise from north."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lon2 - lon1)
    x = math.sin(dl) * math.cos(p2)
    y = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
    return (math.degrees(math.atan2(x, y)) + 360) % 360


def compass(deg: float) -> str:
    return COMPASS[int(((deg % 360) + 11.25) // 22.5) % 16]


def offset(lat: float, lon: float, bearing: float, dist_m: float) -> tuple[float, float]:
    """Point reached from (lat, lon) going dist_m metres on the given bearing (local flat approximation)."""
    x, y = to_xy(lat, lon)
    b = math.radians(bearing)
    la, lo = to_latlon(x + dist_m * math.sin(b), y + dist_m * math.cos(b))
    return float(la), float(lo)
