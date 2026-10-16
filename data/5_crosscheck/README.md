# 5_crosscheck: does the Seek picture hold elsewhere?

Counts on other platforms and markets, the extractor checked against the dataset author's flags, and
how much of our dictionary ESCO reaches. Used by the EDA (`notebooks/vt_eda.ipynb`) and report
section 3, not by the app. Every file here was made by Van Thong. Commands run from the repo root.

| File | What | Rebuild |
|---|---|---|
| `skill_counts_PRIMARY.csv` | The 133-skill dictionary over the 3,204 Seek ads (raw text): the September baseline the others are compared with | September run of `data-eda/src/extract_skills.py` on `data/raw/jobs_au_seek_datascientist_2019-2022.csv` (`data-eda/HOW_TO_USE_DATA.txt`, section 1) |
| `skill_counts_linkedin_us.csv` | The same over 247 US LinkedIn Data Scientist ads, 2023-24 | Van Thong's September EDA notebook (not in the repo), with `extract_skills.py` |
| `skill_counts_glassdoor_au_2022.csv` | The same over 193 Glassdoor Australia data roles, Aug-Dec 2022 | `python data-eda/src/count_glassdoor_au.py` |
| `role_rank_agreement.csv` | Plan D7: Spearman rank correlation per role between live Adzuna 2026 search counts and data_jobs 2023 (7 roles) or Seek 2019-22 (Data Scientist), over the skills both name. Only each role's 15 priority skills were searched, picked from those same sources, so it tests the order within that top group (0.40 Business Analyst to 0.77 Data Engineer; 0.71 Data Scientist vs Seek) | Van Thong, 16 Oct | `python data-eda/src/role_rank_agreement.py` |
| `extractor_agreement.csv` | Our extractor against the dataset author's 25 tool flags: agreement and Cohen's kappa per tool | `python data-eda/src/validate_against_authorflags.py` (reads the poster run's `archive/poster_AT2A/data/ad_skill_long.csv`) |
| `extractor_agreement_decomposed.csv` | Where the disagreements come from (glued words, the author's false positives) | Same script |

Owner: Van Thong. Planned here: `role_rank_agreement.csv` (plan D7).
