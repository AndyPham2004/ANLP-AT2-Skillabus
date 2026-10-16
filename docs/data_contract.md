# Data contract

The shapes that pass between the pipeline (`src/skillabus/`) and the app (`app/`). The app is built
against these shapes on mock data first, so **change this file only through a PR reviewed by Quan
and Phuong Nhi**.

## 1. A skill mention: output of `extract()` + `normalise()`

```json
{
  "text": "in-depth knowledge of deep learning",
  "skill_id": "esco:http://data.europa.eu/esco/skill/...",
  "skill_label": "deep learning",
  "vocab": "esco",
  "method": "dictionary",
  "sentence": "In-depth knowledge of deep learning, Generative AI and other advanced AI technologies.",
  "requirement": "required"
}
```

| Field | Values |
|---|---|
| `skill_id` | For a vocabulary skill (`data/1_knowledge/skills/skills_vocabulary.csv`), its `skill_id` column: the ESCO id when `esco_match` is `exact`, else `skillabus:<slug>`. Outside the vocabulary: `esco:<uri>`, `lightcast:<id>`, or `emerging:<slug>` when neither vocabulary has it |
| `vocab` | `esco`, `seed` (a vocabulary skill whose ESCO match is close or broad, so it keeps its own `skillabus:` id), `lightcast`, `emerging` (includes vocabulary skills ESCO lacks: `esco_match` = `none`) |
| `canonical` | The vocabulary `label` (rows with `extract` in `used_for`) when the phrase is one of its `aliases_ads`, else `null`; used for demand lookups. Set by `extract()` (tiers 1-2, including forms the alias list lacks, such as "REST APIs"); `normalise()` keeps it and fills it only when it is missing |
| `how` | Which normalisation step matched: `dictionary`, `esco_exact`, `esco_embed`, `lightcast`, `emerging` |
| `similarity` | Cosine to the ESCO label for `esco_embed`, else `null` |
| `kind` | LLM tier only: `hard` or `soft` |
| `method` | `dictionary`, `ner`, `llm` |
| `sentence` | The full sentence the skill came from; this is the evidence shown in the app |
| `requirement` | `required`, `preferred`, or `""` when the ad does not say (D14). From a cue in the sentence ("must", "essential" / "desirable", "nice to have", "not required"), else from the heading the sentence sits under ("Essential criteria:", "Nice to have:"); a preferred cue wins over a required one |

## 2. The gap result: output of `match()` + `recommend()`, input of the app

```json
{
  "ad_id": "rw-2026-09-23",
  "skills": [
    {
      "skill_id": "esco:...",
      "skill_label": "machine learning",
      "status": "missing",
      "demand_pct": 62.0,
      "demand_pct_2026": 62.0,
      "demand_pct_2019_22": 72.4,
      "demand_source": "jobspipe_2026",
      "demand_period": "2026-10",
      "total_ads": 71,
      "text_type": "full_text",
      "emerging": false,
      "ad_evidence": "Implement and evaluate advanced machine learning ...",
      "resume_evidence": null
    }
  ],
  "recommendations": [
    {
      "subject_code": "36120",
      "subject_name": "Advanced Machine Learning Application",
      "score": 0.81,
      "covers": ["machine learning", "predictive modelling"],
      "evidence": [
        {"skill_label": "machine learning", "layer": "learning_objective",
         "text": "Implement and evaluate advanced machine learning techniques ...", "match": "named"}
      ],
      "needs": ["36106"],
      "offered": ["Spring"],
      "unverified": false
    }
  ],
  "learning_path": {
    "subjects": ["36106", "36120", "36121"],
    "gaps_closed": 4,
    "gaps_total": 6,
    "demand_covered_pct": 78.0,
    "plan": [
      {"subject_code": "36106", "session": "Autumn 2027", "offered": ["Autumn", "Spring"], "after": [], "unverified": false},
      {"subject_code": "36121", "session": "Autumn 2027", "offered": ["Autumn"], "after": [], "unverified": false},
      {"subject_code": "36120", "session": "Spring 2027", "offered": ["Spring"], "after": ["36106"], "unverified": false}
    ],
    "dropped": [
      {"subject_code": "43023", "subject_name": "Emerging Topics in Artificial Intelligence",
       "reason": "needs 42172 Introduction to Artificial Intelligence or 41040 Introduction to Artificial Intelligence",
       "covers": ["large language models"]}
    ],
    "outside": {
      "courses": ["EXT-HF-LLM"],
      "gaps_open_before": 2,
      "gaps_closed": 1,
      "still_open": ["tableau"],
      "demand_covered_pct": 91.5
    }
  },
  "outside_recommendations": [
    {
      "subject_code": "EXT-HF-LLM",
      "subject_name": "Hugging Face LLM Course",
      "source_url": "https://huggingface.co/learn/llm-course/chapter1/1",
      "provider": "Hugging Face",
      "cost": "free",
      "score": 1.0,
      "covers": ["large language models"],
      "evidence": [{"skill_label": "large language models", "layer": "weekly_topic",
                    "text": "1. Transformer models: Natural Language Processing and Large Language Models", "match": "named"}]
    }
  ]
}
```

