# 5_crosscheck: does the Seek picture hold elsewhere?

Counts on other platforms and markets, the extractor checked against the dataset author's flags, and
how much of our dictionary ESCO reaches. Used by the EDA (`notebooks/vt_eda.ipynb`) and report
section 3, not by the app. Every file here was made by Van Thong. Commands run from the repo root.

| File | What | Rebuild |
|---|---|---|
| `skill_counts_PRIMARY.csv` | The 133-skill dictionary over the 3,204 Seek ads (raw text): the September baseline the others are compared with | September run of `data-eda/src/extract_skills.py` on `data/raw/jobs_au_seek_datascientist_2019-2022.csv` (`data-eda/HOW_TO_USE_DATA.txt`, section 1) |
| `skill_counts_linkedin_us.csv` | The same over 247 US LinkedIn Data Scientist ads, 2023-24 | Van Thong's September EDA notebook (not in the repo), with `extract_skills.py` |
| `skill_counts_glassdoor_au_2022.csv` | The same over 193 Glassdoor Australia data roles, Aug-Dec 2022 | `python data-eda/src/count_glassdoor_au.py` |
| `au_vs_us_comparison.csv` | Share per skill, Australia 2019-22 against US 2023-24 | September EDA notebook (not in the repo) |
| `extractor_agreement.csv` | Our extractor against the dataset author's 25 tool flags: agreement and Cohen's kappa per tool | `python data-eda/src/validate_against_authorflags.py` (reads the poster run's `archive/poster_AT2A/data/ad_skill_long.csv`) |
| `extractor_agreement_decomposed.csv` | Where the disagreements come from (glued words, the author's false positives) | Same script |
| `source_counts.csv` | Rows, columns and size of every raw download (poster block 3) | `archive/poster_AT2A/scripts/source_counts.py` (frozen) |
| `esco_coverage/esco_absent.csv` | Dictionary skills with no ESCO concept (73) | September EDA notebook (not in the repo) |
| `esco_coverage/esco_verbphrase.csv` | Dictionary skills ESCO has only as a verb phrase (12) | September EDA notebook (not in the repo) |

Owner: Van Thong. Planned here: `role_rank_agreement.csv` (plan D7).
