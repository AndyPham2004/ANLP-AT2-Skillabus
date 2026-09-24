# Claude Design brief — MDSI Skills Map poster (AT2A)

How to use this file, in three steps:

1. Open Claude Design, start a new design, and attach the five PNG files from `poster/figures/`:
   `block3_sources.png`, `block4_pipeline.png`, `block5_top_skills.png`, `block6_gap_chart.png`, `block7_course_table.png`.
2. Paste **Prompt 1** (layout only). Check the reading order and column widths before any text goes in.
3. Paste **Prompt 2** together with the whole **Content pack** below it. Then iterate with the short follow-up prompts at the end.

Everything below the line is written for Claude Design, in English, because the poster is in English.

---

## Prompt 1 — layout skeleton (send first, no content yet)

```
Design a research poster for a university assessment. Do not write any body text yet; build the layout skeleton only.

CANVAS
- A0 landscape, 1189 x 841 mm (at 96 px/in that is 4494 x 3179 px). Single artboard. Everything must fit; nothing may overflow the sheet.
- Margins 26 mm top, 30 mm left and right, 24 mm bottom.

STRUCTURE
- A full-width title band across the top: title on the left (about 70% of the width), a course block on the right with a short italic "one-sentence summary" under it. A 1.2 mm ink rule closes the band.
- Below it, four columns. Widths in ratio 1 : 1 : 1.28 : 1.05, gutters 26 mm. The third column is the widest because it holds the key figure.
- Reading order is top-left to bottom-right, column by column. No arrows; the order must be obvious from position alone.
- Reserve these numbered blocks, in this order:
  Column 1: [1] The problem, [2] Users and goals, [10] Ethics + References (small, at the bottom).
  Column 2: [3] Data, [4] Pipeline.
  Column 3: [5] What the market asks for, [6] Preliminary result (the KEY figure, largest element after the title; give it a soft white card background).
  Column 4: [7] Which subject fills each gap, [8] Evaluation plan, [9] Plan to 14 October.
- Each block heading has a small number, then the heading, with a thin teal rule above.
- Leave about 40% of the sheet as white space. Do not box every block; separate blocks with rules and spacing only.

TYPE (poster viewing distance is 3 metres)
- Two fonts only. Headings and labels: Archivo (fallback Arial). Body: Source Serif 4 (fallback Georgia).
- Title 128 pt, weight 800, tight line-height 0.96. Author line 40 pt. Block headings 46 pt. Body text 26 pt (never under 24 pt). Captions 20 pt. Table text 22 pt.
- Sentence case everywhere. No all-caps titles.

COLOUR
- Paper background #F8F7F3. Ink #1B2530. Muted text #5B5A55. Hairlines #D8D7D0.
- Teal #0F6E68 = "have" / market. Copper #B8541F = "missing" / gap. Use copper sparingly, only where something is missing or is a comparison branch.
- No red, no bright yellow, no gradients, no drop shadows.

FIGURES
- Use placeholder frames for now: block 3 (wide, 2:1), block 4 (wide, 8:3), block 5 (tall, 3:2), block 6 (wide, 16:9, the biggest figure), block 7 (wide, 3:2), block 8 (table), block 9 (Gantt strip, three columns).
- Every figure will get a caption directly beneath it, 20 pt muted, with the data source and n.

Show me the skeleton with block numbers and headings only, so I can check proportions before we add content.
```

## Prompt 2 — fill the content (send with the Content pack pasted underneath)

```
Now fill the skeleton with the content pack below. Rules:

- Use the text exactly as written; do not paraphrase, do not add sentences, do not add a legend to any chart. If a block does not fit, tell me which lines to cut instead of shrinking the type below the minimums.
- Replace the placeholder frames with the attached PNGs: block3_sources.png, block4_pipeline.png, block5_top_skills.png, block6_gap_chart.png, block7_course_table.png. Place each at a width that keeps its text at 20 pt or larger on the sheet. Block 6 is the hero: make it the widest figure on the poster.
- Build block 8 as a real table and block 9 as a real Gantt strip in the design, using the same teal and copper. Direct labels only.
- Highlight the shared skill phrase inside the two quotes in block 1 with a soft teal wash (#DCEFEC) behind the words.
- Keep total word count under 550. Report the count when done.
- When finished, list any place where text had to wrap awkwardly or a figure had to be scaled below the size that keeps its labels readable at 20 pt.
```

---

# Content pack

## Block 0 — Title band

Title (11 words): **Skills Map: closing the gap between your degree and the job ad**
Colour "your degree" in teal.

Authors: Quan Pham, Van Thong, Phuong Nhi, Hoai Thuong
Affiliation: Master of Data Science and Innovation, University of Technology Sydney
Course block, right side: **36118 Applied NLP** / Assessment 2A, group poster, Spring 2026
Small UTS logo, top right, above the course block (attach separately; leave a 40 x 40 mm placeholder if none).

