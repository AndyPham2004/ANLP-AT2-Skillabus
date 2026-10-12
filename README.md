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
src/        export_poster.py   HTML -> PDF + PNG with headless Chrome
            skillabus/         the pipeline: extract, normalise, match, recommend, rag, evaluate
data/       raw/               not committed; Van Thong's data-eda folder goes in raw/data-eda/
            processed/         skills_seed_v2.csv (the one dictionary), skill_counts_v2.csv,
                               top_skills.csv, gap.csv: the numbers behind poster blocks 5, 6, 7
            labels/            hand-made test sets, with column templates
            README.md          every source with a link
docs/       team_plan.md       AT2B tasks, owners, reviewers, milestones
            plan/              gantt.html and tasks_by_person.html (open in a browser)
            data_contract.md   the JSON/CSV shapes between pipeline and app
            report/            the technical report, one file per section
            handoffs/          what each teammate delivered for the poster, with figures
notebooks/  exploration only, <initials>_<topic>.ipynb
app/        Streamlit app (AT2B)
```

## Working on AT2B

Read [CONTRIBUTING.md](CONTRIBUTING.md) once (branch per task, pull request, reviewer, no raw
data or keys in git), then pick your issue on the project board. Setup:

```powershell
py -3.12 -m venv .venv; .venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env   # then paste the OpenAI key
```

## Run the app

```powershell
streamlit run app/Home.py
```

It works without any key: the analysis falls back to `app/baseline.py` (dictionary + keyword
match) until the stages in `src/skillabus/` are implemented, and the chat shows Handbook passages
instead of a written answer until `OPENAI_API_KEY` is set. Screens: `docs/wireframes/`.

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
Phuong Nhi (C: pipeline, gap chart, subject table), Hoai Thuong (D: evaluation, plan),
Akash (E: test sets, related work, user testing, ethics section).
