"""Print the numbers needed to set the two embedding thresholds. Exploration only.

    python notebooks/pn_calibrate_matching.py > calibration.txt
    python notebooks/pn_calibrate_matching.py --it            # T1: write the IT rows to judge
    python notebooks/pn_calibrate_matching.py --it-summary    # T1: precision per cut, after judging

1. Skill-name similarity within a dictionary category. Run on 8 Oct: substitutes did not
   separate from unrelated pairs, so match.py does not use it (kept as the evidence).
2. MIN_SIM["embed"] (recommend.py): how close a subject row that does NOT name a skill is to
   that skill. Above the threshold, the row counts as evidence.

3. T1 (plan of 14 Oct): the same check for IT skills. Part 2 was set on 8 Oct with 22 data
   skills; IT skills (Kubernetes, Terraform, React) are worded differently in the Handbook.
   --it writes, for 12 IT skills, the subject rows that do NOT name the skill: every one at
   cosine >= 0.50, and the closest ones down to 0.40 (at most 15 per skill), with a `relevant`
   column to fill by hand (y: the row teaches the skill or a direct part of it; n: it does not).
   Scores keep 5 decimals, enough to compare them with a cut as recommend() does.
   A rerun keeps the judgements already made (matched on skill, subject, layer and text).
   --it-summary prints, for each cut, how many rows above it are relevant.
   None of the 12 skills is in the skill-subject test pairs (skill_subject_pairs.csv).

Pick each threshold where the pairs above it are right and the pairs below it are wrong.
Do not use the labelled test sets (data/4_evaluation/labels/) for this: they are for the evaluation.
"""

import argparse
import csv
import sys
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np  # noqa: E402

from skillabus import paths  # noqa: E402
from skillabus.extract import load_dictionary  # noqa: E402
from skillabus.match import NOT_TRANSFERABLE  # noqa: E402
from skillabus.recommend import MIN_SIM, PROFILE_PATHS, _query, load_profiles  # noqa: E402
from skillabus.similarity import EMBED_MODEL, embed, embeddings_available, similarity  # noqa: E402

SAMPLE = ROOT / "tests" / "fixtures" / "subject_profiles_sample.csv"
SKILLS = ["Machine learning", "Predictive modelling", "Artificial intelligence", "Deep learning",
          "Large language models", "Generative AI", "Natural language processing", "Statistics",
          "Data visualisation", "Spark", "Cloud platforms", "AWS", "Optimisation", "Tableau", "Hadoop",
          "SQL", "Python", "MLOps", "Docker", "RAG", "Data governance", "Time series forecasting"]
CHECK_PAIRS = [("Tableau", "Power BI"), ("Tableau", "Excel"), ("Tableau", "matplotlib"), ("AWS", "Azure"),
               ("AWS", "Snowflake"), ("TensorFlow", "PyTorch"), ("Spark", "Hadoop"), ("Spark", "pandas"),
               ("PostgreSQL", "MySQL"), ("PostgreSQL", "Redis"), ("Kubernetes", "Docker"), ("Kubernetes", "Git"),
               ("XGBoost", "LightGBM"), ("XGBoost", "Clustering"), ("A/B testing", "Experimental design"),
               ("A/B testing", "Econometrics"), ("BERT", "Hugging Face"), ("BERT", "Sentiment analysis")]
# T1: IT skills, none of them in data/4_evaluation/labels/skill_subject_pairs.csv
IT_SKILLS = ["Java", "JavaScript", "React", "Linux", "Git", "Docker", "Kubernetes", "CI/CD", "Terraform",
             "Kafka", "API development", "Data security"]
IT_ROWS = paths.T1_IT_ROWS
IT_ALL = 0.50                             # every unnamed row at or above this is written
IT_FLOOR, IT_PER_SKILL = 0.40, 15         # below it: the closest rows down to the floor, at most this many per skill
CUTS = (0.45, 0.50, 0.55, 0.60, 0.65, 0.70)


def main() -> None:
    if not embeddings_available():
        sys.exit("The embedding model is not available (no internet for the first download, or SKILLABUS_NO_EMBED is set).")
    print(f"model: {EMBED_MODEL}\ncurrent MIN_SIM['embed'] = {MIN_SIM['embed']}\n")

    # ------------------------------------------------------------ 1. substitute skills
    skills = [s for s in load_dictionary() if s["category"] not in NOT_TRANSFERABLE]
    names = [s["canonical"] for s in skills]
    category = {s["canonical"]: s["category"] for s in skills}
    vectors = dict(zip(names, embed(names)))
    pairs = [(float(vectors[a] @ vectors[b]), a, b) for a, b in combinations(names, 2) if category[a] == category[b]]
    pairs.sort(reverse=True)
    sims = np.array([p[0] for p in pairs])
    print(f"== 1. Same-category skill pairs: {len(pairs)}")
    print("percentiles 10/25/50/75/90/95:", np.percentile(sims, [10, 25, 50, 75, 90, 95]).round(2).tolist())
    for cut in (0.4, 0.5, 0.6, 0.7):
        print(f"pairs >= {cut}: {(sims >= cut).sum()}")
    print("\n-- pairs to judge by hand")
    for a, b in CHECK_PAIRS:
        print(f"  {float(vectors[a] @ vectors[b]):.2f}  {a} ~ {b}")
    print("\n-- the 70 closest pairs")
    for sim, a, b in pairs[:70]:
        print(f"  {sim:.2f}  [{category[a]}] {a} ~ {b}")

    # ------------------------------------------------------------- 2. subject evidence
    path = next((p for p in PROFILE_PATHS if p.exists()), SAMPLE)
    rows, named, _ = load_profiles(str(path))
    texts = [row["text"] for row in rows]
    print(f"\n== 2. Subject rows that do NOT name the skill ({path.relative_to(ROOT)}, {len(rows)} rows)")
    emb = similarity([_query(k) for k in SKILLS], texts, "embed")
    tfidf = similarity([_query(k) for k in SKILLS], texts, "tfidf")
    for i, skill in enumerate(SKILLS):
        is_unnamed = np.array([skill not in hits for hits in named])
        unnamed = [j for j in np.argsort(-emb[i]) if is_unnamed[j]][:10]
        print(f"\n-- {skill}  (rows naming it: {int((~is_unnamed).sum())}; unnamed rows >= 0.4: "
              f"{int(((emb[i] >= 0.4) & is_unnamed).sum())}, >= 0.5: {int(((emb[i] >= 0.5) & is_unnamed).sum())})")
        for j in unnamed:
            row = rows[j]
            print(f"  embed {emb[i, j]:.2f} tfidf {tfidf[i, j]:.2f}  {row['subject_code']} [{row['layer'][:9]}] {row['text'][:110]}")


