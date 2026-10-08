# Data sources

Data code lives in `data-eda/` (owner: Van Thong). The cleaned data is committed; the raw
downloads and the resumes are not.

| Folder | What | Size | Where |
|---|---|---|---|
| `data-eda/data/clean/` | cleaned Seek ads, the 200-ad label sample, ESCO skills and label lookup; **use these** | 31 MB | **in this repo** |
| `data-eda/data/clean/resumes_us_2021_clean.csv` | cleaned resumes; names only partly masked | 15 MB | team drive only, gitignored: TEAM-DRIVE-LINK |
| `data-eda/data/raw/` | the downloads, untouched; only needed to rebuild `clean/` | 655 MB | team drive or Kaggle: TEAM-DRIVE-LINK |

Start with `data-eda/data/clean/README.txt`; `data-eda/HOW_TO_USE_DATA.txt` says which file
answers which question. Three clean files are over the 5 MB limit in CONTRIBUTING.md
(Seek 9.7 MB, ESCO skills 6.7 MB, ESCO lookup 14.3 MB); keeping them in the repo means
everyone labels and evaluates on byte-identical files.

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
