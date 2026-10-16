# Appendix

> Appendix A by Van Thong, 17 Oct 2026, from `notebooks/vt_eda.ipynb` and the files on `main`. Tables A.5–A.6 and
> Appendices B and C were drafted by Akash (#79, #91) and updated on 17 Oct for the files merged that day. The full file
> list, with builders and rebuild commands, is `data/README.md`; the pipeline's JSON output is in `docs/data_contract.md`.

**Repository:** https://github.com/AndyPham2004/ANLP-AT2-Skillabus · **App:** [link and QR code: Quan adds]

## Appendix A. Data

**Table A.1.** Every data source, what Skillabus uses it for, and its licence.

| Source | What we use | Period | Role in Skillabus | Licence or terms |
|---|---|---|---|---|
| JobsPipe API (aggregates LinkedIn, Indeed, Workday and 11 job-board platforms) | 1,932 Australian ads, 89–216 per role, 11 roles; skills found and link only | 1 Sep – 16 Oct 2026 | main demand for every role | API terms: ad text not redistributed, link kept; one free account per person (three members' own accounts) |
| Adzuna API | live search counts: 11 role totals, 162 skill × role counts | 16 Oct 2026 | second 2026 view; rank check | API terms (counts only) |
| Public job boards of 65 employers (Greenhouse, Lever, SmartRecruiters, Ashby, Workable) | 392 ads posted within 60 days, 85 with a role | Oct 2026 | third 2026 view | employers' public ads |
| Seek Australia, Data Scientist (nomilk, 2022) | 3,204 listings, full text | Feb 2019 – Jan 2022 | Data Scientist trend | CC0 |
| Seek Australia samples (PromptCloud, 2021) | 2,366 IT ads out of 65,840, 10 roles | 2020–21 | pre-2022 baseline per role | CC0 |
| data_jobs (Barousse, 2025) | 10,925 Australian postings in 7 roles, tool lists | 2023 | cross-check | Apache-2.0 |
| LinkedIn data-science postings (asaniczka, 2024) | 122 Australian data roles | Jan 2024 | trend midpoint | ODC-By |
| LinkedIn job postings (arshkon, 2024) | 247 US Data Scientist ads | 2023–24 | validation | CC BY-SA 4.0 |
| Glassdoor Australia (nadzmiagthomas, 2022) | 193 data roles | Aug – Dec 2022 | validation | CC BY-NC 4.0 |
| ESCO v1.2.1 | 13,960 skills, 100,135 labels; essential and optional skills of each role's occupation | 2025 | base of the vocabulary; core skills | free reuse with attribution |
| O\*NET 31.0 | 8,753 software products (Technology Skills); the "In Demand" ones per occupation | 2026 | in-demand tools per role | CC BY 4.0 |
| Australian Skills Classification v1.0 | core competencies and tool categories per ANZSCO occupation | 2021 | Australian taxonomy | CC BY 4.0 |
| Jobs and Skills Australia | 2025 Occupation Shortage List; Internet Vacancy Index | 2025–26 | shortage label per role | CC BY 4.0 |
| UTS Handbook 2026 | 360 subjects in 44 courses, 19 of them MDSI | 2026 | subject profiles, prerequisites, sessions | public pages; text kept for matching |
| Students' Canvas reports | 305 skill rows for 9 MDSI subjects, 2 students | 2025–26 | what subjects taught | our own data |
| Official course, tutorial and certification pages | 56 outside courses, 250 self-study resources, 49 certifications (19 vendors) | Oct 2026 | outside courses, self-study, certifications | links and our own summaries |
| Resume Dataset (snehaanbhawal, 2021) | 2,481 resumes, 24 categories | 2021 | test inputs, CV–JD pairs | CC0 |

**Table A.2.** Ads per role and source in `data/2_demand/role_skill_demand.csv` (4,494 rows; notebook section 10). The app
reads the first source that has the role, in the order JobsPipe 2026, Adzuna 2026, job boards 2026, data_jobs 2023,
Seek 2019–22 (`match.DEMAND_PRIORITY`); today that is JobsPipe for all 11 roles. The 2026 job-board ads form three blocks
of 30+ ads: Software Engineer 33, data roles (mixed) 26 and IT roles (mixed) 26.

| Family | Role | JobsPipe 2026 | Adzuna 2026 | Seek 2020–21 | data_jobs 2023 | Seek 2019–22 |
|---|---|---|---|---|---|---|
| Data & AI | Data Scientist | 89 | 171 | 30 | 1,047 | 3,204 |
| Data & AI | Data Analyst | 205 | 290 | 145 | 1,362 | – |
| Data & AI | Data Engineer | 188 | 811 | 59 | 4,438 | – |
| Data & AI | Machine Learning Engineer | 204 | 62 | – | 263 | – |
| Software | Software Engineer | 195 | 1,171 | 944 | 1,198 | – |
| Software | QA/Test Engineer | 212 | 105 | 174 | – | – |
| Cloud & infrastructure | Cloud Engineer | 101 | 395 | 43 | 350 | – |
| Cloud & infrastructure | DevOps/SRE | 187 | 330 | 130 | – | – |
| Cloud & infrastructure | Network/Systems Administrator | 203 | 210 | 269 | – | – |
| Security | Cybersecurity Analyst | 132 | 139 | 179 | – | – |
| Business analysis | Business Analyst | 216 | 876 | 389 | 576 | – |

**Table A.3.** Do skill rankings agree across sources? Spearman rank correlation over the skills both name
(`data/5_crosscheck/`; notebook section 5).

| Compared | What differs | Skills | Rank correlation |
|---|---|---|---|
| Seek 2019–22 vs Glassdoor Australia 2022 (193 ads) | platform | 95 | 0.75 |
| Seek 2019–22 vs LinkedIn US 2023–24 (247 Data Scientist ads) | country and years | 100 | 0.82 |
| Seek 2019–22 vs LinkedIn Australia Jan 2024 (122 data roles) | years and role mix | 84 | 0.61 |
| Adzuna 2026 vs data_jobs 2023, per role (7 roles) | years and kind of source | 6–15 | 0.40 (Business Analyst) to 0.97 (Data Scientist); 0.50 Machine Learning Engineer; 0.69–0.77 the other four |
| Adzuna 2026 vs Seek 2019–22, Data Scientist | years and kind of source | 15 | 0.57 |

Only each role's 15 priority skills were searched on Adzuna, and they were picked from the older sources, so the Adzuna
rows test the order within that top group (`role_rank_agreement.csv`).

**Table A.4.** Subject profiles (`data/1_knowledge/uts/subject_profiles.csv`, 6,853 rows, 360 subjects in 44 courses).

| Layer | Rows | Subjects | Source |
|---|---|---|---|
| Learning objective | 1,516 | 354 | one row per objective |
| Assessment | 1,015 | 326 | one row per task: name, type, weight, group or individual, description |
| Weekly topic | 2,769 | 327 | one row per listed topic |
| Description | 1,553 | 360 | one row per sentence |

Alongside them, `prerequisites.csv` holds 2,200 requisite items for 290 subjects, 70 empty rules and 301 anti-requisite
rows for 172 subjects, and `offerings.csv` the teaching sessions of 330 subjects. Tables A.5 and A.6 give the layers per
course and per MDSI subject.

Rows per layer in `data/1_knowledge/uts/subject_profiles.csv`: 6,853 rows for 360 subjects in 44 courses, one row per
learning objective, assessment task, weekly topic or description sentence (UTS Handbook 2026, scraped 13 Oct 2026;
`data/1_knowledge/uts/subject_profiles.md`). A dash means the Handbook has no text for that layer.

**Table A.5.** Courses. A subject in several courses is counted in each, so columns do not add up to the total.

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

**Table A.6.** MDSI subjects (C04372).

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
| `role_skill_demand.csv` | 4,494 | **the one demand table**: one skill for one role from one source and period | `role`, `skill_id`, `skill`, `source`, `period`, `text_type`, `n_ads`, `total_ads`, `pct`, `pct_low`, `pct_high` |
| `ads/jobspipe_2026_skills.csv` | 1,932 | one JobsPipe ad of Sep-Oct 2026, **without its text** | `role`, `title`, `company`, `date_posted`, `employer_type`, `url`, `skills` |
| `ads/seek_2020_21_skills.csv` | 2,366 | one Seek Australia IT ad of 2020–21, **without its text** | `role`, `title`, `company`, `url`, `skills` |
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
| `4_evaluation/labels/ad_skills_2026.csv`, `role_paths_review.csv` | 17 Oct | labels of 18 ads of 2026 across 10 roles; a reader's verdict on each of the 33 role-path subjects |
| `4_evaluation/inputs/` | 200; 2,481; 18 | the 200-ad label sample; the de-identified resumes; the 18 ads of 2026 to label |
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
| Adzuna search count | The number of live ads on Adzuna Australia on one day whose title has a role's words and whose text has a skill's phrase. |
| JobsPipe | A licensed job-ad API that aggregates LinkedIn, Indeed and job-board postings; the main 2026 source. |
| Wilson interval | A 95% confidence interval for a share that stays sensible for small samples. |

## Appendix D. Tables moved out of sections 4 and 6

[Phuong Nhi and Hoai Thuong: tables moved out of sections 4 and 6 go here as Table D.1, D.2, ...]
