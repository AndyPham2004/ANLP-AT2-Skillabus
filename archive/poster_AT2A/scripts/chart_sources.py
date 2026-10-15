"""Poster block 3: data-source cards.

Six cards, each a big number and one line saying what that source gives us. Big
numerals carry at three metres where a table of counts does not, and the block 3
brief is 60 words, so the figure has to do the work.

Every number here is read off a file on disk - see DATASETS.md.

Usage:
    python src/chart_sources.py
"""

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]

TEAL, INK, MUTED, SURFACE, CARD = "#0F6E68", "#1B2530", "#5C6974", "#FFFFFF", "#EEF2F0"
FIG_W_IN, FIG_H_IN, DPI = 9.8, 5.0, 300
PT_NUM, PT_NAME, PT_DESC, PT_CAPTION = 44, 19, 15, 15

CARDS = [
    ("3,204", "Seek Australia", "Data Scientist ads 2019-22,\nfrom 3,895 data listings"),
    ("13,960", "ESCO v1.2.1", "EU skill concepts\nwith alt-labels"),
    ("8,753", "O*NET 31.0", "tool names ESCO\ndoes not cover"),
    ("70", "UTS Handbook", "subjects across\n6 courses"),
    ("124k", "LinkedIn US", "ads scanned 2023-24:\n1.1% data-titled,\n3.6% demand data skills"),
    ("2,484", "Resumes", "to build the\nstudent profile"),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=ROOT / "outputs" / "block3_sources.png", type=Path)
    args = parser.parse_args()

    fig, axes = plt.subplots(2, 3, figsize=(FIG_W_IN, FIG_H_IN), dpi=DPI)
    fig.patch.set_facecolor(SURFACE)

    for ax, (number, name, desc) in zip(axes.flat, CARDS):
        ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
        ax.add_patch(FancyBboxPatch(
            (0.04, 0.08), 0.92, 0.84, boxstyle="round,pad=0.02,rounding_size=0.04",
            facecolor=CARD, edgecolor="none", transform=ax.transAxes, zorder=0))
        ax.text(0.5, 0.74, number, ha="center", va="center", fontsize=PT_NUM,
                fontweight="bold", color=TEAL, transform=ax.transAxes)
        ax.text(0.5, 0.48, name, ha="center", va="center", fontsize=PT_NAME,
                fontweight="bold", color=INK, transform=ax.transAxes)
        ax.text(0.5, 0.24, desc, ha="center", va="center", fontsize=PT_DESC,
                color=MUTED, linespacing=1.35, transform=ax.transAxes)

    fig.text(0.012, 0.015,
             "Every count read from the downloaded file, not a dataset description page",
             fontsize=PT_CAPTION, color=MUTED, ha="left", va="bottom")
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(args.out, dpi=DPI, facecolor=SURFACE, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
