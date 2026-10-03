# CLAUDE.md — Skillabus, formerly MDSI Skills Map (36118 ANLP, AT2)

Notes for Claude Code sessions in this repo. Keep this file short; long material goes in `docs/`.

## What this is

Group project, UTS Master of Data Science and Innovation, Spring 2026. One skills vocabulary (ESCO)
for subject outlines, job ads and resumes, so a student sees which skills a target role demands that
they lack and which subject fills each gap. Details and layout in `README.md`.

| Part | Deliverable | Due |
|---|---|---|
| AT2A | A0 landscape poster, PDF + source file on Canvas | 26 Sep 2026 |
| AT2B | Streamlit app + technical report | 14 Oct 2026 |

## Team and roles

Quan Pham is the user (role A: story, production, submission). Teammates: Van Thong, Phuong Nhi,
Hoai Thuong. Role letters confirmed by Quan on 25 Sep: B = Van Thong (data, EDA),
C = Phuong Nhi (pipeline, gap chart, subject table), D = Hoai Thuong (evaluation, plan).
E = Akash (added by the lecturer, joined 26 Sep; surname to confirm): test-set labelling and the
ethics/limitations section of the report. Deliberately off the critical path: 200 Seek ads tagged
with skills, 30 skill-subject pairs checked against the Handbook, 30 chat questions with reference
answers, all due 6 Oct so Hoai Thuong can score in weeks 2-3; if late, the test sets shrink, nothing
else waits.  Full role plan (Vietnamese) in
`docs/Ke hoach poster Skills Map.html`.

## Poster workflow (AT2A)

