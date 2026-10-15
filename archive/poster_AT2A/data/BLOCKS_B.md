# Role B — poster copy

Two blocks, both inside the word budget from the team plan. Every figure is a
300 dpi PNG sized for one A0 column at 1:1.

---

## Block 3 — Data sources

**Figure:** `outputs/block3_sources.png` (6 cards, 9.8 × 5.0 in)

**Heading:** Six sources, one vocabulary

**Body (58 words):**

> **Seek Australia** — 3,204 Data Scientist ads, 2019–2022, full text: what the
> local market actually asks for.
> **ESCO** — 13,960 skill concepts with alt-labels: the shared vocabulary.
> **O*NET** — 8,753 tool names ESCO omits.
> **UTS Handbook** — 70 subjects across six courses, scraped with learning outcomes.
> **2023 Australian corpus** — 12,955 roles, independently collected, to check our
> ranking holds.
> **2,484 resumes** build the student profile.

**Caption:** Every count read from the downloaded file, not a dataset description page.

---

## Block 5 — What the market asks for

**Figure:** `outputs/block5_top_skills.png` (top 15, 9.8 × 7.0 in)

**Heading:** What Australian employers ask for

**Body (41 words):**

> Python leads at 83%, SQL 57%, statistics 56% — then a long tail where no single
> tool passes 26%.
> The surprise sits outside the chart: **communication appears in 28% of ads, more
> often than Tableau, AWS or Hadoop.** The market asks for a communicator who codes.

**Caption:** Seek Australia · Data Scientist ads 2019–2022 · n = 3,204 ·
technical skills shown; professional skills discussed in text.

---

## Notes for A (layout) and D (evaluation)

**Say this on the poster.** The corpus is 2019–2022, so no LLM, RAG or prompt
engineering appears. That is the sampling window, not the Australian market. Our
2026 pull (n=234) covers the current era but is too small to chart.

**Why professional skills are off the chart.** Communication, teamwork and
leadership rank 4th, 7th and 11th overall. They are real, not noise — but they
crowd out the technical skills that map to subjects, which is what the product
does. The decision is stated in the caption rather than hidden.

**Two numbers D can use in block 8.** Exact label matching maps 36% of our
133-skill dictionary onto ESCO; 73 skills (55%) have no ESCO concept at all,
including Docker, Kubernetes, XGBoost, Snowflake and the entire LLM stack. That is
the measured baseline a semantic matcher has to beat.

**One number C can use in block 7.** AWS appears in 22% of these ads. No MDSI
subject mentions AWS or cloud. Master of AI has two — 42049 and 42904 — both open
to an MDSI student as free electives.