One-sentence summary (italic, teal left rule):
We put subject outlines, job ads and resumes into one skills vocabulary, so a student can see exactly which skills a role needs that they lack, and which subject fills each gap.

## Block 1 — The problem

Lede (28 pt):
Subject outlines speak academic. Job ads speak industry. Nothing maps one to the other, so students guess which electives to take and what to put on a resume.

Quote 1 (teal rule):
"Implement and evaluate advanced **machine learning** techniques to real-world problems."
Source line: UTS Handbook, 36120 Advanced Machine Learning Application, learning outcome

Quote 2 (copper rule):
"Experience in building and deploying **AI models** and solutions. In-depth knowledge of deep learning, Generative AI and other advanced AI technologies; LLM, GenAI etc."
Source line: Robert Walters, Data Scientist, Sydney CBD, September 2026

Closing sentence:
Same skill, different words, and only the ad asks for generative AI, a phrase ESCO has no concept for yet. The app makes that difference visible, taking the teaching team's study-planner idea from the timetable to the job market.

## Block 2 — Users and goals

Three users, three columns (sans, 22 pt, bold name on top):
- **Elective chooser** — Which subject moves me closest to the role I want?
- **Job seeker** — What does my resume lack for this ad?
- **Career switcher** — How far is my profile from a new role?

Five features, bullet list:
- Upload a resume, or tick the subjects you have taken
- Pick a target role and city
- See your skill gap ranked by demand
- Get electives ranked by how much gap they close
- Ask a chat that answers from real ads

## Block 3 — Data

Heading: **Six sources, one vocabulary**
Figure: block3_sources.png (six tiles with big numbers). If you rebuild the tiles natively, the numbers are:

| Big number | Source | Sub-line |
|---|---|---|
| 3,204 | Seek Australia | Data Scientist ads, 2019–2022, full text |
| 13,960 | ESCO v1.2.1 | EU skill concepts with alt-labels |
| 8,753 | O*NET 31.0 | tool names ESCO does not cover |
| 70 | UTS Handbook | subjects across 6 courses |
| 1,355 | LinkedIn US | 2023–24, full text: cross-market check |
| 2,484 | Resumes | to build the student profile |

Body (58 words):
Seek Australia — 3,204 Data Scientist ads, 2019–2022, full text: what the local market actually asks for. ESCO — 13,960 skill concepts with alt-labels: the shared vocabulary. O*NET — 8,753 tool names ESCO omits. UTS Handbook — 70 subjects across six courses, scraped with learning outcomes. LinkedIn US — 1,355 data roles, 2023–24, full text: the cross-market check. 2,484 resumes build the student profile.

Caption: Every count read from the downloaded file, not a dataset description page.

## Block 4 — Pipeline

Heading: **Pipeline**
Figure: block4_pipeline.png (six boxes: Input → Clean → Extract skills → Normalise → Match → Output; copper boxes are the stages compared method-against-method).

Six one-line labels if rebuilt natively:
1. **Input** — resume, job ad or subject outline
2. **Clean** — lowercase, strip boilerplate, split sentences
3. **Extract skills** (copper) — ESCO dictionary now; spaCy NER and LLM compared in Part B
4. **Normalise** (copper) — map aliases to one ESCO id, so "ML" and "machine learning" agree
5. **Match** (grey) — TF-IDF cosine now, versus sentence embeddings in Part B
6. **Output** — gap chart, ranked subjects, RAG chat over ads

Caption: Copper stages are where a traditional and a newer method run side by side and are scored (block 8).

## Block 5 — What the market asks for

Heading: **What Australian employers ask for**
Figure: block5_top_skills.png (top 15 skills, horizontal bars, teal, direct labels).

Body (40 words):
Python leads at 83%, SQL 57%, statistics 56% — then a long tail where no tool passes 26%. The surprise sits off the chart: communication appears in 28% of ads, more often than Tableau, AWS or Hadoop.

Caption (must keep both facts):
Seek Australia · Data Scientist ads 2019–2022 · n = 3,204 · technical skills shown, professional skills discussed in text. No LLM skill appears because the ads predate 2023: large language models sit at 0% here and at 15.8% in 1,355 US ads from 2023–24.

## Block 6 — Preliminary result (KEY FIGURE)

Heading: **Preliminary result: one profile against one role**
Figure: block6_gap_chart.png. Teal bars = the resume already has the skill, copper = missing. Bar length = share of the 3,204 Seek ads that mention the skill.

Three big numbers under the chart (60 pt, sans):
- **14** skills the ad demands
- **3** covered (teal)
- **11** missing (copper)

Body (55 words):
One real Data Scientist ad, Sydney CBD, against a sample early-career resume: 3 of 14 required skills covered, 11 missing. The biggest gaps by market demand are machine learning (71% of ads), predictive models (25%) and AI principles (22%): modelling, not tooling. Six required skills are ESCO phrasings no ad uses, so they are counted but not drawn.

Caption: Skills extracted with the ESCO dictionary plus TF-IDF fuzzy matching · demand from n = 3,204 Seek Australia ads · resume is synthetic, not a real person.

