# Datasets

Every row count below was read off the file on disk, not from a dataset description
page. Verified 23 September 2026.

## Job advertisements — Australian

| File | Rows | Text | Period | Notes |
|---|---|---|---|---|
| `jobs_au_seek_datascientist_2019-2022.csv` | **3,204** | full, ~2.8k chars | 2019–2022 | **PRIMARY — the block 5 chart.** Data Scientist titles only |
| `jobs_au_seek_datascience_2019-2022.csv` | 3,895 | full | 2019–2022 | all data-ish roles; superset of the above |
| `jobs_au_seek_datascience_2019-2022_authorflags.csv` | 3,902 | full | 2019–2022 | superset carrying the author's own 25 tool flags. **Our external validation set** — joins to the primary on `ad_id == jobId`, all 3,204. See `outputs/extractor_agreement.csv` |
| `jobs_au_ats_2026.csv` | 234 | full, ~6.2k | Sept 2026 | current; Greenhouse/Lever/SmartRecruiters. ~27 data roles |
| `jobs_au_adzuna_2026.csv` | 50 | **capped at 500 chars** | Sept 2026 | employers, volume, geography only |

## Job advertisements — international

| File | Rows | Text | Period | Notes |
|---|---|---|---|---|
| `jobs_us_linkedin_2023-2024.csv` | 123,849 | full, ~3.4k | 2023–24 | 1,355 data roles. **99.9% US** — only 131 AU rows |
| `linkedin_mappings/skills.csv` | 35 | — | — | **NOT skills** — 35 broad job functions (IT, SALE, MNFC) |

## Skills taxonomies

| Folder | Contents | Notes |
|---|---|---|
| `taxonomy_esco_v1.2.1/` | 13,960 skills, 3,043 occupations | altLabels 99.9% populated, newline-separated. 36% of our seed maps; 73 modern tools absent |
| `taxonomy_onet_v31/` | 8,753 tool names, 176 "Hot Technology" | covers the tooling ESCO lacks. CC-BY 4.0 |

## Course and profile data

| File | Rows | Notes |
|---|---|---|
| `uts_subjects_2026.csv` | **70** | 6 UTS courses, 13 faculties, 67 with learning outcomes. 19 MDSI + **51 non-MDSI** |
| `resumes_us_2021.csv` | 2,484 | 24 categories; one is enough for C's sample profile |

Courses scraped (`curriculum_group` and `courses` columns record where each sits):

| Code | Course | cp | Subjects |
|---|---|---|---|
| C04372 | Master of Data Science and Innovation | 96 | 19 |
| C04379 | Master of Business Analytics (Extension) | 96 | 33 |
| C04380 | Master of Business Analytics | 72 | 11 |
| C04295 | Master of Information Technology | 96 | 10 |
| C04373 | Master of Quantitative Finance | 72 | 9 |
| C04443 | Master of Artificial Intelligence | 96 | 20 (all new) |

The 51 non-MDSI subjects are what make block 7 work. MDSI reserves **24cp of Free
Electives** — a container the handbook deliberately leaves empty because any UTS
subject qualifies. With MDSI alone the app had nothing to recommend into it; it can
now suggest Business Intelligence (32558), Advanced Data Analytics Algorithms
(32513), Data Visualisation and Visual Analytics (32146), Customer Analytics (24753)
and Data Governance and Regulation (22805), among others.

**Worked example of the product's core claim.** AWS appears in 22% of Australian
Data Scientist ads (Seek, n=3,204). No MDSI subject mentions AWS or cloud at all.
Master of AI has two — Architecting on Amazon Web Services (42049) and Cloud
Computing and SaaS (42904) — both open to an MDSI student as Free Electives, neither
visible from their own course page. Market skill → measured curriculum gap →
specific subject that fills it. (Keyword match over subject text; spot-check before
publishing.) Ethics runs the other way: 22 subjects mention it, 10 inside MDSI.

Subjects 22708 and 22759 exist in the 2025 handbook but not 2026 — discontinued, so
they are excluded. A study planner must not recommend retired subjects.

**Total: 720 MB**

## Authenticity

All Australian job data was checked for synthetic content before use:

- **Seek** — 3,902 unique `seek.com.au` job IDs, 342 real companies (Worley, Downer,
  7-Eleven, Randstad), Australian salary strings (`$90k - $110k p.a.`, `Super`),
  description lengths from 6 to 17,081 chars with std 2,461. Real.
- Several Kaggle "2026" job datasets were **rejected as synthetic** — one is named
  `...-synthetic` outright; `ai-jobs-market-2025-2026-salaries` and
  `pakistan-ai-and-tech-jobs-2026` show the same generated uniformity.

## Two traps, both confirmed by measurement

1. **`linkedin_mappings/skills.csv` is not a skills taxonomy.** 679 bytes, 35 job
   functions. Extract from the `description` free text instead.
2. **80.4% of the Seek ads have glued text.** The source dataset stripped HTML
   without putting whitespace back, so real mentions are welded to the next word
   ("...Power BI and TableauSuperior analytical skills..."). Our word boundaries
   correctly refuse these, which means **every percentage in this folder is a
   slight under-count**: 365 mentions across 11 tools, about +3pp on Python and
   SQL. Measured in `outputs/extractor_agreement_decomposed.csv`.

## Known limitation to state on the poster

The primary Australian corpus is **2019–2022**, which predates the LLM stack — no
RAG, prompt engineering, LangChain or vector databases will appear. That absence is
a property of the sampling window, not of the Australian market. Say so plainly.

## Cleaned versions — `data/clean/` (9 Oct 2026)

Raw files are never edited; the cleaned copies are rebuilt by scripts. Full notes in
`data/clean/README.txt`.

| File | Rows | Script | What changed |
|---|---|---|---|
| `jobs_au_seek_datascientist_2019-2022_clean.csv` | 3,204 | `clean_seek.py` | 13,181 glued words split where the desktop rendering shows a break; Python 82.8% → 84.5%, ranking unchanged (ρ = 0.9996) |
| `jobs_au_recent_2024-2026_clean.csv` | 179 | `build_recent_sample.py` | Australian data roles: 2026 job boards (22 full text) + Adzuna (33, text capped at 500) + LinkedIn Jan 2024 (124, Kaggle asaniczka, ODC-By). Periods kept separate |
| `seek_label_sample_200.csv` | 200 | `make_label_sample.py` | seeded sample for labelling; 4 batches of 50, 20 marked for double labelling |
| `resumes_us_2021_clean.csv` | 2,481 | `clean_resumes.py` | emails, phones, URLs and names masked (names: spaCy NER with filters that protect skills, plus a title / credential rule for referees: 1,146 names in 551 resumes); HTML copy dropped; `n_data_skills` added. **De-identified, not anonymous** |
| `esco_skills_clean.csv` | 13,960 | `clean_esco.py` | alt labels pipe-separated instead of newline-in-cell |
| `esco_label_lookup.csv` | 100,886 | `clean_esco.py` | one row per (label, concept); 716 labels ambiguous, including `sql` |

