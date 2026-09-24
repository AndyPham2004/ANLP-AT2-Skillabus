"""Export poster/poster_design.html (imported from Claude Design) to a vector A0 PDF
and a PNG preview with headless Chrome.

    python src/export_design.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_poster import find_chrome  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
POSTER = ROOT / "poster"
SRC = POSTER / "poster_design.html"
OUT_PDF = POSTER / "poster_design_A0.pdf"
OUT_PNG = POSTER / "poster_design_preview.png"


def export(chrome: str):
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
        sys.exit("Chrome/Edge not found: open poster/poster_design.html and print to PDF "
                 "manually (A0 landscape, no margins, background graphics on).")
    export(chrome)
    print("exported", OUT_PDF.name, "and", OUT_PNG.name)