| Field | Values |
|---|---|
| `mode` | The ad id for a single ad, or `role-<slug>` when the target is a role (top skills over all ads); `none` for the empty result of a role the baseline cannot stand in for |
| `status` | `have`, `partial`, `missing` |
| `ad_evidence` | The ad sentence naming the skill; in role mode, a demand sentence ("Asked for in 72% of ...") |
| `emerging` | `true` when the skill has no ESCO concept (vocab `lightcast` or `emerging`, e.g. LLMs, generative AI, agentic AI); the app flags them with ✦ |
| `found_by` | Optional: `llm` when only the GPT-4o-mini tier found the skill. The app (`backend.augment_with_llm`) keeps such a skill only when the vocabulary knows it; the rest go to `also_in_ad` |
| `score` | Subject score scaled so the best subject is 1.0 |
| `learning_path` | Greedy: repeatedly take the subject covering the most uncovered demand (`demand_pct + 1`, so 0% skills still count; `demand_pct` is a 2026 share, so skills new since 2022 need no floor), at most 3. For a role shown as core skills only (none since C2: the demand table counts the ads of all 11 roles), every gap has `demand_pct` null and weighs 1, so `learning_path.demand_covered_pct` is the share of core gaps covered |
| `demand_pct` | Share of the ads behind `demand_source` that mention the skill, from `data/2_demand/role_skill_demand.csv` (`match.demand_block`): the role's block of the first source in `jobspipe_2026` > `adzuna_2026` > `ats_2026` > `data_jobs_2023` > `seek_2019_22` that counted its ads, JobsPipe 2026 for all 11 roles today; for a pasted ad, the Data Scientist ones (71 ads). `null` for a core skill of a role with no ad counts (below) |
| `demand_pct_2026` | Share of the role's 2026 ads (`match.block_2026`: the first 2026 source in the same order); equal to `demand_pct` today. `0.0` for a skill a full-text block looked for and no ad named; `null` for a skill outside the vocabulary (GPT-only) |
| `demand_pct_2019_22` | The trend column: share of the 3,204 Seek Data Scientist ads of 2019-22 (`match.block_2019_22`, the table's count, same matcher as the 2026 ads), for Data Scientist and a pasted ad; `null` for other roles (Seek has Data Scientist titles only). Not a weight: shown as "was 0% in 2019-22" next to a 2026 share. `backend.source_2019_22` gives its caption |
| `demand_source`, `demand_period`, `total_ads`, `text_type` | The block `demand_pct` comes from, as the demand table names it: `source` (`seek_2019_22`, `jobspipe_2026`, ...), `period` (`2019-22`, `2026-10`), the number of ads (`3204`, `71`) and `text_type` (`full_text`, `tool_list`, `search_count`). For the app's caption: `backend.role_source` turns them into "71 JobsPipe Data Engineer ads, Sep-Oct 2026, full text." |
| `role` | Result level, not a skill row. Role mode: the target role, a `role` of `role_occupations.csv` (11 roles); `null` for a pasted ad |
| `also_in_ad` | Result level, only when the GPT-4o-mini tier ran: what it found in the ad that the vocabulary does not know ("Metaflow", "two-tower architectures", but also "problem framing"), in ad order. No demand count, so never a gap and never weighed by the path; the app lists them in one line under the skills |
| `core_source` | Only for a role with no ad counts in the demand table (until C2: QA/Test Engineer, DevOps/SRE, Network/Systems Administrator, Cybersecurity Analyst; none now, the fallback stays), whose skills are its core skills (`app/backend.py`, `core_skills()`): `onet` (an O*NET in-demand tool, through `onet_tool_map.csv`) or `esco` (an essential ESCO skill in ESCO's digital collection), O*NET first, at most 15; `status` is `have` or `missing`; `demand_pct_2019_22`, `demand_source`, `demand_period`, `total_ads` and `text_type` are `null` |
| `layer` | `learning_objective`, `assessment`, `weekly_topic`, `description` (strongest first) |
| `match` | `named` (the row names the skill) or `similar` (TF-IDF or embedding similarity only) |
| `needs` | Prerequisites the student has not taken yet (at most two, each open now); `[]` = can enrol now, unless `unverified` is true (no record on the access-conditions site, so "no prerequisite" is not confirmed). A recommended subject may still need them; the path adds them before it |
| `offered` | `Autumn` / `Spring` when the subject runs in them in 2026, else the periods it does run in (`Session 3`); `[]` when `offerings.csv` has no row |
| `learning_path.subjects` | In the order chosen (most demand first); a prerequisite comes right before the subject that needs it and also uses one of the three places. A prerequisite that covers no gap is in `recommendations` with `score` 0 and empty `covers` |
| `plan` | The same subjects over sessions, earliest first: each goes in the first session after its prerequisites (`after`) that teaches it, starting from the next session (`recommend(start=...)`). `unverified`: the access-conditions site has no record, so "no prerequisite" is not confirmed |
| `dropped` | Subjects that teach a gap but the student cannot take: not taught in 2026, an antirequisite, admission into another course, or prerequisites they cannot meet in time. Never in `recommendations`. `reason` is short text for the app |
| `outside` | Second tier (ideas doc 4.5): outside courses for the gaps the UTS path leaves open, chosen by the same greedy cover, at most three. `gaps_open_before` = gaps the UTS path left open; `gaps_closed` = how many of those the courses close; `demand_covered_pct` = UTS path **plus** these courses, over all gaps (the UTS-only figure stays in `learning_path.demand_covered_pct`). No UTS credit |
| `outside_recommendations` | The chosen courses first, then the next best, at most six. Same fields as a recommendation plus `provider`, `cost` (`free`, `free-to-audit`, `paid`) and `cost_aud` (the A$ price from `resources.csv`, `null` when none); no `needs` or `offered`. Read from `external_courses.csv` and `resource_modules.csv` together; a course counts for a gap only when its `skills` in `resources.csv` list it. Empty when neither file exists |

Who can enrol (`src/skillabus/requisites.py`, from `prerequisites.csv` and `offerings.csv`): an admission or
credit-point item counts as met only when its text names the student's course (C04372); a subject-code item
when the student took that subject (a corequisite may also be taken in the same session); an item the scrape
did not capture is never met. Subjects taken (`recommend(exclude=...)`, the app's "taken" box) meet
prerequisites. Antirequisites count item by item and in both directions (the site often lists a pair on
one side only). `unverified` is on each recommendation and each `plan` step. Without the two files every
subject is open and `plan` is a single session. The fallback engine (`app/baseline.py`) has no
prerequisite data: it fills `needs`, `offered` and `dropped` with empty values, `plan` with empty sessions, and `outside` with no courses.

## 3. Subject profiles: `data/1_knowledge/uts/subject_profiles.csv`

One row per piece of subject text. The 3 Oct mock with the same columns, built from the Handbook
alone (learning objectives, topics, description; no assessments), is frozen in `archive/mock_2026-10-03/`.

| Column | Example |
|---|---|
| `subject_code` | `36118` |
| `subject_name` | `Applied Natural Language Processing` |
| `course` | `C04372` |
| `layer` | `weekly_topic` |
| `text` | `Week 9: Large language models and retrieval-augmented generation` |
| `source_url` | Handbook or subject outline URL |
| `collected_by` | `Akash` |

Since 13 Oct 2026 the file holds 360 subjects in 44 UTS courses (Masters, graduate certificates and
diplomas, bachelors, honours), all four layers, 6,853 rows; `course` is pipe-joined when a subject
sits in several courses; read it with `dtype=str` (codes such as `090043`). Three companion files
share the `subject_code` key:

| File | One row = | Columns to know |
|---|---|---|
| `prerequisites.csv` | one item of a subject's access-conditions rule | `kind` requisite / antirequisite; `rule` ("(1 AND 2 AND 3)"); `item` ("1a"); `type` academic / admission / other / corequisite; `requisite_code` when the item is a subject; `evop_found` n when the site has no record of the code (then an empty rule is unverified) |
| `offerings.csv` | one teaching period × mode | `teaching_period` ("Autumn Session"), `mode` |
| `external_courses.csv` | one sentence or module of an outside course | same 7 columns as the profiles, `subject_code` = `EXT-<provider>-<slug>`, `course` = `external`, plus `provider`, `cost` (free / free-to-audit / paid), `date_checked` |

## 4. Feedback votes: `data/runtime/feedback.csv` (written by the app, not in git)

`timestamp, subject_code, skill_label, vote (up|down), has_taken_subject (y|n)`. No names.

## 5. Role demand: `data/2_demand/role_skill_demand.csv`

The one demand table (plan D6; columns and sources in `data/2_demand/README.md`, section "The demand table").
Since plan C2 `match.py` reads it with one loader (`_blocks`): a block is one role, source and period
of a counted text type (`full_text`, `tool_list`, `search_count`; `taxonomy` rows have no share).
`match.role_profile(role)` takes the 15 most-asked skills of the role's demand block that are in the
vocabulary, leaving out the Professional category (soft skills) and certifications (the role page lists
those); `match.match_role(resume_skills, role)` matches them like an ad. Each profile row's evidence reads
"Asked for in 87% of 70 JobsPipe Data Engineer ads (Sep-Oct 2026)." (SQL)

Every role, Data Scientist included, is counted on its 2026 JobsPipe ads (Quan, 16 Oct: the 2019-22 Seek
ads predate ChatGPT); Seek is only the trend column. `role_profiles.csv` (7 roles, data_jobs 2023),
`skill_counts_v2.csv`, `top_skills.csv` and `skill_counts_2026.csv` are no longer read by the pipeline; only
the fallback engine (`app/baseline.py`) still reads `skill_counts_v2.csv` and `top_skills.csv`. They move to
`archive/` later.
