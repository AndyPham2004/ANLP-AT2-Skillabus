# Appendix C. Data dictionary

All files are UTF-8 CSV in five folders under `data/`; code takes every path from `src/skillabus/paths.py`. Raw downloads (`data/raw/`, about 0.9 GB) and files written while the app runs (`data/runtime/`: feedback votes, caches) are not committed. Files starting with a `#` provenance line must be read with `skiprows=1`, not `comment="#"`, which truncates the `C#` row.

### C.1 `data/1_knowledge/`: what the app looks up

| **File** | **Rows** | **One row =** | **Key columns** |
|----|----|----|----|
| `skills/skills_vocabulary.csv` | 504 | one skill in the one vocabulary: 148 dictionary skills, added IT skills, ESCO core skills, certifications | `skill_id`, `label`, `category`, `source`, `esco_uri`, `esco_match`, `aliases_ads`, `strict`, `used_for` |
| `skills/skills_seed_v2.csv` | 148 | one dictionary skill (`#` line first) | `canonical`, `category`, `strict`, `aliases` |
| `skills/skill_to_esco.csv` | 132 | one dictionary skill linked to ESCO | `canonical`, `esco_uri`, `esco_preferred_label`, `matched_on` |
| `skills/esco_link_review.csv`, `added_skills.csv`, `onet_tool_map.csv` | 148, 125, 79 | the hand files behind the vocabulary | ESCO link and note; candidate IT skills; O\*NET tool → label |
| `taxonomies/role_occupations.csv` | 34 | one of the 11 IT roles mapped to an ESCO, O\*NET or ASC occupation | `role`, `role_family`, `source`, `occupation_code`, `match` (exact / close / broad), `why` |
| `taxonomies/occupation_skills.csv` | 1,148 | one skill or tool an occupation requires | ESCO essential/optional, O\*NET in-demand tools, ASC core competencies |
| `taxonomies/esco_skills_clean.csv`, `esco_label_lookup.csv` | 13,960; 100,886 | one ESCO v1.2.1 concept; one (label, concept) pair | `concept_uri`, `preferred_label`, `alt_labels`, `skill_type` |
| `uts/subject_profiles.csv` | 6,853 | one piece of subject text | `subject_code`, `subject_name`, `course` (pipe-separated), `layer`, `text`, `source_url`, `collected_by` |
| `uts/assessments_scraped.csv` | 1,015 | one assessment task (before the merge into profiles) | profile columns |
| `uts/prerequisites.csv` | 2,571 | one item of a subject’s access rule | `subject_code`, `kind`, `rule`, `item`, `type`, `requisite_code` |
| `uts/offerings.csv` | 510 | one subject in one teaching period | `subject_code`, `teaching_period`, `mode` |
| `uts/taught_skills_student_reported.csv` | 305 | one skill a student says a subject taught (9 MDSI subjects) | `subject_code`, `skill_id`, `skill`, `collected_by`, `period` |
| `learning_resources/external_courses.csv` | 1,167 | one piece of text from 56 free courses outside UTS | profile columns + `provider`, `cost`, `date_checked` |
| `learning_resources/resources.csv` | 250 | one self-study resource | `provider`, `format`, `level`, `hours`, `cost`, `certificate`, `skills`, `roles`, `url`, `date_checked` |
| `learning_resources/resource_modules.csv` | 2,030 | one description sentence or module title of a resource | for matching |
| `learning_resources/certifications.csv` | 49 | one industry certification | `cert`, `vendor`, `roles`, `skills`, `cost_aud`, `au_ads_count`, `hot` |
| `learning_resources/priority_skills.csv` | 165 | one of the 15 top skills of each role | role, skill |

### C.2 `data/2_demand/`: what employers ask for

