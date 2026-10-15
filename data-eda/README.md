# Role B — Data and EDA

> **Written for the AT2A poster (22 Sep 2026).** Since 15 Oct the data lives in the repo's `data/`
> folder (the map is `data/README.md`) and `data-eda/` holds only code. `data/raw/` below is the repo's
> `data/raw/`; `config/` became `data/1_knowledge/skills/original/` and `data/2_demand/collection/`;
> `outputs/` became `data/5_crosscheck/` and `archive/poster_AT2A/data/`. The poster-only scripts
> (`source_counts.py`, `chart_top15.py`, `chart_sources.py`) are frozen in `archive/poster_AT2A/scripts/`.

Your part of the MDSI Skills Map poster (36118 AT2A). Owns poster **block 3 (Data
sources)** and **block 5 (What the market asks for)**, plus the raw data every
other lane depends on.

---

## 1. The thing to understand first

The team plan says nobody waits for anyone else's chart. That is true for A and D.
It is **not true for you and C**.

C's lane is: extract skills with the ESCO dictionary, match with TF-IDF, and build
the gap chart — poster block 6, labelled `HÌNH CHÍNH`, the single most important
figure on the poster. Every input C needs comes from you:

| C needs | You supply |
|---|---|
| ESCO skill dictionary | `data/raw/esco/` |
| Job advertisements | `data/raw/ads.csv` |
| UTS subject descriptions | `data/raw/uts_subjects.csv` |
| A sample resume | `data/raw/resumes/` |

So your deliverable order is **raw data first, your own charts second**. If you
build your pretty chart before handing C the data, C loses a day and the poster
loses its main figure.

Your charts also depend on A's style sheet, which lands on day 1. So: ship raw
data *before* the style sheet exists, build charts *after* it arrives.

---

## 2. Schedule

Poster is due **Saturday 26 September** (confirmed with the group; the team plan
document's "Friday 26/9" is a typo, and its day-of-week labels are all shifted by
one — 23/9 is a Wednesday, not Thứ Ba).

| When | What |
|---|---|
| **Tue 22 (today)** | Send C the handbook data. Request the ESCO download (email form, 5 min), register for Adzuna, start the Kaggle downloads. |
| **Wed 23** | All raw files in `data/raw/`. **Message C that the data is ready.** Run `source_counts.py`, write block 3. Sync 1 in the evening. |
| **Thu 24** | Run extraction, sanity-check the output, build the block 5 chart in A's style, drop the PNG in the shared folder before 18:00. |
| **Fri 25** | Sync 2. Cut words, verify every number against its source file, hand over. |
| **Sat 26** | Due. Submit Friday night, not Saturday — leave yourself a buffer for a broken export. |

Nothing here is a hard blocker — ESCO is an email form, not an approval queue. The
long pole is the Kaggle download size, so start it early and let it run.

---

## 3. Getting the data

### UTS Handbook — DONE, already scraped

The handbook moved. `handbook.uts.edu.au` now 301-redirects to
`coursehandbook.uts.edu.au`, a Next.js front end over the CourseLoop platform.
The CourseLoop REST API returns 403 without credentials, but every subject page is
server-rendered with its full payload in a `__NEXT_DATA__` script tag, so
`scrape_handbook.py` parses that instead of the rendered HTML.

**MDSI is course C04372.** All 11 subjects are already scraped into
`data/raw/uts_subjects.csv` with 56 learning outcomes between them, zero failures:

```bash
python src/scrape_handbook.py --course C04372 --year 2026
```

Two things to know. First, `--year current` resolves to **2027**, not 2026 — the
handbook has already rolled over, so pass `--year 2026` to match the cohort you are
actually advising. Second, the 11 codes come from the course payload and are the
core subjects; electives listed on separate structure pages are not included. If you
want more breadth, pass extra codes with `--codes`.

This is C's most important input and it is ready now. Tell C.

### ESCO — an email form, not a registration

No account needed. At `esco.ec.europa.eu/en/use-esco/download`: pick the package,
accept the privacy statement, enter an email address, and the download link is
emailed to you. Five minutes.

- Version **v1.2.1** (current, updated Dec 2025)
- Format **CSV** — not RDF/TTL, which are for semantic-web tooling you do not need
- Language **English**
- Extract with **7-Zip**, not Windows Explorer: ESCO warn that their default-Windows
  extracts can come out empty. That warning is about XML/JSON-LD so CSV will likely
  be fine, but it costs nothing to avoid.

The file you want is the skills one with `preferredLabel` and `altLabels`. The
alt-labels are the whole point — they are what collapse "use Python" and "Python
programming" into one skill. Save to `data/raw/esco/`.

