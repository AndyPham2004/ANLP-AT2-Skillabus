# Appendix B: Evaluation tables

These tables support section 6. All numbers come from `PYTHONPATH=src python -m skillabus.evaluate --all`; the saved output is in `data/4_evaluation/results/` (`eval_tables.md` and one JSON file per part).

## B.1 Test sets and what was run

| Stage | Test set (as labelled) | Tiers run |
|---|---|---|
| Extraction | 20 Seek ads, 217 skill labels | Dictionary, spaCy, GPT-4o-mini (read from 30 committed answers) |
| Matching | 45 CV–JD pairs, 287 skill rows (81 have, 6 partial, 200 missing) | `match()` and `rank_evidence()`, all three tiers |
| Subjects P@3 | 33 skill–subject pairs, 13 skills | Keyword, TF-IDF, embeddings |
| Chat | 15 questions with reference answers | Retrieval: TF-IDF and embeddings; LLM judge on the TF-IDF answers |
| Annotator agreement | 20 overlap ads, two annotators | Cohen's kappa |

Five of the 50 selected pairs (CVJD01, CVJD02, CVJD33, CVJD43, CVJD49) have no scored skills, so 45 remain.

## B.2 Extraction

| Tier | Precision | Recall | F1 | TP / FP / FN |
|---|---|---|---|---|
| Dictionary, all skills | 0.841 | 0.705 | 0.767 | 153 / 29 / 64 |
| Dictionary, dictionary skills only | 0.864 | 0.705 | 0.777 | 153 / 24 / 64 |
| spaCy, all skills | 0.648 | 0.737 | 0.690 | 160 / 87 / 57 |
| spaCy, dictionary skills only | 0.865 | 0.737 | 0.796 | 160 / 25 / 57 |
| GPT-4o-mini, all skills | 0.502 | 0.700 | 0.585 | 152 / 151 / 65 |
| GPT-4o-mini, dictionary skills only | 0.910 | 0.700 | 0.792 | 152 / 15 / 65 |

Of the 64 dictionary-tier misses, 25 are soft skills, 13 programming (11 are the bare letter "R") and 12 machine learning. The 29 false positives are 12 real errors (a degree list such as "Statistics, Data Science, Mathematics" in six ads; a partner list; a company description; "Dash" read as Plotly) and 17 judgement calls or label gaps (for example "text mining" as NLP, "data pipelines" as ETL, and four tools that entered the dictionary after labelling: Kafka, React, Linux, Microsoft Office).

### Extraction on 18 ATS ads of 2026 (10 roles, 273 labels)

| Tier | Scored on | Precision | Recall | F1 | TP / FP / FN |
|---|---|---|---|---|---|
| Dictionary | all labels | 0.686 | 0.527 | 0.596 | 144 / 66 / 129 |
| Dictionary | vocabulary skills only | 0.686 | 0.809 | 0.742 | 144 / 66 / 34 |
| spaCy | all labels | 0.500 | 0.674 | 0.574 | 184 / 184 / 89 |
| spaCy | vocabulary skills only | 0.677 | 0.826 | 0.744 | 147 / 70 / 31 |
| GPT-4o-mini | all labels | 0.392 | 0.608 | 0.477 | 166 / 257 / 107 |
| GPT-4o-mini | vocabulary skills only | 0.843 | 0.601 | 0.702 | 107 / 20 / 71 |

Cohen's kappa between the two annotators on 6 of these ads: 0.361 on vocabulary skills (observed agreement 0.982; 9 labels shared, 29 only the first annotator's, 2 only the second's) and 0.319 on all labels (0.965), both "fair".

## B.3 Matching

| Tier | Ad skills from | Accuracy | Macro F1 | have P / R | partial P / R | missing P / R |
|---|---|---|---|---|---|---|
| Dictionary | `extract()` | 0.909 | 0.739 | 0.98 / 0.79 | 0.33 / 0.50 | 0.91 / 0.97 |
| Dictionary | gold labels | 0.927 | 0.768 | 0.97 / 0.84 | 0.33 / 0.67 | 0.95 / 0.97 |
| spaCy | `extract()` | 0.909 | 0.739 | 0.98 / 0.79 | 0.33 / 0.50 | 0.91 / 0.97 |
| spaCy | gold labels | 0.927 | 0.768 | 0.97 / 0.84 | 0.33 / 0.67 | 0.95 / 0.97 |
| GPT-4o-mini | `extract()` | 0.944 | 0.796 | 0.96 / 0.89 | 0.50 / 0.50 | 0.95 / 0.98 |
| GPT-4o-mini | gold labels | 0.958 | 0.811 | 0.97 / 0.94 | 0.40 / 0.67 | 0.98 / 0.97 |

Confusion (dictionary, gold labels). Of 287 rows, 266 are right and 21 are wrong:

| Gold → predicted | Rows | What happened |
|---|---|---|
| have → missing | 11 | Eight are the bare "R" in the resume; two are "predictive modelling", one is "ETL" |
| missing → partial | 6 | The six false partials below |
| have → partial | 2 | Data visualisation (CVJD06), Statistics (CVJD24) |
| partial → have | 2 | Statistics (CVJD26, CVJD28) |

The six false partials: in CVJD37–40 ("machine learning") an economics resume mentions *forecasting* money supply and the umbrella rule credits "time series forecasting" as part of machine learning; CVJD38 ("data visualisation") is credited from "Proficient in Excel"; CVJD12 ("data visualisation") from "MS Visio", which maps to Microsoft Office. A stricter umbrella rule (a method or library from the category, not a topic) would remove four of the six.

## B.4 Evidence ranking (87 have and partial rows)

| Ranker | P@5 | Hit@5 | MRR |
|---|---|---|---|
| `rank_evidence()` (sentences that name the skill first) | 0.200 | 0.943 | 0.829 |
| TF-IDF only | 0.200 | 0.943 | 0.826 |
| Embeddings only | 0.189 | 0.885 | 0.753 |

Each row has one gold phrase, so P@5 sits near its ceiling of 0.2.

## B.5 Subject recommendation (P@3)

| Method | P@3 (y or partly) | P@3 (y only) | Labelled / recommended | Coverage |
|---|---|---|---|---|
| Keyword | 0.950 | 0.900 | 20 / 37 | 0.541 |
| TF-IDF | 0.950 | 0.900 | 20 / 37 | 0.541 |
| Embeddings | 1.000 | 0.947 | 19 / 37 | 0.514 |

A subject name counts once, and a label on any code with the same name counts. Recommended subjects with no label are left out, so the last column gives how much of the top three was labelled. For a skill in the dictionary, `subject_evidence()` gives similarity 1.0 to every row that names the skill, so the subjects that name the skill always come first. Keyword and TF-IDF return identical lists for all 13 skills, and all three methods share the same top three for 12 of 13. This table is not a comparison of the methods.

## B.6 Chat

| Method | Hit@5 | Subject recall@5 |
|---|---|---|
| TF-IDF | 0.933 | 0.778 |
| Embeddings | 0.800 | 0.567 |

LLM judge (TF-IDF retrieval, 15 answers, none unparsed): relevance 4.13 / 5, faithfulness 4.33 / 5, 93% of answers with faithfulness 4 or above. Q05 is the weakest (3 / 3): a wrong subject code and missing techniques. Q01 also has a wrong code (431031 for 43031). Across three runs, relevance ranged from 4.13 to 4.40 and faithfulness from 4.33 to 4.47.

## B.7 Annotator agreement

Cohen's kappa between two annotators on 20 ads: 0.856 on dictionary skills (observed agreement 0.980, almost perfect) and 0.686 on all labels including free text (0.966, substantial).
