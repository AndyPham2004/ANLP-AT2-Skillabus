"""Map the extraction dictionary onto ESCO concept URIs - the normalisation layer.

This is the step that makes the product's central claim true. Extraction finds a
skill mentioned in a job ad or a subject outline; this maps that mention onto a
stable ESCO concept, so a subject saying "text mining" and an ad saying "NLP" can
be recognised as the same thing rather than two unrelated strings.

Division of labour, and why it is this way round:

    skills_seed.csv  EXTRACTS.  Curated, tuned to how ads actually write. Matching
                     ESCO's own labels against raw ad text directly works badly -
                     they are verbose and formal ("use Python (computer
                     programming)") in a way job ads never are.
    ESCO             NORMALISES. Supplies the stable identifier, the skill/knowledge
                     distinction, and the recognised standard behind the claim.

ESCO stores altLabels newline-separated, which is what makes this work: the concept
"Python (computer programming)" carries the plain alt-label "Python".

Usage:
    python src/map_to_esco.py
    python src/map_to_esco.py --show-unmapped
"""

import argparse
import logging
import re
import unicodedata
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger("map_to_esco")


def normalise(text):
    """Lowercase, strip accents and punctuation, collapse whitespace.

    Deliberately blunt: it lets "Data-visualisation" and "data visualization"
    meet, which is the whole point of a normalisation key.
    """
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", str(text))
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower()
    text = text.replace("&", " and ")
    # British/American spellings that matter in this domain.
    text = re.sub(r"\b(\w+)ization\b", r"\1isation", text)
    text = re.sub(r"\b(\w+)izing\b", r"\1ising", text)
    text = re.sub(r"[^a-z0-9+#. ]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def build_esco_index(esco_path):
    """Return {normalised label -> (conceptUri, preferredLabel, skillType)}.

    preferredLabels are indexed last so they win over any altLabel collision.
    """
    esco = pd.read_csv(esco_path, low_memory=False)
    log.info("loaded %s ESCO concepts", f"{len(esco):,}")

    index = {}
    for row in esco.itertuples(index=False):
        entry = (row.conceptUri, row.preferredLabel, row.skillType)
        # altLabels and hiddenLabels are newline-separated in the ESCO CSVs.
        for field in ("altLabels", "hiddenLabels"):
            raw = getattr(row, field, "")
            if isinstance(raw, str):
                for label in raw.split("\n"):
                    key = normalise(label)
                    if key and key not in index:
                        index[key] = entry
    for row in esco.itertuples(index=False):
        key = normalise(row.preferredLabel)
        if key:
            index[key] = (row.conceptUri, row.preferredLabel, row.skillType)

    log.info("indexed %s distinct labels", f"{len(index):,}")
    return index


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", default=ROOT / "config" / "skills_seed.csv", type=Path)
    parser.add_argument("--esco", default=ROOT / "data" / "raw" / "taxonomy_esco_v1.2.1" / "skills_en.csv", type=Path)
    parser.add_argument("--out", default=ROOT / "config" / "skill_to_esco.csv", type=Path)
    parser.add_argument("--show-unmapped", action="store_true")
    args = parser.parse_args()

    if not args.esco.exists():
        raise SystemExit(f"{args.esco} not found - put the ESCO CSVs in data/raw/taxonomy_esco_v1.2.1/ first.")

    index = build_esco_index(args.esco)
    seed = pd.read_csv(args.seed)

    rows = []
    for row in seed.itertuples(index=False):
        # Try the canonical name, then each alias, then the alias with any
        # parenthetical stripped. First hit wins.
        candidates = [row.canonical] + [a.strip() for a in str(row.aliases).split("|")]
        hit, matched_on = None, ""
        for cand in candidates:
            key = normalise(cand)
            if key in index:
                hit, matched_on = index[key], cand
                break
        rows.append({
            "canonical": row.canonical,
            "category": row.category,
            "esco_uri": hit[0] if hit else "",
            "esco_preferred_label": hit[1] if hit else "",
            "esco_skill_type": hit[2] if hit else "",
            "matched_on": matched_on,
        })

    mapping = pd.DataFrame(rows)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    mapping.to_csv(args.out, index=False, encoding="utf-8")

    mapped = (mapping["esco_uri"] != "").sum()
    print(f"\nWrote {args.out}")
    print(f"Mapped {mapped} of {len(mapping)} seed skills to ESCO ({mapped/len(mapping):.0%})")
    print("\nBy ESCO skill type:")
    print(mapping[mapping.esco_uri != ""]["esco_skill_type"].value_counts().to_string())

    print("\nCoverage by category:")
    cov = mapping.assign(ok=mapping.esco_uri != "").groupby("category")["ok"].agg(["sum", "count"])
    cov["pct"] = (cov["sum"] / cov["count"] * 100).round(0).astype(int)
    print(cov.to_string())

    unmapped = mapping[mapping.esco_uri == ""]["canonical"].tolist()
    if args.show_unmapped and unmapped:
        print(f"\nUnmapped ({len(unmapped)}):")
        print("  " + ", ".join(unmapped))
    elif unmapped:
        print(f"\n{len(unmapped)} unmapped - rerun with --show-unmapped to list them.")
    print(
        "\nUnmapped skills are not a failure. ESCO predates much of the current tool\n"
        "landscape, so gaps here are a finding worth a sentence on the poster."
    )


if __name__ == "__main__":
    main()
