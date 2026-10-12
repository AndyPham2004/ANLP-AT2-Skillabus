# 4 Methods

> Draft by Phuong Nhi, 11 Oct 2026. **[eval]** = number from section 6. **[Quan]** / **[Van Thong]** = please check the
> sentence about your stage. Code: `src/skillabus/`. Every threshold below was set on text that is not in a test set.

Each stage pairs a traditional baseline with a stronger method, so section 6 can show what the stronger method adds.

| Stage | Baseline | Final method | Why the final method |
|---|---|---|---|
| Extraction | Dictionary lookup | + spaCy rules, + GPT-4o-mini | Finds plurals, skills outside the dictionary and new terms ("agentic AI") |
| Normalisation | Dictionary aliases | ESCO exact → ESCO embedding → Lightcast → emerging | One shared vocabulary that keeps skills ESCO lacks |
| Matching | Exact skill identity | + umbrella rule for "partial" | Credits a resume that shows part of a broad skill |
| Subject evidence | Keyword (alias) match | + TF-IDF, + sentence embeddings | Finds subject sentences that teach a skill without naming it |
| Learning path | Top subject per gap | Greedy demand-weighted cover | Fewest subjects for the most employer demand |

## 4.1 Skill extraction

**Text units.** Ads and resumes are mostly bullet lists, where statistical sentence splitters perform poorly. A rule-based
splitter treats each bullet or line as a unit, joins hard-wrapped lines back together and splits prose after `.`, `!` and `?`.
Every tier uses the same splitter, so a skill carries the same evidence sentence whichever tier found it.

**Tier 1, dictionary (baseline).** We match the aliases of the 138-skill dictionary (`skills_seed_v2.csv`: Van Thong's 133
skills plus five generic rows). Only aliases are matched, never the display name, because the dictionary deliberately leaves
out ambiguous bare forms such as "R", "Go" and "RAG". Skills marked `strict` (R, SAS) are matched case-sensitively. The longest
alias wins, so "SQL Server" does not also produce "SQL". Character lookarounds replace `\b`, which fails on "C++", "C#" and
".NET". URLs and e-mail addresses are blanked first. On the Robert Walters ad, tier 1 reproduces the eight technical skills
of the poster's gap chart exactly.

**Tier 2, spaCy (`en_core_web_sm`).** The pretrained NER model has no skill label, and on our sentences it tagged Python and
Tableau as places and Scala and Keras as people. A custom NER model would need training data; our only labelled ads are the
test set, and training on them would leak. Tier 2 therefore keeps tier 1's hits and uses spaCy's tagger and parser for three
rules:

1. A one-word alias used as a finite verb is dropped ("you will *excel* in a team", "*spark* new ideas"). Gerunds are kept,
   because "coaching juniors" and "forecasting demand" are skills.
2. Plural nouns are folded to the singular before a second lookup, which finds "REST APIs", "data warehouses" and
   "stakeholders". We fold only nouns the tagger marks plural; full lemmatisation turned the alias "clustering" into
   "cluster" and matched "Kubernetes clusters".
3. Skills outside the dictionary are proposed from noun phrases governed by a cue ("experience with", "knowledge of",
   "using", "such as", "including") and from PRODUCT entities, after removing numbers, dates, places, generic heads
   ("experience", "solutions") and single lower-case nouns. This finds "Alteryx", "KNIME" and "customer segmentation".
   These candidates have no dictionary name; normalisation decides what they are.

Tier 2 is still wrong when the parse is ("I use spark and excel daily" loses Excel) and when a dictionary alias is an
ordinary noun ("dash" for Plotly). These cases feed the error analysis in section 6.

**Tier 3, GPT-4o-mini [Quan].** A fixed prompt asks for skills as JSON at temperature 0. Every returned skill must occur
verbatim in the text, and the evidence sentence is cut from the text, not generated, so the model cannot invent skills or
quotes. E-mail addresses, phone numbers and URLs are masked before the call, and responses are cached by a hash of model,
prompt and text, so the evaluation can be re-run at no cost.

## 4.2 Normalisation [Quan]

