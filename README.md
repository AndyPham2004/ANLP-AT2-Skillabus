# Skillabus

Group project for **36118 Applied Natural Language Processing** (UTS, Spring 2026),
Assessment 2. One shared skills vocabulary for UTS subject outlines, job ads and
resumes, so a student can see which skills a target role demands that they do not
yet have, and which subject fills each gap. Poster title: *Syllabus to Seek*.

| Part | Deliverable | Due |
| --- | --- | --- |
| AT2A | Digital poster: `archive/poster_AT2A/poster/AT2A_Poster_Skillabus_A0.pdf` + the HTML source | 26 Sep 2026 |
| AT2B | Streamlit app + technical report (`app/`, `docs/`) | 17 Oct 2026 |

## Layout

```text
app/        Streamlit app (AT2B); app/mock/ holds only the sample ad and resume
src/        skillabus/         the pipeline: extract, normalise, match, recommend, rag, evaluate;
                               paths.py declares every path the code uses
            make_qr.py         QR code for the deployed app (docs/deploy.md)
tests/      pytest, with small fixtures
data/       1_knowledge/       what the app looks up: skill dictionary, ESCO, UTS subjects, outside courses
            2_demand/          what employers ask for: skill counts, role profiles, cleaned ads
            3_tuning/          which threshold was set on which data
            4_evaluation/      test labels, the inputs they were made on, results, the GPT cache
            5_crosscheck/      other platforms and markets, ESCO coverage
            raw/, runtime/     not committed: downloads; votes, caches and indexes the app writes
            README.md          the map (every file, who made it, how to rebuild it) and every source
data-eda/   Van Thong's scripts that collect and clean the data (code only)
notebooks/  exploration, <initials>_<topic>.ipynb; vt_eda is the EDA
docs/       team_plan.md       AT2B tasks, owners, reviewers, milestones
            data_contract.md   the JSON/CSV shapes between pipeline and app
            deploy.md          putting the app on Streamlit Community Cloud
            report/            the technical report, one file per section
            figures/           the EDA figures the report uses
            notes/             working notes and plans (gantt.html, tasks_by_person.html: open in a browser)
archive/    frozen: the AT2A poster with its data and handoffs, the 3 Oct mock (archive/README.md)
```

Only `data/` holds data, and every path the code uses comes from `src/skillabus/paths.py`.

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

It works without any key: the pipeline in `src/skillabus/` runs on the dictionary tiers (and falls
back to `app/baseline.py` if a stage fails); with `OPENAI_API_KEY` set, the GPT-4o-mini tier adds
the skills the dictionary does not know and the chat writes answers instead of quoting passages.
The look and flow follow the Claude Design prototype kept in `docs/design/` (dark theme, Literata
and Public Sans). To put it online, see [docs/deploy.md](docs/deploy.md).

## Using the app

Skillabus compares what employers ask for with what your resume shows, then points to the
UTS subjects that teach the missing skills, quoting the Handbook text it relied on. The sidebar
shows the three steps and opens the Handbook chat.

**1. Who you are.** Three cards:

| Card | Question it answers | What you give it |
| --- | --- | --- |
| UTS student | Which elective moves me closest to the job I want? | a target role and the UTS subjects you have taken |
| Job seeker | What does my resume lack for this ad? | a job ad (browse 160 Australian ads from 2024-26, paste one, or try the sample) and your resume |
| Career switcher | How far am I from a new field? | a target role and your resume |

**2. Your inputs.** Say where you are in your studies (about to enrol, studying MDSI, already
working, and your course: it decides which subjects count as open to you). Pick one of 11 data and
IT roles: each comes with the 15 skills most often asked for in its JobsPipe ads of 2026. Upload a
resume as PDF or text, paste it, or use the sample (a synthetic early-career MDSI student); it stays
in memory for the session and is never stored. Press **Find my gaps**.

**3. Results.** One line says how many of the skills you still have to learn and names the
biggest gaps. Below it, one section at a time: Skills, Your path, Outside UTS and, in the role
modes, Certifications.

- **Skills the ad (or role) asks for**: one row per skill with a bar for how often the 2026 ads ask
  for it (hover for the 2019-22 share; hatched = a skill the older ads never named) and its status:
  have, partial (your resume names a related skill, not this one) or missing. A ✦ marks an emerging
  skill with no ESCO concept yet.
  *Show where these appear in the ad* colours the skills on the ad text.
- **Your path**: the fewest subjects that close the most gaps, each with its session, the gaps it
  closes and whether it needs a prerequisite first. Tick *Already taken* on a subject (or *What if I
  had taken …*) and the gaps and the path are recomputed.
- **Outside UTS**: free or low-cost courses for the gaps the UTS path leaves open; not for credit.
- **Click a skill** to see what the ad said, what your resume said, the UTS subjects that teach it
  with the exact Handbook sentence (labelled learning objective, assessment, weekly topic or
  description), 👍 / 👎 to say whether the match is right, and self-study resources filtered by
  level and cost. Click a subject name for its sessions, prerequisites, the gaps it closes and the
  Handbook link. A line under the skill rows names the ads behind the bars.

**4. Ask the Handbook.** The button in the sidebar opens a chat that answers from the UTS
Handbook 2026 text and cites the passages it used ("Which subject teaches LLMs?"). Without an
OpenAI key it shows the matching passages instead of a written answer. Your resume is never sent
to the model.

**Good to know.** Results are suggestions, not academic advice: check prerequisites and
teaching sessions in the Handbook before enrolling. A subject "names" a skill when its
Handbook text mentions it, which says nothing about depth. Demand figures come from
Australian ads per role; the sources and the 2026 sample are described in
`docs/report/03_data.md`.

## Rebuild the poster

The AT2A poster is frozen in [`archive/poster_AT2A/`](archive/README.md) with the data behind each block; `python archive/poster_AT2A/tools/export_poster.py` rebuilds its PDF.

## Team

Quan Pham (A: story, production, submission), Van Thong (B: data, EDA),
Phuong Nhi (C: pipeline, gap chart, subject table), Hoai Thuong (D: evaluation, plan),
Akash (E: test sets, related work, user testing, ethics section).
