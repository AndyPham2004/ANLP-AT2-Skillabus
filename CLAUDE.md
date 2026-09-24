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
Hoai Thuong. Role letters assumed from the order given on 24 Sep: B = Van Thong (data, EDA),
C = Phuong Nhi (pipeline, gap chart, subject table), D = Hoai Thuong (evaluation, plan). Confirm the
mapping before the final export; it only affects names in the Gantt. Full role plan (Vietnamese) in
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
  The notebook needs B's `data-eda/` folder, which is not in this repo; figures were regenerated from the
  printed outputs (`poster/figures/block*.png`, 300 dpi).
- Role D, blocks 8 and 9: `Poster_blocks_8_and_9_Role_D_handoff.html`. Test sets 200 / 50 / 30,
  weeks from 23 Sep, Python 3.11 + venv, "LLM API" (provider not yet chosen).
- `data/processed/top_skills.csv` and `gap.csv` are those numbers in the form `src/figures.py` reads.

## Open items before submission (as of 24 Sep 2026)

1. Fix pipeline order in the Claude Design project (Extract → Normalise → Match).
2. Block 9 lost the technical-setup line (repo, Python 3.11, spaCy, scikit-learn, sentence-transformers,
   FAISS, Streamlit, LLM API). It is a marking criterion; add it back.
3. Block 6 has no subject for the two biggest gaps (machine learning 71%, principles of AI 22%) and
   uses a 0%-demand skill instead. Ask Phuong Nhi to run the matcher for those two.
4. Block 1 quote from the Robert Walters ad is paraphrased inside quote marks; use the exact wording.
5. References: add O*NET, LinkedIn US, Resume Dataset, UTS Handbook; get the Seek dataset citation from
   Van Thong.
6. Word count is 743; team budget is 550, hard ceiling 800.
7. Decide LLM provider (API vs Ollama) and confirm the B/C/D name mapping.
8. Brief asks for a PowerPoint or Canva source file. The current source is HTML; either export from
   Claude Design or build a PPTX before submitting.

## Conventions

- Poster rules the team agreed: under 800 words, body text 24 pt or more, two fonts, two or three
  colours, no legends, direct labels, every chart captioned with source and n, 40% white space.
- Do not commit `data/raw/`. Small processed CSVs are fine.
- `poster/figures/uts_logo.png` is the cleaned transparent logo; `uts_logo_source.png` is the web
  original with a baked-in checkerboard, do not place it on the poster.
- Commit messages: plain summary line; end with the Co-Authored-By line the harness provides.
