# subject_profiles.csv

Four-layer subject profiles, the thing `recommend()` matches a missing skill against
and `retrieve()` indexes for the chat. Shape is `docs/data_contract.md` section 3.

| | |
|---|---|
| Rows | 6,853 |
| Subjects | 360, in 44 UTS courses; 19 are MDSI (`C04372`), 276 rows |
| Built by | `python data-eda/src/build_subject_profiles.py` |
| Source | `data-eda/data/raw/uts_subjects_2026.csv` (not committed), UTS Handbook 2026, scraped 13 Oct 2026; assessment tasks from the handbook's per-offering data route (`data-eda/src/scrape_assessments.py`) |
| Owner | Van Thong (data); the 13 Oct rebuild by Quan's session |
| Built | 13 Oct 2026 (first build 8 Oct, 70 subjects, 1,039 rows; every one of those rows is still here) |

## Rows per layer

| Layer | Rows | Subjects | From |
|---|---|---|---|
| `learning_objective` | 1,516 | 354 | `learning_outcomes`, split on `SLO<n>:`, trailing `(CILO ...)` removed, "TBC" placeholders dropped |
| `assessment` | 1,015 | 326 | `selected_assessment` of the first two offerings: "name (type, weight%, group/individual). description", with the subject's AI-use policy sentences removed (see below) |
| `weekly_topic` | 2,769 | 327 | `topics`, split on `\|`, `•`, `;`, or on "(1) ... (2) ..." numbering |
| `description` | 1,553 | 360 | `description`, one sentence per row |

## Courses

Masters: C04372 MDSI, C04370 Executive MDSI, C04379/C04380/C04467 Business Analytics, C04295/C04296
Information Technology, C04373 Quantitative Finance, C04443 Artificial Intelligence, C04256 AI (Online),
C04430/C04431 Cybersecurity, C04434/C04435 Technology Management, C04450 Technology Innovation, C04265
Science (Extension), C04277 Engineering (Extension). Graduate diplomas: C06113 IT, C06124 Data Science
and Innovation, C06147 AI. Graduate certificates: C11142, C11247 IT, C11191 AI, C11274 Data Science and
Innovation, C11280/C11385 Business Analytics, C11308 Quantitative Finance, C11329 Health Analytics,
C11339 AI Management, C11340 Cybersecurity Management, C11350 Data Visualisation and Storytelling, C11376
Applied AI for Finance. Bachelors: C10148/C10143 Information Technology, C10474 AI, C10476 Computing
Science, C10471 Cybersecurity, C10457 Mathematical Sciences, C10395 Information Systems, C10229 Games
Development, C10242 Science, C10347 Advanced Science; honours C09019 IT, C09119 Computing Science,
C09129 Mathematical Sciences, C09168 Science, C09066 Engineering.

Course codes were found by probing every handbook course page in C04000-C04500, C06000-C06300,
C09000-C09200, C10000-C10600 and C11000-C11400 (250 courses exist; the data/IT/AI/maths/analytics
ones above were scraped). Double degrees (with Law, Business, International Studies) share their
subjects with the single degree and were not scraped separately. **Bachelor subjects (C10/C09) are
for prospective students and for the "does UTS teach this anywhere?" question; MDSI students usually
cannot enrol in them**, so the app tags them.

## Read it like this

```python
profiles = pd.read_csv("data/processed/subject_profiles.csv", dtype=str)   # dtype=str: 090043 is a code
mdsi = profiles[profiles.course.str.contains("C04372", na=False)]          # contains, not ==
```

Three traps:

1. **`course` is pipe-separated** (`"C04372|C04379|C11274|C06124"`) because a subject can belong to
   several courses. Use `.str.contains()`, never `==`.
2. **This file has no `#` comment line, on purpose.** `skills_seed_v2.csv` has one, and because that
   file also contains a literal `C#`, reading it with `pandas.read_csv(..., comment="#")` silently
   truncates the C# row. Provenance lives here instead so the CSV stays a plain CSV.
3. **Read with `dtype=str`.** Six-digit codes with a leading zero (`090043`) become integers otherwise
   and no longer match `prerequisites.csv` or `offerings.csv`.

## Companion files (13 Oct 2026)

