# Data sources

Data code lives in `data-eda/` (owner: Van Thong). The cleaned data is committed; the raw
downloads are not.

| Folder | What | Size | Where |
|---|---|---|---|
| `data-eda/data/clean/` | cleaned Seek ads, the 200-ad label sample, de-identified resumes, ESCO skills and label lookup; **use these** | 46 MB | **in this repo** |
| `data-eda/data/raw/` | the downloads, untouched; only needed to rebuild `clean/` | 655 MB | not in git: re-download from the Kaggle links below, or ask Van Thong for the zip |

Start with `data-eda/data/clean/README.txt`; the EDA notebook is `notebooks/vt_eda.ipynb` (runs on
committed files only, about 3 minutes; figures in `data-eda/outputs/figures/`); `data-eda/HOW_TO_USE_DATA.txt` says which file
answers which question. Four clean files are over the 5 MB limit in CONTRIBUTING.md
(Seek 9.7 MB, resumes 14.8 MB, ESCO skills 6.7 MB, ESCO lookup 14.3 MB); keeping them in the repo means
everyone labels and evaluates on byte-identical files.

| Source | What we use | Period | Role | Link |
|---|---|---|---|---|
| Seek Australia, Data Scientist ads (Kaggle, nomilk) | **3,204** full-text ads | 2019–22 | the demand side: every demand % | [kaggle](https://www.kaggle.com/datasets/nomilk/data-science-job-listings-australia-20192020) |
| LinkedIn Job Postings (Kaggle, arshkon) | 123,849 ads, 99.9% US; 1,355 data roles | 2023–24 | validation only: ranking agrees with Seek at ρ = 0.819 | [kaggle](https://www.kaggle.com/datasets/arshkon/linkedin-job-postings) |
| Glassdoor Australia (Kaggle, nadzmiagthomas) | 193 data roles, full text | Aug–Dec 2022 | platform check only: rank correlation 0.75 with Seek (technical skills) | [kaggle](https://www.kaggle.com/datasets/nadzmiagthomas/australia-data-science-jobs) |
| ESCO v1.2.1 | 13,960 skill concepts, 100,886 labels | 2025 | the vocabulary `normalise()` maps to | [esco](https://esco.ec.europa.eu/en/use-esco/download) |
| O*NET 31.0 | 8,753 tool names | 2026 | tools ESCO lacks | [onet](https://www.onetcenter.org/database.html) |
| UTS Handbook 2026 | 70 subjects, 6 courses (19 MDSI) | 2026 | subject profiles | [handbook](https://coursehandbook.uts.edu.au) |
| Resume Dataset (Kaggle, snehaanbhawal) | 2,481 resumes; 125 with 2+ data skills | 2021 | resume parsing and CV–JD test pairs | [kaggle](https://www.kaggle.com/datasets/snehaanbhawal/resume-dataset) |
| Job-board APIs (Greenhouse, Lever, SmartRecruiters) + Adzuna API | 55 Australian data roles: 22 full text, 33 cut at 500 characters by Adzuna | Sept 2026 | the 2026 sample | public APIs |
| LinkedIn data-science postings (Kaggle, asaniczka) | 124 Australian data roles, full text | Jan 2024 | Australian middle point for the 2019–22 → 2026 trend | [kaggle](https://www.kaggle.com/datasets/asaniczka/data-science-job-postings-and-skills) |

Notes for anyone citing these:

- **The Seek data is not PromptCloud's.** The poster's reference list says PromptCloud; the
  file we use is `listings2019_2022.csv` from the nomilk dataset above. Cite that one.
- We scraped neither Seek nor LinkedIn; both are published Kaggle datasets. The handbook was
  read with about 90 targeted, rate-limited requests, not a crawl; its `robots.txt`
  disallows crawling.
- **Label and evaluate on `data-eda/data/clean/`**, not `raw/`. The raw Seek text has words
  welded together where HTML was stripped (`TableauSuperior`); the clean file repairs that,
  so the labeller and the extractor see the same words.
- **The 2026 sample is small: 22 full-text roles, not the ~150 planned.** Indeed was dropped
  because its terms forbid scraping and it has no public search API. Adzuna's API cuts every
  description at 500 characters, so its 33 roles count as roles but not for skill shares.
  The January 2024 LinkedIn rows are kept as their own period, not merged into 2026. All of
  it is in `data-eda/data/clean/jobs_au_recent_2024-2026_clean.csv`
  (`python src/build_recent_sample.py`).
- Resumes are de-identified, not anonymous: emails, phones, URLs and 1,071 person names are
  masked, but a name in capitals or a lone first name can survive. Mask again with spaCy
  before sending any resume text to an LLM.

Rebuild the cleaned files from `data-eda/`:

```powershell
python src/clean_seek.py; python src/clean_resumes.py; python src/clean_esco.py; python src/make_label_sample.py
```

## Processed files behind the poster

Small CSVs, committed. They are the record of what the poster shows; the bars in the HTML were generated from them on 25 Sep 2026.

- `data/processed/skills_seed_v2.csv` — the one dictionary every poster chart uses (B's 133 aliases + 5 generic rows)
- `data/processed/skill_counts_v2.csv` — every dictionary skill counted over the 3,204 Seek ads
- `data/processed/top_skills.csv` — block 7: columns `skill,pct_ads`, n in the header comment
- `data/processed/gap.csv` — block 5: columns `skill,pct_ads,covered` (`covered` = 1 if the sample resume has the skill)

- `data/processed/skill_counts_2026.csv` — every v2 dictionary skill in three periods, same
  method: `pct_2019_22` (3,204 Seek ads, clean text), `pct_2024_01` (124 Australian LinkedIn data
  roles), `n_2026` / `pct_2026` (22 full-text 2026 roles) with a 95% Wilson interval. `match.py`
  reads `pct_2026` as `demand_pct_2026`. Built by `python data-eda/src/recount_recent.py`.
  **Read with care:** 2026 is 22 ads from a few tech employers, AI-titled roles included, so
  per-skill 2026 shares carry intervals of ±20 points. The one robust signal is direction: any
  LLM-era skill 0% → 2.4% → 50% (11 of 22), and the rise holds within non-AI-titled roles
  (0.9% → 30%, n = 10). Show 2026 as "n of 22", not as a bare percentage.

Careful with `skills_seed_v2.csv`: it starts with a `#` comment line and also contains the
skill `C#`, so `pd.read_csv(..., comment="#")` silently cuts that row down to `C` with no
aliases. Use `skiprows=1` instead.
