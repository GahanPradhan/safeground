"""Central configuration: study area, paths and runtime settings."""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load_dotenv(path: Path) -> None:
    """Read KEY=VALUE lines from the project's .env (gitignored) without overriding real env vars."""
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_load_dotenv(ROOT / ".env")
# Older local .env files use the CITYGUARD_ prefix (the product's former name).
for _k, _v in list(os.environ.items()):
    if _k.startswith("CITYGUARD_"):
        os.environ.setdefault("SAFEGROUND_" + _k.removeprefix("CITYGUARD_"), _v)
DATA_RAW = ROOT / "data" / "raw"
SNAPSHOT = ROOT / "data" / "snapshot"
RULEBOOKS = Path(__file__).resolve().parent / "rulebooks"

# Study area: Greater Chennai (lat/lon, EPSG:4326).
BBOX = {"south": 12.90, "west": 80.15, "north": 13.25, "east": 80.33}
H3_RES = 9  # ~0.1 km² hexagons

# Metric CRS for distances/areas (UTM zone 44N covers Chennai).
METRIC_CRS = "EPSG:32644"

# Showcase areas used for the demo and accuracy checks (approximate centres).
SHOWCASE_AREAS = {
    "Velachery": (12.9792, 80.2210),
    "Ennore": (13.2146, 80.3203),
    "Manali": (13.1667, 80.2610),
    "T. Nagar": (13.0418, 80.2341),
}

# Walking speeds (m/s) used for evacuation routing.
WALK_SPEED = {"default": 1.25, "assisted": 0.8}

# Runtime (Gemini / Google APIs)
PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "global")
MODEL = os.getenv("SAFEGROUND_MODEL", "gemini-3.5-flash")
MAPS_BROWSER_KEY = os.getenv("MAPS_BROWSER_KEY", "")
MAPS_SERVER_KEY = os.getenv("MAPS_SERVER_KEY", "")
