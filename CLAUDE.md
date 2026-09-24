# CLAUDE.md — MDSI Skills Map (36118 ANLP, AT2)

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
C = Phuong Nhi (pipeline, gap chart, subject table), D = Hoai Thuong (evaluation, plan).  Full role plan (Vietnamese) in
`docs/Ke hoach poster Skills Map.html`.

## Poster workflow (AT2A)

The poster is designed in **Claude Design**, project "Design Layout at A0"
(https://claude.ai/design/p/94418544-6e65-44c3-b0bf-5176367b5295). That project is the source of truth
for layout. This repo holds the imported copy and the export:

- `poster/poster_design.html` — plain-HTML import of `Skills Map Poster.dc.html` (x-dc wrapper and
  `support.js` removed, `@page` size added, logo path fixed).
- `python src/export_design.py` — headless Chrome export to `poster/poster_design_A0.pdf` (vector,
  1189 x 841 mm) and `poster/poster_design_preview.png`.
- To re-import after edits in Claude Design: read the project with the DesignSync tool
  (`get_file` on `Skills Map Poster.dc.html`), paste the body into `poster_design.html`, keep the head,
  re-export. Check the pipeline order stays Extract → Normalise → Match; the first design had it wrong.
- `poster/poster_template.html` + `src/build_poster.py` is the older hand-built template. Still works,
  reads `data/processed/*.csv`, but it is no longer the submitted design.
- Prompt and content pack used for Claude Design: `docs/claude_design_prompt.md` (free-form, principles
  not rules) and `docs/claude_design_brief.md` (stricter, two-stage). Poster design guides the team
  follows: `docs/guides/`.

## Where the numbers come from

Every figure on the poster traces to a teammate handoff kept in `poster/`:

- Role B, blocks 3 and 5: `Poster blocks 3 and 5 — Role B handoff.pdf`. Seek Australia 3,204 Data
  Scientist ads 2019–22 (published dataset, Seek forbids scraping), ESCO 13,960, O*NET 8,753 tools,
  UTS Handbook 70 subjects, LinkedIn US 1,355, resumes 2,484. LLM skills 0% in Seek vs 15.8% in US ads.
  Baseline: exact ESCO match covers 36% of a 133-skill dictionary, 55% have no ESCO concept.
- Role C, blocks 4, 6, 7: `MDSI_Skills_Map_Student_C_pipeline.ipynb`. One Robert Walters ad (Sydney CBD)
  vs one synthetic resume: 14 required skills, 3 covered, 11 missing. Demand axis from the Seek corpus.
  The notebook needs B's `data-eda/` folder, now at `data/raw/data-eda/` (gitignored); figures were regenerated from the
  printed outputs (`poster/figures/block*.png`, 300 dpi).
- Role D, blocks 8 and 9: `Poster_blocks_8_and_9_Role_D_handoff.html`. Test sets 200 / 50 / 30,
  weeks from 23 Sep, Python 3.11 + venv in the handoff; the repo uses Python 3.12, and the LLM is the OpenAI API (decided 25 Sep).
- `data/processed/top_skills.csv` and `gap.csv` are those numbers in the form `src/figures.py` reads.

## Status (25 Sep 2026): poster fact-checked and exported, ready to submit

Every number on `poster/poster_design.html` was re-derived from the files in
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
source file for Canvas = `poster_design_A0.pdf` + `poster_design.html` (brief allows "other files").

Still open: the Claude Design project itself was not edited (DesignSync is read-only for this
project type), so the repo copy is now ahead of it; Van Thong should confirm the exact Kaggle URL of
the PromptCloud Seek dataset for the report; the "22%" bar for principles of AI is 22.5% rounded
half-to-even, as in Student C's chart.

## Conventions

- Poster rules the team agreed: under 800 words, body text 24 pt or more, two fonts, two or three
  colours, no legends, direct labels, every chart captioned with source and n, 40% white space.
- Do not commit `data/raw/`. Small processed CSVs are fine.
- `poster/figures/uts_logo.png` is the cleaned transparent logo; `uts_logo_source.png` is the web
  original with a baked-in checkerboard, do not place it on the poster.
- Commit messages: plain summary line; end with the Co-Authored-By line the harness provides.
