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
| `canonical` | The dictionary name (`skills_seed_v2.csv`) when the phrase is one of its aliases, else `null`; used for demand lookups |
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
         "text": "Implement and evaluate advanced machine learning techniques ..."}
      ]
    }
  ],
  "learning_path": {
    "subjects": ["36120", "94691"],
    "gaps_closed": 4,
    "gaps_total": 6,
    "demand_covered_pct": 78.0
  }
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

## 3. Subject profiles: `data/processed/subject_profiles.csv`

One row per piece of subject text. Until Van Thong's file lands, `app/mock/subject_layers.csv`
has the same columns built from the Handbook alone (learning objectives, topics, description;
no assessments yet), by `app/mock/build_mock.py`.

| Column | Example |
|---|---|
| `subject_code` | `36118` |
| `subject_name` | `Applied Natural Language Processing` |
| `course` | `C04372` |
| `layer` | `weekly_topic` |
| `text` | `Week 9: Large language models and retrieval-augmented generation` |
| `source_url` | Handbook or subject outline URL |
| `collected_by` | `Akash` |

## 4. Feedback votes: `data/processed/feedback.csv` (written by the app)

`timestamp, subject_code, skill_label, vote (up|down), has_taken_subject (y|n)`. No names.
