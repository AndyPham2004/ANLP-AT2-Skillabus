# Data

Only `data/` holds data (layout of 15 Oct 2026). Code, scripts, tests and notebooks take every path from
`src/skillabus/paths.py`. The scripts that build these files are in `data-eda/src/` (owner: Van Thong)
and `src/skillabus/`; commands below run from the repo root. Each folder's README has the details.

| Folder | What it is for | In git |
|---|---|---|
| [`1_knowledge/`](1_knowledge/README.md) | What the app looks up: skill dictionary, ESCO, UTS subjects, outside courses | yes |
| [`2_demand/`](2_demand/README.md) | What employers ask for: skill counts, role profiles, cleaned ads, collection lists | yes |
| [`3_tuning/`](3_tuning/README.md) | Every threshold, where it is and what it was set on | yes |
| [`4_evaluation/`](4_evaluation/README.md) | Test labels, the inputs they were made on, results, the committed GPT answers | yes |
| [`5_crosscheck/`](5_crosscheck/README.md) | Other platforms and markets, the extractor against the author's flags, ESCO coverage | yes |
| `raw/` | Every download, untouched, 655 MB; only needed to rebuild the files above | no: re-download (links below) or ask Van Thong for the zip |
| `runtime/` | Written while the app runs: `feedback.csv` (votes), `cache/llm_extract/`, `cache/lightcast/`, `cache/esco/`, `cache/rag/` | no |

The poster's numbers are frozen in `archive/poster_AT2A/data/` (see `archive/README.md`).

## Every file

