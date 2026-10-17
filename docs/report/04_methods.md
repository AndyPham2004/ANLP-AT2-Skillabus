# 4 Methods

Each stage pairs a traditional method with a newer one on the same inputs, so section 6 can show what the newer method
adds and where it fails (Table 4.1).

**Table 4.1** Traditional and newer method per stage.

| Stage | Traditional | Newer | Why we keep the newer one | Its typical failure |
|---|---|---|---|---|
| Extraction | Vocabulary lookup | + spaCy rules, + GPT-4o-mini | Plurals, verbs and tools outside the vocabulary | Candidates that are not skills ("Social Club") |
| Normalisation | ESCO exact label | + fuzzy string, + MiniLM embedding, "emerging" class | Paraphrases; skills ESCO lacks are kept | A broader concept ("data extraction" → *information extraction*) |
| Emerging skills | Added by hand | n-grams, spaCy, GPT, scored by weighted log-odds | New terms found without a person noticing first | Career-site boilerplate |
| Matching | Same skill | + umbrella rule for "partial" | Credits part of a broad skill | — (rule-based) |
| Subject evidence | Alias match | + TF-IDF, + sentence embeddings | Subjects that teach a skill without naming it | Generic sentences ("key concepts and algorithms") |
| Learning path | Best subject per gap | Greedy cover with prerequisites and sessions | Fewest subjects, ones the student can take | Long prerequisite chains |

## 4.1 Skill extraction

A rule-based splitter treats each bullet or line of an ad or resume as a unit, so a skill carries the same evidence
sentence whichever tier found it.

**Tier 1, vocabulary lookup.** We match the ad aliases of the 283 detection rows of the skill vocabulary (section 3):
the 148 skills of the original dictionary plus IT tools and certifications that Australian ads name. Bare ambiguous
forms ("R", "Go") are not aliases, some aliases are case-sensitive (R, SAS, React), and the longest alias wins ("SQL
Server" does not also give "SQL"). Lookup is fast, transparent and precise,
so it stays the backbone.

**Tier 2, spaCy.** The pretrained NER model has no skill label (it tagged Python and Tableau as places), and training one
would need labelled ads beyond our test set. Tier 2 instead uses the tagger and parser: it drops a one-word alias used as
a verb ("*spark* new ideas"), folds plurals ("REST APIs"), and proposes phrases outside the vocabulary from noun chunks
after a cue ("experience with", "such as").

**Tier 3, GPT-4o-mini.** A fixed prompt at temperature 0 returns skills as JSON. A returned skill must occur verbatim in
the text and its evidence sentence is cut from the text, so the model cannot invent skills or quotes; contact details are
masked first and responses are cached.

Every mention is also tagged **required** or **preferred** from a cue in its sentence ("must", "desirable") or the heading
it sits under ("Essential criteria", "Nice to have"). On dictionary skills the three tiers are close (section 6); the
newer tiers matter for what lies outside the vocabulary, and that is also their weak point: of 211 distinct phrases
outside the dictionary that spaCy proposed, 69 (33%) are not skills (employers, perks, job titles).

## 4.2 Normalisation

Each mention passes five steps, first hit wins: the vocabulary; an exact ESCO label (after dropping filler such as
"skills"); the nearest ESCO label by MiniLM embedding (cosine ≥ 0.82); a Lightcast Open Skills lookup (built, not run: no API key); and an explicit
**emerging** class. A vocabulary skill keeps its own id, and the ESCO id only when the link is exact: a broad link would
merge distinct tools (Tableau and Power BI fall under one ESCO concept).

**Table 4.2** Mapping 211 phrases outside the dictionary to ESCO, judged by hand.

| | Exact label | Fuzzy string (≥ 0.85) | Embedding (≥ 0.82) |
|---|---|---|---|
| Right / mapped | 12 / 12 | 12 / 24 | 10 / 14 |
| Precision | 1.00 | 0.50 | 0.71 |

Exact matching is never wrong but maps only 12 of the 142 real skills. Fuzzy matching doubles that by matching letters,
not meaning (gRPC → *gel permeation chromatography*, Canva → *Canvas*). The embedding errs more subtly, moving to a
broader concept ("customer analytics" → *marketing analytics*); beyond the exact step it adds one right mapping. The
threshold was not changed on these results, because 58 of the phrases come from test ads.

**Skills outside ESCO.** ESCO v1.2.1 has no concept for large language models, generative AI, DuckDB or RLHF. Forcing them
onto the nearest label would be wrong (DuckDB → *breed ducks*, cosine 0.56), so they skip the embedding step and are kept
as **emerging** skills, shown with a ✦ in the app. The vocabulary adds 145 skills Australian ads ask for and ESCO lacks,
each with its nearest ESCO concept recorded as broad, close or none.

## 4.3 Emerging-skill detection

LLMs and generative AI are in the vocabulary only because we added them by hand. To find the next ones,
`skillabus.emerging` proposes phrases three ways (1–3-word n-grams, spaCy candidates, GPT skills) and scores all three
the same way: the weighted log-odds of the 2026 ads against the 3,204 Seek ads of 2019–22, with an informative Dirichlet
prior (Monroe, Colaresi & Quinn, 2008). A candidate needs z ≥ 1.96, at least 3 ads from 2 employers (one employer's
boilerplate cannot qualify), and must be neither a vocabulary alias nor an ESCO label; only requirement sentences are
counted, because the career-site prose of 2026 ads otherwise makes any word look new. spaCy keeps fewer, cleaner
phrases than n-grams (*agentic workflows*, *Claude*); the output is a list for a person to accept, not an automatic update.

## 4.4 Matching and demand

A skill the ad asks for is **have** when the resume names the same vocabulary skill, **missing** when nothing supports
it, and **partial** when the ad asks for the umbrella skill of a category (machine learning, cloud, statistics, ...)
and the resume shows a part of it (scikit-learn for machine learning). Programming languages are never partial, and
soft skills are listed apart. We tested counting close substitutes (Tableau and Power BI) as partial by embedding
similarity, but true substitutes scored lower than unrelated pairs (Tableau–Power BI 0.30, Airflow–MLflow 0.54), so the
rule was dropped.

Each gap carries **demand**: the share of the target role's 2026 job-board ads that name it (for a pasted ad, the Data
Scientist ones), with the source and period on every row so the app can say where the number comes from. The 2019–22
Seek share is shown only as the trend, because those ads predate ChatGPT and name LLMs in 0% of cases.

