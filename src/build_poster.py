"""Assemble poster/poster.html from poster/poster_template.html plus the charts,
then export a vector PDF (A0 landscape) and a PNG preview with headless Chrome.

    python src/build_poster.py            # build + export
    python src/build_poster.py --no-pdf   # build only
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import figures  # noqa: E402

ROOT = figures.ROOT
POSTER = ROOT / "poster"
TEMPLATE = POSTER / "poster_template.html"
OUT_HTML = POSTER / "poster.html"
OUT_PDF = POSTER / "poster_A0.pdf"
OUT_PNG = POSTER / "poster_preview.png"

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


def build_html() -> dict:
    fig5, ill5 = figures.fig_top_skills()
    fig6, ill6, summary = figures.fig_gap()
    (POSTER / "figures").mkdir(exist_ok=True)
    figures.write_standalone(fig5, POSTER / "figures" / "fig5_top_skills.svg")
    figures.write_standalone(fig6, POSTER / "figures" / "fig6_gap.svg")

    illustrative = ill5 or ill6
    html = TEMPLATE.read_text(encoding="utf-8")
    repl = {
        "{{FIG_TOP_SKILLS}}": fig5,
        "{{FIG_GAP}}": fig6,
        "{{GAP_N}}": str(summary["n"]),
        "{{GAP_COVERED}}": str(summary["covered"]),
        "{{GAP_MISSING}}": str(summary["missing"]),
        "{{GAP_TOP_MISSING}}": ", ".join(summary["top_missing"]),
        "{{GAP_OMITTED}}": str(summary["omitted"]),
        "{{DRAFT_CLASS}}": "draft" if illustrative else "",
    }
    for k, v in repl.items():
        html = html.replace(k, v)
    OUT_HTML.write_text(html, encoding="utf-8")
    return {"illustrative": illustrative, **summary}


def export(chrome: str):
    url = OUT_HTML.resolve().as_uri()
    common = [chrome, "--headless=new", "--disable-gpu", "--no-sandbox",
              "--hide-scrollbars", "--virtual-time-budget=20000",
              "--font-render-hinting=none"]
    subprocess.run(common + [f"--print-to-pdf={OUT_PDF}", "--no-pdf-header-footer", url],
                   check=True, capture_output=True)
    # A0 landscape at 96 css px per inch: 1189 mm = 4494 px, 841 mm = 3179 px
    subprocess.run(common + ["--window-size=4494,3179", f"--screenshot={OUT_PNG}", url],
                   check=True, capture_output=True)


if __name__ == "__main__":
    info = build_html()
    print("built", OUT_HTML.name, info)
    if "--no-pdf" not in sys.argv:
        chrome = find_chrome()
        if not chrome:
            sys.exit("Chrome/Edge not found: open poster/poster.html and print to PDF "
                     "manually (A0 landscape, no margins, background graphics on).")
        export(chrome)
        print("exported", OUT_PDF.name, "and", OUT_PNG.name)
