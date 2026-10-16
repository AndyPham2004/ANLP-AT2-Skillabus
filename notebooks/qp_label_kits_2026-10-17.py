"""Label kits of 17 Oct 2026: the files three teammates read and mark, so the evaluation covers 2026 ads,
the IT roles and the subject recommendations for IT skills. Owner: Quan (written with Claude).

    PYTHONPATH=src python notebooks/qp_label_kits_2026-10-17.py

Writes, under data/4_evaluation/:
  inputs/ats_2026_label_sample.csv / .md   18 ATS 2026 ads, 2 per role (1 for Cloud and Data Engineer; the ATS
                                           file has no QA ad), seed 17; second_annotator = y for 6 of them
  labels/ad_skills_2026.csv                empty, same columns as ad_skills.csv
  inputs/vocabulary_detection_labels.csv   the names to use in skill_label (the vocabulary's detection rows)
  inputs/it_skill_subjects_to_check.csv    15 IT skills x the app's top 3 subjects, teaches left blank
  inputs/role_paths_2026-10-17.md, labels/role_paths_review.csv   the 11 role paths, and a sheet to mark them

The kits show only the ad text, never what the extractor found, so the labels stay independent of the system.
"""
from __future__ import annotations

import csv
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "app")]

import pandas as pd  # noqa: E402

from skillabus import paths  # noqa: E402

SEED = 17
MIN_CHARS = 600                      # a full ad, not a stub
SECOND_ANNOTATOR_ROLES = ["Software Engineer", "Data Scientist", "Machine Learning Engineer",
                          "Cybersecurity Analyst", "DevOps/SRE", "Network/Systems Administrator"]
IT_ROLES = ["Software Engineer", "Cloud Engineer", "Cybersecurity Analyst", "DevOps/SRE",
            "Network/Systems Administrator", "QA/Test Engineer", "Business Analyst"]
N_IT_SKILLS, TOP_SUBJECTS = 15, 3
INPUTS, LABELS = paths.EVALUATION / "inputs", paths.LABELS


def ad_sample() -> pd.DataFrame:
    ads = pd.read_csv(paths.ATS_2026_ADS, dtype=str, keep_default_na=False)
    ads = ads[(ads.role != "other") & (ads.description.str.len() >= MIN_CHARS)].sort_values("ad_id")
    rng = random.Random(SEED)
    picked = []
    for role, group in sorted(ads.groupby("role"), key=lambda g: g[0]):
        rows = group.to_dict("records")
        picked += rng.sample(rows, min(2, len(rows)))
    out = pd.DataFrame(picked)
    first = out.drop_duplicates("role").set_index("role").ad_id
    out["second_annotator"] = out.ad_id.isin({first[r] for r in SECOND_ANNOTATOR_ROLES if r in first}).map({True: "y", False: "n"})
    return out[["ad_id", "role", "company", "title", "url", "second_annotator", "description"]]


def write_ads(sample: pd.DataFrame) -> None:
    sample.to_csv(INPUTS / "ats_2026_label_sample.csv", index=False, encoding="utf-8", lineterminator="\n")
    parts = ["# 2026 ads to label (17 Oct 2026)\n",
             "Label into `data/4_evaluation/labels/ad_skills_2026.csv`, rules in `data/4_evaluation/labels/README.md`.",
             "`skill_label` = a name from `inputs/vocabulary_detection_labels.csv` when it is there, else your own short",
             "name with `in_dictionary` = n. Ads marked **second annotator** are labelled by both annotators.\n"]
    for i, ad in enumerate(sample.itertuples(), 1):
        tag = " · **second annotator**" if ad.second_annotator == "y" else ""
        parts += [f"## {i}. {ad.ad_id} · {ad.role}{tag}", f"*{ad.title}*, {ad.company}. {ad.url}\n", ad.description.strip(), ""]
    (INPUTS / "ats_2026_label_sample.md").write_text("\n".join(parts), encoding="utf-8")
    header = ["ad_id", "skill_label", "in_dictionary", "evidence_text", "annotator"]
    target = LABELS / "ad_skills_2026.csv"
    if not target.exists():
        target.write_text(",".join(header) + "\n", encoding="utf-8")


def write_vocabulary() -> pd.DataFrame:
    vocab = pd.read_csv(paths.SKILLS_VOCABULARY, dtype=str, keep_default_na=False)
    det = vocab[vocab.used_for.str.contains("extract") & (vocab.aliases_ads != "")]
    det = det[["label", "category", "aliases_ads"]].sort_values(["category", "label"])
    det.to_csv(INPUTS / "vocabulary_detection_labels.csv", index=False, encoding="utf-8", lineterminator="\n")
    return det


