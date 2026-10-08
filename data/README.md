# Data sources

Data code lives in `data-eda/` (owner: Van Thong). The data itself is never committed:
`data-eda/data/` is gitignored, and both halves of it are on the team drive.

| Folder | What | Size | Where |
|---|---|---|---|
| `data-eda/data/raw/` | the downloads, untouched | 655 MB | team drive: TEAM-DRIVE-LINK |
| `data-eda/data/clean/` | cleaned files, built by scripts; **use these** | 44 MB | team drive: TEAM-DRIVE-LINK |

Unzip both into `data-eda/data/` and every script in `data-eda/src/` runs with its default
paths. Start with `data-eda/data/clean/README.txt`; `data-eda/HOW_TO_USE_DATA.txt` says which
file answers which question.

| Source | What we use | Period | Role | Link |
|---|---|---|---|---|
| Seek Australia, Data Scientist ads (Kaggle, nomilk) | **3,204** full-text ads | 2019–22 | the demand side: every demand % | [kaggle](https://www.kaggle.com/datasets/nomilk/data-science-job-listings-australia-20192020) |
| LinkedIn Job Postings (Kaggle, arshkon) | 123,849 ads, 99.9% US; 1,355 data roles | 2023–24 | validation only: ranking agrees with Seek at ρ = 0.819 | [kaggle](https://www.kaggle.com/datasets/arshkon/linkedin-job-postings) |
| ESCO v1.2.1 | 13,960 skill concepts, 100,886 labels | 2025 | the vocabulary `normalise()` maps to | [esco](https://esco.ec.europa.eu/en/use-esco/download) |
| O*NET 31.0 | 8,753 tool names | 2026 | tools ESCO lacks | [onet](https://www.onetcenter.org/database.html) |
| UTS Handbook 2026 | 70 subjects, 6 courses (19 MDSI) | 2026 | subject profiles | [handbook](https://coursehandbook.uts.edu.au) |
| Resume Dataset (Kaggle, snehaanbhawal) | 2,481 resumes; 125 with 2+ data skills | 2021 | resume parsing and CV–JD test pairs | [kaggle](https://www.kaggle.com/datasets/snehaanbhawal/resume-dataset) |
| Job-board APIs (Greenhouse, Lever, SmartRecruiters) | 234 ads, 22 Australian data roles | Sept 2026 | the 2026 sample | public APIs |

Notes for anyone citing these:

- **The Seek data is not PromptCloud's.** The poster's reference list says PromptCloud; the
  file we use is `listings2019_2022.csv` from the nomilk dataset above. Cite that one.
- We scraped neither Seek nor LinkedIn; both are published Kaggle datasets. The handbook was
  read with about 90 targeted, rate-limited requests, not a crawl; its `robots.txt`
  disallows crawling.
- **Label and evaluate on `data-eda/data/clean/`**, not `raw/`. The raw Seek text has words
  welded together where HTML was stripped (`TableauSuperior`); the clean file repairs that,
  so the labeller and the extractor see the same words.
- Resumes stay on the drive. Emails, phones and URLs are masked; names only partly.

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

Careful with `skills_seed_v2.csv`: it starts with a `#` comment line and also contains the
skill `C#`, so `pd.read_csv(..., comment="#")` silently cuts that row down to `C` with no
aliases. Use `skiprows=1` instead.
