"""Build the mock data the app is designed against (docs/data_contract.md).

1. subject_layers.csv: Handbook 2026 text for the 70 subjects, one row per learning objective,
   topic or description sentence (needs Van Thong's data/raw/data-eda/).
2. The two example gap results, run through app/baseline.py on the committed sample ad and resume.

Run from the repo root:  python app/mock/build_mock.py
"""

from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "app"))
import baseline  # noqa: E402
from baseline import fix_text, split_sentences  # noqa: E402

MOCK = ROOT / "app" / "mock"
RAW = ROOT / "data/raw/data-eda"
# Links checked by hand and found wrong. ESCO "SPARK" is a Java web micro-framework, not Apache
# Spark; ESCO has no Apache Spark concept, so Spark stays a dictionary (seed) skill.
WRONG_ESCO_LINKS = {"Spark"}


def split_topics(s: str) -> list[str]:
    s = fix_text(s)
    parts = re.split(r"\s*(?:\||•|\(\d+\)|(?<!\d)\d{1,2}\.\s)\s*", s) if s else []
    out = []
    for p in (p.strip(" :;-") for p in parts):
        if len(p) <= 3 or re.search(r"will cover (the )?(following )?topics|topics from the following", p, re.I):
            continue
        # Some subjects put a whole week's paragraph in one bullet; keep evidence sentence-sized.
        out.extend(split_sentences(p) if len(p) > 250 else [p])
    return out


def split_outcomes(s: str) -> list[str]:
    return [p.strip() for p in re.split(r"(?=SLO\s?\d+\s?:)", fix_text(s)) if len(p.strip()) > 5]


def subject_layers() -> pd.DataFrame:
    u = pd.read_csv(RAW / "data/raw/uts_subjects_2026.csv", dtype=str)
    rows = []
    for _, r in u.iterrows():
        base = {"subject_code": r.subject_code, "subject_name": fix_text(r.subject_name),
                "course": r.courses, "source_url": r.handbook_url, "collected_by": "handbook"}
        rows += [{**base, "layer": "learning_objective", "text": t} for t in split_outcomes(r.learning_outcomes)]
        rows += [{**base, "layer": "weekly_topic", "text": t} for t in split_topics(r.topics)]
        rows += [{**base, "layer": "description", "text": t} for t in split_sentences(r.description)]
    return pd.DataFrame(rows)


def main() -> None:
    # Van Thong's dictionary-to-ESCO links, small enough to commit so the app has them on the cloud.
    links = pd.read_csv(RAW / "config/skill_to_esco.csv", dtype=str)
    links = links[~links.canonical.isin(WRONG_ESCO_LINKS)]
    links.to_csv(ROOT / "data/processed/skill_to_esco.csv", index=False)
    layers = subject_layers()
    layers.to_csv(MOCK / "subject_layers.csv", index=False)
    baseline.resources.cache_clear()

    ad = (MOCK / "sample_ad.txt").read_text(encoding="utf-8")
    cv = (MOCK / "sample_resume.txt").read_text(encoding="utf-8")
    job = baseline.analyse(cv, ad, ad_id="rw-2026-09-23")
    role = baseline.analyse(cv, None, partial={"Statistics": "Statistics: descriptive statistics, hypothesis testing basics"})

    for name, data in (("gap_job_seeker.json", job), ("gap_role_data_scientist.json", role)):
        (MOCK / name).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        p = data["learning_path"]
        print(f"{name}: {sum(s['status'] != 'have' for s in data['skills'])}/{len(data['skills'])} gaps, "
              f"path {p['subjects']} closes {p['gaps_closed']}/{p['gaps_total']} ({p['demand_covered_pct']}% of demand)")
    print(f"subject_layers.csv: {len(layers)} rows, {layers.subject_code.nunique()} subjects, "
          f"{layers.layer.value_counts().to_dict()}")


if __name__ == "__main__":
    main()
