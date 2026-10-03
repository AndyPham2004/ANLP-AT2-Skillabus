# Hand-made test sets

Copy the `_TEMPLATE.csv` file, drop `_TEMPLATE` from the name, keep the columns exactly.
One row per item. UTF-8. Commit through a pull request like any other change.

| File | One row = | Columns to know |
|---|---|---|
| `ad_skills.csv` | one skill in one ad | `ad_id` from `jobs_au_seek_datascientist_2019-2022.csv`; `skill_label` = the `canonical` name in `data/processed/skills_seed_v2.csv` when it exists, otherwise your own short name with `in_dictionary` = n; `evidence_text` = the words in the ad |
| `skill_subject_pairs.csv` | one skill-subject claim | `teaches` = y / partly / n; `layer` = learning_objective, assessment, weekly_topic, description |
| `chat_questions.csv` | one question | `reference_answer` in 1-3 sentences; `source` = where the answer comes from |
| `subject_content.csv` | one piece of subject text | `layer` as above; one row per learning objective, assessment or weekly topic |

Labelling rules for `ad_skills.csv`:
- Label skills the ad asks for, not company perks or job duties that are not skills.
- Soft skills count (communication, teamwork) but tag only when the ad names them.
- Unsure? Label it and write `?` at the start of `evidence_text`; we review those together.
- Batches of 50 ads: `ad_skills.csv` grows by PR, one PR per batch.