### Job advertisements — the plan needs revising

I checked the Adzuna docs before building against them, and there is a problem:

> "we currently only provide a snipped of the job description in the response"

**Adzuna truncates descriptions to a snippet.** That kills my earlier suggestion of
using it as your primary source for block 5 — you would only see whatever each ad
said in its opening lines, biasing counts towards skills named early and against
skills buried in a requirements list. A skill-frequency chart built on snippets
would be quietly wrong.

So split the job by what each source is actually good for:

| Source | Use it for | Do not use it for |
|---|---|---|
| **LinkedIn postings (Kaggle)** — full text, large n | the block 5 skill-frequency chart | claiming to measure the Australian market |
| **ATS boards** — full text, Australian, small n (~22 data roles) | cross-checking the block 5 ranking on Australian text | being the primary chart |
| **Adzuna API** — Australian, truncated to exactly 500 chars | market size, employers, geography; block 3 grounding | skill counts of any kind |

Three sources each doing the one thing it is good at, with the limits stated, is a
stronger story for the technical band than one source pretending to do everything.

`fetch_adzuna.py` prints the description-length distribution on every run so you can
confirm the truncation yourself rather than taking my word for it.

On the Kaggle LinkedIn dump (~124k rows — verify the count yourself rather than
quoting the description page), one further trap: the bundled skills table holds
LinkedIn's broad *function* codes (`IT`, `SALE`, `MNFC`), **not** granular skills
like Python or SQL. You must extract from the `description` free text.

It is also US-heavy. Be upfront about this in the caption rather than hoping nobody
asks — "n = X US postings, cross-checked against Y Australian listings" is a
stronger, more honest line than an unlabelled chart, and the honesty is itself worth
marks in a subject that assesses ethics.

**Do not scrape Seek or LinkedIn.** LinkedIn's User Agreement bans automated
access. After *hiQ Labs v. LinkedIn* that is a contract breach rather than a
criminal CFAA matter, but LinkedIn enforces it with auth walls and IP bans, and a
marker reading "we scraped LinkedIn" directly above your responsible-AI block will
notice the contradiction. You also do not need to: the Kaggle dump **is** LinkedIn
data, already collected, with full text.

### ATS job boards — full-text Australian ads, no key, no ToS problem

Many employers publish vacancies through applicant tracking systems whose job
boards expose a public JSON API intended to be consumed — it is what renders their
own careers page. `fetch_ats.py` covers two:

```
Greenhouse  https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true
Lever       https://api.lever.co/v0/postings/{slug}?mode=json
```

```bash
python src/fetch_ats.py --australia-only
```

Verified working, 8 Australian employers in `data/2_demand/collection/ats_companies.csv`: **81
Australian roles, median description 6,422 characters** against Adzuna's flat 500.

**But only ~22 are data roles**, so this cannot carry block 5 either. Its job is to
*validate* the LinkedIn-derived chart on genuinely Australian full text — "our top
skills hold on an Australian sample" is a strong sentence, and it is the honest use
of an n this size.

To grow it, add slugs to `data/2_demand/collection/ats_companies.csv`. Most probes 404 (Canva and
Atlassian are not on either platform), so verify before adding:

```bash
curl -s "https://boards-api.greenhouse.io/v1/boards/SLUG/jobs" | head -c 200
```

Coverage skews to tech companies using a modern ATS, so it is not a representative
sample of the Australian labour market. Say so on the poster.

### Resumes
Kaggle "Resume Dataset" (~2.4k resumes, ~24 categories). You strictly need **one**
for C's sample profile; the full set lets you say something about resume language in
block 3.

### Worth 30 minutes: Jobs and Skills Australia
JSA publishes the **Australian Skills Classification**, the local analogue to ESCO
and O*NET. Pairing it with ESCO strengthens the "built for the Australian market"
claim, which is where block 3 earns its marks — and it partly offsets the US skew in
the LinkedIn data.

## 4. Running the pipeline

```bash
pip install -r requirements.txt
```

**Scrape the handbook** (already run once; re-run if you want more subjects):

```bash
python src/scrape_handbook.py --course C04372 --year 2026
python src/scrape_handbook.py --course C04372 --list-only   # just the codes
```

**Pull Australian ads** (needs Adzuna credentials in `ADZUNA_APP_ID` / `ADZUNA_APP_KEY`):

```bash
python src/fetch_adzuna.py --what "data scientist" "data analyst" --where Sydney --pages 5
```

**Block 3 numbers** — counts rows in everything you actually downloaded:

```bash
python archive/poster_AT2A/scripts/source_counts.py   # frozen with the poster
```

