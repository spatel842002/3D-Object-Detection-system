"""Download a single, properly licensed sample photo for local demos and manual QA.

No third-party media is committed to this repository (see
THIRD_PARTY_NOTICES.md). This script fetches one CC-BY 2.0 licensed street
photo from Wikimedia Commons into ./data/samples/, which is gitignored.

Usage:
    python scripts/download_sample_assets.py
"""

from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

SAMPLE_IMAGE_URL = (
    "https://upload.wikimedia.org/wikipedia/commons/1/16/"
    "%22Respect_the_Crosswalk%22_-_Flickr_-_Diego3336.jpg"
)
SAMPLE_IMAGE_ATTRIBUTION = (
    'Photo: "Respect the Crosswalk" by Diego Torres Silvestre (Flickr: Diego3336), '
    "via Wikimedia Commons, licensed CC BY 2.0. "
    "Source: https://commons.wikimedia.org/wiki/File:%22Respect_the_Crosswalk%22_-_Flickr_-_Diego3336.jpg"
)

DEST_DIR = Path(__file__).resolve().parent.parent / "data" / "samples"
DEST_FILE = DEST_DIR / "street_scene_sample.jpg"


def main() -> int:
    DEST_DIR.mkdir(parents=True, exist_ok=True)
    if DEST_FILE.exists():
        print(f"Already downloaded: {DEST_FILE}")
    else:
        print(f"Downloading sample image from {SAMPLE_IMAGE_URL} ...")
        try:
            request = urllib.request.Request(
                SAMPLE_IMAGE_URL,
                headers={"User-Agent": "3D-Object-Detection-System/0.1 (portfolio demo script)"},
            )
            with urllib.request.urlopen(request) as response, open(DEST_FILE, "wb") as out_file:  # noqa: S310
                out_file.write(response.read())
        except OSError as exc:
            print(f"ERROR: could not download sample asset: {exc}", file=sys.stderr)
            print("You can supply your own licensed image to scripts/run_real_demo.py instead.")
            return 1
        print(f"Saved to {DEST_FILE}")

    attribution_file = DEST_DIR / "ATTRIBUTION.txt"
    attribution_file.write_text(SAMPLE_IMAGE_ATTRIBUTION + "\n", encoding="utf-8")
    print(SAMPLE_IMAGE_ATTRIBUTION)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
