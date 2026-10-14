# Appendix

> Draft by Akash (#79), revised 15 Oct after #81 merged. Appendix A is printed by
> `python data-eda/src/appendix_subjects.py` from `data/processed/subject_profiles.csv`; row counts in Appendix B are
> from the files on `main` on 15 Oct.

## Appendix A. UTS subjects in the subject profiles

Rows per layer in `data/processed/subject_profiles.csv`: 6,853 rows for 360 subjects in 44 courses, one row per
learning objective, assessment task, weekly topic or description sentence (UTS Handbook 2026, scraped 13 Oct 2026;
`data/processed/subject_profiles.md`). A dash means the Handbook has no text for that layer.

**A.1 Courses.** A subject in several courses is counted in each, so columns do not add up to the total.

| Course | Level | Name | Subjects | Obj. | Assess. | Topics | Desc. |
|---|---|---|---|---|---|---|---|
| C04256 | Master | AI (Online) | 11 | 50 | 12 | 89 | 43 |
| C04265 | Master | Science (Extension) | 18 | 74 | 45 | 145 | 69 |
| C04277 | Master | Engineering (Extension) | 11 | 42 | 33 | 84 | 43 |
| C04295 | Master | Information Technology | 10 | 44 | 33 | 79 | 39 |
| C04296 | Master | Information Technology | 5 | 22 | 13 | 28 | 17 |
| C04370 | Master | Executive MDSI | 3 | 15 | 9 | 17 | 15 |
| C04372 | Master | MDSI | 19 | 76 | 46 | 75 | 91 |
| C04373 | Master | Quantitative Finance | 9 | 36 | 25 | 71 | 36 |
| C04379 | Master | Business Analytics | 31 | 137 | 99 | 200 | 150 |
| C04380 | Master | Business Analytics | 11 | 44 | 35 | 80 | 45 |
| C04430 | Master | Cybersecurity | 15 | 58 | 52 | 151 | 64 |
| C04431 | Master | Cybersecurity | 15 | 58 | 52 | 151 | 64 |
| C04434 | Master | Technology Management | 18 | 72 | 53 | 150 | 57 |
| C04435 | Master | Technology Management | 12 | 49 | 35 | 112 | 40 |
| C04443 | Master | Artificial Intelligence | 20 | 82 | 56 | 148 | 78 |
| C04450 | Master | Technology Innovation | 11 | 44 | 26 | 83 | 38 |
| C04467 | Master | Business Analytics | 11 | 45 | 29 | 72 | 45 |
| C06113 | Grad. diploma | IT | 62 | 266 | 188 | 499 | 241 |
| C06124 | Grad. diploma | Data Science and Innovation | 16 | 76 | 46 | 75 | 72 |
| C06147 | Grad. diploma | AI | 17 | 68 | 49 | 131 | 67 |
| C09019 | Honours | IT | 3 | 13 | 8 | 26 | 14 |
| C09066 | Honours | Engineering | 27 | 115 | 71 | 160 | 131 |
| C09119 | Honours | Computing Science | 19 | 84 | 69 | 194 | 85 |
| C09129 | Honours | Mathematical Sciences | 10 | 39 | 24 | 51 | 33 |
| C10143 | Bachelor | Information Technology | 78 | 324 | 244 | 665 | 344 |
| C10148 | Bachelor | Information Technology | 9 | 37 | 38 | 117 | 46 |
| C10229 | Bachelor | Games Development | 20 | 83 | 73 | 195 | 90 |
| C10395 | Bachelor | Information Systems | 29 | 125 | 108 | 288 | 137 |
| C10457 | Bachelor | Mathematical Sciences | 14 | 61 | 43 | 143 | 44 |
| C10471 | Bachelor | Cybersecurity | 29 | 117 | 97 | 311 | 132 |
| C10474 | Bachelor | AI | 27 | 113 | 93 | 270 | 117 |
| C10476 | Bachelor | Computing Science | 17 | 75 | 62 | 170 | 77 |
| C11142 | Grad. certificate | IT | 56 | 242 | 173 | 442 | 219 |
| C11191 | Grad. certificate | AI | 4 | 19 | 5 | 44 | 15 |
| C11247 | Grad. certificate | IT | 4 | 18 | 16 | 45 | 19 |
| C11274 | Grad. certificate | Data Science and Innovation | 16 | 76 | 46 | 75 | 72 |
| C11280 | Grad. certificate | Business Analytics | 4 | 15 | 14 | 28 | 16 |
| C11308 | Grad. certificate | Quantitative Finance | 9 | 36 | 25 | 71 | 36 |
| C11329 | Grad. certificate | Health Analytics | 21 | 93 | 55 | 179 | 123 |
| C11339 | Grad. certificate | AI Management | 4 | 16 | 10 | 29 | 13 |
| C11340 | Grad. certificate | Cybersecurity Management | 4 | 16 | 7 | 53 | 15 |
| C11350 | Grad. certificate | Data Visualisation and Storytelling | 4 | 17 | 13 | 42 | 14 |
| C11376 | Grad. certificate | Applied AI for Finance | 4 | 19 | 12 | 28 | 24 |
| C11385 | Grad. certificate | Business Analytics | 4 | 18 | 11 | 31 | 19 |
| **All** | | 44 courses | **360** | 1,516 | 1,015 | 2,769 | 1,553 |

**A.2 MDSI subjects (C04372).**

| Code | Subject | Obj. | Assess. | Topics | Desc. |
|---|---|---|---|---|---|
| 36100 | Data Science for Innovation | 5 | 3 | 5 | 5 |
| 36101 | Leading Data Science Initiatives | 5 | 3 | 12 | 5 |
| 36103 | Statistical Thinking for Data Science | 5 | 3 | 12 | 5 |
| 36104 | Data Visualisation and Narratives | 4 | 3 | 1 | 4 |
| 36106 | Machine Learning Algorithms and Applications | 5 | 3 | – | 5 |
| 36118 | Applied Natural Language Processing | 5 | 3 | 9 | 3 |
| 36120 | Advanced Machine Learning Application | 5 | 3 | 5 | 4 |
| 36121 | Artificial Intelligence Principles and Applications | 5 | 3 | 5 | 8 |
| 36122 | Python Programming | 8 | 3 | 9 | 7 |
| 36123 | Research Paper 1 | 3 | 1 | 2 | 3 |
| 36124 | Applied Data Science for Innovation | – | – | – | 5 |
| 36125 | Advanced Data Science for Innovation | – | – | – | 4 |
| 36126 | Innovation Lab: Research Project | 3 | 2 | – | 3 |
| 36127 | Innovation Lab: Capstone Project | 4 | 4 | – | 6 |
| 94689 | Special Subject 1 (FTDI) | – | – | – | 10 |
| 94691 | Deep Learning | 5 | 3 | – | 3 |
| 94692 | Data Science Practice | 5 | 3 | – | 1 |
| 94693 | Big Data Engineering | 4 | 3 | 15 | 3 |
| 94699 | Innovation Lab: Internship Project | 5 | 3 | – | 7 |
| **Total** | 19 subjects | 76 | 46 | 75 | 91 |

## Appendix B. Data dictionary

All files are UTF-8 CSV. Raw sources (`data/raw/`, `data-eda/data/raw/`) are not committed: the Seek ads, the
resume dataset and the ESCO download are shared on the team drive. Files starting with a `#` provenance line must be
read with `skiprows=1`, not `comment="#"`, which truncates the `C#` row.

### B.1 Processed data (`data/processed/`)

| File | Rows | One row = | Columns | Built by | Read by |
|---|---|---|---|---|---|
| `subject_profiles.csv` | 6,853 | one piece of subject text | `subject_code`, `subject_name`, `course` (pipe-separated course codes), `layer` (learning_objective / assessment / weekly_topic / description), `text`, `source_url`, `collected_by` | `data-eda/src/build_subject_profiles.py` after `scrape_handbook.py` and `scrape_assessments.py` | `recommend.py`, `rag.py`, `app/baseline.py` |
| `assessments_scraped.csv` | 1,015 | one assessment task | same columns as `subject_profiles.csv` | `data-eda/src/scrape_assessments.py` | `build_subject_profiles.py` |
| `prerequisites.csv` | 2,571 | one item of a subject's requisite rule | `subject_code`, `kind`, `rule`, `item`, `type`, `requisite_code`, `requisite_text`, `evop_found`, `source_url` | `data-eda/src/scrape_requisites.py` (#81, #98) | `recommend()` (in review, #82) |
| `offerings.csv` | 510 | one subject in one teaching period | `subject_code`, `teaching_period`, `mode` | `data-eda/src/scrape_handbook.py` | `recommend()` (in review, #82) |
| `external_courses.csv` | 1,167 | one piece of text from a course outside UTS | profile columns plus `provider`, `cost` (free / free-to-audit), `date_checked`; 56 courses from 42 providers | `data-eda/src/external/build_external.py` (#81); links checked in #96 | two-tier `recommend()` (in review, #83) |
| `uncovered_skills_2026-10-13.csv` | 73 | one skill no UTS subject names, or a covered skill in at least 10% of 2026 ads | `skill`, `category`, `pct_2019_22`, `pct_2026`, `covered_by_uts` (54 n, 19 y) | `build_external.py` | external-course search |
| `skills_seed_v2.csv` | 148 | one dictionary skill | `canonical`, `category`, `strict` (1 = case-sensitive), `aliases` (pipe-separated). `#` line first | Van Thong's dictionary, 5 generic rows (poster) and 10 tool rows (#86) | `extract.py`, `normalise.py`, `evaluate.py`, `rag.py`, `app/baseline.py` |
| `skill_to_esco.csv` | 132 | one dictionary skill linked to ESCO | `canonical`, `category`, `esco_uri`, `esco_preferred_label`, `esco_skill_type`, `matched_on` | `data-eda/src/map_to_esco.py`; Spark row dropped by `app/mock/build_mock.py` | `normalise.py`, `app/baseline.py` |
| `skill_counts_v2.csv` | 148 | one skill's demand in 2019-22 | `skill`, `category`, `n_ads`, `pct_ads` (share of 3,204 Seek Data Scientist ads) | poster stage (`docs/handoffs/`) | `match.py`, `app/baseline.py` |
| `skill_counts_2026.csv` | 148 | one skill's demand in three periods | `skill`, `category`, `pct_2019_22`, `pct_2024_01`; `n_2026`, `pct_2026` and 95% bounds for the 9 data-scientist ads; `n_2026_all`, `pct_2026_all` and bounds for all 22 ads; `total_*` denominators | `data-eda/src/recount_recent.py` (#87, #99) | `match.py` (only skills under 1% before 2023) |
| `role_profiles.csv` | 441 | one skill in one of 7 data and IT roles | `role`, `skill`, `category`, `n_ads`, `pct_ads`, `pct_low`, `pct_high`, `total_ads`, `source` | `data-eda/src/build_role_profiles.py` (#86) | role mode (in review, #83) |
| `emerging_candidates.csv` | 52 | one candidate phrase from one detection method | `sample`, `method` (n-gram / spaCy / GPT), `rank`, `phrase`, `df_new`, `pct_new`, `df_2019_22`, `pct_2019_22`, `employers_new`, `z` (weighted log-odds), `is_skill` (hand judgement) | `src/skillabus/emerging.py` (#84) | section 6 |
| `emerging_candidates_2024-2026.csv` | 76 | as above, on the 2024-2026 sample | as above | `emerging.py` with the wider sample | section 6 |
| `top_skills.csv` | 15 | one of the 15 most-demanded technical skills | `skill`, `pct_ads`. `#` line first | poster stage | `match.py` (role mode), `app/baseline.py` |
| `gap.csv` | 8 | one skill in the poster example | `skill`, `pct_ads`, `covered` (1 = in the resume). `#` line first | poster stage | app demo, `tests/test_match.py` |
| `feedback.csv` | grows | one thumbs up/down vote | `timestamp`, `subject_code`, `skill_label`, `vote`, `has_taken_subject` (y/n). Nothing from the CV; lost when Streamlit Cloud restarts | `app/Home.py` | validation |

Notes files: `subject_profiles.md`, `external_courses.md` and `role_profiles.md` describe how each file was built.

### B.2 Hand-labelled test sets (`data/labels/`)

Each set starts from a `_TEMPLATE.csv` with the same columns; rules in `data/labels/README.md`.

| File | Rows | One row = | Columns |
|---|---|---|---|
| `ad_skills.csv` | 534 | one skill asked for in one of 20 ads, by one annotator (217 Hoai Thuong, 317 Van Thong; #55, #85) | `ad_id`, `skill_label` (dictionary `canonical` when it exists), `in_dictionary`, `evidence_text`, `annotator` |
| `cv_jd_pairs.csv` | 287 | one skill in one of 45 CV-ad pairs (16 ads, 10 resumes; #42) | `pair_id`, `ad_id`, `resume_id`, `skill_label`, `in_dictionary`, `gold_status` (have / partial / missing), `resume_evidence_text`, `annotator` |
| `skill_subject_pairs.csv` | 33 | one skill-subject claim (#92) | `skill_label`, `subject_code`, `teaches` (y / partly / n), `layer`, `evidence_text`, `source_url`, `annotator` |
| `chat_questions.csv` | 15 | one chat test question (#92) | `question_id`, `question`, `reference_answer` (1-3 sentences), `source`, `annotator` |

### B.3 Pipeline output (`docs/data_contract.md`)

The pipeline returns one JSON object per analysis (gaps with have / partial / missing status, evidence
sentences, recommended subjects and the learning path). Its fields are defined in `docs/data_contract.md`
sections 1-2 and are not repeated here.

## Appendix C. Glossary

| Term | Meaning in this report |
|---|---|
| Ad (job ad) | A job advertisement; the "JD" in CV-JD pair. |
| Alias | Another way of writing a dictionary skill (e.g. `sklearn` for scikit-learn). |
| Canonical skill | The one name a dictionary skill is stored under. |
| Cohen's kappa (κ) | Agreement between two annotators corrected for chance; 1 = perfect, 0 = chance level. |
| Demand weight | A skill's share of job ads; used to rank gaps and choose the learning path. |
| Embedding | A vector representing the meaning of a sentence (here, all-MiniLM-L6-v2), compared by cosine similarity. |
| Emerging skill | A skill found in ads with no ESCO concept, such as many GenAI terms; kept and flagged. (A Lightcast lookup is designed for these but needs API keys.) |
| ESCO | European Skills, Competences, Qualifications and Occupations: the EU's open skills taxonomy. |
| Evidence | The ad sentence that asks for a skill and the subject sentence that teaches it, shown side by side. |
| External course | A free or free-to-audit course outside UTS, suggested for skills no UTS subject teaches. |
| FAISS | A library for fast nearest-neighbour search over embeddings, used to retrieve text for the chat. |
| Gap | A skill the ad asks for that the CV does not show: missing, or partial when only a related skill is present. |
| GPT-4o-mini | The OpenAI language model used for tier-3 extraction and the chat. |
| Hit@5, MRR | Ranking metrics: whether the right item is in the top 5, and the average of 1 / its rank. |
| Layer | The kind of subject text a match comes from: learning objective, assessment, weekly topic or description. |
| Learning path | The 2-3 subjects that together close the most demand-weighted gaps, chosen greedily. |
| Lightcast | A commercial labour-market data company whose open skills taxonomy covers many skills ESCO lacks. |
| MDSI | Master of Data Science and Innovation at UTS (C04372). |
| NER | Named entity recognition: finding names of things (here, skills) in text. |
| P@3, F1 | Precision of the top 3 recommendations; the balance of precision and recall for extraction. |
| Prerequisite / anti-requisite | A subject that must be passed before another (prerequisite), or one that cannot be counted together with it (anti-requisite). |
| PII | Personally identifiable information, such as names, emails and phone numbers. |
| RAG | Retrieval-augmented generation: the model answers from retrieved text, not from memory. |
| Role profile | The skills most often asked for in one job role (e.g. Data Engineer), with their share of ads; used when a student picks a role instead of an ad. |
| spaCy | An open-source NLP library, used for tier-2 extraction. |
| Subject profile | All the Handbook text about one subject, one row per piece, labelled by layer. |
| TF-IDF | A keyword-weighting method; the baseline for matching and ranking. |
| Tier 1 / 2 / 3 | The three extraction steps: dictionary, spaCy, GPT-4o-mini. |
