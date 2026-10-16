# Hand-made test sets

To start a new set, copy its empty template from `archive/templates_2026-10/`, drop `_TEMPLATE` from the name, keep the columns exactly.
One row per item. UTF-8. Commit through a pull request like any other change.

| File | One row = | Columns to know |
|---|---|---|
| `ad_skills.csv` | one skill in one ad | `ad_id` from `jobs_au_seek_datascientist_2019-2022.csv`; `skill_label` = the `canonical` name in `data/1_knowledge/skills/skills_seed_v2.csv` when it exists, otherwise your own short name with `in_dictionary` = n; `evidence_text` = the words in the ad |
| `skill_subject_pairs.csv` | one skill-subject claim | `teaches` = y / partly / n; `layer` = learning_objective, assessment, weekly_topic, description |
| `chat_questions.csv` | one question | `reference_answer` in 1-3 sentences; `source` = where the answer comes from |
| `subject_content.csv` | one piece of subject text | `layer` as above; one row per learning objective, assessment or weekly topic. Not a test set: it feeds the subject profiles, so it and its template live in `data/1_knowledge/uts/` |
| `cv_jd_pairs.csv` | one ad skill checked against one resume | `pair_id` groups the rows of one CV-JD pair (CVJD01-CVJD50); `ad_id` as in `ad_skills.csv`; `resume_id` = the ID in the Kaggle Resume Dataset, never a name; `gold_status` = have / partial / missing; `resume_evidence_text` = the resume sentence that supports it, empty when missing |

Labelling rules for `ad_skills.csv`:
- Label skills the ad asks for, not company perks or job duties that are not skills.
- Soft skills count (communication, teamwork) but tag only when the ad names them.
- Unsure? Label it and write `?` at the start of `evidence_text`; we review those together.
- Batches of 50 ads: `ad_skills.csv` grows by PR, one PR per batch.

Labelling rules for `cv_jd_pairs.csv` (owner: Hoai Thuong, reviewer: Phuong Nhi):
- 50 pairs. Take 10 resumes from the data/IT categories and pair each with 5 ads: 2 good fits, 2 partial fits, 1 poor fit, so all three statuses occur.
- Per pair, label the ad skills that are in `skills_seed_v2.csv` (about 8 per ad). The ad skills come from `ad_skills.csv`, so label those ads first.
- `skill_label` is the `canonical` name in `skills_seed_v2.csv`, spelled exactly.
- Skip skills in the Professional category (communication, teamwork, ...); `match()` reports them separately and does not give them a status.
- `have` = the resume clearly shows the skill. `missing` = nothing in the resume supports it.
  - `partial` = the ad asks for a broad skill and the resume shows only a specific tool or method within it, e.g. ad "machine learning", resume "scikit-learn". Broad skills: machine learning, deep learning, natural language processing, cloud platforms, statistics, data visualisation, computer vision. A substitute tool (ad "Tableau", resume "Power BI") is `missing`. This is what `match()` does, so the gold labels and the system use one definition.
- `resume_evidence_text` is one short phrase or sentence copied from a single sentence of the resume, enough to see why. Never join two sentences: the score counts a hit when your words sit inside the sentence the system returns. Pick a phrase that contains no personal details (names, emails, phone numbers, addresses, employers), so it never needs `[removed]`.
- Never commit resume files. Only `resume_id` and the short evidence snippets go in the CSV.
- Unsure? Write `?` at the start of `resume_evidence_text`; we review those together.
- This file is the gold standard for matching: P@5 and MRR rank the resume sentences for each ad skill and check whether the gold evidence sentence comes first. `partial` rows count as relevant (`matching_gold(..., include_partial=False)` gives the stricter have-only score; report both).
