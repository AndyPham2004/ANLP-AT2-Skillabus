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
| `taxonomies/role_occupations.csv` | The 11 IT roles -> their ESCO, O*NET and ASC occupation, 34 rows, with match and reason (see below) | Quan's session, 15 Oct (plan D4) | `python data-eda/src/build_occupation_skills.py` |
| `taxonomies/occupation_skills.csv` | What those occupations require, 1,148 rows: ESCO essential/optional skills, O*NET in-demand tools, ASC core competencies and tool categories | Quan's session, 15 Oct (plan D4) | `python data-eda/src/build_occupation_skills.py` |
| `uts/subject_profiles.csv` | 360 UTS subjects in 44 courses, 6,853 rows, four layers; notes in `subject_profiles.md` | Van Thong; 13 Oct rebuild by Quan's session | `python data-eda/src/build_subject_profiles.py` |
| `uts/prerequisites.csv` | One row per item of each subject's access-conditions rule | Quan's session, 13-14 Oct | `python data-eda/src/scrape_requisites.py` |
| `uts/offerings.csv` | One row per subject, teaching period and mode | Quan's session, 13 Oct | `python data-eda/src/scrape_requisites.py` |
| `uts/assessments_scraped.csv` | Assessment tasks from the Handbook, before the merge into the profiles | Quan's session 13 Oct, Van Thong 14 Oct | `python data-eda/src/scrape_assessments.py` |
| `uts/subjects_template.csv` | The column shape of `data/raw/uts_subjects_2026.csv`, for pasting a subject by hand | Van Thong | Template |
| `uts/subject_content_TEMPLATE.csv` | Columns for hand-collected subject rows; save as `uts/subject_content.csv` and `build_subject_profiles.py` merges them | Quan | Template |
| `learning_resources/external_courses.csv` | 56 free or free-to-audit outside courses, one row per sentence or module; notes in `external_courses.md` | Quan's session 13 Oct, Van Thong 14 Oct | `python data-eda/src/external/build_external.py` (needs the saved pages in `data/raw/external_courses_pages/`) |

Owner of the folder: Van Thong (data). Planned here: `skills/skills_vocabulary.csv` (D5),
`uts/taught_skills_student_reported.csv` (D10), `learning_resources/resources.csv` and
`certifications.csv` (D9, D11).

## Occupation skills per role (plan D4)

The app's "core skills" for a role, and the `taxonomy` rows of the demand table (plan 4.3), come
from here. Built by Quan's session on 15 Oct; Van Thong's `2_demand/roles.csv` (D1) starts from
`role_occupations.csv`. Rebuild (needs `data/raw/taxonomy_esco_v1.2.1/`, `taxonomy_onet_v31/`,
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