**Skill extraction** — writes `ad_skill_long.csv` (this is C's file) and `skill_counts.csv`
to `data/runtime/extract_skills/`; the poster run's copies are in `archive/poster_AT2A/data/`:

```bash
python data-eda/src/extract_skills.py --input data/raw/ads.csv --text-col description
```

Useful flags: `--filter-col location --filter-contains Australia` to restrict
geography, `--sample 5000` to iterate fast on a big file, `--id-col job_id` if
your file has a real identifier.

**Block 5 chart** — 300 dpi PNG, sized for one A0 column at 1:1:

```bash
python archive/poster_AT2A/scripts/chart_top15.py --source "LinkedIn postings 2023-24" --exclude-category Professional
```

The `--source` string is what prints in the caption, so name the corpus the counts
actually came from — the full-text one, not Adzuna.

Open the PNG and look at it. The script checks nothing about layout.

---

## 5. Sanity checks before anything goes on the poster

The extraction is dumb string matching, and dumb string matching fails in
predictable ways. Check all of these:

- **Any skill above ~85%** — almost certainly an alias over-matching.
- **A "Professional" skill in the top 3** — `communication` and `stakeholder`
  appear in boilerplate in nearly every ad. They are real, but they crowd out the
  technical skills that make your chart interesting. `--exclude-category
  Professional` is a defensible editorial choice; say so in the caption.
- **R and Go are deliberately under-counted.** Bare `R` matches `R&D`, and bare
  `Go` matches the verb, so the seed dictionary only catches them in explicit
  contexts (`R programming`, `RStudio`, `golang`). R's true share is higher than
  your chart says. Either disclose this or improve the pattern — don't quietly
  publish a number you know is low.
- **Spot-read ten ads by hand** against what the extractor found for them. Ten
  minutes, and it is the only thing that will catch a systematic error.
- **The plan's example numbers are invented.** "Python 71%, SQL 64%, cloud 38%" in
  the team plan is placeholder text. Replace all of it. Nothing invented ships.

---

## 6. Your two blocks

**Block 3 — Data sources (60 words, source cards with big numbers).**
One line per source saying *what it gives us*, not what it is. "ESCO — 13.9k
skills, the shared vocabulary everything maps onto" beats "ESCO is a European
skills taxonomy". Every number comes from `source_counts.py`, i.e. from a file on
your disk. **List nothing you did not actually load** — markers ask about the
impressive ones.

Four sources you loaded beats six you half-obtained.

**Block 5 — What the market asks for (40 words, the top-15 chart).**
Two sentences of standout numbers, then two on what surprised you. The surprise is
what makes a marker stop. Candidates: a tool nobody teaches that the market wants,
or a skill MDSI covers heavily that barely appears in ads. Either one is a better
sentence than "Python is common".

Caption must carry source and `n`.

---

## 7. Handoff checklist

To **C**, by end of Wed 23:
- [ ] `data/raw/esco/` — skills with labels and alt-labels
- [ ] `data/raw/ads.csv` — job ads, text column named, geography stated
- [x] `data/raw/uts_subjects.csv` — **done**, 11 MDSI subjects, 56 learning outcomes
- [ ] one sample resume
- [ ] `ad_skill_long.csv` (now `archive/poster_AT2A/data/`) — ad-to-skill pairs, if extraction is already running

To **A**, by 18:00 Thu 24:
- [ ] `block5_top_skills.png`, 300 dpi, A's colours, no legend, labels horizontal
- [ ] block 3 text, ≤60 words
- [ ] block 5 text, ≤40 words
- [ ] the `n` and source string for each figure caption

---

## 8. Layout

Since 15 Oct 2026 (code only here; every path comes from `src/skillabus/paths.py`):

```
data-eda/
├── src/                       collect, clean and count
│   ├── extract_skills.py      dictionary extraction; recount_recent.py and the EDA import it
│   └── external/              outside-course pages -> data/1_knowledge/learning_resources/
├── DATASETS.md                every raw file: rows, period, licence
└── HOW_TO_USE_DATA.txt        which file answers which question

data/raw/                                    your downloads go here (never committed)
data/1_knowledge/skills/original/            skills_seed.csv (133 skills), skill_to_esco.csv
data/1_knowledge/uts/subjects_template.csv   the shape C needs for handbook data
data/2_demand/collection/                    ats_companies.csv, ats_candidates.csv, probe results
data/5_crosscheck/                           counts on other platforms and markets
archive/poster_AT2A/                         the poster's outputs and scripts (block 3, block 5)
```

The dictionary the app uses is `data/1_knowledge/skills/skills_seed_v2.csv` (these 133 rows plus
later additions). Add anything the ads mention that it misses there, through a pull request.