## 4.5 Subject evidence: keyword → TF-IDF → embeddings

Each UTS subject is a set of rows, one per learning objective, assessment, weekly topic or description sentence (6,853
rows, 360 subjects). A row is evidence for a skill when it names it (aliases), or when it is similar enough: TF-IDF
(cosine ≥ 0.35) as the traditional baseline, `all-MiniLM-L6-v2` sentence embeddings (Reimers & Gurevych, 2019; cosine ≥
0.55) as the newer method. Embeddings find paraphrases TF-IDF scores near zero ("Classification and prediction" for
machine learning), while TF-IDF's extra matches share misleading words ("Machine Translation"). The 0.55 threshold was set
by reading the closest non-naming rows for 22 data skills, and rechecked for 12 IT skills: all 6 rows at or above 0.55
were right, but all came from one skill (data security); tool names such as Kubernetes never reach it, because the
Handbook names concepts, not tools. We kept 0.55, since the IT rows rest on one skill and 0.50 was too loose for data
skills. The deployed app runs TF-IDF (no PyTorch on the free host).

A row's score is its similarity (1.0 when it names the skill) times its layer weight: a skill that is taught and
assessed (learning objective, assessment) outweighs one covered in class (weekly topic) or only mentioned
(description). A subject's strength is its best row plus a bonus for further rows and for a title that names the skill,
and it covers a skill only at 60% of the strongest subject's strength, so one passing mention does not count. Reading
weekly topics, not only objectives, is what shows that 36118 and 43023 teach large language models.

## 4.6 Learning path

Choosing at most three subjects that close the most demand is a maximum coverage problem; the greedy algorithm takes the
subject that closes the most uncovered demand, then the next (Nemhauser, Wolsey & Fisher, 1978). A subject counts only
if the student can enrol in it, read from the scraped access conditions: admission rules must name the student's
course, prerequisites must be taken or planned earlier in the path, and an antirequisite closes a subject in either
direction. A subject needing one or two open prerequisites enters with them, valued per place used; one that cannot be
taken is listed with the reason. The path is laid out over Autumn and Spring sessions; valuing a step per place gives up
the (1 − 1/e) guarantee of plain greedy, a small price for a path the student can take. The sample-ad path is in section 1.

Gaps the UTS path leaves open get a second greedy pass over 250 self-study resources (free, free-to-audit or paid, with
the price shown), never mixed with UTS subjects. A course counts for a gap only when its hand-checked skill list names
the gap: matching the text alone picked courses that mention a skill in passing ("Sign up for an AWS account" in a
Redshift course).

For the role modes, a role is matched like an ad: its 15 most-asked technical skills in its 2026 ads, with the role's own
shares as demand.

## 4.7 Chat

The chat is retrieval-augmented generation (Lewis et al., 2020): MiniLM embeddings in a FAISS index (TF-IDF where
PyTorch is absent) retrieve subject passages, a subject code in the question restricts the search, weak passages are
dropped, and GPT-4o-mini answers from the rest with citations.

## References

- Lewis, P., Perez, E., Piktus, A., et al. (2020). Retrieval-augmented generation for knowledge-intensive NLP tasks. *NeurIPS 2020*.
- Monroe, B. L., Colaresi, M. P., & Quinn, K. M. (2008). Fightin' words: Lexical feature selection and evaluation for identifying the content of political conflict. *Political Analysis, 16*(4), 372–403.
- Nemhauser, G. L., Wolsey, L. A., & Fisher, M. L. (1978). An analysis of approximations for maximizing submodular set functions—I. *Mathematical Programming, 14*, 265–294.
- Reimers, N., & Gurevych, I. (2019). Sentence-BERT: Sentence embeddings using Siamese BERT-networks. *EMNLP-IJCNLP 2019*.