## Block 7 — Which subject fills each gap

Heading: **Which UTS subject fills each gap**
Figure: block7_course_table.png, or rebuild as a four-row table:

| Missing skill | Best matching subject | Matched learning outcome |
|---|---|---|
| Predictive models | 36120 Advanced Machine Learning Application | Implement and evaluate advanced machine learning techniques to real-world problems |
| Cloud technologies | 42904 Cloud Computing and Software as a Service | Articulate the need for cloud computing and its elements |
| Data models | 94693 Big Data Engineering | Data modelling, big data, distributed processing and streaming |
| Analytical calculations | 36103 Statistical Thinking for Data Science | Formulate precise inquiries and justify the statistical tools used |

Caption: Keyword match between each missing ESCO skill and the learning outcomes of 70 UTS subjects; Part B replaces it with embedding similarity. 42904 sits outside MDSI but is open as an elective.

## Block 8 — Evaluation plan

Heading: **How we will measure each stage: traditional vs. modern**

Table:

| Task | Methods compared | Metric | Test set (size) |
|---|---|---|---|
| Skill extraction | ESCO dictionary → spaCy NER → LLM (API) | Precision / Recall / F1 | Hand-labelled LinkedIn ads (200) |
| Skill matching | TF-IDF cosine → sentence embeddings | Precision@5, MRR | Team-labelled CV–JD pairs (50) |
| Chat / Q&A (RAG) | Keyword search → LLM + FAISS retrieval | LLM-as-judge, relevance and faithfulness 1–5 | Curated user questions (30) |

Body (60 words):
Each pipeline stage pits a traditional baseline against a modern method. Extraction is scored by F1; matching, a ranking task, by Precision@5; open-ended chat by an LLM-as-judge. A measured baseline already justifies the comparison: exact ESCO matching covers only 36% of our 133-skill dictionary, and 55% — including the whole LLM stack — have no ESCO concept at all.

Caption: Baseline from the data EDA (133-skill dictionary vs ESCO); all metrics on held-out labelled data with test-set n shown per task.

## Block 9 — Plan to 14 October

Heading: **Three-week plan, owners named, technical setup**

Gantt strip, three week columns. A bar spanning the weeks marked, owner name inside the bar (teal bars; the report row copper):

| Task | Owner | W1 23–29 Sep | W2 30 Sep–6 Oct | W3 7–14 Oct |
|---|---|---|---|---|
| Data collection and cleaning | Van Thong | ████ | ██ | |
| Skill extraction (dictionary → NER → LLM) | Phuong Nhi | ██ | ████ | |
| Matching (TF-IDF → embeddings) | Phuong Nhi | | ████ | ██ |
| Evaluation and benchmarking | Hoai Thuong | | ██ | ████ |
| Streamlit app and RAG chat | Quan Pham | | ██ | ████ |
| Report writing | All | | ██ | ████ |

Milestones line under the strip: 7 Oct pipeline end-to-end (feature freeze) · 11 Oct app and evaluation done · 14 Oct Part B due.

Technical setup (22 pt, bold labels):
**Repo / env** GitHub AndyPham2004/ANLP-AT2-Skills-Map, branch per member · Python 3.11, venv, requirements.txt
**Extraction** ESCO dictionary · spaCy NER · LLM API
**Matching** scikit-learn TF-IDF · sentence-transformers · FAISS
**Chat** LLM API + FAISS retrieval (RAG)
**Frontend** Streamlit, deployed on Streamlit Cloud or Hugging Face Spaces
**Privacy** resumes processed in memory · PII masked before any API call

## Block 10 — Ethics and references (small, bottom of column 1)

Ethics (22 pt):
Resumes stay in memory, never on disk. Names, emails and phone numbers are masked before any LLM call. Ads are used under the dataset licence. Results are labelled as suggestions, not career advice.

References (19 pt, muted):
- European Commission (2024). ESCO v1.2.1 skills taxonomy.
- Seek Australia Data Scientist job ads 2019–2022, published dataset (citation to be supplied by Van Thong).
- Reimers, N. and Gurevych, I. (2019). Sentence-BERT. EMNLP.
- Lewis, P. et al. (2020). Retrieval-augmented generation for knowledge-intensive NLP. NeurIPS.

---

## Follow-up prompts for iteration

- "Count the words on the poster and list the three longest blocks." (target under 550)
- "Show me the poster at 25% zoom. Which block would a stranger read first, second, third?" (checks reading order)
- "Increase white space in column 2; block 3 and 4 may shrink their figures to 80%."
- "Export as PDF at true A0 size, 1189 x 841 mm, no margins, fonts embedded." Then also export the design source file for Canvas.

## Still open before export

- Role letters to names: assumed B = Van Thong, C = Phuong Nhi, D = Hoai Thuong. Swap if wrong.
- LLM provider in block 9: "LLM API" as Role D drafted; write "OpenAI API" once the team confirms.
- UTS logo file.
- Citation for the Seek dataset, from Van Thong.
