"""Print the numbers needed to set the two embedding thresholds. Exploration only.

    python notebooks/pn_calibrate_matching.py > calibration.txt

1. Skill-name similarity within a dictionary category. Run on 8 Oct: substitutes did not
   separate from unrelated pairs, so match.py does not use it (kept as the evidence).
2. MIN_SIM["embed"] (recommend.py): how close a subject row that does NOT name a skill is to
   that skill. Above the threshold, the row counts as evidence.

Pick each threshold where the pairs above it are right and the pairs below it are wrong.
Do not use the labelled test sets (data/4_evaluation/labels/) for this: they are for the evaluation.
"""

import sys
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np  # noqa: E402

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


if __name__ == "__main__":
    main()
