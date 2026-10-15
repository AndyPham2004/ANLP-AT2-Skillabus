"""Merge several scrape_handbook.py outputs into one uts_subjects_2026.csv.

A subject can appear in more than one run (a core in one course, an option in another), so
rows are merged on subject_code: the first non-empty value wins for every column except
`courses` and `curriculum_group`, which are unioned (pipe-joined). Runs are given in priority
order; a later file only fills gaps.

Usage (from the repo root):
    python data-eda/src/merge_subjects.py --out data/raw/uts_subjects_2026.csv \
        data/raw/uts_subjects_2026_batch1.csv data/raw/uts_subjects_2026_batch2.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def merge(frames: list[pd.DataFrame]) -> pd.DataFrame:
    rows: dict[str, dict] = {}
    for df in frames:
        for rec in df.fillna("").astype(str).to_dict("records"):
            code = rec["subject_code"]
            if code not in rows:
                rows[code] = dict(rec)
                continue
            cur = rows[code]
            for k, v in rec.items():
                if k in ("courses", "curriculum_group"):
                    parts = [p for p in (cur.get(k, "") + "|" + v).split("|") if p]
                    cur[k] = "|".join(dict.fromkeys(parts))
                elif not cur.get(k) and v:
                    cur[k] = v
    out = pd.DataFrame(list(rows.values()))
    return out.sort_values("subject_code").reset_index(drop=True)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("inputs", nargs="+", type=Path)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    frames = [pd.read_csv(f, dtype=str) for f in a.inputs if f.exists()]
    df = merge(frames)
    df.to_csv(a.out, index=False, encoding="utf-8")
    print(f"Wrote {a.out}: {len(df)} subjects from {len(frames)} files; "
          f"{(df.sessions.fillna('') == '').sum()} without sessions")


if __name__ == "__main__":
    main()
