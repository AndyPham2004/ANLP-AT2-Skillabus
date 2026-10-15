"""Reshape ESCO v1.2.1 skills into the two forms the pipeline uses.

`skills_en.csv` keeps alternative labels in one cell, separated by newlines,
which most CSV tools display as one long label and which is easy to split wrong.
This script writes:

  esco_skills_clean.csv   one row per skill concept; alt labels pipe-separated
  esco_label_lookup.csv   one row per (surface form, concept) - what normalise()
                          needs to turn "machine learning" into an ESCO URI

The lookup also records how ambiguous ESCO's own vocabulary is: a surface form
that points at more than one concept cannot be normalised by lookup alone, which
is one concrete answer to "how are ambiguous skills handled?".

Usage:
    python src/clean_esco.py
"""

from __future__ import annotations

import argparse
import logging
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))  # repo src/, for skillabus.paths
from skillabus import paths  # noqa: E402

DEFAULT_IN = paths.ESCO_RAW
DEFAULT_OUT = paths.TAXONOMIES

log = logging.getLogger("clean_esco")


def labels(cell) -> list[str]:
    if not isinstance(cell, str):
        return []
    return [re.sub(r"\s+", " ", x).strip() for x in cell.split("\n") if x.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", type=Path, default=DEFAULT_IN)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    esco = pd.read_csv(args.input, low_memory=False)
    esco = esco[esco.status == "released"]

    pipes = esco[["preferredLabel", "altLabels"]].fillna("").apply(
        lambda c: c.str.contains("|", regex=False)).to_numpy().sum()
    if pipes:
        raise SystemExit(f"{pipes} labels contain '|'; pick another separator")

    skills = pd.DataFrame({
        "concept_uri": esco.conceptUri,
        "preferred_label": esco.preferredLabel.str.strip(),
        "alt_labels": esco.altLabels.apply(lambda c: "|".join(labels(c))),
        "skill_type": esco.skillType,
        "reuse_level": esco.reuseLevel,
        "description": esco.description.fillna("").str.replace(r"\s+", " ", regex=True).str.strip(),
    })

    rows = []
    for r in esco.itertuples(index=False):
        rows.append((r.preferredLabel.strip(), r.conceptUri, r.preferredLabel.strip(), "preferred"))
        rows += [(a, r.conceptUri, r.preferredLabel.strip(), "alt") for a in labels(r.altLabels)]
        rows += [(h, r.conceptUri, r.preferredLabel.strip(), "hidden") for h in labels(r.hiddenLabels)]
    lookup = pd.DataFrame(rows, columns=["label", "concept_uri", "preferred_label", "label_type"])
    lookup["label"] = lookup.label.str.lower()
    lookup = lookup.drop_duplicates(subset=["label", "concept_uri"])

    per_label = lookup.groupby("label").concept_uri.nunique()
    lookup["ambiguous"] = lookup.label.map(per_label > 1)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    skills_path = args.out_dir / "esco_skills_clean.csv"
    lookup_path = args.out_dir / "esco_label_lookup.csv"
    skills.to_csv(skills_path, index=False, encoding="utf-8")
    lookup.sort_values(["label", "concept_uri"]).to_csv(lookup_path, index=False, encoding="utf-8")

    log.info("Wrote %s: %d skill concepts", skills_path.name, len(skills))
    log.info("Wrote %s: %d (label, concept) rows, %d distinct labels, %.1f MB",
             lookup_path.name, len(lookup), lookup.label.nunique(),
             lookup_path.stat().st_size / 1e6)
    amb = per_label[per_label > 1]
    log.info("  %d labels (%.1f%%) point at more than one concept, e.g. %s",
             len(amb), 100 * len(amb) / len(per_label),
             ", ".join(f'"{x}"' for x in amb.sort_values(ascending=False).index[:4]))


if __name__ == "__main__":
    main()
