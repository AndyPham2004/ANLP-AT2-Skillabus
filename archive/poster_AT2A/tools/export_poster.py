"""Export archive/poster_AT2A/poster/AT2A_Poster_Skillabus.html to a vector A0 PDF and a
PNG preview with headless Chrome or Edge.

    python archive/poster_AT2A/tools/export_poster.py

The HTML is the single source for the poster (layout imported from the Claude
Design project "Design Layout at A0", content edited in the repo). The poster was
submitted on 26 Sep 2026 and is frozen; this script stays so the PDF can be rebuilt.
Until 15 Oct 2026 it lived in src/ and the poster in poster/.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]          # archive/poster_AT2A/
POSTER = ROOT / "poster"
SRC = POSTER / "AT2A_Poster_Skillabus.html"
OUT_PDF = POSTER / "AT2A_Poster_Skillabus_A0.pdf"
OUT_PNG = POSTER / "AT2A_Poster_Skillabus_preview.png"

CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "google-chrome", "chromium", "chromium-browser",
]


def find_chrome() -> str | None:
    for c in CHROME_CANDIDATES:
        if Path(c).exists() or shutil.which(c):
            return c
    return None


def export(chrome: str) -> None:
    url = SRC.resolve().as_uri()
    common = [chrome, "--headless=new", "--disable-gpu", "--no-sandbox",
              "--hide-scrollbars", "--virtual-time-budget=20000",
              "--font-render-hinting=none"]
    subprocess.run(common + [f"--print-to-pdf={OUT_PDF}", "--no-pdf-header-footer", url],
                   check=True, capture_output=True)
    # A0 landscape at 96 css px per inch: 1189 mm = 4494 px, 841 mm = 3179 px
    subprocess.run(common + ["--window-size=4494,3179", f"--screenshot={OUT_PNG}", url],
                   check=True, capture_output=True)


if __name__ == "__main__":
    chrome = find_chrome()
    if not chrome:
        sys.exit("Chrome/Edge not found: open the HTML in a browser and print to PDF "
                 "manually (A0 landscape, no margins, background graphics on).")
    export(chrome)
    print("exported", OUT_PDF.name, "and", OUT_PNG.name)
