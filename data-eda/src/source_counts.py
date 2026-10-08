"""Poster block 3: count every dataset you actually loaded.

Walks data/raw, counts rows in each file, and writes a table you can read the
block 3 source-card numbers straight off. The point is that every number on the
poster comes from a file on your disk, not from a dataset description page.

Usage:
    python src/source_counts.py
"""

import argparse
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
READABLE = {".csv", ".tsv", ".json", ".jsonl", ".parquet", ".xlsx"}


def count_rows(path):
    """Return (n_rows, n_cols, note) for one data file, or (None, None, error)."""
    try:
        suffix = path.suffix.lower()
        if suffix in {".csv", ".tsv"}:
            sep = "\t" if suffix == ".tsv" else ","
            df = pd.read_csv(path, sep=sep, low_memory=False)
        elif suffix == ".parquet":
            df = pd.read_parquet(path)
        elif suffix == ".xlsx":
            df = pd.read_excel(path)
        elif suffix == ".jsonl":
            with open(path, encoding="utf-8") as fh:
                return sum(1 for line in fh if line.strip()), None, "jsonl"
        elif suffix == ".json":
            with open(path, encoding="utf-8") as fh:
                payload = json.load(fh)
            if isinstance(payload, list):
                return len(payload), None, "json array"
            if isinstance(payload, dict):
                for key in ("results", "data", "items", "records"):
                    if isinstance(payload.get(key), list):
                        return len(payload[key]), None, f"json.{key}"
                return 1, len(payload), "json object"
            return None, None, "unrecognised json"
        else:
            return None, None, "unsupported"
        return len(df), len(df.columns), ""
    except Exception as exc:  # noqa: BLE001 - we want the reason in the table
        return None, None, f"ERROR: {type(exc).__name__}"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", default=ROOT / "data" / "raw", type=Path)
    parser.add_argument("--out", default=ROOT / "outputs" / "source_counts.csv", type=Path)
    args = parser.parse_args()

    if not args.raw_dir.exists():
        raise SystemExit(f"{args.raw_dir} does not exist yet - download something first.")

    rows = []
    for path in sorted(args.raw_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in READABLE:
            continue
        n_rows, n_cols, note = count_rows(path)
        rows.append(
            {
                "file": str(path.relative_to(args.raw_dir)),
                "rows": n_rows,
                "cols": n_cols,
                "size_mb": round(path.stat().st_size / 1_048_576, 1),
                "note": note,
            }
        )

    if not rows:
        raise SystemExit(f"No readable data files found in {args.raw_dir}.")

    table = pd.DataFrame(rows)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(args.out, index=False)

    print(table.to_string(index=False))
    print(f"\nWrote {args.out}")
    print("Use these row counts for the block 3 source cards - and list nothing you did not load.")


if __name__ == "__main__":
    main()
