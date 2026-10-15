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
  "sentence": "In-depth knowledge of deep learning, Generative AI and other advanced AI technologies."
}
```

| Field | Values |
|---|---|
| `skill_id` | `esco:<uri>`, `lightcast:<id>`, `emerging:<slug>` when neither vocabulary has it, or `seed:<slug>` for a dictionary skill (`skills_seed_v2.csv`) not yet linked to ESCO |
| `vocab` | `esco`, `seed` (a dictionary skill ESCO words differently), `lightcast`, `emerging` |
| `canonical` | The dictionary name (`skills_seed_v2.csv`) when the phrase is one of its aliases, else `null`; used for demand lookups. Set by `extract()` (tiers 1-2, including forms the alias list lacks, such as "REST APIs"); `normalise()` keeps it and fills it only when it is missing |
| `how` | Which normalisation step matched: `dictionary`, `esco_exact`, `esco_embed`, `lightcast`, `emerging` |
| `similarity` | Cosine to the ESCO label for `esco_embed`, else `null` |
| `kind` | LLM tier only: `hard` or `soft` |
| `method` | `dictionary`, `ner`, `llm` |
| `sentence` | The full sentence the skill came from; this is the evidence shown in the app |

## 2. The gap result: output of `match()` + `recommend()`, input of the app

```json
{
  "ad_id": "rw-2026-09-23",
  "skills": [
    {
      "skill_id": "esco:...",
      "skill_label": "machine learning",
      "status": "missing",
      "demand_pct": 72.2,
      "demand_pct_2026": 80.0,
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
      "offered": ["Spring"]
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
| `mode` | The ad id for a single ad, or `role-<slug>` when the target is a role (top skills over all ads) |
| `status` | `have`, `partial`, `missing` |
| `ad_evidence` | The ad sentence naming the skill; in role mode, a demand sentence ("Asked for in 72% of ...") |
| `emerging` | `true` when the skill has no ESCO concept (vocab `lightcast` or `emerging`, e.g. LLMs, generative AI, agentic AI); the app flags them with ✦ |
| `found_by` | Optional: `llm` when only the GPT-4o-mini tier found the skill |
| `score` | Subject score scaled so the best subject is 1.0 |
| `learning_path` | Greedy: repeatedly take the subject covering the most uncovered demand (`demand_pct + 1`, so 0% skills still count), at most 3 |
| `demand_pct` | Share of the 3,204 Seek ads 2019-22 that mention the skill (`skill_counts_v2.csv`) |
| `demand_pct_2026` | Same over the 2026 sample; `null` until that sample exists |
| `layer` | `learning_objective`, `assessment`, `weekly_topic`, `description` (strongest first) |
| `match` | `named` (the row names the skill) or `similar` (TF-IDF or embedding similarity only) |
| `needs` | Prerequisites the student has not taken yet (at most two, each open now); `[]` = can enrol now, unless `unverified` is true (no record on the access-conditions site, so "no prerequisite" is not confirmed). A recommended subject may still need them; the path adds them before it |
| `offered` | `Autumn` / `Spring` when the subject runs in them in 2026, else the periods it does run in (`Session 3`); `[]` when `offerings.csv` has no row |
| `learning_path.subjects` | In the order chosen (most demand first); a prerequisite comes right before the subject that needs it and also uses one of the three places. A prerequisite that covers no gap is in `recommendations` with `score` 0 and empty `covers` |
| `plan` | The same subjects over sessions, earliest first: each goes in the first session after its prerequisites (`after`) that teaches it, starting from the next session (`recommend(start=...)`). `unverified`: the access-conditions site has no record, so "no prerequisite" is not confirmed |
| `dropped` | Subjects that teach a gap but the student cannot take: not taught in 2026, an antirequisite, admission into another course, or prerequisites they cannot meet in time. Never in `recommendations`. `reason` is short text for the app |

| `outside` | Second tier (ideas doc 4.5): outside courses for the gaps the UTS path leaves open, chosen by the same greedy cover, at most three. `gaps_open_before` = gaps the UTS path left open; `gaps_closed` = how many of those the courses close; `demand_covered_pct` = UTS path **plus** these courses, over all gaps (the UTS-only figure stays in `learning_path.demand_covered_pct`). No UTS credit |
| `outside_recommendations` | The chosen courses first, then the next best, at most six. Same fields as a recommendation plus `provider` and `cost` (`free`, `free-to-audit`, `paid`); no `needs` or `offered`. Empty when `external_courses.csv` is missing |

Who can enrol (`src/skillabus/requisites.py`, from `prerequisites.csv` and `offerings.csv`): an admission or
credit-point item counts as met only when its text names the student's course (C04372); a subject-code item
when the student took that subject (a corequisite may also be taken in the same session); an item the scrape
did not capture is never met. Subjects taken (`recommend(exclude=...)`, the app's "taken" box) meet
prerequisites. Antirequisites count item by item and in both directions (the site often lists a pair on
one side only). `unverified` is on each recommendation and each `plan` step. Without the two files every
subject is open and `plan` is a single session. The fallback engine (`app/baseline.py`) has no
prerequisite data: it fills `needs`, `offered` and `dropped` with empty values `plan` with empty sessions, and `outside` with no courses.

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

## 5. Role profiles: `data/2_demand/role_profiles.csv`

Built by Van Thong (`data-eda/src/build_role_profiles.py`, #65) from 10,925 Australian 2023 postings
(lukebarousse/data_jobs). One row per role and skill. `match.role_profile(role)` takes the role's 15
most-asked technical skills; `match.match_role(resume_skills, role)` matches them like an ad, with
`demand_pct` = the role's own share. Data Scientist always comes from `top_skills.csv` (3,204
full-text Seek ads): the 2023 file has tool lists only, so it has no concepts such as machine learning.

| Column | Example |
|---|---|
| `role` | `Data Engineer` |
| `skill` | `Spark`: the canonical name in `skills_seed_v2.csv`; other names are skipped |
| `n_ads` | `1331`: ads naming the skill |
| `pct_ads` | `30.0`: share of the role's ads (0-100) |
| `pct_low`, `pct_high` | 95% Wilson interval |
| `total_ads` | `4438`: the role's ads with a tool list (shown as "Asked for in 30% of 4,438 Australian Data Engineer ads (2023).") |
| `category`, `source` | the dictionary category; the dataset (`lukebarousse/data_jobs (2023, Australia)`) |
