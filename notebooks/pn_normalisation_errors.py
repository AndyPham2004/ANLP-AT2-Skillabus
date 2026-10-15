"""Normalisation error table (issue #71): traditional vs newer ways to map a skill phrase to ESCO.

Normalisation only matters for skills outside our dictionary (dictionary skills keep their own
id since c3d1ca4), so the test phrases are the spaCy-tier candidates that are NOT dictionary
skills, from two sets of ads nobody tuned normalisation on:
    the 20 double-labelled Seek ads (seek_label_sample_200.csv, double_label = y)
    the 22 full-text 2026 ads (jobs_au_recent_2024-2026_clean.csv)

For each phrase, side by side:
    exact     ESCO preferred or alternative label equal to the phrase (traditional)
    fuzzy     closest ESCO label by string similarity, difflib ratio >= FUZZY_MIN (traditional+)
    embed     closest ESCO preferred label by MiniLM cosine (newer; needs sentence-transformers)
    final     what normalise() returns: dictionary / esco_exact / esco_embed / lightcast / emerging

Writes data/4_evaluation/results/normalisation_errors.csv with empty `judgement` and `error_type` columns
to fill by hand (see ERROR_TYPES), then rerun with --summary to print the error table.

Run from the repo root:
    python notebooks/pn_normalisation_errors.py            # build the CSV (overwrites the judgements)
    python notebooks/pn_normalisation_errors.py --summary  # after judging

The judged table in the repo was built on 14 Oct, on the 22 full-text 2026 ads of the 13 Oct sample;
#87 replaced that sample on 14 Oct, so a rebuild gives different 2026 phrases and needs judging again.
"""

from __future__ import annotations

import argparse
import csv
import difflib
from collections import Counter
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from skillabus import paths  # noqa: E402
from skillabus.extract import extract  # noqa: E402
from skillabus.normalise import _esco_labels, esco_nearest, key, normalise  # noqa: E402
from skillabus.text import mask_pii  # noqa: E402

OUT = paths.RESULTS / "normalisation_errors.csv"
FUZZY_MIN = 0.85
EMBED_MIN = 0.82          # normalise.ESCO_MIN_SIM; reported, not tuned here

# How to fill `judgement` (per method column: exact_ok, fuzzy_ok, embed_ok, final_ok = y / n / blank
# when that method returned nothing) and `error_type` for the final answer:
ERROR_TYPES = {
    "ok":          "right concept, or rightly left emerging",
    "too_broad":   "a parent concept (\"use databases\" for DynamoDB)",
    "wrong_sense": "same words, another meaning (ESCO \"SPARK\" the Java framework)",
    "missed":      "left emerging although ESCO has the concept",
    "not_a_skill": "the phrase is not a skill (extraction error upstream); any mapping is wrong",
}


def _read(path: Path) -> list[dict]:
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def phrases() -> list[dict]:
    """Non-dictionary spaCy candidates from the two ad sets, one row per distinct phrase."""
    ads = [("seek_test", r["ad_id"], r["description"]) for r in _read(paths.LABEL_SAMPLE)
           if r.get("double_label") == "y"]
    ads += [("2026", r["ad_id"], r["description"]) for r in _read(paths.RECENT_ADS)
            if r.get("period", "").startswith("2026") and r.get("full_text") in ("True", "true", "1")]
    seen, out = set(), []
    for source, ad_id, text in ads:
        for m in extract(text or "", "ner"):
            k = key(m["text"])
            if m.get("canonical") or not k or k in seen:
                continue
            seen.add(k)
            out.append({"source": source, "ad_id": ad_id, "text": m["text"], "sentence": m["sentence"], "mention": m})
    return out


def build() -> None:
    rows = phrases()
    exact, _ = _esco_labels()
    labels = list(exact)
    nearest = esco_nearest([r["text"] for r in rows])
    final = normalise([r["mention"] for r in rows])
    table = []
    for r, near, fin in zip(rows, nearest, final):
        k = key(r["text"])
        ex = exact.get(k)
        close = difflib.get_close_matches(k, labels, n=1, cutoff=FUZZY_MIN)
        fz = exact[close[0]] if close else None
        table.append({
            "source": r["source"], "ad_id": r["ad_id"], "text": r["text"],
            "exact_label": ex[1] if ex else "",
            "fuzzy_label": fz[1] if fz else "",
            "fuzzy_ratio": round(difflib.SequenceMatcher(None, k, close[0]).ratio(), 2) if close else "",
            "embed_label": near[1] if near else "", "embed_sim": round(near[2], 3) if near else "",
            "final_how": fin["how"], "final_label": fin["skill_label"],
            "exact_ok": "", "fuzzy_ok": "", "embed_ok": "", "final_ok": "", "error_type": "", "note": "",
            "sentence": mask_pii(r["sentence"]),           # emails, phones, URLs out of the committed table
        })
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(table[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(table)
    print(f"{len(table)} phrases ({Counter(r['source'] for r in table)}) -> {OUT}")
    print("returned something:  exact", sum(bool(r["exact_label"]) for r in table),
          "| fuzzy", sum(bool(r["fuzzy_label"]) for r in table),
          f"| embed >= {EMBED_MIN}", sum(bool(r["embed_sim"]) and r["embed_sim"] >= EMBED_MIN for r in table))
    print("final step:", dict(Counter(r["final_how"] for r in table)))
    if not any(r["embed_label"] for r in table):
        print("No embedding model here: run on a machine with sentence-transformers for the embed column.")


def summary() -> None:
    table = _read(OUT)
    judged = [r for r in table if r["final_ok"]]
    print(f"{len(judged)} of {len(table)} phrases judged\n")
    print(f"{'method':<8} {'returned':>9} {'right':>6} {'precision':>10}")
    for method, col, ok in (("exact", "exact_label", "exact_ok"), ("fuzzy", "fuzzy_label", "fuzzy_ok"),
                            ("embed", "embed_label", "embed_ok")):
        returned = [r for r in judged if r[col] and (method != "embed" or float(r["embed_sim"] or 0) >= EMBED_MIN)]
        right = [r for r in returned if r[ok] == "y"]
        prec = f"{len(right) / len(returned):.2f}" if returned else "-"
        print(f"{method:<8} {len(returned):>9} {len(right):>6} {prec:>10}")
    print("\nfinal answer, error types:", dict(Counter(r["error_type"] or "?" for r in judged)))
    for etype in ERROR_TYPES:
        if etype == "ok":
            continue
        for r in [r for r in judged if r["error_type"] == etype][:3]:
            print(f"  {etype:<12} {r['text']!r} -> {r['final_label']!r} ({r['final_how']}) {r['note']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--summary", action="store_true")
    (summary if parser.parse_args().summary else build)()
