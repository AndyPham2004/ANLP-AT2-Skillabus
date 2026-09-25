# Skillabus (MDSI Skills Map)

Group project for **36118 Applied Natural Language Processing** (UTS, Spring 2026),
Assessment 2. One shared skills vocabulary for UTS subject outlines, job ads and
resumes, so a student can see which skills a target role demands that they do not
yet have, and which subject fills each gap.

| Part | Deliverable | Due |
|---|---|---|
| AT2A | Digital poster (this repo, `poster/`) | ~26 Sep 2026 (extended) |
| AT2B | Streamlit app + technical report (`app/`, `docs/`) | 14 Oct 2026 |

## Layout

```
poster/     poster_template.html  editable source (content + CSS, A0 landscape)
            poster.html           built page, charts inlined
            poster_A0.pdf         vector PDF for Canvas
            poster_preview.png    quick preview
            figures/              standalone SVG charts
src/        figures.py            chart builders (read data/processed, else sample values)
            build_poster.py       assemble poster.html, export PDF + PNG with headless Chrome
data/       raw/ (not committed), processed/ small CSVs the poster reads, README.md with sources
notebooks/  EDA and matching notebooks (produce data/processed/*.csv)
docs/       team plan (Vietnamese), report drafts
app/        AT2B Streamlit app (from 28 Sep)
```

## Build the poster

```powershell
# from the repo root, any Python 3.10+ works (no third-party packages needed)
python src/build_poster.py          # writes poster/poster.html, poster_A0.pdf, poster_preview.png
python src/build_poster.py --no-pdf # HTML only
```

Charts fall back to illustrative sample values until `data/processed/top_skills.csv`
and `data/processed/gap.csv` exist (formats in `data/README.md`). While they do, the
poster carries a "Draft" tag in the top-right corner; it disappears automatically
once real data is in place.

To edit text: change `poster/poster_template.html`, rebuild. Keep the whole poster
under 800 words, body text at 24 pt or more, two fonts, two colours plus ink.

## Team

Quan Pham and three teammates (roles A–D in `docs/Ke hoach poster Skills Map.html`).