The poster is designed in **Claude Design**, project "Design Layout at A0"
(https://claude.ai/design/p/94418544-6e65-44c3-b0bf-5176367b5295). That project is the source of truth
for layout. This repo holds the imported copy and the export:

- `poster/AT2A_Poster_Skillabus.html` — plain-HTML import of `Skills Map Poster.dc.html` (x-dc wrapper and
  `support.js` removed, `@page` size added, logo path fixed).
- `python src/export_poster.py` — headless Chrome export to `poster/AT2A_Poster_Skillabus_A0.pdf`
  (vector, 1189 x 841 mm) and `poster/AT2A_Poster_Skillabus_preview.png`.
- To re-import after edits in Claude Design: read the project with the DesignSync tool
  (`get_file` on `Skills Map Poster.dc.html`), paste the body into `AT2A_Poster_Skillabus.html`, keep the head,
  re-export. Check the pipeline order stays Extract → Normalise → Match; the first design had it wrong.
- The older hand-built template (`poster_template.html`, `src/build_poster.py`, `src/figures.py`) was
  deleted on 25 Sep; git history has it.
- Prompt and content pack used for Claude Design: `docs/claude_design_prompt.md` (free-form, principles
  not rules) and `docs/claude_design_brief.md` (stricter, two-stage). Poster design guides the team
  follows: `docs/guides/`.

## Where the numbers come from

Every figure on the poster traces to a teammate handoff kept in `docs/handoffs/`:

- Role B, blocks 3 and 5: `Role_B_blocks_3_and_5_Van_Thong.pdf`. Seek Australia 3,204 Data
  Scientist ads 2019–22 (published dataset, Seek forbids scraping), ESCO 13,960, O*NET 8,753 tools,
  UTS Handbook 70 subjects, LinkedIn US 1,355, resumes 2,484. LLM skills 0% in Seek vs 15.8% in US ads.
  Baseline: exact ESCO match covers 36% of a 133-skill dictionary, 55% have no ESCO concept.
- Role C, blocks 4, 6, 7: `Role_C_pipeline_Phuong_Nhi.ipynb`. One Robert Walters ad (Sydney CBD)
  vs one synthetic resume: 14 required skills, 3 covered, 11 missing. Demand axis from the Seek corpus.
  The notebook needs B's `data-eda/` folder, now at `data/raw/data-eda/` (gitignored); figures were regenerated from the
  printed outputs (`docs/handoffs/figures/block*.png`, 300 dpi).
- Role D, blocks 8 and 9: `Role_D_blocks_8_and_9_Hoai_Thuong.html`. Test sets 200 / 50 / 30,
  weeks from 23 Sep, Python 3.11 + venv in the handoff; the repo uses Python 3.12, and the LLM is the OpenAI API (decided 25 Sep).
- `data/processed/skills_seed_v2.csv`, `skill_counts_v2.csv`, `top_skills.csv` and `gap.csv` are the
  numbers actually on the poster (see the one-dictionary note below).

## Status (25 Sep 2026): poster fact-checked and exported, ready to submit

Every number on `poster/AT2A_Poster_Skillabus.html` was re-derived from the files in
`data/raw/data-eda/` (Van Thong's folder, copied from `C:\MDSI.Big Data Engineering\Assignment2\data-eda`,
gitignored): Seek 3,204; ESCO `skills_en.csv` 13,960 rows (the ESCO site quotes 13,939 for v1.2;
we cite the file); O*NET 31.0 unique tool names 8,753; UTS 70 subjects, 19 MDSI; LinkedIn 1,355 data
roles, of which 247 Data Scientist-titled ads carry the US comparison (LLMs 39/247 = 15.8%);
resumes 2,484 in 24 categories; ESCO baseline 48/133 = 36% mapped, 73/133 = 55% absent; gap chart
percentages recomputed identically; top-15 chart matches `outputs/skill_counts_PRIMARY.csv`.
No ESCO concept contains "generative" or "large language model" (API search, 25 Sep).

Resolved on 25 Sep: pipeline order (already correct in the repo copy); technical-setup line added to
block 9; block 6 now lists machine learning → 36120, principles of AI → 36121, data models → 94693,
cloud → 42904 (Student C's keyword matcher re-run over `uts_subjects_2026.csv`; SLO wording checked
against the Handbook); block 1 ad quote is now verbatim from the ad text in the notebook; references
cover every source; word count 798 (hard ceiling 800; team target 550 was not reachable with the
plan the brief demands); LLM = OpenAI API, GPT-4o-mini; B/C/D name mapping confirmed by Quan;
source file for Canvas = `AT2A_Poster_Skillabus_A0.pdf` + `AT2A_Poster_Skillabus.html` (brief allows "other files").

Rubric pass (25 Sep, evening): expected-outcome sentence added to block 2; block 8 gained a
"Subject ranking" row (keyword → embeddings, P@3 on 30 hand-checked pairs) so block 6 is no longer
unevaluated; block 3 says what the 2,484 resumes are for (parsing test set, the 50 CV–JD pairs);
column 3 re-spaced (block 8 at 460 mm, block 9 at 650 mm).

Renamed 25 Sep: app = **Skillabus**, poster title = **Syllabus to Seek** (GitHub repo renamed to
`ANLP-AT2-Skillabus`; the old URL redirects). Layout opened up the same day: section cards removed,
only the hero (block 5) stays boxed, per the Penn State "limit boxes and lines" rule.

One dictionary for the whole poster (25 Sep, Quan's decision after Van Thong asked why blocks 5
and 7 disagreed). B's 133-alias dictionary had no generic "machine learning", "AI", "cloud" or
"predictive modelling" row, so those were absent from block 7; C's block 5 matched ESCO labels plus
synonyms and a char-n-gram fuzzy step, which produced false positives ("cloud technologies" from
"AI technologies") and six 0% ESCO phrasings. Fix: `data/processed/skills_seed_v2.csv` = B's 133
rows + 5 generic rows (Machine learning, Artificial intelligence, Predictive modelling, Generative
AI, Cloud platforms). Every chart now runs on it:
- block 7 top-15 recounted (`data/processed/skill_counts_v2.csv`, `top_skills.csv`): machine
  learning 72%, predictive modelling 30%, cloud platforms 25%, AI 22% enter; SAS, Power BI,
  Scala, time series drop out. Percentages use Python's `.0f` rounding like B's chart.
- block 5 hero (`gap.csv`): the Robert Walters ad yields 10 skills, 8 technical (Python, SQL
  have; machine learning, predictive modelling, AI, deep learning, LLMs, generative AI missing);
  teamwork and problem solving are named in the caption, not drawn, as in block 7.
- block 6: machine learning + predictive → 36120, AI → 36121, deep learning → 94691 Deep
  Learning (MDSI; 42028 scores higher but sits in C04379), generative AI / LLMs → no learning
  objective in any of the 70 subjects (36118 mentions LLMs only in its description).
- block 8 baseline recomputed on 138 rows: 50 exact ESCO matches (36%), 74 absent (54%).
Van Thong's and Phuong Nhi's original figures stay in `docs/handoffs/`.

Still open: the Claude Design project itself was not edited (DesignSync is read-only for this
project type), so the repo copy is now ahead of it; Van Thong should confirm the exact Kaggle URL of
the PromptCloud Seek dataset for the report; the "22%" bar for principles of AI is 22.5% rounded
half-to-even, as in Student C's chart.

## AT2B (from 3 Oct 2026)

Poster marked: 27/35 problem/innovation, 30/35 technical. Marker wants the innovation stated, richer
subject data than Handbook learning objectives (36118 does teach LLMs), method justification,
emerging-skill handling, validation of subject recommendations, error analysis. Plan, owners and
milestones: `docs/team_plan.md`; app/pipeline shapes: `docs/data_contract.md`; team rules:
`CONTRIBUTING.md`. Quan owns UI/app, fresh 2026 data, report intro/innovation, submission.
Van Thong already has 2026 AU ads in `data/raw/data-eda/data/raw/jobs_au_ats_2026.csv` (234, full
text) and `jobs_au_adzuna_2026.csv` (50, truncated to 500 chars); several Kaggle "2026" sets were
rejected as synthetic (see `DATASETS.md` there).

## Conventions

- Poster rules the team agreed: under 800 words, body text 24 pt or more, two fonts, two or three
  colours, no legends, direct labels, every chart captioned with source and n, 40% white space.
- Do not commit `data/raw/`. Small processed CSVs are fine.
- `poster/figures/uts_logo.png` is the cleaned transparent logo (the checkerboard web original was deleted).
- Commit messages: plain summary line; end with the Co-Authored-By line the harness provides.
