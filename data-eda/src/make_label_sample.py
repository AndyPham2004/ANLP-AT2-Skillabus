"""Draw the fixed 200-ad labelling sample from the clean Seek corpus.

Akash labels all 200 in four batches of 50; Hoai Thuong labels the 20 marked
`double_label = y` as well, so Cohen's kappa is computed on ads both people
actually saw. The draw is seeded, so re-running gives the same 200 ads.

Usage:
    python src/make_label_sample.py
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_IN = ROOT / "data" / "clean" / "jobs_au_seek_datascientist_2019-2022_clean.csv"
DEFAULT_OUT = ROOT / "data" / "clean" / "seek_label_sample_200.csv"
SEED = 36118  # the subject code, so nobody wonders where the number came from


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", type=Path, default=DEFAULT_IN)
    parser.add_argument("--n", type=int, default=200)
    parser.add_argument("--batch", type=int, default=50)
    parser.add_argument("--overlap", type=int, default=20)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    ads = pd.read_csv(args.input)
    sample = ads.sample(n=args.n, random_state=SEED).reset_index(drop=True)
    sample.insert(0, "batch", sample.index // args.batch + 1)
    # The overlap sits in batch 1, the earliest batch, so the agreement check can start first.
    sample.insert(1, "double_label", ["y" if i < args.overlap else "n" for i in range(len(sample))])
    sample = sample[["batch", "double_label", "ad_id", "title", "company", "listingDate", "description"]]
    sample.to_csv(args.out, index=False, encoding="utf-8")
    print(f"Wrote {args.out}: {len(sample)} ads in {sample.batch.nunique()} batches, "
          f"{(sample.double_label == 'y').sum()} marked for double labelling (seed {SEED})")


if __name__ == "__main__":
    main()
