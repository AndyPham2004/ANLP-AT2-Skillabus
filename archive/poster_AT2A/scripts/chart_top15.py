"""Poster block 5: top-N skills by share of job ads, as a horizontal bar chart.

Follows the poster design rules in the team plan and the Penn State handbook:
direct value labels instead of an x-axis, no legend (there is only one series, and
the title names it), all labels horizontal, heavy marks so the chart reads from
three metres, and a source + sample size line underneath.

Sized to drop straight into one column of an A0 landscape poster at 1:1, so the
point sizes below are the point sizes that get printed.

Usage:
    python src/chart_top15.py --title "Skills employers ask for" --source "Adzuna AU, Sept 2026"
"""

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]

# ---------------------------------------------------------------------------
# Style sheet. Replace these with A's exact values once the team style sheet lands.
# ---------------------------------------------------------------------------
TEAL = "#0F6E68"       # "what the market asks for" / "already have"
COPPER = "#B8541F"     # "missing" - not used here, kept so the two scripts agree
INK = "#1B2530"        # all text
MUTED = "#5C6974"      # caption
SURFACE = "#FFFFFF"

FIG_W_IN, FIG_H_IN = 9.8, 7.0   # ~250 x 178 mm, one A0 column
DPI = 300

PT_LABEL = 22    # skill names
PT_VALUE = 20    # the % at the end of each bar
PT_TITLE = 30
PT_CAPTION = 18  # absolute floor for poster body text


def plot(counts, top_n, title, source, outfile):
    top = counts.head(top_n).iloc[::-1]  # reverse so the largest sits at the top

    fig, ax = plt.subplots(figsize=(FIG_W_IN, FIG_H_IN), dpi=DPI)
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)

    y = range(len(top))
    ax.barh(y, top["pct_ads"], height=0.72, color=TEAL, zorder=2)

    ax.set_yticks(list(y))
    ax.set_yticklabels(top["skill"], fontsize=PT_LABEL, color=INK)
    ax.tick_params(axis="y", length=0, pad=10)

    # The value labels replace the x-axis entirely.
    ax.set_xticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)

    span = top["pct_ads"].max()
    for i, value in enumerate(top["pct_ads"]):
        ax.text(
            value + span * 0.015, i, f"{value:.0f}%",
            va="center", ha="left", fontsize=PT_VALUE, color=INK, fontweight="bold",
        )

    ax.set_xlim(0, span * 1.12)

    # Title and caption both hang off the figure's left edge so they line up with
    # each other rather than with the plot area, which starts after the y-labels.
    fig.text(0.01, 0.975, title, fontsize=PT_TITLE, fontweight="bold", color=INK,
             ha="left", va="top")

    # Keep the caption short: a long one stretches the figure under bbox_inches
    # ="tight" and makes the bars look smaller than they are.
    n = int(counts["total_ads_in_sample"].iloc[0])
    fig.text(0.01, 0.015, f"{source}  ·  n = {n:,} ads",
             fontsize=PT_CAPTION, color=MUTED, ha="left", va="bottom")

    fig.tight_layout(rect=(0, 0.05, 1, 0.91))
    fig.savefig(outfile, dpi=DPI, facecolor=SURFACE, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {outfile}  ({FIG_W_IN}x{FIG_H_IN} in @ {DPI} dpi)")
    print("Now open it and check: no clipped skill names, no overlapping labels.")


def main():
    import pandas as pd

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--counts", default=ROOT / "outputs" / "skill_counts.csv", type=Path)
    parser.add_argument("--top-n", type=int, default=15)
    parser.add_argument("--title", default="What employers actually ask for")
    parser.add_argument("--source", required=True, help='e.g. "Adzuna AU, Sept 2026"')
    parser.add_argument("--exclude-category", default=None,
                        help='drop a category before ranking, e.g. "Professional"')
    parser.add_argument("--out", default=ROOT / "outputs" / "block5_top_skills.png", type=Path)
    args = parser.parse_args()

    counts = pd.read_csv(args.counts)
    if args.exclude_category:
        counts = counts[counts["category"] != args.exclude_category].reset_index(drop=True)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    plot(counts, args.top_n, args.title, args.source, args.out)


if __name__ == "__main__":
    main()