def it_rows() -> None:
    """T1: the closest unnamed subject rows for each IT skill, to judge by hand."""
    if not embeddings_available():
        sys.exit("The embedding model is not available (no internet for the first download, or SKILLABUS_NO_EMBED is set).")
    path = next((p for p in PROFILE_PATHS if p.exists()), SAMPLE)
    rows, named, _ = load_profiles(str(path))
    texts = [row["text"] for row in rows]
    emb = similarity([_query(k) for k in IT_SKILLS], texts, "embed")
    tfidf = similarity([_query(k) for k in IT_SKILLS], texts, "tfidf")
    def _id(r: dict) -> tuple:
        return r["skill"], r["subject_code"], r["layer"], r["text"]

    judged = {}
    if IT_ROWS.exists():                  # keep the judgements of an earlier run
        with open(IT_ROWS, encoding="utf-8", newline="") as f:
            judged = {_id(r): (r["relevant"], r["note"]) for r in csv.DictReader(f) if r.get("relevant")}
    out = []
    for i, skill in enumerate(IT_SKILLS):
        n_named = sum(skill in hits for hits in named)
        order = [j for j in np.argsort(-emb[i], kind="stable") if skill not in named[j] and emb[i, j] >= IT_FLOOR]
        unnamed = [j for j in order if emb[i, j] >= IT_ALL]
        unnamed += [j for j in order if emb[i, j] < IT_ALL][: max(0, IT_PER_SKILL - len(unnamed))]
        print(f"{skill:<16} rows naming it {n_named:>4} | unnamed rows >= {IT_FLOOR}: {len(unnamed)}"
              + "".join(f" | >= {c}: {int(((emb[i] >= c) & np.array([skill not in h for h in named])).sum())}"
                        for c in (0.5, 0.55, 0.6)))
        for j in unnamed:
            row = rows[j]
            new = {"skill": skill, "embed": round(float(emb[i, j]), 5), "tfidf": round(float(tfidf[i, j]), 3),
                   "subject_code": row["subject_code"], "subject_name": row.get("subject_name", ""),
                   "layer": row["layer"], "text": row["text"], "relevant": "", "note": ""}
            new["relevant"], new["note"] = judged.get(_id(new), ("", ""))
            out.append(new)
    IT_ROWS.parent.mkdir(parents=True, exist_ok=True)
    with open(IT_ROWS, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(out)
    kept = sum(bool(r["relevant"]) for r in out)
    print(f"\n{len(out)} rows from {path.relative_to(ROOT)} ({len(rows)} rows), model {EMBED_MODEL} -> {IT_ROWS.relative_to(ROOT)}")
    print(f"{kept} judgements kept from the earlier run, {len(out) - kept} rows to judge")


def it_summary() -> None:
    """T1: for each cut, the judged rows above it and how many are relevant."""
    with open(IT_ROWS, encoding="utf-8", newline="") as f:
        table = list(csv.DictReader(f))
    judged = [r for r in table if r["relevant"] in ("y", "n")]
    print(f"{len(judged)} of {len(table)} rows judged, {sum(r['relevant'] == 'y' for r in judged)} relevant\n")
    print(f"{'cut':>5} {'above':>6} {'relevant':>9} {'precision':>10} {'relevant below':>15}")
    for cut in CUTS:
        above = [r for r in judged if float(r["embed"]) >= cut]
        right = sum(r["relevant"] == "y" for r in above)
        below = sum(r["relevant"] == "y" for r in judged if float(r["embed"]) < cut)
        prec = f"{right / len(above):.2f}" if above else "-"
        print(f"{cut:>5} {len(above):>6} {right:>9} {prec:>10} {below:>15}")
    for cut in (0.50, MIN_SIM["embed"]):
        print(f"\nper skill at {cut}")
        for skill in IT_SKILLS:
            above = [r for r in judged if r["skill"] == skill and float(r["embed"]) >= cut]
            if above:
                print(f"  {skill:<16} {sum(r['relevant'] == 'y' for r in above)}/{len(above)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--it", action="store_true", help="T1: write the IT rows to judge")
    parser.add_argument("--it-summary", action="store_true", help="T1: precision per cut on the judged rows")
    args = parser.parse_args()
    it_rows() if args.it else it_summary() if args.it_summary else main()
