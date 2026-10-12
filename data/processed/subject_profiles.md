# subject_profiles.csv

Four-layer subject profiles, the thing `recommend()` matches a missing skill against
and `retrieve()` indexes for the chat. Shape is `docs/data_contract.md` section 3.

| | |
|---|---|
| Rows | 1,039 |
| Subjects | 70, of which 19 are MDSI (`C04372`) with 242 rows |
| Built by | `python data-eda/src/build_subject_profiles.py` |
| Source | `data-eda/data/raw/uts_subjects_2026.csv` (not committed), UTS Handbook 2026, collected 25 Sep 2026 |
| Owner | Van Thong |
| Built | 8 Oct 2026 |

## Rows per layer

| Layer | Rows | Subjects | From |
|---|---|---|---|
| `learning_objective` | 289 | 67 | `learning_outcomes`, split on `SLO<n>:`, trailing `(CILO ...)` removed |
| `assessment` | **0** | 0 | **not collected yet** — see below |
| `weekly_topic` | 444 | 58 | `topics`, split on `\|`, `•`, `;` |
| `description` | 306 | 70 | `description`, one sentence per row |

## Read it like this

```python
profiles = pd.read_csv("data/processed/subject_profiles.csv")       # no comment= needed
mdsi = profiles[profiles.course.str.contains("C04372", na=False)]   # contains, not ==
```

Two traps:

1. **`course` is pipe-separated** (`"C04380|C04379"`) because a subject can belong to
   several courses, and the contract's "one row per piece of subject text" rule forbids
   repeating the same sentence once per course. Use `.str.contains()`, never `==`.
2. **This file has no `#` comment line, on purpose.** `skills_seed_v2.csv` has one, and
   because that file also contains a literal `C#`, reading it with
   `pandas.read_csv(..., comment="#")` silently truncates the C# row to `C` with no
   aliases. Provenance lives here instead so the CSV stays a plain CSV.

## The assessment layer is empty

It is hand-collected, not scrapable: the assessment table is on
`coursehandbook.uts.edu.au`, whose `robots.txt` is `User-agent: * / Disallow: /`, so it
is out of bounds for an automated fetch. A person reading the pages in a browser is
fine, which is why the team plan assigns it to Akash (due 6 Oct) as a manual task.

To add it: put the rows in `data/labels/subject_content.csv` with `layer = assessment`,
following `data/labels/subject_content_TEMPLATE.csv`, then re-run the script. It merges
them in automatically — no code change.

Until then matching runs on three layers, and the report has to say so.

## Known gaps in the source data

These are holes in the handbook collection, not bugs in the build. All of them are in
the script's output every run.

| Gap | Subjects |
|---|---|
| No learning objectives | 36124, 36125, 94689 |
| No topic list | 36106, 36124, 36125, 36126, 36127, 43030, 49016, 94689, 94691, 94692, 94699, 95563 |
| Topic list arrived with no delimiters, kept whole | 32040, 32558, 36104, 42050, 42904, 43024 |

Worth knowing:

- **36124, 36125 and 94689 have description text only.** Two of them are MDSI electives
  (Applied and Advanced Data Science for Innovation), so they will rank low against any
  skill purely because there is less text to match. That is a retrieval artefact, and
  the evaluation should not read it as "these subjects teach less".
- **36106 Machine Learning Algorithms and Applications has no topic list** — an MDSI
  core subject, and the obvious match for the biggest gap on the poster (machine
  learning, 72% of ads). It still has five learning objectives, so it is matchable.
- The six no-delimiter subjects lost their `<li>` markup during collection. Splitting on
  capital letters would shred phrases like "Natural Language Processing", so the whole
  string is kept as one row. They are longer than a good evidence snippet.

## Cleaning applied

- **Encoding repaired.** The handbook was served UTF-8 and read as a single-byte codec,
  so 40 punctuation marks across 13 subjects arrived as `â\x80\x99` and friends. The
  usual whole-string round-trip does not fix it (part of the damage is no longer valid
  UTF-8), so the script replaces each known sequence. Zero remain.
- **CILO codes stripped** from learning objectives: `(CILO 2.2, 2.3)` is course-level
  mapping, not subject content, and it pollutes an embedding.
- **Sentences run together are split.** Some handbook prose has no space after the full
  stop (`solutions.This simulates`), so the splitter does not require whitespace.
- **Prose that leaked into the topics field** (a delimited topic over 200 characters) is
  sentence-split, so the evidence panel has something quotable.
- Duplicate `(subject_code, layer, text)` rows dropped: 0 found.

## What this changes on the poster

Block 6 says *"generative AI, LLMs — no learning objective in any of the 70 subjects.
36118 Applied NLP mentions LLMs only in its description."* With four layers that is
wrong in one direction and right in another:

- **36118 has "Large Language Models (LLMs)" as a weekly topic**, not just a description
  mention. 43023 has it as a weekly topic too. This is the marker's own point: the
  handbook learning objectives miss what the subject actually teaches.
- **But the gap survives, and sharpens.** Across all 70 subjects and all three layers:
  prompt engineering, RAG and transformers/BERT/GPT return **zero hits**. Generative AI
  appears once, inside a 32130 topic entry, in a non-MDSI subject.

So the honest claim for the report is narrower and stronger than the poster's: UTS
teaches *about* LLMs, and does not yet teach the LLM toolchain the 2026 ads ask for.