| File | What | Made by | Rebuild |
|---|---|---|---|
| `1_knowledge/skills/skills_seed_v2.csv` | The one dictionary, 148 skills (starts with a `#` line: `skiprows=1`, not `comment="#"`, or `C#` becomes `C`) | Van Thong, Quan | By hand, through a PR |
| `1_knowledge/skills/skills_vocabulary.csv`, `esco_link_review.csv` | One vocabulary, ESCO plus what ESCO lacks (D5; part 1 = the 148 dictionary skills); the hand-checked ESCO link of each | Claude, Van Thong to check | `python data-eda/src/build_vocabulary.py` after editing the review file |
| `1_knowledge/skills/skill_to_esco.csv` | Dictionary skill -> ESCO concept, 132 rows | Van Thong, Quan | `data-eda/src/map_to_esco.py`, minus the Spark row |
| `1_knowledge/skills/original/skills_seed.csv`, `skill_to_esco.csv` | Van Thong's 133-row original and its ESCO links | Van Thong | `data-eda/src/map_to_esco.py` |
| `1_knowledge/taxonomies/esco_skills_clean.csv`, `esco_label_lookup.csv` | ESCO v1.2.1: 13,960 concepts; 100,886 (label, concept) rows | Van Thong | `python data-eda/src/clean_esco.py` |
| `1_knowledge/taxonomies/role_occupations.csv` | The 11 IT roles -> ESCO, O*NET and ASC occupations, 34 rows, each with match (exact/close/broad) and reason | Quan's session (D4) | `python data-eda/src/build_occupation_skills.py` |
| `1_knowledge/taxonomies/occupation_skills.csv` | What those occupations require, 1,148 rows: ESCO essential/optional skills, O*NET in-demand tools, ASC core competencies and tool categories | Quan's session (D4) | `python data-eda/src/build_occupation_skills.py` |
| `1_knowledge/uts/subject_profiles.csv` (+ `.md`) | 360 subjects, 6,853 rows in four layers | Van Thong, Quan | `python data-eda/src/build_subject_profiles.py` |
| `1_knowledge/uts/prerequisites.csv`, `offerings.csv` | Access-condition rules; teaching periods | Quan | `python data-eda/src/scrape_requisites.py` |
| `1_knowledge/uts/assessments_scraped.csv` | Assessment tasks before the merge | Quan, Van Thong | `python data-eda/src/scrape_assessments.py` |
| `1_knowledge/uts/subjects_template.csv`, `subject_content_TEMPLATE.csv` | Templates for adding a subject or subject rows by hand | Van Thong, Quan | Templates |
| `1_knowledge/learning_resources/external_courses.csv` (+ `.md`) | 56 free outside courses, 1,167 rows | Quan, Van Thong | `python data-eda/src/external/build_external.py` |
| `1_knowledge/learning_resources/certifications.csv` (+ `.md`) | 49 industry certifications for the 11 IT roles: price, official page, "hot" signal (D11) | Quan, Van Thong (Adzuna counts) | By hand; `count_cert_mentions.py`, `count_cert_adzuna.py` |
| `2_demand/skill_counts_v2.csv` | Every dictionary skill over 3,204 Seek ads 2019-22 (the app's `demand_pct`) | Quan, Van Thong | `data-eda/src/extract_skills.py` with this dictionary |
| `2_demand/skill_counts_2026.csv` | The same in 2019-22, Jan 2024 and 2026, with 95% intervals | Van Thong | `python data-eda/src/recount_recent.py` |
| `2_demand/top_skills.csv` | The 15 most-asked technical skills (the Data Scientist role) | Quan | From `skill_counts_v2.csv` |
| `2_demand/role_profiles.csv` (+ `.md`) | Tool profiles of 7 data and IT roles, 2023 | Van Thong | `python data-eda/src/build_role_profiles.py` |
| `2_demand/skills_not_taught_by_uts.csv` | 73 skills no UTS subject names, or names but 2026 ads ask for a lot | Quan | Recompute after D5 and D8 |
| `2_demand/ads/` | 3,204 Seek ads (2019-22) and 192 recent Australian data roles, cleaned; `CLEANING_NOTES.txt` | Van Thong | `clean_seek.py`, `build_recent_sample.py` |
| `2_demand/collection/` | The 65 job boards fetched, 206 candidate employers, the probe of 13 Oct | Van Thong, Quan | `probe_ats.py`; lists by hand |
| `2_demand/emerging/` | Emerging-skill candidates, 2026 and 2024+2026 | Phuong Nhi | `python -m skillabus.emerging [--with-2024]` |
| `4_evaluation/labels/` | Test sets: ad skills, CV-JD pairs, skill-subject pairs, chat questions; templates | Hoai Thuong, Van Thong, Akash | By hand |
| `4_evaluation/inputs/` | The 200-ad label sample; 2,481 de-identified resumes | Van Thong | `make_label_sample.py`, `clean_resumes.py` |
| `4_evaluation/llm_cache/` | 30 GPT-4o-mini answers for the evaluation texts (read only) | Quan | Rerun with a key |
| `4_evaluation/results/` | Scores for report section 6 | Hoai Thuong | The evaluation run (#56) |
| `5_crosscheck/*.csv` | LinkedIn US, Glassdoor AU, AU vs US, extractor agreement, source counts | Van Thong | `count_glassdoor_au.py`, `validate_against_authorflags.py`; others from the September EDA |
| `5_crosscheck/esco_coverage/` | Dictionary skills ESCO lacks (73) or has only as verb phrases (12) | Van Thong | September EDA |

Four committed files are over the 5 MB limit in CONTRIBUTING.md (Seek 9.7 MB, resumes 14.8 MB, ESCO
skills 6.7 MB, ESCO lookup 14.3 MB); keeping them in the repo means everyone labels and evaluates on
byte-identical files (`.gitattributes` keeps their line ends). The EDA notebook is
`notebooks/vt_eda.ipynb` (committed files only, about 3 minutes; figures in `docs/figures/`);
`data-eda/HOW_TO_USE_DATA.txt` says which file answers which question.

## Sources

| Source | What we use | Period | Role | Link |
|---|---|---|---|---|
| Seek Australia, Data Scientist ads (Kaggle, nomilk) | **3,204** full-text ads | 2019–22 | the demand side: every demand % | [kaggle](https://www.kaggle.com/datasets/nomilk/data-science-job-listings-australia-20192020) |
| LinkedIn Job Postings (Kaggle, arshkon) | 123,849 ads, 99.9% US; 1,355 data roles | 2023–24 | validation only: ranking agrees with Seek at ρ = 0.819 | [kaggle](https://www.kaggle.com/datasets/arshkon/linkedin-job-postings) |
| Glassdoor Australia (Kaggle, nadzmiagthomas) | 193 data roles, full text | Aug–Dec 2022 | platform check only: rank correlation 0.75 with Seek (technical skills) | [kaggle](https://www.kaggle.com/datasets/nadzmiagthomas/australia-data-science-jobs) |
| ESCO v1.2.1 | 13,960 skill concepts, 100,135 distinct labels (100,886 label–concept rows); the essential and optional skills of 11 occupations | 2025 | the vocabulary `normalise()` maps to; core skills per role | [esco](https://esco.ec.europa.eu/en/use-esco/download) |
| O*NET 31.0 | 8,753 tool names; the "In Demand" tools of 10 occupations | 2026 | tools ESCO lacks; in-demand tools per role | [onet](https://www.onetcenter.org/database.html) |
| Australian Skills Classification v1.0 (National Skills Commission, now Jobs and Skills Australia), CC BY 4.0 | Core competencies (level 1-10) and technology tool categories of 9 ANZSCO 2013 codes | Mar 2021 | the Australian taxonomy beside ESCO and O*NET, per role | [jsa](https://www.jobsandskills.gov.au/australian-skills-classification) (no longer downloadable, see below) |
| UTS Handbook 2026 | 360 subjects in 44 courses (19 MDSI) | 2026 | subject profiles, prerequisites, teaching sessions | [handbook](https://coursehandbook.uts.edu.au) |
| Resume Dataset (Kaggle, snehaanbhawal) | 2,481 resumes; 125 with 2+ data skills | 2021 | resume parsing and CV–JD test pairs | [kaggle](https://www.kaggle.com/datasets/snehaanbhawal/resume-dataset) |
| Job-board APIs of 65 employers (Greenhouse, Lever, SmartRecruiters, Ashby, Workable) + Adzuna API | 38 Australian data roles with full text (22 in the sample, 9 of them data scientists) + 32 Adzuna roles cut at 500 characters | Sep–Oct 2026 | the 2026 sample | public APIs |
| LinkedIn data-science postings (Kaggle, asaniczka) | 122 Australian data roles, full text | Jan 2024 | Australian middle point for the 2019–22 → 2026 trend | [kaggle](https://www.kaggle.com/datasets/asaniczka/data-science-job-postings-and-skills) |
| data_jobs (Hugging Face, lukebarousse), Apache-2.0 | 12,955 Australian postings, tool lists only | 2023 | role profiles for 7 data and IT roles | [huggingface](https://huggingface.co/datasets/lukebarousse/data_jobs) |

Notes for anyone citing these:

- **The Seek data is not PromptCloud's.** The poster's reference list says PromptCloud; the
  file we use is `listings2019_2022.csv` from the nomilk dataset above. Cite that one.
- We scraped neither Seek nor LinkedIn; both are published Kaggle datasets. The handbook's
  `robots.txt` disallows crawling; its 360 subject pages, their assessment tasks and their
  access conditions were read one request at a time, at least 1.2 s apart.
- **Label and evaluate on the cleaned files** (`2_demand/ads/`, `4_evaluation/inputs/`), not `raw/`.
  The raw Seek text has words welded together where HTML was stripped (`TableauSuperior`); the clean
  file repairs that, so the labeller and the extractor see the same words.
- **The 2026 sample is small: 22 roles, not the ~150 planned** (posted within 60 days of a
  snapshot, at most 3 per employer and role group; 9 are data scientists). Indeed was dropped because its
  terms forbid scraping and it has no public search API. Adzuna's API cuts every description
  at 500 characters, so its 32 roles count as roles but not for skill shares.
  The January 2024 LinkedIn rows are kept as their own period, not merged into 2026. All of
  it is in `2_demand/ads/jobs_au_recent_2024-2026_clean.csv`
  (`python data-eda/src/build_recent_sample.py`).
- **ASC licence and attribution.** Our copy (`raw/taxonomy_asc_australia/`, Version 1.0, current at
  March 2021) says in its Index sheet that the content is licensed under CC BY 4.0, except the Coat of
  Arms, logos, images and trade marks; it includes O*NET 21.2 / 23.1 and ABS material, also CC BY 4.0.
  Cite it as: "This app includes content derived from the Australian Skills Classification by the
  National Skills Commission, Commonwealth of Australia. Used under CC BY 4.0 licence. Skillabus has
  modified some of this content, and the National Skills Commission has not approved, endorsed or tested
  the modified content." Jobs and Skills Australia decommissioned the ASC in December 2023 and took it
  off its website in January 2025; it is now released only for research under a data access agreement.
  A CC BY 4.0 grant cannot be withdrawn for copies already obtained under it, so the 2021 copy stays
  usable with that attribution, but it cannot be re-downloaded and it is five years old.
- Resumes are de-identified, not anonymous: emails, phones, URLs and 1,146 person names are
  masked, but a name in capitals or a lone first name can survive. Mask again with spaCy
  before sending any resume text to an LLM.

Rebuild the cleaned files (needs `data/raw/`):

```powershell
python data-eda/src/clean_seek.py; python data-eda/src/clean_resumes.py; python data-eda/src/clean_esco.py; python data-eda/src/make_label_sample.py
```