def role_results() -> dict[str, dict]:
    """The app's role mode for every role: empty resume, nothing taken, MDSI as home course."""
    import backend
    from skillabus.match import roles
    names = [r["role"] if isinstance(r, dict) else r for r in roles()]
    return {role: backend.analyse("", None, [], role=role, use_llm=False)[0] for role in names}


def write_it_subjects(results: dict[str, dict], det: pd.DataFrame) -> list[str]:
    from skillabus.recommend import subject_evidence
    done = {r["skill_label"] for r in csv.DictReader(open(LABELS / "skill_subject_pairs.csv", encoding="utf-8"))}
    category = dict(zip(det.label, det.category))
    best: dict[str, float] = {}
    for role in IT_ROLES:
        for s in results[role]["skills"]:
            name = s["skill_label"]
            if name in done or category.get(name) in (None, "Professional", "Certification"):
                continue
            best[name] = max(best.get(name, 0.0), s.get("demand_pct") or 0.0)
    skills = sorted(best, key=lambda n: (-best[n], n))[:N_IT_SKILLS]
    evidence = subject_evidence(skills)
    rows = []
    for name in skills:
        for rank, e in enumerate(evidence.get(name, [])[:TOP_SUBJECTS], 1):
            rows.append({"skill_label": name, "top_demand_pct": best[name], "rank": rank, "subject_code": e["subject_code"],
                         "subject_name": e["subject_name"], "layer": e["layer"], "app_evidence": e["text"],
                         "source_url": e["source_url"], "teaches": "", "evidence_text": "", "annotator": ""})
        if not evidence.get(name):
            rows.append({"skill_label": name, "top_demand_pct": best[name], "rank": 0, "subject_code": "",
                         "subject_name": "(the app finds no subject)", "layer": "", "app_evidence": "", "source_url": "",
                         "teaches": "", "evidence_text": "", "annotator": ""})
    pd.DataFrame(rows).to_csv(INPUTS / "it_skill_subjects_to_check.csv", index=False, encoding="utf-8", lineterminator="\n")
    return skills


def write_paths(results: dict[str, dict]) -> None:
    parts = ["# Learning paths of the 11 roles (17 Oct 2026)\n",
             "What the app shows a student with an empty resume and no subject taken, MDSI as home course",
             "(`backend.analyse(\"\", None, [], role=...)`, no GPT tier). Mark each path subject in",
             "`data/4_evaluation/labels/role_paths_review.csv`: verdict ok / odd, and why when odd.\n"]
    review = []
    for role, res in results.items():
        path = res.get("learning_path") or {}
        names = {r["subject_code"]: r.get("subject_name", "") for r in res.get("recommendations", [])}
        covers = {r["subject_code"]: r.get("covers") or [] for r in res.get("recommendations", [])}
        parts.append(f"## {role}: {' → '.join(path.get('subjects', [])) or '(no path)'}, {path.get('demand_covered_pct', '')}% of the gap weight\n")
        parts.append("| Skill | 2026 share | Status |\n|---|---|---|")
        parts += [f"| {s['skill_label']} | {s.get('demand_pct')}% | {s['status']} |" for s in res["skills"]]
        parts.append("\n| Path subject | Name | Covers |\n|---|---|---|")
        for code in path.get("subjects", []):
            parts.append(f"| {code} | {names.get(code, '')} | {', '.join(covers.get(code, []))} |")
            review.append({"role": role, "subject_code": code, "subject_name": names.get(code, ""),
                           "covers": "; ".join(covers.get(code, [])), "verdict": "", "why": "", "reviewer": ""})
        parts.append("")
    (INPUTS / "role_paths_2026-10-17.md").write_text("\n".join(parts), encoding="utf-8")
    target = LABELS / "role_paths_review.csv"
    if not target.exists():
        pd.DataFrame(review).to_csv(target, index=False, encoding="utf-8", lineterminator="\n")


def main() -> None:
    sample = ad_sample()
    write_ads(sample)
    det = write_vocabulary()
    results = role_results()
    skills = write_it_subjects(results, det)
    write_paths(results)
    print(f"{len(sample)} ads ({(sample.second_annotator == 'y').sum()} for the second annotator):",
          sample.role.value_counts().to_dict())
    print(f"{len(det)} vocabulary labels; IT skills to check: {skills}")


if __name__ == "__main__":
    main()
