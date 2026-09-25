# Skillabus

Group project for **36118 Applied Natural Language Processing** (UTS, Spring 2026),
Assessment 2. One shared skills vocabulary for UTS subject outlines, job ads and
resumes, so a student can see which skills a target role demands that they do not
yet have, and which subject fills each gap. Poster title: *Syllabus to Seek*.

| Part | Deliverable | Due |
| --- | --- | --- |
| AT2A | Digital poster: `poster/AT2A_Poster_Skillabus_A0.pdf` + the HTML source | 26 Sep 2026 |
| AT2B | Streamlit app + technical report (`app/`, `docs/`) | 14 Oct 2026 |

## Layout

```text
poster/     AT2A_Poster_Skillabus.html         the poster (single source: layout + content)
            AT2A_Poster_Skillabus_A0.pdf       vector PDF for Canvas, 1189 x 841 mm
            AT2A_Poster_Skillabus_preview.png  quick preview
            figures/uts_logo.png
src/        export_poster.py                   HTML -> PDF + PNG with headless Chrome
data/       raw/        not committed; Van Thong's data-eda folder goes in raw/data-eda/
            processed/  skills_seed_v2.csv (the one dictionary), skill_counts_v2.csv,
                        top_skills.csv, gap.csv: the numbers behind blocks 5, 6, 7
            README.md   every source with a link
docs/       handoffs/   what each teammate delivered for the poster (B, C, D) and their figures
            Ke hoach poster Skills Map.html    team plan (Vietnamese)
            claude_design_*.md                 prompts used for the Claude Design layout
notebooks/  EDA and matching notebooks (AT2B)
app/        Streamlit app (AT2B, from 28 Sep)
```

## Rebuild the poster

```powershell
python src/export_poster.py     # writes the PDF and PNG next to the HTML
```

Edit `poster/AT2A_Poster_Skillabus.html` directly; charts are plain HTML bars whose
widths and labels come from `data/processed/`. Rules the team follows: under 800
words, body text 24 pt or more, two fonts (IBM Plex Sans, IBM Plex Serif for
quotes), two colours plus ink, direct labels, every chart captioned with source
and n.

## Team

Quan Pham (A: story, production, submission), Van Thong (B: data, EDA),
Phuong Nhi (C: pipeline, gap chart, subject table), Hoai Thuong (D: evaluation, plan).
Working notes for Claude Code sessions are in `CLAUDE.md`.
