# 1_knowledge: what the app looks up

Reference data the pipeline reads at run time. Code takes these paths from `src/skillabus/paths.py`.
Commands run from the repo root; "raw" inputs are in `data/raw/` (not in git, see `data/README.md`).

| File | What | Made by | Rebuild |
|---|---|---|---|
| `skills/skills_seed_v2.csv` | The one skill dictionary: 148 skills, `canonical, category, strict, aliases`. Starts with a `#` note: read with `skiprows=1`, never `comment="#"` (that cuts `C#` to `C`) | Van Thong's 133 rows + 5 generic rows (Quan, 25 Sep) + 10 tool rows (Van Thong, 14 Oct) | Edited by hand through a PR. To be replaced by `skills_vocabulary.csv` (plan D5) |
| `skills/skill_to_esco.csv` | Dictionary skill -> ESCO concept, 132 rows (the wrong "SPARK" link removed) | Van Thong (`map_to_esco.py`), copied by Quan's 3 Oct mock builder | `python data-eda/src/map_to_esco.py` writes `original/skill_to_esco.csv`; drop the Spark row, copy here |
| `skills/original/skills_seed.csv` | Van Thong's original 133-row dictionary: poster counts, resume cleaning, Glassdoor counts, EDA | Van Thong | Hand-edited; goes to `archive/dictionary_v1/` once D5 lands |
| `skills/original/skill_to_esco.csv` | Its ESCO links, 133 rows | Van Thong | `python data-eda/src/map_to_esco.py` (needs `data/raw/taxonomy_esco_v1.2.1/`) |
| `taxonomies/esco_skills_clean.csv` | ESCO v1.2.1, 13,960 skill concepts, alt labels pipe-joined | Van Thong | `python data-eda/src/clean_esco.py` |
| `taxonomies/esco_label_lookup.csv` | 100,886 (label, concept) rows; 716 ambiguous labels | Van Thong | `python data-eda/src/clean_esco.py` |
| `uts/subject_profiles.csv` | 360 UTS subjects in 44 courses, 6,853 rows, four layers; notes in `subject_profiles.md` | Van Thong; 13 Oct rebuild by Quan's session | `python data-eda/src/build_subject_profiles.py` |
| `uts/prerequisites.csv` | One row per item of each subject's access-conditions rule | Quan's session, 13-14 Oct | `python data-eda/src/scrape_requisites.py` |
| `uts/offerings.csv` | One row per subject, teaching period and mode | Quan's session, 13 Oct | `python data-eda/src/scrape_requisites.py` |
| `uts/assessments_scraped.csv` | Assessment tasks from the Handbook, before the merge into the profiles | Quan's session 13 Oct, Van Thong 14 Oct | `python data-eda/src/scrape_assessments.py` |
| `uts/subjects_template.csv` | The column shape of `data/raw/uts_subjects_2026.csv`, for pasting a subject by hand | Van Thong | Template |
| `uts/subject_content_TEMPLATE.csv` | Columns for hand-collected subject rows; save as `uts/subject_content.csv` and `build_subject_profiles.py` merges them | Quan | Template |
| `learning_resources/external_courses.csv` | 56 free or free-to-audit outside courses, one row per sentence or module; notes in `external_courses.md` | Quan's session 13 Oct, Van Thong 14 Oct | `python data-eda/src/external/build_external.py` (needs the saved pages in `data/raw/external_courses_pages/`) |
| `learning_resources/certifications.csv` | 49 industry certifications for the 11 IT roles, with price, official page and a "hot" signal; notes in `certifications.md` | Quan's session 15 Oct (D11); Adzuna counts by Van Thong | Checked by hand on the vendors' pages; counts: `count_cert_mentions.py`, `count_cert_adzuna.py` |

Owner of the folder: Van Thong (data). Planned here: `skills/skills_vocabulary.csv` (D5),
`taxonomies/occupation_skills.csv` (D4), `uts/taught_skills_student_reported.csv` (D10),
`learning_resources/resources.csv` (D9).

## Certifications (D11)

`learning_resources/certifications.csv` lists 49 current certifications (AWS, Microsoft, Google Cloud, CompTIA,
Cisco, ISC2, ISACA, Linux Foundation / CNCF, Red Hat, HashiCorp, Databricks, Snowflake, Tableau, ISTQB, Scrum.org,
Scrum Alliance, ITIL, IIBA, ACS), at least four per role. Each row has the current exam code, level, roles, skills
(dictionary spelling), how ads write it, the exam price in AUD and USD, the vendor's page and `date_checked`;
`status_note` records renames and retirements (seven Microsoft exams retired between June and September 2026:
DP-100, AI-102, AI-900, AZ-204, AZ-500, AZ-800, AZ-801).

"Hot" is measured, not asserted, because our own ads rarely name a certificate (7 of 49 appear in 4,098 local
ads; `local_ads_mentions`):

1. `au_ads_count`: live Adzuna AU ads per certificate phrase (`python data-eda/src/count_cert_adzuna.py`, run by
   Van Thong with the key in `.env`);
2. `report_signal`: named in an industry report from the last 12 months (Robert Half 2027 Salary Guide, Oct 2026);
3. the trend between two Adzuna counts.

`hot` and `hot_reason` stay blank until step 1 runs. The rule, the USD to AUD rate and every caveat are in
`learning_resources/certifications.md`.
