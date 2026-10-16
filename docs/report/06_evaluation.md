# 6 Evaluation and error analysis

> Re-run 17 Oct 2026 on `main`, after the extractors moved to the skill vocabulary (#109, #142) and a bare "AI" stopped counting as the skill (#148, #149). Every number comes from `PYTHONPATH=src python -m skillabus.evaluate --all` (needs spaCy and the embedding libraries; the GPT-4o-mini extraction answers are read from the committed cache, so only the chat judge needs an API key). The results are saved in `data/4_evaluation/results/` (`eval_tables.md` and one JSON per part).
> Scripts: `src/skillabus/evaluate.py` (metrics), `src/skillabus/eval_run.py` (the run).

## 6.1 What was run

Section 4.7 lists four stages. The table says what the numbers below cover.

| Stage | Test set (as labelled) | Tiers run | Status |
|---|---|---|---|
| Extraction | 20 Seek ads, 217 skill labels | Dictionary (tier 1) | Done |
| Extraction | same | spaCy (tier 2) | Done |
| Extraction | same | GPT-4o-mini (tier 3) | Done, from the 30 committed answers (20 ads and 10 resumes) |
| Matching | 45 CV–JD pairs, 287 skill rows (81 have, 6 partial, 200 missing) | `match()` and `rank_evidence()`, all three tiers | Done |
| Subjects P@3 | 33 skill–subject pairs, 13 skills | Keyword, TF-IDF, embeddings | Run, but only about half of the top three is labelled (see 6.5) |
| Chat | 15 questions with reference answers | Retrieval: TF-IDF and embeddings; LLM judge on the TF-IDF answers | Done: judge relevance 4.13 / 5, faithfulness 4.33 / 5 (see 6.5) |
| Annotator agreement | 20 overlap ads, two annotators | Cohen's kappa | **0.856** on dictionary skills (almost perfect); 0.686 on all labels incl. free text (substantial) |

The test sets are much smaller than planned (200 ads, 50 pairs). Five of the 50 selected pairs (CVJD01, CVJD02, CVJD33, CVJD43 and CVJD49) have no scored skills in the labelled file, so 45 pairs remain. Every figure below is therefore a small-sample estimate.

The test sets were labelled following the rules in `data/4_evaluation/labels/README.md`. The 20 overlap ads are also labelled separately by a second annotator (Van Thong) so that inter-annotator agreement can be measured with Cohen’s kappa.

## 6.2 Extraction

On the 20 ads, the dictionary tier finds 153 of the 217 labelled skills and adds 29 that were not labelled. The extraction is scored after `normalise()`, as the app runs it; for tiers 1 and 2 this changes nothing, but GPT-4o-mini returns raw phrases that only `normalise()` maps to dictionary names.

| Tier | Precision | Recall | F1 | TP / FP / FN |
|---|---|---|---|---|
| Dictionary, all skills | 0.841 | 0.705 | 0.767 | 153 / 29 / 64 |
| Dictionary, dictionary skills only | 0.864 | 0.705 | 0.777 | 153 / 24 / 64 |
| spaCy, all skills | 0.648 | 0.737 | 0.690 | 160 / 87 / 57 |
| spaCy, dictionary skills only | 0.865 | 0.737 | 0.796 | 160 / 25 / 57 |
| GPT-4o-mini, all skills | 0.502 | 0.700 | 0.585 | 152 / 151 / 65 |
| GPT-4o-mini, dictionary skills only | 0.910 | 0.700 | 0.792 | 152 / 15 / 65 |

All labelled skills come from the 148-row dictionary (`skills_seed_v2.csv`), but tiers 1 and 2 now read the 283 detection
rows of the skill vocabulary (`skills_vocabulary.csv`, section 4.1), so they can name skills the labels could not contain. For the dictionary tier this adds five
false positives (Teradata, Salesforce, tidyverse, test automation, process mapping; see below). A bare "AI" no longer counts
(#148): in one ad the labelled skill list "R programming - Python - AI - Machine learning" now gives no AI, so every tier
loses one hit. Together, dictionary F1 moves from 0.780 (#56) to 0.767 on all skills and to 0.777 on dictionary skills. For spaCy the dictionary-only row is the fair one: it finds 7
more labelled skills (plural forms) for one more false positive. The 62 extra false positives in its all-skills row are off-dictionary candidates ("customer segmentation", tool
names); the labels hold only dictionary skills, so every candidate counts as wrong, right or not. GPT-4o-mini shows the same pattern: 136 of its 151 false positives are skills outside the dictionary, which is what the tier is for, and on dictionary skills it has the best precision of the three tiers (0.910) with recall of 0.700, about the same as the dictionary tier's 0.705 and below spaCy's 0.737. Its F1 on dictionary skills (0.792) is close to spaCy's (0.796). (GPT-4o-mini's figures are those of #56: it returns "AI" as a skill and `normalise()` maps the whole mention to Artificial intelligence, #149.)

**Where it fails.** Of the 64 misses, 25 are soft skills (communication, teamwork, stakeholder management), 13 are
programming skills and 12 are machine-learning skills (one is the bare "AI" above). Eleven of the 13 programming misses are the bare letter "R". This is
by design, as section 4.1 explains: the dictionary matches only aliases such as "R programming", never the ambiguous bare
"R". The 29 false positives split into two kinds. Twelve are real errors: the dictionary reads a skill word that the ad does not ask for, such as a degree list ("Statistics, Data Science, Mathematics", six ads), a partner list (Snowflake, Alteryx and Salesforce in one ad), a company description (artificial intelligence; "the analytics and process modelling functions" read as process mapping) and "Dash" read as Plotly. Seventeen are judgement calls or label gaps where the extractor found a phrase the labeller did not list: "text mining" as NLP (2), "data pipelines" as ETL (2), leadership (2), one each of agile, problem solving, cloud and optimisation, four tools the ads do ask for (Kafka, React, Linux and Microsoft Office) that entered the dictionary after the labelling, and three vocabulary skills the ads name (Teradata, ggplot2 as tidyverse, test automation). Precision of 0.841 is therefore 0.934 if the seventeen count as correct. The next two tiers are meant to recover the soft skills
and the bare "R".

## 6.3 Matching

We ran `match()` two ways. In *end to end*, the ad skills come from the dictionary extractor. In *matching only*, the ad
skills are the gold labels, so the score does not include extraction misses.

| Setting | Accuracy | Macro F1 | have P / R | partial P / R | missing P / R |
|---|---|---|---|---|---|
| End to end | 0.909 | 0.739 | 0.98 / 0.79 | 0.33 / 0.50 | 0.91 / 0.97 |
| Matching only | 0.927 | 0.768 | 0.97 / 0.84 | 0.33 / 0.67 | 0.95 / 0.97 |

The table is for the dictionary tier. The spaCy rows are identical to it, because the extra skills spaCy finds do not change any status. With GPT-4o-mini the ad skills come from a different extractor and the numbers change: end to end 0.944 accuracy and 0.796 macro F1, matching only 0.958 and 0.811. Its end-to-end have recall is 0.89 against 0.79 for the dictionary.

In the end-to-end run, 61 of the 287 labelled skills were never extracted from the ad, so they get no status. We count
them as "missing"; 45 of them really are missing, which is why accuracy stays high.

**Read partial with care.** There are only six partial rows, so one row moves partial recall by 17 points. We report the
counts and put the weight on accuracy and on the have and missing classes.

**Confusion (matching only).** Of 287 rows, 266 are right (194 missing, 68 have and 4 partial) and 21 are wrong. The errors are:

| Gold → predicted | Rows | What happened |
|---|---|---|
| have → missing | 11 | Eight are the bare "R" in the resume, which tier 1 does not extract; two are "predictive modelling" and one is "ETL" |
| missing → partial | 6 | See below |
| have → partial | 2 | Data visualisation (CVJD06), Statistics (CVJD24): the resume has a related tool but not the named skill |
| partial → have | 2 | Statistics (CVJD26, CVJD28) |

**The six false partials.** In four of them (CVJD37–40, "machine learning") the resume is an economics resume with a
line about *forecasting* money supply. The umbrella rule treats "time series forecasting" as part of machine learning, so it
credits a partial. Under the labelling rules this is wrong, because the resume shows no machine-learning method. In the fifth
(CVJD38, "data visualisation") the credit comes from "Proficient in Excel". Whether Excel is a visualisation tool is
debatable, and our labels say no. The sixth (CVJD12, "data visualisation") comes from the resume's "MS Visio", which maps to Microsoft Office, a tool that entered the dictionary's visualisation category after the labelling. A stricter umbrella rule (for example, a method or library from the category, not
forecasting as a topic) would remove four of the six.

## 6.4 Evidence ranking

For each have or partial row, `rank_evidence()` ranks the resume's sentences, and the gold evidence is the labelled phrase.
A sentence counts as correct when it contains the phrase.

| Ranker (k = 5, n = 87) | P@5 | Hit@5 | MRR |
|---|---|---|---|
| `rank_evidence()` (sentences that name the skill first) | 0.200 | 0.943 | 0.829 |
| TF-IDF only | 0.200 | 0.943 | 0.826 |
| Embeddings only | 0.189 | 0.885 | 0.753 |

Each row has one gold phrase, so P@5 sits near its ceiling of 0.2 and says little; Hit@5 and MRR are the informative figures. Hit@5 says the right sentence is in the top five for 94.3% of rows, and MRR of
0.829 says it is usually first. The result does not depend on the extraction tier. (With lowercased skill labels the ranker
lost its dictionary lookup and scored 0.189 / 0.885 / 0.756; `eval_run.py` now passes the canonical name.) The TF-IDF baseline is almost as good as `rank_evidence()` (MRR 0.826 against 0.829), because the resume sentence that names the skill usually shares its words. Embeddings alone are clearly worse (Hit@5 0.885, MRR 0.753): they pull up sentences about related skills. With 87 rows the gap between `rank_evidence()` and TF-IDF is within noise; the gap to embeddings is larger (Hit@5 differs by 5 rows), but still a small sample.

## 6.5 Subject recommendation and chat

**Subject P@3.** For each of the 13 labelled skills, the top three subjects returned by `subject_evidence()` are compared with the 33 labelled skill–subject pairs. Some subjects appear under more than one code in the Handbook (for example Data Visualisation and Visual Analytics), so a subject name counts once, and a label on any code with the same name counts for the subject. A recommended subject with no label is left out of the count, so the table also gives how much of the top three was labelled.

| Method | P@3 (y or partly) | P@3 (y only) | Labelled / recommended | Coverage |
|---|---|---|---|---|
| Keyword | 0.950 | 0.900 | 20 / 37 | 0.541 |
| TF-IDF | 0.950 | 0.900 | 20 / 37 | 0.541 |
| Embeddings | 1.000 | 0.947 | 19 / 37 | 0.514 |

**This is not a comparison of the three methods.** For a skill that is in the dictionary, `subject_evidence()` gives similarity 1.0 to every row that names the skill, whatever the method, so the subjects that name the skill always come first and ties are sorted by subject code. Keyword and TF-IDF return identical lists for all 13 skills, and all three methods have the same top three for 12 of the 13 (only Data cleaning differs, at rank 3). The rows above therefore differ by one or two pairs, not because one method is better. A comparison of the methods needs similarity-only ranking or skills outside the dictionary. In addition, about half of the recommended subjects have a label, and the labelled pairs are almost all "y" (25 of 33; 7 "partly", 1 "n"), so P@3 is an optimistic estimate; the unlabelled recommendations are not counted.

**Chat retrieval.** For the 15 questions, retrieval returns at least one of the subjects named in the reference answer within the top five for 93.3% of the questions with TF-IDF and 80.0% with embeddings (Hit@5), and finds 77.8% and 56.7% of all the subjects the reference answers cite (recall@5). Subjects are compared by name, because one subject can have several codes. TF-IDF is ahead of the embeddings on this set; with 15 questions that is a difference of two questions. **LLM judge.** GPT-4o-mini wrote an answer to each question from the five TF-IDF passages, and GPT-4o-mini then scored it against the reference answer from 1 to 5. All 15 replies could be read. Mean relevance is 4.13 and mean faithfulness is 4.33; 14 of the 15 answers (93%) have faithfulness 4 or 5. The weakest is Q05 (relevance 3, faithfulness 3): the judge says the answer gave a wrong subject code and left out techniques the reference lists; Q01 also has a wrong code (431031 for 43031). The same model writes and judges the answers, which tends to flatter it. The answers are written afresh on every run (they are saved in `eval_chat.json` but not cached), so the scores move between runs with the same retrieval: three runs gave relevance 4.13 to 4.40 and faithfulness 4.33 to 4.47 (16 and 17 Oct), and Q05 was the weakest each time. A difference below about 0.3 is therefore not a result; the scores are indicative only.

## 6.6 Limits of these numbers

- 20 ads, 45 pairs, 33 skill–subject pairs and 15 chat questions are small; the confidence intervals are wide, and results from different tiers will differ by less
  than the noise unless the gap is large.
- One ad row and one pair row carry the "unsure" mark; `load_ad_skills()` and `load_cv_jd_pairs()` drop the mark, so unsure labels count as gold, which slightly lowers recall.
- Gold labels come from one annotator. Cohen's kappa on the 20 overlap ads is 0.856 for dictionary skills (observed agreement 0.980) and 0.686 when free-text labels are included (0.966), so another annotator largely agrees on dictionary skills and disagrees more on free-text skills outside the dictionary. Extraction scores use the first annotator's rows only.
- Retrieval can fill the top five with one subject under several codes (TF-IDF returns Machine Learning as 31005, 320513 and 321513 for one question), which lowers recall for the other subjects; fixing that belongs in `rag.py`.
- The matching and ranking tables are for the dictionary tier; the spaCy rows are identical to them, and only GPT-4o-mini changes the matching result (6.3).
