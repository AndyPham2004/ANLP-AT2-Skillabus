# Appendix

> Draft by Akash (#79), revised 17 Oct for the data layout of 15 Oct (`src/skillabus/paths.py`). Appendix A is printed by
> `python data-eda/src/appendix_subjects.py`; row counts in Appendix B are from the files on `main` on 17 Oct. The full
> file list, with builders and rebuild commands, is `data/README.md`.

## Appendix A. UTS subjects in the subject profiles

Rows per layer in `data/1_knowledge/uts/subject_profiles.csv`: 6,853 rows for 360 subjects in 44 courses, one row per
learning objective, assessment task, weekly topic or description sentence (UTS Handbook 2026, scraped 13 Oct 2026;
`data/1_knowledge/uts/subject_profiles.md`). A dash means the Handbook has no text for that layer.

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

All files are UTF-8 CSV in five folders under `data/`; code takes every path from `src/skillabus/paths.py`. Raw
downloads (`data/raw/`, 655 MB) and files written while the app runs (`data/runtime/`: feedback votes, caches) are not
committed. Files starting with a `#` provenance line must be read with `skiprows=1`, not `comment="#"`, which
truncates the `C#` row.

### B.1 `data/1_knowledge/`: what the app looks up

| File | Rows | One row = | Key columns |
|---|---|---|---|
| `skills/skills_vocabulary.csv` | 504 | one skill in the one vocabulary: 148 dictionary skills, added IT skills, ESCO core skills, certifications | `skill_id`, `label`, `category`, `source`, `esco_uri`, `esco_match`, `aliases_ads`, `strict`, `used_for` |
| `skills/skills_seed_v2.csv` | 148 | one dictionary skill (`#` line first) | `canonical`, `category`, `strict`, `aliases` |
| `skills/skill_to_esco.csv` | 132 | one dictionary skill linked to ESCO | `canonical`, `esco_uri`, `esco_preferred_label`, `matched_on` |
| `skills/esco_link_review.csv`, `added_skills.csv`, `onet_tool_map.csv` | 148, 125, 79 | the hand files behind the vocabulary | ESCO link and note; candidate IT skills; O*NET tool → label |
| `taxonomies/role_occupations.csv` | 34 | one of the 11 IT roles mapped to an ESCO, O*NET or ASC occupation | `role`, `role_family`, `source`, `occupation_code`, `match` (exact / close / broad), `why` |
| `taxonomies/occupation_skills.csv` | 1,148 | one skill or tool an occupation requires | ESCO essential/optional, O*NET in-demand tools, ASC core competencies |
| `taxonomies/esco_skills_clean.csv`, `esco_label_lookup.csv` | 13,960; 100,886 | one ESCO v1.2.1 concept; one (label, concept) pair | `concept_uri`, `preferred_label`, `alt_labels`, `skill_type` |
| `uts/subject_profiles.csv` | 6,853 | one piece of subject text | `subject_code`, `subject_name`, `course` (pipe-separated), `layer`, `text`, `source_url`, `collected_by` |
| `uts/assessments_scraped.csv` | 1,015 | one assessment task (before the merge into profiles) | profile columns |
| `uts/prerequisites.csv` | 2,571 | one item of a subject's access rule | `subject_code`, `kind`, `rule`, `item`, `type`, `requisite_code` |
| `uts/offerings.csv` | 510 | one subject in one teaching period | `subject_code`, `teaching_period`, `mode` |
| `uts/taught_skills_student_reported.csv` | 305 | one skill a student says a subject taught (9 MDSI subjects) | `subject_code`, `skill_id`, `skill`, `collected_by`, `period` |
| `learning_resources/external_courses.csv` | 1,167 | one piece of text from 56 free courses outside UTS | profile columns + `provider`, `cost`, `date_checked` |
| `learning_resources/resources.csv` | 250 | one self-study resource | `provider`, `format`, `level`, `hours`, `cost`, `certificate`, `skills`, `roles`, `url`, `date_checked` |
| `learning_resources/resource_modules.csv` | 2,030 | one description sentence or module title of a resource | for matching |
| `learning_resources/certifications.csv` | 49 | one industry certification | `cert`, `vendor`, `roles`, `skills`, `cost_aud`, `au_ads_count`, `hot` |
| `learning_resources/priority_skills.csv` | 165 | one of the 15 top skills of each role | role, skill |

### B.2 `data/2_demand/`: what employers ask for

| File | Rows | One row = | Key columns |
|---|---|---|---|
| `role_skill_demand.csv` | 3,086 | **the one demand table**: one skill for one role from one source and period | `role`, `skill_id`, `skill`, `source`, `period`, `text_type`, `n_ads`, `total_ads`, `pct`, `pct_low`, `pct_high` |
| `ads/jobspipe_2026_skills.csv` | 793 | one JobsPipe ad of Sep-Oct 2026, **without its text** | `role`, `title`, `company`, `date_posted`, `employer_type`, `url`, `skills` |
| `ads/ats_2026_clean.csv` | 392 | one ad from 65 employers' job boards, Oct 2026, with a role | `company`, `title`, `role`, `posted`, `description`, `url` |
| `ads/jobs_au_seek_datascientist_2019-2022_clean.csv` | 3,204 | one Seek Data Scientist ad, glued words repaired | ad text |
| `ads/jobs_au_recent_2024-2026_clean.csv` | 192 | one recent data-role ad (job boards 2026, Adzuna, LinkedIn Jan 2024) | ad text, period |
| `adzuna_counts_2026-10.csv` | 165 | one live Adzuna search count, skill × role | `role`, `role_query`, `skill`, `skill_query`, `count`, `role_total`, `date` |
| `role_outlook.csv` | 12 | one role's official outlook (Jobs and Skills Australia) | `anzsco_code`, `shortage_2025`, `vacancies_latest`, `vacancies_12m_ago` |
| `skills_not_taught_by_uts.csv` | 73 | a skill no UTS subject names (54), or names but 2026 ads ask for a lot (19) | `skill`, `pct_2019_22`, `pct_2026`, `covered_by_uts` |
| `emerging/emerging_candidates.csv`, `..._2024-2026.csv` | 55; 77 | one rising phrase from one detection method | `method`, `phrase`, `df_new`, `z`, `is_skill` |
| `skill_counts_v2.csv`, `skill_counts_2026.csv`, `top_skills.csv`, `role_profiles.csv` | 148, 148, 15, 441 | earlier demand files, superseded by `role_skill_demand.csv`; only the fallback engine still reads two of them | |
| `collection/` | | the job boards, candidate employers, Adzuna queries and JobsPipe totals used to collect the ads | |

### B.3 `data/4_evaluation/` and the other folders

| File | Rows | One row = |
|---|---|---|
| `4_evaluation/labels/ad_skills.csv` | 534 (+679 in #123) | one skill asked for in one labelled ad, by one annotator |
| `4_evaluation/labels/cv_jd_pairs.csv` | 287 | one skill in one of 45 CV-ad pairs: `gold_status` have / partial / missing |
| `4_evaluation/labels/skill_subject_pairs.csv` | 33 (+15 in #124) | one skill-subject claim: `teaches` y / partly / n, with the Handbook evidence |
| `4_evaluation/labels/chat_questions.csv` | 15 | one chat test question with a reference answer |
| `4_evaluation/inputs/` | 200; 2,481 | the 200-ad label sample; the de-identified resumes |
| `4_evaluation/results/` | | scores for section 6 |
| `3_tuning/` | | every threshold, where it is set and on what data |
| `5_crosscheck/` | | other platforms and markets (LinkedIn US, Glassdoor AU), extractor agreement, role rank agreement |

The pipeline's JSON output (gaps with have / partial / missing status, evidence sentences, recommended subjects and the
learning path) is defined in `docs/data_contract.md` and not repeated here.

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
