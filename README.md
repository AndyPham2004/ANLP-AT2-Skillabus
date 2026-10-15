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

It works without any key: the analysis falls back to `app/baseline.py` (dictionary + keyword
match) until the stages in `src/skillabus/` are implemented, and the chat shows Handbook passages
instead of a written answer until `OPENAI_API_KEY` is set. Screens: `docs/wireframes/`. To put it
online, see [docs/deploy.md](docs/deploy.md).

## Using the app

Skillabus compares what employers ask for with what your resume shows, then points to the
UTS subjects that teach the missing skills, quoting the Handbook text it relied on.

**1. Choose a question.** The start screen offers three:

| Mode | Question it answers | What you give it |
| --- | --- | --- |
| Job seeker | What does my resume lack for this ad? | a job ad (paste it, or use the sample) and your resume |
| Elective chooser | Which subject moves me closest to my target role? | your resume and the UTS subjects you have taken |
| Career switcher | How far is my profile from a new role? | your resume |

In Elective chooser and Career switcher the target role is Data Scientist, the only option in
the role picker for now: the 15 skills most often asked for in 3,204 Seek Data Scientist ads.

**2. Add your inputs.** Upload a resume as PDF or text, or tick *Use the sample resume*
(a synthetic early-career MDSI student). The resume stays in memory for the session and is
never stored. In Elective chooser, subjects you have taken count as skills you already have.
Press **Show my gaps**.

**3. Read the results.**

- **The headline** counts the skills the role asks for that are missing or partial in your
  profile. *Partial* means your resume names a related skill (scikit-learn for machine
  learning) but not the skill itself.
- **How often employers ask for each skill**: each bar is the share of 3,204 Seek Australia
  Data Scientist ads (2019–22) naming the skill. A ✦ marks an emerging skill with no ESCO
  concept yet. LLMs and generative AI show 0% because those ads predate ChatGPT; the caption
  notes that 15.8% of 247 US Data Scientist ads in 2023–24 ask for LLMs (for Australian ads
  in 2026, see report section 3.7).
- **Your shortest path**: the fewest subjects that close the most gaps, and the share of
  employer demand behind those gaps they cover. Gaps no subject names are listed under it.
- **Why these subjects?**: pick a gap to see what the ad (or employers) said and the exact
  Handbook sentence for up to three subjects, labelled by where it came from: learning
  objective, assessment, weekly topic or description. *👍 Teaches it* / *👎 Not really*
  records whether the match is right, and *I've taken it* marks a subject you have done, so
  votes from students who took it can be told apart; the votes help us check the matcher.
- **All recommended subjects** lists every match with its score and a link to the Handbook.

**4. Ask about subjects.** The chat in the sidebar answers from the UTS Handbook 2026 text
and cites the passages it used ("Which subject teaches LLMs?"). Without an OpenAI key it
shows the matching passages instead of a written answer. Your resume is never sent to the
model.

**Good to know.** Results are suggestions, not academic advice: check prerequisites and
teaching sessions in the Handbook before enrolling. A subject "names" a skill when its
Handbook text mentions it, which says nothing about depth. Demand figures come from
Australian Data Scientist ads; other roles and the 2026 sample are described in
`docs/report/03_data.md`.

## Rebuild the poster

The AT2A poster is frozen in [`archive/poster_AT2A/`](archive/README.md) with the data behind each block; `python archive/poster_AT2A/tools/export_poster.py` rebuilds its PDF.

## Team

Quan Pham (A: story, production, submission), Van Thong (B: data, EDA),
Phuong Nhi (C: pipeline, gap chart, subject table), Hoai Thuong (D: evaluation, plan),
Akash (E: test sets, related work, user testing, ethics section).
