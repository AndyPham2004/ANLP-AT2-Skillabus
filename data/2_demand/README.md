# 2_demand: what employers ask for

Market demand by skill (and, from `role_profiles.csv`, by role), plus the cleaned ads it is counted on
and the lists used to collect them. Code takes these paths from `src/skillabus/paths.py`. Commands run
from the repo root.

| File | What | Made by | Rebuild |
|---|---|---|---|
| `skill_counts_v2.csv` | Every dictionary skill (148) over the 3,204 Seek Data Scientist ads 2019-22, counted on the raw text as on the poster; `match.py` reads `pct_ads` as `demand_pct` | Quan 25 Sep (poster), Van Thong 14 Oct (10 new rows) | `python data-eda/src/extract_skills.py --input data/raw/jobs_au_seek_datascientist_2019-2022.csv --text-col description --id-col ad_id --seed data/1_knowledge/skills/skills_seed_v2.csv`; keep the columns `skill, category, n_ads, pct_ads` of `data/runtime/extract_skills/skill_counts.csv` |
| `skill_counts_2026.csv` | Every dictionary skill in 2019-22, Jan 2024 and 2026 with 95% Wilson intervals (see below) | Van Thong | `python data-eda/src/recount_recent.py` |
| `top_skills.csv` | The 15 most-asked technical skills, the Data Scientist role profile (`match.role_profile`) | Quan, 25 Sep | From `skill_counts_v2.csv`, technical categories only |
| `role_profiles.csv` | Tool profiles of 7 data and IT roles (data_jobs 2023, Apache-2.0), 441 rows; notes in `role_profiles.md` | Van Thong | `python data-eda/src/build_role_profiles.py` |
| `skills_not_taught_by_uts.csv` | 73 skills: 54 that no UTS subject names, plus 19 named but asked for in 10%+ of 2026 ads (was `uncovered_skills_2026-10-13.csv`) | Quan's session, 13 Oct | Recompute after the vocabulary (D5) and the IT subjects (D8) |
| `ads/jobs_au_seek_datascientist_2019-2022_clean.csv` | 3,204 Seek Data Scientist ads, glued words split | Van Thong | `python data-eda/src/clean_seek.py` |
| `ads/jobs_au_recent_2024-2026_clean.csv` | 192 Australian data roles: job boards 2026, Adzuna 2026 (500 characters), LinkedIn Jan 2024 | Van Thong | `python data-eda/src/build_recent_sample.py` |
| `ads/CLEANING_NOTES.txt` | What each cleaned file is, who uses it, how it was cleaned (was `data-eda/data/clean/README.txt`) | Van Thong | Text |
| `collection/ats_companies.csv` | The 65 job boards `fetch_ats.py` reads | Van Thong, Quan | Edited by hand |
| `collection/ats_candidates.csv` | 206 candidate employers with a slug guess per platform | Quan, 13 Oct | Edited by hand |
| `collection/ats_probe_2026-10-13.csv` | Which boards answered, with how many Australian data roles | Quan, 13 Oct | `python data-eda/src/probe_ats.py` (writes `ats_probe_<date>.csv`) |
| `emerging/emerging_candidates.csv` | Phrases rising in the 2026 ads that neither the dictionary nor ESCO knows, n-gram and spaCy | Phuong Nhi | `python -m skillabus.emerging` (with `PYTHONPATH=src`) |
| `emerging/emerging_candidates_2024-2026.csv` | The same with the Jan 2024 LinkedIn ads added | Phuong Nhi | `python -m skillabus.emerging --with-2024 --out data/2_demand/emerging/emerging_candidates_2024-2026.csv` |

`skill_counts_2026.csv` columns: `pct_2019_22` (3,204 Seek listings, clean text, counted per listing as
on the poster), `pct_2024_01` (122 Australian LinkedIn data roles), `n_2026` / `pct_2026` (the 9
data-scientist ads of the 2026 sample) and `n_2026_all` / `pct_2026_all` (all 22 sample roles), each
with a 95% Wilson interval. `match.py` reads `pct_2026` as `demand_pct_2026` (trend column) and
`pct_2026_all_low` as the 2026 floor of the gap weight in `recommend._weight` (via
`match.demand_2026_low`). **Read with care:** 22 ads from 12 employers, 9 of them data scientists from
5, so one ad moves a data-scientist share by 11 points. Show 2026 as "n of 9", not as a bare percentage.

Owner of the folder: Van Thong. Planned here (plan D1, D6, D13): `roles.csv`, `role_skill_demand.csv`
(one table for every source; then `skill_counts_*`, `top_skills.csv` and `role_profiles.*` go to
`archive/demand_files_v1/`), `role_outlook.csv`.
