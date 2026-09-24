# Data sources

Nothing under `data/raw/` is committed. Van Thong's full EDA folder (raw files, scripts, outputs, `DATASETS.md`) lives at `data/raw/data-eda/`; ask him for the zip (about 690 MB). Download each source into `data/raw/<name>/`
and run the notebooks in `notebooks/` to produce the small CSVs in `data/processed/`
that the poster build reads.

| Source | What it gives us | Where |
|---|---|---|
| LinkedIn Job Postings 2023–2024 (Kaggle, arshkon) | ~124k job ads with title, description, location; the demand side | https://www.kaggle.com/datasets/arshkon/linkedin-job-postings |
| ESCO v1.2 skills taxonomy | 13.9k skills with labels and aliases; the shared vocabulary everything is normalised to | https://esco.ec.europa.eu/en/use-esco/download |
| O*NET 29 | role → skill/technology priors, used to seed the target-role profile | https://www.onetcenter.org/database.html |
| UTS Handbook (MDSI + related subjects) | subject descriptions and learning objectives, ~180 subjects | https://coursehandbook.uts.edu.au |
| Resume Dataset (Kaggle, snehaanbhawal) | 2.4k resumes in 24 categories; test set for resume parsing | https://www.kaggle.com/datasets/snehaanbhawal/resume-dataset |
| Seek AU sample (planned) | Australian ads for the Sydney view; only if the site terms allow a small research sample | — |

## Processed files read by the poster build

`src/build_poster.py` looks for these; if a file is missing it falls back to the
illustrative sample values baked into `src/figures.py` and stamps the chart as illustrative.

- `data/processed/top_skills.csv` — columns `skill,pct_ads` (share of Data Scientist ads mentioning the skill), `n_ads` in the header comment
- `data/processed/gap.csv` — columns `skill,pct_ads,covered` (`covered` = 1 if the sample profile already has the skill)
