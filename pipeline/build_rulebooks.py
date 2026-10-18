"""Download the official guidance documents and extract their text.

The extracted text (data/raw/guides/*.txt) is the source from which the hazard
rulebooks in safeground/rulebooks/*.yaml are curated. Every advice line in a
rulebook keeps the document id it was taken from.

Run:  .venv/bin/python -m pipeline.build_rulebooks
"""
from __future__ import annotations

import re
import sys

import httpx
from pypdf import PdfReader

from safeground.config import DATA_RAW

UA = {"User-Agent": "SafeGround-hackathon/0.1 (research prototype)"}

DOCS = {
    # ERG 2024 orange guides (via NOAA CAMEO Chemicals)
    "erg_guide_112": "https://cameochemicals.noaa.gov/erg_guides/en/Guide_112.pdf",  # explosives 1.1
    "erg_guide_115": "https://cameochemicals.noaa.gov/erg_guides/en/Guide_115.pdf",  # flammable gases (LPG)
    "erg_guide_124": "https://cameochemicals.noaa.gov/erg_guides/en/Guide_124.pdf",  # toxic oxidizing gases (chlorine)
    "erg_guide_125": "https://cameochemicals.noaa.gov/erg_guides/en/Guide_125.pdf",  # toxic corrosive gases (ammonia)
    # IMD flood do's and don'ts
    "imd_flood_dos_donts": "https://www.imdnagpur.gov.in/docs_general/Floods_Dos_and_Donts.pdf",
}
# ERG Table 1/3 distances per UN number (HTML pages on CAMEO)
UN_PAGES = {"UN1005_ammonia": "https://cameochemicals.noaa.gov/unna/1005",
            "UN1017_chlorine": "https://cameochemicals.noaa.gov/unna/1017",
            "UN1075_lpg": "https://cameochemicals.noaa.gov/unna/1075"}


def main() -> int:
    out = DATA_RAW / "guides"
    out.mkdir(parents=True, exist_ok=True)
    ok = True
    with httpx.Client(headers=UA, timeout=60, follow_redirects=True) as client:
        for doc_id, url in DOCS.items():
            try:
                r = client.get(url)
                r.raise_for_status()
                pdf = out / f"{doc_id}.pdf"
                pdf.write_bytes(r.content)
                text = "\n".join((p.extract_text() or "") for p in PdfReader(str(pdf)).pages)
                (out / f"{doc_id}.txt").write_text(text)
                print(f"{doc_id}: {len(r.content):,} bytes, {len(text):,} chars")
            except Exception as e:  # report and continue; curation step will flag gaps
                ok = False
                print(f"{doc_id}: FAILED {e}", file=sys.stderr)
        for doc_id, url in UN_PAGES.items():
            try:
                r = client.get(url)
                r.raise_for_status()
                text = re.sub(r"<script.*?</script>|<style.*?</style>", " ", r.text, flags=re.S)
                text = re.sub(r"<[^>]+>", " ", text)
                text = re.sub(r"[ \t]+", " ", re.sub(r"\n\s*\n+", "\n", text))
                (out / f"{doc_id}.txt").write_text(text)
                print(f"{doc_id}: {len(text):,} chars")
            except Exception as e:
                ok = False
                print(f"{doc_id}: FAILED {e}", file=sys.stderr)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