| **File** | **Rows** | **One row =** | **Key columns** |
|----|----|----|----|
| `role_skill_demand.csv` | 4,494 | **the one demand table**: one skill for one role from one source and period | `role`, `skill_id`, `skill`, `source`, `period`, `text_type`, `n_ads`, `total_ads`, `pct`, `pct_low`, `pct_high` |
| `ads/jobspipe_2026_skills.csv` | 1,932 | one JobsPipe ad of Sep-Oct 2026, **without its text** | `role`, `title`, `company`, `date_posted`, `employer_type`, `url`, `skills` |
| `ads/seek_2020_21_skills.csv` | 2,366 | one Seek Australia IT ad of 2020–21, **without its text** (2,362 in the 10 roles used, 4 Machine Learning Engineer) | `role`, `title`, `company`, `url`, `skills` |
| `ads/ats_2026_clean.csv` | 392 | one ad from 51 employers’ public boards, fetched 13–16 Oct 2026; role is one of the 11 roles for 85 ads, “other” for 307 | `company`, `title`, `role`, `posted`, `description`, `url` |
| `ads/jobs_au_seek_datascientist_2019-2022_clean.csv` | 3,204 | one Seek Data Scientist ad, glued words repaired | ad text |
| `ads/jobs_au_recent_2024-2026_clean.csv` | 192 | one recent data-role ad (job boards 2026, Adzuna, LinkedIn Jan 2024) | ad text, period |
| `adzuna_counts_2026-10.csv` | 165 | one live Adzuna search count, skill × role | `role`, `role_query`, `skill`, `skill_query`, `count`, `role_total`, `date` |
| `role_outlook.csv` | 12 | one role and ANZSCO occupation: the official outlook (Jobs and Skills Australia) | `anzsco_code`, `shortage_2025`, `vacancies_latest`, `vacancies_12m_ago` |
| `skills_not_taught_by_uts.csv` | 73 | a skill no UTS subject names (54), or names but 2026 ads ask for a lot (19) | `skill`, `pct_2019_22`, `pct_2026`, `covered_by_uts` |
| `emerging/emerging_candidates.csv`, `..._2024-2026.csv` | 55; 77 | one rising phrase from one detection method | `method`, `phrase`, `df_new`, `z`, `is_skill` |
| `skill_counts_v2.csv`, `skill_counts_2026.csv`, `top_skills.csv`, `role_profiles.csv` | 148, 148, 15, 441 | earlier demand files, superseded by `role_skill_demand.csv`; only the fallback engine still reads two of them |  |
| `collection/` |  | the job boards, candidate employers, Adzuna queries and JobsPipe totals used to collect the ads |  |

### C.3 `data/4_evaluation/` and the other folders

| **File** | **Rows** | **One row =** |
|----|----|----|
| `4_evaluation/labels/ad_skills.csv` | 534 | one skill asked for in one labelled ad, by one annotator |
| `4_evaluation/labels/cv_jd_pairs.csv` | 287 | one skill in one of 45 CV-ad pairs: `gold_status` have / partial / missing |
| `4_evaluation/labels/skill_subject_pairs.csv` | 33 | one skill-subject claim: `teaches` y / partly / n, with the Handbook evidence |
| `4_evaluation/labels/chat_questions.csv` | 15 | one chat test question with a reference answer |
| `4_evaluation/labels/ad_skills_2026.csv`, `role_paths_review.csv` | 293; 32 | labels of 18 ads of 2026 across 10 roles; a reader’s verdict on each of the 32 role–subject pairs (18 subjects) |
| `4_evaluation/inputs/` | 200; 2,481; 18 | the 200-ad label sample; the de-identified resumes; the 18 ads of 2026 to label |
| `4_evaluation/results/` |  | scores for section 6 |
| `3_tuning/` |  | every threshold, where it is set and on what data |
| `5_crosscheck/` |  | other platforms and markets (LinkedIn US, Glassdoor AU), extractor agreement, role rank agreement |

The pipeline’s JSON output (gaps with have / partial / missing status, evidence sentences, recommended subjects and the learning path) is defined in `docs/data_contract.md` and not repeated here.

# Appendix D. Glossary

| **Term** | **Meaning in this report** |
|----|----|
| Ad (job ad) | A job advertisement; the “JD” in CV-JD pair. |
| Alias | Another way of writing a dictionary skill (e.g. `sklearn` for scikit-learn). |
| Canonical skill | The one name a dictionary skill is stored under. |
| Cohen’s kappa (κ) | Agreement between two annotators corrected for chance; 1 = perfect, 0 = chance level. |
| Demand weight | A skill’s share of job ads; used to rank gaps and choose the learning path. |
| Embedding | A vector representing the meaning of a sentence (here, all-MiniLM-L6-v2), compared by cosine similarity. |
| Emerging skill | A skill found in ads with no ESCO concept, such as many GenAI terms; kept and flagged. (A Lightcast lookup is designed for these but needs API keys.) |
| ESCO | European Skills, Competences, Qualifications and Occupations: the EU’s open skills taxonomy. |
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
| Role profile | The skills most often asked for in one job role (e.g. Data Engineer), with their share of ads; used when a student picks a role instead of an ad. |
| spaCy | An open-source NLP library, used for tier-2 extraction. |
| Subject profile | All the Handbook text about one subject, one row per piece, labelled by layer. |
| TF-IDF | A keyword-weighting method; the baseline for matching and ranking. |
| Tier 1 / 2 / 3 | The three extraction steps: dictionary, spaCy, GPT-4o-mini. |
| Adzuna search count | The number of live ads on Adzuna Australia on one day whose title has a role’s words and whose text has a skill’s phrase. |
| JobsPipe | A licensed job-ad API that aggregates LinkedIn, Indeed and job-board postings; the main 2026 source. |
| Wilson interval | A 95% confidence interval for a share that stays sensible for small samples. |
