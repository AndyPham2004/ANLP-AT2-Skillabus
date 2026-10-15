# 4 Methods

> Draft by Phuong Nhi, 15 Oct 2026, rewritten around the technical frame (ideas doc, section 7). **[eval]** = number
> from section 6. **[Quan]** / **[Van Thong]** = please check the sentence about your stage. Code: `src/skillabus/`.
> Every threshold below was set on text that is not in a test set.

Each stage pairs a traditional method with a newer one, both run on the same inputs, so section 6 can show what the newer
method adds and where it fails. Table 4.1 is the frame; the subsections give the reasons and the failure cases.

**Table 4.1** Traditional and newer method per stage.

| Stage | Traditional | Newer | Measured on | Typical failure of the newer method | Why we keep it |
|---|---|---|---|---|---|
| Extraction | Dictionary lookup (148 skills) | + spaCy rules, + GPT-4o-mini | 20 labelled ads, P/R/F1 | spaCy: candidates that are not skills ("Social Club") | Finds plurals and tools outside the dictionary |
| Normalisation | ESCO exact label + aliases | + fuzzy string, + MiniLM embedding, "emerging" label | 211 non-dictionary phrases, hand-judged | "data extraction" → ESCO *information extraction* | Maps paraphrases; keeps skills ESCO lacks |
| Emerging skills | Added to the dictionary by hand | n-grams → spaCy → GPT, weighted log-odds | Hand-judged top 20 per method | Boilerplate that rises with career-site ads | Finds new terms (*agentic workflows*) without a person noticing first |
| Matching | Exact skill identity | + umbrella rule for "partial" | 45 CV–JD pairs, accuracy, macro F1 | — (rule-based) | Credits part of a broad skill |
| Subject evidence | Keyword (alias) match | + TF-IDF, + sentence embeddings | Skill–subject pairs, P@3 | Generic sentences ("key concepts and algorithms") | Finds subjects that teach a skill without naming it |
| Learning path | Top subject per gap | Greedy cover with prerequisites, sessions, outside courses | Demand closed by the path | A prerequisite chain longer than two subjects | Fewest subjects, ones the student can enrol in |

## 4.1 Skill extraction

**Text units.** Ads and resumes are mostly bullet lists, where statistical sentence splitters fail. A rule-based splitter
treats each bullet or line as a unit, rejoins hard-wrapped lines and splits prose after `.`, `!` and `?`. Every tier
uses it, so a skill carries the same evidence sentence whichever tier found it.

**Tier 1, dictionary (traditional).** We match the aliases of `skills_seed_v2.csv` (148 skills since 14 Oct: Van Thong's
133, five generic rows, ten tools for the role profiles of section 4.6). Only aliases are matched, never the display
name, because the dictionary leaves out ambiguous bare forms ("R", "Go", "RAG"). Skills marked `strict` (R, SAS, SAP,
React) are case-sensitive; the longest alias wins ("SQL Server" does not also give "SQL"); character lookarounds replace
`\b`, which fails on "C++", "C#" and ".NET". On the Robert Walters ad, tier 1 reproduces the eight technical skills of
the poster's gap chart.

**Tier 2, spaCy (`en_core_web_sm`).** The pretrained NER model has no skill label (it tagged Python and Tableau as places),
and training one would need labelled ads beyond our test set. Tier 2 therefore keeps tier 1's hits and uses the tagger
and parser for three rules: drop a one-word alias used as a finite verb ("*spark* new ideas", keeping gerunds such as
"forecasting demand"); fold plural nouns before a second lookup ("REST APIs", "data warehouses"); and propose phrases
outside the dictionary from noun chunks after a cue ("experience with", "such as") and from PRODUCT entities.

**Tier 3, GPT-4o-mini [Quan].** A fixed prompt asks for skills as JSON at temperature 0. A returned skill must occur
verbatim in the text and its evidence sentence is cut from the text, so the model cannot invent skills or quotes.
Contact details are masked before the call, and responses are cached, so the evaluation re-runs at no cost.

