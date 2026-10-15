"""Draw the fixed 200-ad labelling sample from the clean Seek corpus.

Akash labels all 200 in four batches of 50; Hoai Thuong labels the 20 marked
`double_label = y` as well, so Cohen's kappa is computed on ads both people
actually saw. The draw is seeded, so re-running gives the same 200 ads.

No two sampled ads share the same text. 697 of the 3,204 ads are re-listings (the
same employer posting the same ad on another date or in another city), and the
first version of this sample, on 9 Oct, drew 4 of them twice. A repeat is now
replaced in place by an unused ad, so the other 196 rows - and every batch and
double-label position - are unchanged from that first version.

Usage:
    python src/make_label_sample.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))  # repo src/, for skillabus.paths
from skillabus import paths  # noqa: E402

DEFAULT_IN = paths.SEEK_ADS
DEFAULT_OUT = paths.LABEL_SAMPLE
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
    first = ads.sample(n=args.n, random_state=SEED)          # the 9 Oct draw, kept stable
    pool = ads[~ads.description.isin(set(first.description))].drop_duplicates("description")
    spare = iter(pool.sample(frac=1, random_state=SEED).itertuples(index=False))
    rows, seen = [], set()
    for row in first.itertuples(index=False):
        if row.description in seen:                           # a re-listing already drawn
            row = next(spare)
        seen.add(row.description)
        rows.append(row)
    sample = pd.DataFrame(rows, columns=ads.columns)
    sample.insert(0, "batch", sample.index // args.batch + 1)
    # The overlap sits in batch 1, the earliest batch, so the agreement check can start first.
    sample.insert(1, "double_label", ["y" if i < args.overlap else "n" for i in range(len(sample))])
    sample = sample[["batch", "double_label", "ad_id", "title", "company", "listingDate", "description"]]
    sample.to_csv(args.out, index=False, encoding="utf-8")
    print(f"Wrote {args.out}: {len(sample)} ads in {sample.batch.nunique()} batches, "
          f"{(sample.double_label == 'y').sum()} marked for double labelling (seed {SEED})")


if __name__ == "__main__":
    main()