| File | Rows | What |
|---|---|---|
| `prerequisites.csv` | 2,571 (360 subjects; 290 with a requisite rule; 172 with anti-requisites, 301 rows, re-scraped 14 Oct after the parser fix) | One row per item of the access-conditions rule: `kind` (requisite / antirequisite), `rule` ("(1 AND 2 AND 3)"), `item`, `type` (academic, admission, other, corequisite), `requisite_code`, `requisite_text`, `evop_found` (n for 47 subjects the access-conditions site has no record of: an empty rule there is unverified). 36118 needs 36100, 36103, 36106; 43023 needs 42172 or 41040, which MDSI does not offer; 139 academic items point at codes outside the 360. From `data-eda/src/scrape_requisites.py`. |
| `offerings.csv` | 510 (330 subjects) | `teaching_period` × `mode` per subject (94691 Autumn only, 36120 Spring only). 30 subjects have no offering listed for 2026. |
| `assessments_scraped.csv` | 1,015 (326 subjects) | The assessment layer before merging; `collected_by = "script (handbook)"`. |

## The assessment layer

Until 13 Oct it was empty: the subject page shows no assessment until an availability is chosen.
Choosing one makes the browser fetch `/_next/data/<buildId>/subject/2026/<code>.json?offering=...`,
which answers without cookies and carries `selected_assessment` (name, type, weight, group or
individual; sometimes a description). The task names are concrete where the handbook prose is not:
94693 Big Data Engineering has "Data lake with Snowflake", "Data processing with Spark", "Data
pipelines with Airflow"; 94691 Deep Learning has "Building Neural Network Architectures".

34 subjects have no task list in the handbook, among them MDSI's 36124, 36125 and 94689 (research
and special subjects). Hand-collected rows can still be added through `data/labels/subject_content.csv`
(`layer = assessment`); the build merges both files.

**AI-use policy is not content.** 30 task descriptions mention generative AI, and 29 of them state
the subject's policy ("students may use generative AI tools for grammar checking", "No GenAI"), so by
keyword 32547 UNIX Systems Programming "taught" generative AI. `build_subject_profiles.drop_ai_policy`
removes a sentence when it names AI tools and uses policy wording (permit, allow, must not, may use,
guidelines, usage ...). The one sentence kept, in 32130, asks students to use GenAI in the task.
Checked 13 Oct by an independent pass over all 30 rows.

## Known gaps in the source data

| Gap | Subjects |
|---|---|
| No learning objectives | 35002, 36124, 36125, 40011, 40012, 94689 |
| No topic list (33) | includes MDSI 36106, 36126, 36127, 94689, 94691, 94692, 94699 |
| Topic list arrived with no delimiters, kept whole (23) | includes 32040, 36104, 42050, 43024 (42904's "(1) ... (9)" list is split) |
| No 2026 offering listed (30) | see `offerings.csv` |

Worth knowing:

- **36124, 36125 and 94689 have description text only.** Two are MDSI electives (Applied and
  Advanced Data Science for Innovation): they rank low against any skill purely because there is
  less text to match, a retrieval artefact, not "these subjects teach less".
- **36106 Machine Learning Algorithms and Applications has no topic list** but now has five
  learning objectives and three assessment tasks ("Regression models", "Building and Interpreting a
  classification model", "End-end Data Science Project"), so it is matchable.
- The handbook caps out at roughly 200-250 words per subject even with four layers; the teaching
  materials themselves (slides, notebooks) are the only richer source (ideas doc 4.3 item 1).

## Cleaning applied

- **Encoding repaired.** The handbook serves UTF-8 that was read as a single-byte codec somewhere
  upstream, so punctuation arrives as `â\x80\x99` and friends, in descriptions and in assessment
  descriptions alike. The script replaces each known sequence (quotes, dashes, hyphens, zero-width
  and no-break spaces); an independent check on 13 Oct found zero left. Assessment descriptions
  also arrive HTML-escaped (`&#39;`); they are unescaped.
- **Rows keep the handbook's order** within a layer (SLO1 first, task 1 first); the file is sorted
  by subject and layer only.
- **CILO codes stripped** from learning objectives; **run-together sentences split**; **prose that
  leaked into the topics field** sentence-split; duplicate `(subject_code, layer, text)` rows dropped.

## What this changes on the poster

Block 6 said *"generative AI, LLMs: no learning objective in any of the 70 subjects"*. With four
layers over 360 subjects: 36118 and 43023 carry "Large Language Models" as a weekly topic, 32130
teaches generative AI in the data pipeline, and the assessment layer names the tools (Snowflake,
Spark, Airflow, neural network architectures). The gap that survives is narrower: prompt
engineering, RAG and the transformer toolchain still return no hits in any handbook text. UTS
teaches *about* LLMs; it does not yet teach the LLM toolchain the 2026 ads ask for.