Each mention passes five steps, first hit wins: the dictionary (47 of its skills carry Van Thong's ESCO link), an exact ESCO
label match, the nearest ESCO label by sentence embedding (cosine ≥ 0.82), the Lightcast Open Skills API, and finally an
explicit "emerging" class. Generative AI and large language models skip the ESCO steps: ESCO v1.2.1 has no concept for them,
and an embedding would force them onto a loosely related one. ESCO's "SPARK" (a Java web framework) is blocked by hand.

## 4.3 Matching: have, partial, missing

A skill the ad asks for is **have** when the resume names the same dictionary skill or the same `skill_id`, and **missing**
when nothing in the resume supports it. It is **partial** when the ad asks for the umbrella skill of a dictionary category
(machine learning, deep learning, NLP, cloud platforms, statistics, data visualisation, computer vision) and the resume shows
a part of it; for example, an ad asks for machine learning and the resume lists scikit-learn. Programming languages never count as
partial, because knowing Java is not partly knowing Python. Professional skills (communication, teamwork) are reported
separately: they matter, but no subject maps to them.

**A rule we tested and dropped.** We also tried to treat close substitutes as partial (Tableau and Power BI) by the
embedding similarity of the two skill names. Across the 652 same-category pairs in the dictionary, true substitutes scored
lower than unrelated pairs (Tableau–Power BI 0.30, AWS–Azure 0.44, but Airflow–MLflow 0.54 and machine
learning–artificial intelligence 0.70), so no threshold separates them (`notebooks/pn_calibrate_matching.py`).

**Demand.** Each skill carries the share of the 3,204 Seek Data Scientist ads (2019–22) that name it, and its share
of the 2026 sample (`skill_counts_2026.csv`, section 3). Skills that appeared after 2022, such as large language models,
sit at 0% in the older ads. The 2026 sample is only 22 full-text ads from 8 employers, so a 2026 share carries about
±20 points. The weight of a gap is therefore `max(share 2019–22, lower end of the 95% Wilson interval of the 2026 share)
+ 1`: a new skill counts by the most it can be relied on to be, not by its point value, and the +1 keeps a 0% skill in play.

## 4.4 Subject evidence: keyword → TF-IDF → embeddings

Subject profiles hold one row per learning objective, assessment, weekly topic or description sentence (`subject_profiles.csv`:
1,039 rows for 70 subjects from the 2026 Handbook, section 3). The assessment layer is still empty, so matching runs on three
layers **[update if Akash's assessment rows land]**. A row is evidence for a skill when it
names the skill (dictionary aliases) or is similar enough to it. The skill is represented by its name plus its aliases.

- **TF-IDF** (baseline): word unigrams and bigrams, sublinear term frequency, English stop words, a token pattern that
  keeps "c++" and single letters; cosine ≥ 0.35.
- **Sentence embeddings** (final): `all-MiniLM-L6-v2` (Wang et al., 2020; Reimers & Gurevych, 2019), the same model the
  normalisation uses; cosine ≥ 0.55.

The deployed app runs the TF-IDF path: the free hosting tier leaves out PyTorch, which the embedding model needs. The code
switches automatically, and the evaluation in section 6 reports both methods from a local run.

The embedding threshold was set by reading the closest rows that do not name the skill, on 429 Handbook rows from 31
subjects. At 0.50 about half of them were generic sentences ("key concepts, definitions, and algorithms"); at 0.55 the kept
rows were mostly real paraphrases that TF-IDF scored near zero, for example "Classification and prediction" for machine
learning (0.55), "statistical models and estimation techniques" for statistics (0.62) and "Evaluate and deploy predictive
models in business production" for MLOps (0.57). TF-IDF, in contrast, added almost nothing beyond rows that already named
the skill: on short Handbook rows it can only see shared words, and the words it shared were often misleading ("Machine
Translation" for machine learning, "business intelligence" for artificial intelligence).

**Teaches or mentions?** A row's score is its similarity (1.0 when it names the skill) times the weight of its layer:
learning objective 1.0, assessment 0.9, weekly topic 0.8, description 0.5. A subject's strength for a skill is its best row,
plus 0.15 for each further row about the skill (at most three), plus 0.40 when the subject's name names the skill, plus 0.10
for an MDSI subject. A subject covers a skill only when it is at least 60% as strong as the strongest subject for that skill.
This is what separates 94691 *Deep Learning* from a subject with one weekly topic on deep learning, and it stops 32130's
"collaboration with AI tools" from counting as teaching artificial intelligence. Embeddings alone would not: that sentence
is semantically close to "AI".

## 4.5 Learning path

Choosing at most three subjects that close the most demand is a maximum coverage problem with a cardinality constraint. We
use the greedy algorithm: repeatedly take the subject that covers the most still-uncovered demand weight, until three
subjects are chosen or no subject adds anything. Greedy is guaranteed at least (1 − 1/e) ≈ 63% of the best possible
coverage (Nemhauser, Wolsey & Fisher, 1978), and with 70 subjects and a few dozen gaps at most it runs in milliseconds. Ties go to the
subject with the higher overall score, then the lower subject code, so the result is reproducible. `demand_covered_pct`
uses the same weights as the choice. For the Robert Walters ad and the sample resume, the path is 36106 → 36121 → 32130, which
closes 5 of 6 gaps and 99.3% of the demand behind them; large language models stay open, and 36118 and 43023 teach them.

## 4.6 Chat [Van Thong / Quan: please check]

The chat is retrieval-augmented generation (Lewis et al., 2020). `retrieve()` searches the subject profiles with the same
two methods as section 4.4: MiniLM embeddings in a FAISS inner-product index, or TF-IDF where PyTorch is not installed (the
deployed app). A subject code in the question restricts the search to that subject, each passage is indexed with its
subject's name and layer, and passages below a minimum score are dropped, so an off-topic question gets no answer rather
than the least-bad sentence. GPT-4o-mini then answers from the retrieved passages and cites them.

## 4.7 How each stage is evaluated

| Stage | Metric | Test set | Section |
|---|---|---|---|
| Extraction (three tiers) | Precision, recall, F1 | 200 hand-labelled Seek ads | 6 **[eval]** |
| Matching | Status accuracy and macro F1; P@5 and MRR of the evidence sentence | 50 CV–JD pairs | 6 **[eval]** |
| Subjects | P@3 | 30 hand-checked skill–subject pairs | 6 **[eval]** |
| Chat | LLM-as-judge, relevance and faithfulness 1–5 | 30 questions | 6 **[eval]** |

## References

- Lewis, P., Perez, E., Piktus, A., et al. (2020). Retrieval-augmented generation for knowledge-intensive NLP tasks.
  *NeurIPS 2020*.
- Nemhauser, G. L., Wolsey, L. A., & Fisher, M. L. (1978). An analysis of approximations for maximizing submodular set
  functions—I. *Mathematical Programming, 14*, 265–294.
- Reimers, N., & Gurevych, I. (2019). Sentence-BERT: Sentence embeddings using Siamese BERT-networks. *EMNLP-IJCNLP 2019*.
- Wang, W., Wei, F., Dong, L., Bao, H., Yang, N., & Zhou, M. (2020). MiniLM: Deep self-attention distillation for
  task-agnostic compression of pre-trained transformers. *NeurIPS 2020*.
