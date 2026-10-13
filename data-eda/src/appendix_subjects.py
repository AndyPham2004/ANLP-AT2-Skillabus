"""Print report Appendix A: rows per layer for every subject in subject_profiles.csv.

Usage: python data-eda/src/appendix_subjects.py > table.md
Owner: Akash (#79). Reads data/processed/subject_profiles.csv only.
"""
import collections
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROFILES = ROOT / "data" / "processed" / "subject_profiles.csv"
SHORT = {"C04372": "MDSI", "C04379": "BA", "C04380": "BA", "C04295": "IT", "C04373": "QF", "C04443": "AI"}
ORDER = ["MDSI", "BA", "IT", "QF", "AI"]


def main() -> None:
    names, courses = {}, collections.defaultdict(set)
    layers = collections.defaultdict(collections.Counter)
    with open(PROFILES, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            code = row["subject_code"]
            names[code] = row["subject_name"].strip()
            courses[code].update(row["course"].split("|"))
            layers[code][row["layer"]] += 1

    print("| Code | Subject | Courses | Obj. | Topics | Desc. |\n|---|---|---|---|---|---|")
    total = collections.Counter()
    for code in sorted(names, key=lambda c: ("C04372" not in courses[c], c)):
        short = sorted({SHORT.get(c, c) for c in courses[code]}, key=lambda s: ORDER.index(s) if s in ORDER else 99)
        n = layers[code]
        total.update(n)
        cell = lambda k: n[k] or "–"
        print(f"| {code} | {names[code]} | {', '.join(short)} | {cell('learning_objective')} "
              f"| {cell('weekly_topic')} | {cell('description')} |")
    print(f"| **Total** | {len(names)} subjects | | **{total['learning_objective']}** "
          f"| **{total['weekly_topic']}** | **{total['description']}** |")


if __name__ == "__main__":
    main()
