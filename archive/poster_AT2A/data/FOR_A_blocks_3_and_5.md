# Role B handoff — blocks 3 and 5 (and two corrections elsewhere)

Everything below is read off a file on disk. Nothing is estimated. Counts can be
re-run with `python src/source_counts.py` and `python src/extract_skills.py`.

---

## 1. Corrections to what is on the draft right now

These four are factually wrong in the current poster.html and need changing
whatever else we do.

| Where | Says now | Should say | Why |
|---|---|---|---|
| Block 3, card 3 | `~180 UTS subjects` | `70 UTS subjects` | 70 is what we actually scraped, across six courses. There are 3,107 subjects at UTS in total; 180 is not a number from anywhere. |
| Block 5 caption | "LinkedIn postings 2023–24, ESCO dictionary extraction" | "Seek Australia, Data Scientist ads 2019–2022, n = 3,204" | The chart is Australian Seek data, not LinkedIn. And our extractor is a 133-skill curated dictionary — only 36% of it maps to ESCO, so "ESCO dictionary extraction" overclaims. |
| Block 3, card 5 | `O*NET … release 29` | `O*NET 31.0 — 8,753 tool names` | We downloaded 31.0, and we use the tool list, not occupation profiles. |
| Block 3, card 6 | "Seek — Australian ads, small sample, **if site terms allow**" | see card 1 below | Seek is now our *primary* source (3,204 full-text ads) and it came from a published Kaggle dataset, not scraping. Leaving "if site terms allow" on a poster that has an ethics block invites the exact question we do not want. |

---

## 2. Block 3 — Data sources

**Figure (drop-in, 300 dpi, 9.8 × 5.0 in, sized for one A0 column at 1:1):**
`outputs/block3_sources.png`

If you would rather keep your own card markup, here are the six cards as text:

| Number | Source | One line |
|---|---|---|
| **3,204** | Seek Australia | Data Scientist ads 2019–22, full text (from 3,895 data listings) |
| **13,960** | ESCO v1.2.1 | EU skill concepts with alt-labels — the shared vocabulary |
| **8,753** | O*NET 31.0 | tool names ESCO does not cover |
| **70** | UTS Handbook | subjects across 6 courses, with learning outcomes |
| **124k** | LinkedIn US | ads scanned 2023–24: 1.1% data-titled, 3.6% demand data skills |
| **2,484** | Résumés | to build the student profile |

**Heading:** Six sources, one vocabulary

**Body (58 words):**

> **Seek Australia** — 3,204 Data Scientist ads, 2019–2022, full text: what the
> local market actually asks for. **ESCO** — 13,960 skill concepts with
> alt-labels: the shared vocabulary. **O*NET** — 8,753 tool names ESCO omits.
> **UTS Handbook** — 70 subjects across six courses, with learning outcomes.
> **LinkedIn US** — 124k ads, 2023–24, an independent market to validate against.
> **2,484 résumés** build the student profile.

**Caption:** Every count read from the downloaded file, not from a dataset description page.

**One line worth adding somewhere in block 3 or block 9** — it is our strongest
methods claim and it costs one sentence:

> Skill demand is largely global: our Australian ranking correlates **ρ = 0.819**
> with 1,355 US data roles across 100 shared skills.

---

## 3. Block 5 — What the market asks for

Two options. **Option A is less work for you.**

### Option A — keep your SVG, swap the 15 numbers

Same labels, same layout, real numbers. Measured on 3,204 Seek Australia Data
Scientist ads, 2019–2022. Re-ranked, so the bar order changes:

| # | Label | Now | **Change to** |
|---|---|---|---|
| 1 | Python | 71% | **83%** |
| 2 | Machine learning | 58% | **64%** |
| 3 | SQL | 64% | **58%** |
| 4 | Statistics | 46% | **56%** |
| 5 | Spark / big data | 27% | **31%** |
| 6 | Cloud (AWS, Azure, GCP) | 38% | **29%** |
| 7 | Communication | 44% | **28%** |
| 8 | Data visualisation | 36% | **25%** |
| 9 | Power BI / Tableau | 26% | **25%** |
| 10 | Deep learning | 29% | **21%** |
| 11 | NLP | 22% | **17%** |
| 12 | R | 20% | **12%** |
| 13 | Git | 21% | **10%** |
| 14 | Experimentation / A-B | 17% | **5%** |
| 15 | MLOps | 15% | **4%** |

Two honesty notes on that table:

- **R is under-counted at 12%.** A bare "R" matches "R&D", "R programming" and
  every stray capital R, so we only count it when it appears as "R," in a tool
  list or as "R programming". The true figure is higher. If anyone asks, say
  that — do not defend 12%.
- **Experimentation and MLOps are genuinely low** in 2019–22 Australian ads.
  That is a real finding, not a bug.

### Option B — use my chart instead

`outputs/block5_top_skills.png` — top 15 **technical** skills, professional
skills held out so the bars map onto subjects. Different labels (individual
tools, not groups): Python 83, SQL 57, Statistics 56, Spark 26, Data
visualisation 25, AWS 22, Optimisation 20, Tableau 19, Hadoop 17, NLP 17,
Deep learning 16, SAS 15, Power BI 15, Scala 15, Time series 13.

**Heading:** What Australian employers ask for

**Body (41 words):**

> Python leads at 83%, SQL 57%, statistics 56% — then a long tail where no single
> tool passes 26%. The surprise sits outside the chart: **communication appears in
> 28% of ads, more often than Tableau, AWS or Hadoop.** The market asks for a
> communicator who codes.

**Caption:** Seek Australia · Data Scientist ads 2019–2022 · n = 3,204 ·
technical skills shown; professional skills discussed in text.

---

## 4. Block 6 uses the same 15 labels

The gap chart in block 6 is the block 5 list again, split teal/copper. Whatever
you change in block 5 has to change there too, or the two charts will disagree
in front of a marker standing one metre away.

---

## 5. Say this on the poster somewhere

**The corpus is 2019–2022.** No LLM, RAG or prompt engineering appears in it.
That is our sampling window, not the Australian market. We can date the gap
precisely: LLM skills are **0.0%** in the 2019–22 Australian ads and **15.8%** in
the 2023–24 US ads. Our own 2026 live pull (n = 234) covers the current era but
is too small to chart. Stating this pre-empts the obvious question.

**Why professional skills are off the block 5 chart.** Communication, teamwork
and leadership rank 4th, 7th and 11th overall. They are real. They are held out
because they do not map to a subject, which is what the product does. That
decision is in the caption, not hidden.

---

## 6. Numbers for other blocks

**C, block 7:** AWS appears in 22% of these ads. No MDSI subject mentions AWS or
cloud. Master of AI has two that do — 42049 and 42904 — both open to an MDSI
student as free electives.

**D, block 8:** exact label matching maps 36% of our 133-skill dictionary onto
ESCO; 73 skills (55%) have no ESCO concept at all, including Docker, Kubernetes,
XGBoost, Snowflake and the whole LLM stack. That is the measured baseline a
semantic matcher has to beat.

**Ethics block:** the handbook data was collected with ~90 targeted, rate-limited
requests to the public UTS handbook, not a crawl. Both job corpora are published
Kaggle datasets — we did not scrape Seek or LinkedIn. Résumés are processed in
memory and never committed. Worth one line.
