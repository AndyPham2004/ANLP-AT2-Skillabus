"""Print report Appendix A from data/1_knowledge/uts/subject_profiles.csv.

A.1: one row per UTS course (level, name, subjects, rows per layer).
A.2: one row per MDSI subject (C04372), rows per layer.
Course names are read from the "## Courses" section of data/1_knowledge/uts/subject_profiles.md.

Usage: python data-eda/src/appendix_subjects.py > appendix_a.md
Owner: Akash (#79). Standard library only.
"""
import collections
import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROFILES = ROOT / "data" / "1_knowledge" / "uts" / "subject_profiles.csv"
NOTES = ROOT / "data" / "1_knowledge" / "uts" / "subject_profiles.md"
LAYERS = ["learning_objective", "assessment", "weekly_topic", "description"]
HEAD = "| Obj. | Assess. | Topics | Desc. |"
LEVEL = {"C04": "Master", "C06": "Grad. diploma", "C09": "Honours", "C10": "Bachelor", "C11": "Grad. certificate"}
MDSI = "C04372"


def course_names() -> dict:
    """Map course code -> name from the notes, e.g. 'C04379/C04380 Business Analytics'."""
    text = NOTES.read_text(encoding="utf-8").split("## Courses", 1)[1].split("Course codes were found", 1)[0]
    text = re.sub(r"\s+", " ", text)
    names, pending = {}, []
    for token in re.split(r"(C\d{5})", text):
        if re.fullmatch(r"C\d{5}", token):
            pending.append(token)
            continue
        name = re.split(r"[;.]", token)[0].strip(" ,/")
        name = re.sub(r"^(Masters|Graduate diplomas|Graduate certificates|Bachelors|honours):?\s*", "", name).strip(" ,/")
        if pending and name:
            names.update({code: name for code in pending})
            pending = []
    return names


def cells(counter: collections.Counter) -> str:
    return " | ".join(f"{counter[layer]:,}" if counter[layer] else "–" for layer in LAYERS)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    names = course_names()
    subject_name, subject_layers = {}, collections.defaultdict(collections.Counter)
    course_subjects, course_layers = collections.defaultdict(set), collections.defaultdict(collections.Counter)
    with open(PROFILES, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            code = row["subject_code"]
            subject_name[code] = row["subject_name"].strip()
            subject_layers[code][row["layer"]] += 1
            for course in row["course"].split("|"):
                course_subjects[course].add(code)
                course_layers[course][row["layer"]] += 1

    print("**A.1 Courses.** A subject in several courses is counted in each, so columns do not add up to the total.\n")
    print(f"| Course | Level | Name | Subjects {HEAD}\n|---|---|---|---|---|---|---|---|")
    for course in sorted(course_subjects, key=lambda c: (c[:3] != "C04", c[:3], c)):
        print(f"| {course} | {LEVEL.get(course[:3], '')} | {names.get(course, '')} "
              f"| {len(course_subjects[course])} | {cells(course_layers[course])} |")
    total = collections.Counter()
    for counts in subject_layers.values():
        total.update(counts)
    print(f"| **All** | | {len(course_subjects)} courses | **{len(subject_name)}** | {cells(total)} |")

    print(f"\n**A.2 MDSI subjects ({MDSI}).**\n")
    print(f"| Code | Subject {HEAD}\n|---|---|---|---|---|---|")
    mdsi_total = collections.Counter()
    for code in sorted(course_subjects[MDSI]):
        mdsi_total.update(subject_layers[code])
        print(f"| {code} | {subject_name[code]} | {cells(subject_layers[code])} |")
    print(f"| **Total** | {len(course_subjects[MDSI])} subjects | {cells(mdsi_total)} |")


if __name__ == "__main__":
    main()
