"""Hand-built SVG charts for the AT2A poster.

Charts are emitted as inline SVG so they inherit the poster's web fonts and
scale with the column width. Values come from data/processed/*.csv when those
files exist; otherwise the illustrative sample values below are used and the
poster is stamped as a draft with illustrative figures.
"""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"

TEAL = "#0d9488"    # covered / market demand
COPPER = "#c2612b"  # missing
INK = "#1c1c1a"
MUTED = "#5b5a55"
HAIR = "#d8d7d0"

# --- illustrative sample values (replace with notebook output) -----------------
SAMPLE_TOP_SKILLS = [
    ("Python", 71), ("SQL", 64), ("Machine learning", 58), ("Statistics", 46),
    ("Communication", 44), ("Cloud (AWS, Azure, GCP)", 38), ("Data visualisation", 36),
    ("Deep learning", 29), ("Spark / big data", 27), ("Power BI / Tableau", 26),
    ("NLP", 22), ("Git", 21), ("R", 20), ("Experimentation / A-B", 17), ("MLOps", 15),
]
SAMPLE_GAP = [  # (skill, pct_ads, covered)
    ("Python", 71, 1), ("SQL", 64, 1), ("Machine learning", 58, 1), ("Statistics", 46, 1),
    ("Communication", 44, 1), ("Cloud (AWS, Azure, GCP)", 38, 0), ("Data visualisation", 36, 1),
    ("Deep learning", 29, 1), ("Spark / big data", 27, 0), ("Power BI / Tableau", 26, 0),
    ("NLP", 22, 1), ("Git", 21, 0), ("Experimentation / A-B", 17, 0), ("MLOps", 15, 0),
]


def _load_csv(name: str):
    path = PROCESSED / name
    if not path.exists():
        return None
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(line for line in f if not line.startswith("#")))


def top_skills_data():
    rows = _load_csv("top_skills.csv")
    if rows:
        return [(r["skill"], float(r["pct_ads"])) for r in rows][:15], False
    return SAMPLE_TOP_SKILLS, True


def gap_data():
    rows = _load_csv("gap.csv")
    if rows:
        return [(r["skill"], float(r["pct_ads"]), int(r["covered"])) for r in rows], False
    return SAMPLE_GAP, True


def _esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def hbar_svg(rows, *, colors, width=1000, bar=27, gap=10, label_w=395,
             value_fmt="{:.0f}%", font=28, top_pad=8):
    """Horizontal bar chart. rows = [(label, value, color_index), ...]"""
    n = len(rows)
    height = top_pad + n * (bar + gap) + 6
    vmax = max(v for _, v, _ in rows)
    plot_w = width - label_w - 110
    out = [f'<svg class="chart" viewBox="0 0 {width} {height}" width="100%" '
           f'xmlns="http://www.w3.org/2000/svg" role="img">']
    out.append(f'<line x1="{label_w}" y1="{top_pad}" x2="{label_w}" y2="{height-6}" '
               f'stroke="{HAIR}" stroke-width="2"/>')
    for i, (label, v, ci) in enumerate(rows):
        y = top_pad + i * (bar + gap)
        w = max(4, plot_w * v / vmax)
        r = 5  # rounded data-end, square at the baseline
        path = (f'M{label_w},{y} h{w-r:.1f} a{r},{r} 0 0 1 {r},{r} v{bar-2*r} '
                f'a{r},{r} 0 0 1 -{r},{r} h-{w-r:.1f} z')
        out.append(f'<path d="{path}" fill="{colors[ci]}"/>')
        out.append(f'<text x="{label_w-16}" y="{y+bar*0.74:.1f}" text-anchor="end" '
                   f'font-size="{font}" fill="{INK}">{_esc(label)}</text>')
        out.append(f'<text x="{label_w+w+14:.1f}" y="{y+bar*0.74:.1f}" font-size="{font}" '
                   f'font-weight="600" fill="{MUTED}">{value_fmt.format(v)}</text>')
    out.append("</svg>")
    return "\n".join(out)


def fig_top_skills():
    rows, illustrative = top_skills_data()
    svg = hbar_svg([(s, v, 0) for s, v in rows], colors=[TEAL])
    return svg, illustrative


def fig_gap():
    rows, illustrative = gap_data()
    rows = sorted(rows, key=lambda r: -r[1])
    # Skills the ad requires but no Seek ad phrases the ESCO way (0% demand) are
    # counted in the totals but not drawn, as in Student C's notebook chart.
    drawn = [r for r in rows if r[1] > 0]
    omitted = len(rows) - len(drawn)
    svg = hbar_svg([(s, v, 0 if c else 1) for s, v, c in drawn],
                   colors=[TEAL, COPPER], bar=31, gap=12, font=30)
    covered = sum(1 for r in rows if r[2])
    missing = [r[0].split(" (")[0].split(" /")[0] for r in drawn if not r[2]][:3]
    return svg, illustrative, {"n": len(rows), "covered": covered,
                               "missing": len(rows) - covered, "top_missing": missing,
                               "omitted": omitted}


def write_standalone(svg: str, path: Path):
    """Save a copy with an explicit font so the SVG also opens on its own."""
    styled = svg.replace(
        '<svg class="chart"',
        '<svg style="font-family:Archivo,Arial,sans-serif;background:#f8f7f3" class="chart"', 1)
    path.write_text(styled, encoding="utf-8")


if __name__ == "__main__":
    out = ROOT / "poster" / "figures"
    out.mkdir(parents=True, exist_ok=True)
    s1, i1 = fig_top_skills()
    s2, i2, summary = fig_gap()
    write_standalone(s1, out / "fig5_top_skills.svg")
    write_standalone(s2, out / "fig6_gap.svg")
    print("top skills illustrative:", i1, "| gap illustrative:", i2, summary)