On the 20 labelled ads, tier 2 adds recall for little precision on dictionary skills (F1 0.780 → 0.799 with the current
dictionary, #56 table of 15 Oct). Its new candidates are the weak point: of 211 distinct non-dictionary phrases it
proposed on test and 2026 ads, 69 (33%) are not skills at all: employers ("Canva", "Bankwest"), perks ("Volunteer Days"),
job titles ("Product Managers") and one recruiter's name. Section 4.2 measures normalisation on these same phrases.

## 4.2 Normalisation

Each mention passes five steps, first hit wins: the dictionary, an exact ESCO label (preferred or alternative, after
dropping filler such as "skills" or "knowledge of"), the nearest ESCO label by MiniLM embedding (cosine ≥ 0.82), the
Lightcast Open Skills API, and an explicit "emerging" class **[Quan]**. Generative AI and large language models skip the
ESCO steps: ESCO v1.2.1 has no concept for them. Since c3d1ca4, dictionary skills keep their own id, so normalisation
only decides what the non-dictionary phrases are.

**Error analysis.** We ran three mappers side by side on the 211 phrases (`notebooks/pn_normalisation_errors.py`) and
judged every answer by hand (`data/4_evaluation/results/normalisation_errors.csv`, judgements in `exact_ok`,
`fuzzy_ok`, `embed_ok`, `error_type`). The 2026 phrases come from the 22 full-text ads, from 8 employers, of the 10 Oct sample
(738726c), not the 22 in-sample roles of sections 4.3 and 4.4; the script rebuilds the table from that file with `--ads`. A string-similarity mapper (difflib ratio ≥ 0.85) stands in for the fuzzy matching the frame
lists as the middle option. Lightcast was not run (no API key), so every phrase it might have mapped is in "emerging".

**Table 4.2** Mapping 211 non-dictionary phrases to ESCO.

| | Exact label | Fuzzy string (≥ 0.85) | Embedding (≥ 0.82) |
|---|---|---|---|
| Phrases mapped | 12 | 24 | 14 |
| Right concept | 12 | 12 | 10 |
| Precision | 1.00 | 0.50 | 0.71 |
| Mapped beyond exact | — | 13, of which 1 right | 5, of which 1 right |

Exact matching is never wrong but maps only 12 of the 142 real skills. Fuzzy matching doubles that by matching letters,
not meaning: gRPC became *gel permeation chromatography*, ECS *European Train Control System*, Canva *Canvas* (a learning
management system). The embedding is right more often, and its errors are of a subtler kind: "service-oriented
architecture" → *service-oriented modelling* is right, but "data extraction" → *information extraction* moves an ETL step
into NLP, and "customer analytics" → *marketing analytics* and "accessibility guidelines" → *develop strategies for
accessibility* are a broader concept. With the exact column built as the pipeline's exact step (filler words dropped), the embedding answers 5 phrases beyond
it and 1 is right (service-oriented architecture): its true gain is 1 phrase out of 142, and these are exactly the 5
phrases it answers in the pipeline. 58 of these phrases come from the test ads, so the threshold stays as set on 4 Oct and is not
changed on these results.

The final answers, by error type: 125 right (of which 110 correctly left "emerging"), 69 not a skill (an extraction error,
not a normalisation one), 14 missed, 2 too broad, 1 wrong sense. The 14 misses are mostly spans with an extra word that
hides an ESCO concept ("clear communication", "especially mathematics", "data analytics workflows") and two just under
the threshold ("market reporting", 0.80; "Compliance", 0.798). The "emerging" class is doing its job: ESCO has no concept for DuckDB,
Langfuse, RLHF or Claude Code, and forcing them onto the nearest label (DuckDB → *breed ducks*, 0.56) would be
worse than keeping them unmapped.

## 4.3 Emerging-skill detection

Large language models and generative AI are found today only because we added them to the dictionary by hand. To find the
next ones automatically, `skillabus.emerging` proposes phrases three ways, from traditional to newer (n-grams of 1–3
words; the spaCy tier-2 candidates; the GPT tier-3 skills) and scores all three the same way, so the comparison is about
what each method proposes. A phrase is counted in an ad only in a requirement line (a sentence that names a dictionary
skill): on whole ads, the benefits and hiring sections of company career sites, which the 2019–22 Seek ads lack, made
almost any word look new. Rise is the weighted log-odds of the 2026 ads against the 3,204 Seek ads with an informative
Dirichlet prior (Monroe, Colaresi & Quinn, 2008), with pseudo-counts floored at 0.5 so a phrase absent before 2023 is not
penalised for its zero (without the floor, 3 of 22 ads against 0 of 3,204 scored z = 1.0). A candidate must have z ≥ 1.96,
appear in at least 3 ads from at least 2 employers (so one employer's boilerplate cannot qualify), and be neither a dictionary
alias nor an ESCO label. A short, hand-made list of career-site words ("thrive", "hiring") is removed; it was made from the
n-gram output, not from a test set.

On the 22 in-sample 2026 roles from 12 employers (#87), n-grams surface *workflows, using ai, ai capabilities, product
engineering* and *agentic*, but most of their top 50 is still career-site prose (*fostering, modern, genuine*); spaCy keeps
five phrases, two of them absent from every 2019–22 ad (*agentic workflows*, *Claude*), because most tools it finds appear
in a single ad. With the 122 LinkedIn ads of January 2024 added (144 ads), spaCy finds tool names (Fivetran, Matillion,
Glue, Flink, NiFi, KServe, Seldon), but that sample is mostly data engineers, so a change of role mix is mixed with a
change over time. Precision@20 of each method, judged by hand, is in section 6 **[eval]**; the GPT tier is **[Quan]**.

## 4.4 Matching: have, partial, missing

A skill the ad asks for is **have** when the resume names the same dictionary skill and **missing** when nothing in the
resume supports it. A shared ESCO id counts only for skills outside the dictionary: several dictionary skills map to one
broad ESCO concept (PyTorch and matplotlib), so naming one must not count as having the other. It is **partial** when the
ad asks for the umbrella skill of a category (machine learning, deep learning, NLP, cloud, statistics, data
visualisation, computer vision) and the resume shows a part of it (scikit-learn for machine learning). Programming
languages never count as partial, and professional skills are reported separately.

We also tested counting close substitutes (Tableau and Power BI) as partial by the embedding similarity of the two names.
Across the 652 same-category pairs, true substitutes scored lower than unrelated pairs (Tableau–Power BI 0.30, AWS–Azure
0.44, Airflow–MLflow 0.54), so no threshold separates them and the rule was dropped.

**Demand.** A gap is weighted by its share of the 3,204 Seek Data Scientist ads (2019–22) + 1. Skills under 1% before
2023 (large language models) use the lower end of the 95% Wilson interval of their 2026 share instead, over all 22 data
roles of the 2026 sample from 12 employers (9 of them data scientists; `pct_2026_all_low`), since a share of 9 moves 11
points per ad. Skills already asked for keep their 2019–22 share, because the 2026 sample over-represents AI work.

## 4.5 Subject evidence: keyword → TF-IDF → embeddings

Subject profiles hold one row per learning objective, assessment, weekly topic or description sentence: 6,853 rows for 360
subjects in 44 UTS courses **[Van Thong]**. A row is evidence for a skill when it names it (aliases) or is similar enough:
TF-IDF (unigrams and bigrams, cosine ≥ 0.35) as the traditional baseline, `all-MiniLM-L6-v2` sentence embeddings
(cosine ≥ 0.55) as the newer method. The embedding threshold was set by reading the closest non-naming rows on 429
Handbook rows: at 0.55 the kept rows were mostly real paraphrases TF-IDF scored near zero ("Classification and
prediction" for machine learning), while TF-IDF's extra matches shared misleading words ("Machine Translation" for machine
learning). We rechecked the threshold on 15 Oct with 12 IT skills outside the test pairs (Java to Data security) over all
6,853 rows (`data/3_tuning/t1_it_unnamed_rows.csv`, 55 closest non-naming rows judged by hand): all 7 rows at
or above 0.55 were right, against 17 of the 19 judged at 0.50. All 7 are Data security rows from cybersecurity subjects;
for the other 11 skills no row reaches 0.55. Tool names such as Kubernetes or Terraform never get there, because the Handbook describes concepts ("Automating Your Infrastructure"), so IT tools are found almost only when a
row names them. Two failures show why we did not lower it: "CI/CD" lands on *Computational Intelligence* (an acronym
clash) and Java on object-oriented programming in general. We kept 0.55. The deployed app runs TF-IDF (no PyTorch on the
free host); section 6 reports both.

A row's score is its similarity (1.0 when it names the skill) times its layer weight (learning objective 1.0, assessment
0.9, weekly topic 0.8, description 0.5). A subject's strength is its best row, +0.15 per further row (at most three),
+0.40 when its name names the skill, +0.10 for an MDSI subject; it covers the skill only at 60% of the strongest subject's
strength. This separates 94691 *Deep Learning* from a subject with one weekly topic on it.

## 4.6 Learning path

**UTS subjects.** Choosing at most three subjects that close the most demand is a maximum coverage problem; the greedy
algorithm repeatedly takes the subject that closes the most uncovered demand (Nemhauser, Wolsey & Fisher, 1978). Since
14 Oct a subject counts only if the student can enrol in it (`requisites.py`, from the scraped access conditions):
admission and credit-point conditions are met only when they name the student's course; a prerequisite already taken, or
planned earlier in the path, is met; antirequisites close a subject when any listed subject is taken, in either direction
(the site often lists a pair on one side only). A subject that needs one or two open prerequisites enters with them, as one
step valued per place used; one that cannot be taken is listed with the reason (43023 needs 42172 or 41040, which an MDSI
student cannot enrol in). The path is then laid out over Autumn and Spring sessions, prerequisites first. Valuing a step
per place breaks the (1 − 1/e) guarantee of plain greedy, which holds for unit costs only; with three places this is a
small price for a path the student can actually take.

**Outside courses.** The gaps the UTS path leaves open get a second greedy pass, over 56 free or free-to-audit courses from
42 providers (`external_courses.csv`), at most three, never mixed with UTS subjects in one pass (a short course aimed at one
skill would push subjects out). For the Robert Walters ad and the sample resume, the UTS path is 36106 → 36121 → 32130
(5 of 6 gaps, 87.9% of the demand, with the 2026 counts of 15 Oct; 36106 → 32130 → 36121 and 88.3% with those of 13 Oct)
and the Hugging Face LLM Course closes the last gap.

**Roles.** For the Elective chooser and Career switcher modes, a role is matched like an ad: its 15 most-asked technical
skills, with the role's own shares as demand. Six roles come from 10,925 Australian 2023 postings (tool lists only)
**[Van Thong]**; Data Scientist keeps the Seek full-text profile, which also has concepts such as machine learning.

## 4.7 Chat [Van Thong / Quan: please check]

The chat is retrieval-augmented generation (Lewis et al., 2020): MiniLM embeddings in a FAISS index (TF-IDF where PyTorch is
absent) retrieve subject-profile passages, a subject code in the question restricts the search, passages below a minimum
score are dropped, and GPT-4o-mini answers from them with citations.

## 4.8 How each stage is evaluated

| Stage | Metric | Test set | Result (section 6) |
|---|---|---|---|
| Extraction | Precision, recall, F1 | 20 labelled Seek ads, 217 labels | F1 0.780 (dictionary), 0.799 (spaCy), #56 15 Oct; LLM **[eval]** |
| Normalisation | Precision per mapper, error types | 211 non-dictionary phrases | Table 4.2 |
| Emerging skills | Precision@20 per method, by hand | 2026 ads vs 2019–22 | **[eval]** |
| Matching | Status accuracy, macro F1 | 45 CV–JD pairs, 287 rows | 0.927, 0.768 (#56, 15 Oct) |
| Evidence ranking | Hit@5, MRR | 87 have/partial rows | 0.943, 0.829 (#56, 15 Oct) |
| Subjects | P@3 | Skill–subject pairs (#73) | **[eval]** |
| Chat | LLM-as-judge, 1–5 | Chat questions (#73) | **[eval]** |

The test sets are smaller than planned, so these are small-sample estimates.

## References

- Lewis, P., Perez, E., Piktus, A., et al. (2020). Retrieval-augmented generation for knowledge-intensive NLP tasks. *NeurIPS 2020*.
- Monroe, B. L., Colaresi, M. P., & Quinn, K. M. (2008). Fightin' words: Lexical feature selection and evaluation for identifying the content of political conflict. *Political Analysis, 16*(4), 372–403.
- Nemhauser, G. L., Wolsey, L. A., & Fisher, M. L. (1978). An analysis of approximations for maximizing submodular set functions—I. *Mathematical Programming, 14*, 265–294.
- Reimers, N., & Gurevych, I. (2019). Sentence-BERT: Sentence embeddings using Siamese BERT-networks. *EMNLP-IJCNLP 2019*.
- Wang, W., Wei, F., Dong, L., Bao, H., Yang, N., & Zhou, M. (2020). MiniLM: Deep self-attention distillation for task-agnostic compression of pre-trained transformers. *NeurIPS 2020*.
