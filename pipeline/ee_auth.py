"""Initialise Earth Engine only with the owner's SafeGround gcloud login (never a stray service-account key)."""
from __future__ import annotations

import os

import ee
import google.auth


def init_ee(project: str) -> None:
    if not os.getenv("CLOUDSDK_CONFIG", "").endswith("gcloud-cityguard"):
        raise RuntimeError("Set CLOUDSDK_CONFIG=~/.config/gcloud-cityguard so the SafeGround login is used.")
    if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        raise RuntimeError("GOOGLE_APPLICATION_CREDENTIALS is set; refusing to use another credential.")
    creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/earthengine",
                                          "https://www.googleapis.com/auth/cloud-platform"])
    if getattr(creds, "service_account_email", None):
        raise RuntimeError("A service-account credential was found; SafeGround only uses the owner's user login.")
    ee.Initialize(credentials=creds, project=project)
    ee.data.setDeadline(150_000)  # fail a stuck request after 150 s instead of hanging forever
