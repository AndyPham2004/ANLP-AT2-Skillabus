# 1_knowledge: what the app looks up

Reference data the pipeline reads at run time. Code takes these paths from `src/skillabus/paths.py`.
Commands run from the repo root; "raw" inputs are in `data/raw/` (not in git, see `data/README.md`).

| File | What | Made by | Rebuild |
|---|---|---|---|
| `skills/skills_seed_v2.csv` | The one skill dictionary: 148 skills, `canonical, category, strict, aliases`. Starts with a `#` note: read with `skiprows=1`, never `comment="#"` (that cuts `C#` to `C`) | Van Thong's 133 rows + 5 generic rows (Quan, 25 Sep) + 10 tool rows (Van Thong, 14 Oct) | Edited by hand through a PR. To be replaced by `skills_vocabulary.csv` (plan D5) |
| `skills/skills_vocabulary.csv` | **The one vocabulary** (plan D5), 503 rows: the 148 dictionary skills, 95 IT skills added from O\*NET, data_jobs and the 2026 ads, 211 ESCO core skills of the 11 roles, 49 certifications. Section below | Claude 15 Oct, Van Thong to check | `python data-eda/src/build_vocabulary.py` (`--check` says if it is stale) |
| `skills/esco_link_review.csv` | The hand-checked ESCO link of each dictionary skill: old link, new link, `esco_match`, a note for every link that is not exact | Claude 15 Oct, Van Thong to check | Edit by hand, then rerun `build_vocabulary.py` |
| `skills/added_skills.csv` | Candidate IT skills beyond the dictionary: ad-style aliases, ESCO link and note, origin. 123 rows; the builder keeps those that pass the ad rule | Claude 15 Oct, Van Thong to check | Edit by hand, then `build_vocabulary.py --recount` |
| `skills/onet_tool_map.csv` | Each of the 79 O\*NET in-demand tools of the 11 roles -> a vocabulary label ("Amazon Web Services AWS software" -> AWS), or dropped with a reason. D6 maps the O\*NET rows of the demand table with it | Claude 15 Oct | By hand |
| `skills/vocabulary_ad_counts.csv` | Distinct Australian ads naming each dictionary or candidate skill, by source, and their employers | `build_vocabulary.py --recount` | Needs the raw ATS ads in `data/raw/` (`--raw <folder>` reads them elsewhere) |
| `skills/skill_to_esco.csv` | Dictionary skill -> ESCO concept, 132 rows (the wrong "SPARK" link removed) | Van Thong (`map_to_esco.py`), copied by Quan's 3 Oct mock builder | `python data-eda/src/map_to_esco.py` writes `original/skill_to_esco.csv`; drop the Spark row, copy here |
| `skills/original/skills_seed.csv` | Van Thong's original 133-row dictionary: poster counts, resume cleaning, Glassdoor counts, EDA | Van Thong | Hand-edited; goes to `archive/dictionary_v1/` once D5 lands |
| `skills/original/skill_to_esco.csv` | Its ESCO links, 133 rows | Van Thong | `python data-eda/src/map_to_esco.py` (needs `data/raw/taxonomy_esco_v1.2.1/`) |
| `taxonomies/esco_skills_clean.csv` | ESCO v1.2.1, 13,960 skill concepts, alt labels pipe-joined | Van Thong | `python data-eda/src/clean_esco.py` |
| `taxonomies/esco_label_lookup.csv` | 100,886 (label, concept) rows; 716 ambiguous labels | Van Thong | `python data-eda/src/clean_esco.py` |
| `taxonomies/role_occupations.csv` | The 11 IT roles -> their ESCO, O*NET and ASC occupation, 34 rows, with match and reason (see below) | Quan's session, 15 Oct (plan D4) | `python data-eda/src/build_occupation_skills.py` |
| `taxonomies/occupation_skills.csv` | What those occupations require, 1,148 rows: ESCO essential/optional skills, O*NET in-demand tools, ASC core competencies and tool categories | Quan's session, 15 Oct (plan D4) | `python data-eda/src/build_occupation_skills.py` |
| `uts/subject_profiles.csv` | 360 UTS subjects in 44 courses, 6,853 rows, four layers; notes in `subject_profiles.md` | Van Thong; 13 Oct rebuild by Quan's session | `python data-eda/src/build_subject_profiles.py` |
| `uts/prerequisites.csv` | One row per item of each subject's access-conditions rule | Quan's session, 13-14 Oct | `python data-eda/src/scrape_requisites.py` |
| `uts/offerings.csv` | One row per subject, teaching period and mode | Quan's session, 13 Oct | `python data-eda/src/scrape_requisites.py` |
| `uts/assessments_scraped.csv` | Assessment tasks from the Handbook, before the merge into the profiles | Quan's session 13 Oct, Van Thong 14 Oct | `python data-eda/src/scrape_assessments.py` |
| `uts/subjects_template.csv` | The column shape of `data/raw/uts_subjects_2026.csv`, for pasting a subject by hand | Van Thong | Template |
| `uts/taught_skills_student_reported.csv` | Skills each UTS subject actually taught, **reported by students, not official**: one row per subject x skill, `subject_code, skill_id, skill, collected_by, period`. `skill` is a `skills_vocabulary.csv` label with its `skill_id` where one fits, else the student's own short name with `skill_id` empty. Van Thong: 9 MDSI subjects, 297 rows, Spring 2025 to Spring 2026, from his own Canvas module lists, schedules and assessment briefs (Claude proposed names from those pages and matched them to the vocabulary; he added, removed and confirmed each). Phuong Nhi (same classes as Van Thong): 8 rows for 94693 Big Data Engineering, taken from what her own assessments used (Spark and Spark MLlib in AT2; medallion layers, slowly changing dimensions, star schema, dbt data tests, Cloud Composer and Cloud SQL in AT3); Spark, data modelling and data quality repeat his rows as a second report. She added nothing for the other eight subjects. Skill names only: no course text is stored | Each team member for the subjects they took (D10, #119) | By hand, one PR per person; append rows, keep `collected_by` |
| `learning_resources/external_courses.csv` | 56 free or free-to-audit outside courses, one row per sentence or module; notes in `external_courses.md` | Quan's session 13 Oct, Van Thong 14 Oct | `python data-eda/src/external/build_external.py` (needs the saved pages in `data/raw/external_courses_pages/`) |
| `learning_resources/certifications.csv` | 49 industry certifications for the 11 IT roles, with price, official page and a "hot" signal; notes in `certifications.md` | Quan's session 15 Oct (D11); Adzuna counts by Van Thong | Checked by hand on the vendors' pages; counts: `count_cert_mentions.py`, `count_cert_adzuna.py` |
| `learning_resources/resources.csv` | **The self-study store** (D9): 250 resources, one row each, with level, format, hours, cost, certificate, skills, roles, url. Section below | Quan's session 15 Oct (D9); Akash and Van Thong check a sample | Collected by hand on the providers' pages |
| `learning_resources/resource_modules.csv` | The text of the 192 resources added on 15 Oct (2,028 rows: one description, then module titles), same schema as `external_courses.csv` | Quan's session 15 Oct (D9) | By hand, with `resources.csv` |
| `learning_resources/spot_check_2026-10-16.csv` | The D9 spot-check (#122): 51 checks on 33 resources (free claims, Coursera audit, estimated hours, URLs) with the verdict and the evidence seen on each page; the fixes are applied in `resources.csv` (two TAU courses re-pointed, two hours corrected, two resources added) | Claude for Quan, 16 Oct | By hand |
| `learning_resources/priority_skills.csv` | The 15 skills D9 covers first for each role (165 rows, 69 distinct skills), and where each list comes from | Quan's session 15 Oct (D9) | From `2_demand/role_profiles.csv`, `top_skills.csv`, and D4's O\*NET and ESCO rows for the four roles with no ad counts |

Owner of the folder: Van Thong (data). Student-reported subject skills (D10): `uts/taught_skills_student_reported.csv`, see the table.

## The skill vocabulary (plan D5)

`skills/skills_vocabulary.csv` replaces the dictionary plus its ESCO links once the pipeline reads it (plan C2;
until then `skills_seed_v2.csv` and `skill_to_esco.csv` stay as they are). Columns: `skill_id, label, category,
source, esco_uri, esco_label, esco_match, reviewed_by, aliases_ads, strict, used_for, why_added`.

- **`skill_id`** is `esco:<uri>` (the data contract's form) only when `esco_match = exact`; otherwise
  `skillabus:<slug>`. So Tableau and Power BI, which ESCO files under one "data visualisation software", keep two
  ids and `match.py` never confuses them.
- **`esco_match`** follows SKOS, the mapping relations ESCO itself uses: `exact` (same concept), `close` (near,
  not the same), `broad` (ESCO has only a wider concept; it is still given), `none`. Strict: a tool under a generic
  ESCO concept is `broad`. Links found wrong on 14 Oct are gone and refused by the builder (Transformers ->
  "electrical machines", TensorFlow and Keras -> "computer vision", Spark -> the Java framework "SPARK").
- **Only rows with `aliases_ads` detect skills in ads** (`used_for` has `extract`); ESCO labels never do.
  `core_skill` = an essential ESCO skill of a role's occupation, or an O\*NET in-demand tool of a role.
- **Parts.** (1) The 148 dictionary skills, labels and aliases unchanged: 47 exact, 7 close, 90 broad, 4 none.
  Of the 47 links in `skill_to_esco.csv`, 38 are kept (28 exact, 8 broad, 2 close), 3 wrong ones dropped and 6
  replaced by a better concept; the 97 skills without a link got one (17 exact, 4 close, 76 broad). (3) `added_skills.csv`: 123 candidates; 84 pass the **ad rule** (named in at least 3 distinct
  Australian ads from at least 2 employers, counted with extract's tier-1 matcher, an employer's ads about its
  own product not counted) and are used to detect; 11 O\*NET in-demand tools below it (Selenium, Appium, JMeter,
  ServiceNow, Firewalls, ...) are core skills without aliases; 28 are left out. A new alias may not repeat or
  contain another skill's alias (it would take that skill's mentions), so the dictionary's counts do not move.
  One alias is shared on purpose: `pl/sql` belongs to both SQL and Oracle, because PL/SQL is Oracle's SQL and
  an ad asking for it asks for both. `extract()` gives one hit per skill for it, the same as the per-skill
  counters behind the demand files; a test keeps it the only shared alias (#93).
  (2) ESCO's essential skills of the 11 roles that no row above already is: 211 rows, no aliases; they include
  ESCO's research items for data scientist ("apply for research funding"). (+) The 49 certifications of
  `learning_resources/certifications.csv`, `strict = 1` so a certificate name cannot take a skill's mention,
  exempt from the ad rule (ads rarely name certificates; their demand is D11's Adzuna count).
- **Ads counted**: Seek 2019-22 (2,495 distinct texts of the 3,204 ads), the recent 2024-26 sample (192) and
  the 2026 ATS fetches (575 after removing repeats): 3,262 ads. Rerun `--recount` after a new ATS fetch.
- **For the report**: "Skillabus extends ESCO with **145** skills the Australian IT market asks for but ESCO
  lacks" = vocabulary rows used for detection whose `esco_match` is `broad` or `none` and that pass the ad rule:
  86 from the dictionary, 59 added for IT (O\*NET, data_jobs, 2026 ads, generative AI). Not counted: 11 `close`
  rows, 49 certifications. The builder prints the sentence.

```powershell
python data-eda/src/build_vocabulary.py --recount --raw "C:/path/to/data/raw"   # after editing added_skills.csv
python data-eda/src/build_vocabulary.py                                          # after editing a review file
```

## Occupation skills per role (plan D4)

The app's "core skills" for a role, and the `taxonomy` rows of the demand table
`2_demand/role_skill_demand.csv` (plan D6), come from here: the ESCO rows whose skill is in the vocabulary
(every essential skill; 139 of the 399 optional ones) and the O\*NET rows mapped through
`skills/onet_tool_map.csv`. ASC rows are not in that table. Built by Quan's session on 15 Oct; Van
Thong's `2_demand/roles.csv` (D1) starts from `role_occupations.csv`. Rebuild (needs `data/raw/taxonomy_esco_v1.2.1/`, `taxonomy_onet_v31/`,
`taxonomy_asc_australia/`; `--raw <folder>` reads them from another checkout):

```powershell
python data-eda/src/build_occupation_skills.py
```

- **`role_occupations.csv`**: `role, role_family, source, occupation_code, occupation_title, match, why`.
  One row per role and source occupation: ESCO concept URI, O*NET-SOC code or ANZSCO code. `match` is
  `exact` (the occupation's title names the role), `close` (the role's title is an alternate title of the
  occupation) or `broad` (the source has no such occupation; the nearest wider one). Found by searching
  the files and O*NET OnLine's alternate titles, 15 Oct. Role names are those of `2_demand/role_profiles.csv`
  ("Machine Learning Engineer", not "ML Engineer"), so the two join on `role`.
- **`occupation_skills.csv`**: `role, source, occupation_code, occupation_title, skill, skill_ref,
  skill_type, importance, esco_digital, onet_hot`, one row per role, source and skill.
  - ESCO v1.2.1: every essential and optional skill of the occupation (the app shows essential).
    `skill_ref` = skill URI; `skill_type` = `knowledge` or `skill/competence` (blank for 4 rows where
    ESCO has none); `esco_digital` = `y` if the skill is in ESCO's digital skills collection.
  - O*NET 31.0: only tools with **In Demand = Y**, which O*NET sets per occupation. The Hot Technology
    flag is market-wide (it marks Microsoft Excel for 859 of 923 occupations), so `onet_hot` is kept for information
    and never used for ranking. `skill_ref` = `onet:<element id>:<tool>`; `skill_type` = O*NET's tool category.
  - ASC v1.0 (Australian Skills Classification): the 10 core competencies, `importance` = the level the
    occupation needs, 1-10 (1-3 basic, 4-7 intermediate, 8-10 high), and the technology tool categories,
    `importance` = `listed`. ASC tools are categories ("Object oriented development software"), not
    products. Left out: specialist tasks (work activities, "Monitor the security of digital information",
    not skill names) and the example tools (one list per category for the whole market, not per occupation).
  - Network/Systems Administrator has two ASC occupations (262113, 263112). A skill both list is one
    row: codes and titles joined with `|`, the higher level kept.
- **Read before using**: Software Engineer and DevOps/SRE share one O*NET occupation (15-1252.00), so
  their O*NET tools are identical; ASC v1.0 uses ANZSCO 2013, which has no data scientist, data analyst,
  data engineer, ML engineer, cloud or DevOps occupation (all `broad`); ESCO's data scientist lists
  research skills such as "apply for research funding" as essential.

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

## Self-study store (D9)

IT is a field people keep learning in, so the "Self-study" column next to "Learn at UTS" is meant to be deep and
wide, not only a patch for what UTS does not teach. `learning_resources/resources.csv` has 250 resources from 145
providers: the 56 outside courses of 13 Oct and 192 added on 15 Oct.

- **Wide:** every one of the 69 skills in `priority_skills.csv` (the top 15 of each of the 11 roles) has at least
  2 options and a beginner one; the median is 5 (only Airflow and Appium have exactly 2).
- **Deep:** each resource records `level` (150 beginner, 81 intermediate, 17 advanced), `format` (128 course, 54
  tutorial, 33 official docs, 22 hands-on lab, 11 book), `hours`, `cost` (237 free, 9 free-to-audit, 2 paid, with
  `cost_aud`), `certificate` (92 give a certificate or badge), `provider_type` (149 vendor, 63 community, 19
  university, 17 platform), the skills it teaches (vocabulary labels) and the roles it serves.
- **Sources:** vendors' own free training and docs first (AWS Skill Builder, Microsoft Learn, Google Skills,
  Databricks, Snowflake, Cisco Networking Academy, Atlassian, SAP Learning, MITRE), then official project docs,
  universities' free courses (CS50, MIT OpenCourseWare, Stanford), then community resources (freeCodeCamp, Kaggle
  Learn, The Odin Project, MDN, OWASP). Every URL was opened on 15 Oct; final URLs are stored after redirects.
- **Text for matching:** `resource_modules.csv` holds the description and module titles of the 192 new resources;
  `external_courses.csv` keeps the 56 of 13 Oct. Read both with `skillabus.resources.text_rows()`; filter by level,
  cost and role with `skillabus.resources.for_skill()`.
- **Roles:** a resource serves every role whose top 15 names one of its skills; a 13 Oct course for a skill in no
  top 15 serves Data Scientist (those were picked for the Data Scientist gaps UTS does not teach).

To check by hand (Akash and Van Thong, a sample): 55 rows have estimated hours ("hours estimated" in `note`);
"free" is not stated on the page for SAP Learning, Databricks Academy and the Atlassian paths; Coursera's free
audit is no longer certain (Econometrics now needs the paid certificate track, so it is `paid`); Nessus has no free
official course (the one paid row besides Econometrics); Microsoft retired its Office training pages.
