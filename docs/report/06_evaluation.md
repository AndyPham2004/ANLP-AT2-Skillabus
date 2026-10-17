# 6 Evaluation and error analysis

We ran every stage of the pipeline on hand-labelled test sets, using `python -m skillabus.evaluate --all`. Full tables are in Appendix B. The GPT-4o-mini extraction answers are read from a committed cache, so the run is repeatable; only the chat judge needs an API key.

## 6.1 What was run

| **Stage** | **Test set** | **Result in one line** |
|----|----|----|
| Extraction | 20 Seek ads, 217 skill labels | Dictionary F1 0.767; spaCy 0.690; GPT-4o-mini 0.585 (0.777 / 0.796 / 0.792 on dictionary skills) |
| Extraction, 2026 | 18 ATS ads of 10 roles, 273 labels | F1 on vocabulary skills: dictionary 0.742, spaCy 0.744, GPT-4o-mini 0.702 |
| Matching | 45 CV–JD pairs, 287 skill rows | Accuracy 0.909 end to end, 0.927 with gold ad skills |
| Evidence ranking | 87 have/partial rows | Hit@5 0.943, MRR 0.829 |
| Subject recommendation | 33 pairs, 13 data skills; 30 pairs, 11 IT skills | Data: P@3 0.95 to 1.00 (not a method comparison); IT: 0.87 (y or partly), 0.43 (y only) |
| Chat | 15 questions | Hit@5 0.933; judge relevance 4.13, faithfulness 4.33 (of 5) |
| Annotator agreement | 20 ads, two annotators; 6 ads of 2026 | Kappa 0.856 (dictionary skills), 0.686 (all labels); 2026: 0.361, 0.319 |

The test sets are much smaller than planned (200 ads and 50 pairs), so every figure is a small-sample estimate. Extraction is scored after `normalise()`, as the app runs it.

## 6.2 Extraction

| **Tier**    | **Scored on**          | **Precision** | **Recall** | **F1** |
|-------------|------------------------|---------------|------------|--------|
| Dictionary  | all skills             | 0.841         | 0.705      | 0.767  |
| Dictionary  | dictionary skills only | 0.864         | 0.705      | 0.777  |
| spaCy       | all skills             | 0.648         | 0.737      | 0.690  |
| spaCy       | dictionary skills only | 0.865         | 0.737      | 0.796  |
| GPT-4o-mini | all skills             | 0.502         | 0.700      | 0.585  |
| GPT-4o-mini | dictionary skills only | 0.910         | 0.700      | 0.792  |

The labels contain only skills from the 148-row seed dictionary, while tiers 1 and 2 read the 283 detection rows of the skill vocabulary (section 4.1). Any skill outside the labels counts as wrong, even when the ad does ask for it. That is why spaCy (87 false positives) and GPT-4o-mini (151, of which 136 are outside the dictionary) look weak on all skills. Those off-dictionary skills are what the tiers are for. On dictionary skills the three tiers are close: F1 0.777, 0.796 and 0.792, with GPT-4o-mini the most precise (0.910). The differences are within what 20 ads can resolve.

**Where the dictionary fails.** Of 64 misses, 25 are soft skills, 13 programming and 12 machine learning. Eleven of the 13 programming misses are the bare letter “R”, which the dictionary refuses to match by design (section 4.1). Of the 29 false positives, 12 are real errors, such as a degree list (“Statistics, Data Science, Mathematics”) read as skills or “Dash” read as Plotly. The other 17 are judgement calls or label gaps, such as tools that entered the dictionary after labelling. Precision is 0.934 if these count as correct. GPT-4o-mini recovers the bare “R” (programming misses fall from 13 to 2) but misses more soft skills (30); spaCy recovers four soft skills and no “R”.

**2026 ads of ten roles.** Van Thong labelled 18 ATS ads of 2026 on the skill vocabulary (two per role for eight roles, one each for Cloud Engineer and Data Engineer; no QA ad in the source): 273 labels, 178 of them vocabulary skills. On vocabulary skills the three tiers are again close (F1 0.742, 0.744 and 0.702; Appendix B.2), with GPT-4o-mini the most precise (0.843). Phuong Nhi labelled six of the ads: kappa is only 0.361, mostly because she labelled fewer skills (9 shared, 29 only Van Thong’s, 2 only hers), so the 2026 gold set rests on one annotator’s broader reading.

## 6.3 Matching

We ran `match()` end to end (ad skills from the extractor) and with the gold ad skills, which removes extraction misses.

| **Setting**    | **Accuracy** | **Macro F1** | **have P / R** | **missing P / R** |
|----------------|--------------|--------------|----------------|-------------------|
| End to end     | 0.909        | 0.739        | 0.98 / 0.79    | 0.91 / 0.97       |
| Gold ad skills | 0.927        | 0.768        | 0.97 / 0.84    | 0.95 / 0.97       |

The spaCy rows are identical, because the extra skills it finds do not change any status. With GPT-4o-mini accuracy rises to 0.944 end to end and 0.958 with gold skills, mainly through higher have recall (0.89).

Of 287 rows, 21 are wrong with gold ad skills. Eleven are have → missing, eight of them the bare “R” in the resume. Six are false partials: four come from an economics resume whose line about *forecasting* money supply the umbrella rule counts as machine learning. A stricter rule, requiring a method or library rather than a topic, would remove four of the six (Appendix B.3). There are only six partial rows in the test set, so one row moves partial recall by 17 points. We therefore put the weight on accuracy and on the have and missing classes.

## 6.4 Evidence ranking

For each have or partial row, `rank_evidence()` ranks the resume’s sentences; a sentence is correct when it contains the labelled phrase.

| **Ranker (n = 87)** | **Hit@5** | **MRR** |
|---------------------|-----------|---------|
| `rank_evidence()`   | 0.943     | 0.829   |
| TF-IDF only         | 0.943     | 0.826   |
| Embeddings only     | 0.885     | 0.753   |

The right sentence is in the top five for 94% of rows and is usually first. TF-IDF alone is almost as good, because the sentence that names the skill shares its words; the gap is within noise at n = 87. Embeddings alone are worse, since they pull up sentences about related skills. P@5 is near its ceiling of 0.2 (one gold phrase per row) and says little.

## 6.5 Subject recommendation and chat

**Subject P@3** is 0.950 for keyword and TF-IDF and 1.000 for embeddings against the 33 labelled pairs (Appendix B.5). This is not a comparison of the three methods. For a skill in the dictionary, `subject_evidence()` gives similarity 1.0 to every subject that names the skill, so those subjects always come first; all three methods share the same top three for 12 of 13 skills. Also, only about half of the recommended subjects carry a label (coverage 0.51 to 0.54), and 25 of the 33 labelled pairs are “y”, so P@3 is optimistic.

**IT skills.** Phuong Nhi checked the top three subjects for the 15 most demanded IT skills of the seven non-data roles against the Handbook (`inputs/it_skill_subjects_to_check.csv`). All 30 recommended pairs are labelled, unlike the data set above: P@3 is 0.87 counting “partly” and 0.43 counting only “y”, and the first subject is right (y or partly) for 10 of the 11 skills that have one, and “y” for 6. IT skills are more often touched (one weekly topic, a platform named as an example) than taught. The wrong matches are word-sense errors: incident response matched a clinical incident-management subject, and test automation matched two iOS subjects whose code is graded by automated tests and one on industrial automation. Terraform, CI/CD, Kubernetes and SIEM have no UTS subject; the outside courses cover them.

**Learning paths.** Van Thong read the 11 role paths of an MDSI student (`labels/role_paths_review.csv`): 26 of 32 path subjects were sensible, but 16 rows were subjects UTS lists only in Bachelor courses, among them 31250 and 43007 on the sample ad’s path. The Handbook gives them no access rule, so the recommender had treated them as open; `enrolment()` now closes Bachelor-only subjects to a postgraduate student, and the sample path is 36106, 36121, 32130 (82.8% of the demand-weighted gap).

**Chat retrieval.** At least one subject named in the reference answer is in the top five for 93.3% of the 15 questions with TF-IDF and 80.0% with embeddings; recall of all cited subjects is 77.8% and 56.7%. The difference is two questions. **LLM judge.** GPT-4o-mini answered each question from the five TF-IDF passages, and GPT-4o-mini then scored the answer against the reference from 1 to 5. Mean relevance is 4.13 and mean faithfulness 4.33; 14 of 15 answers (93%) score 4 or 5 on faithfulness. The weakest, Q05, gave a wrong subject code and left out techniques the reference lists. The same model writes and judges, which tends to flatter it, and the answers are written afresh each run: three runs gave relevance 4.13 to 4.40 and faithfulness 4.33 to 4.47. A difference below about 0.3 is therefore not a result.

## 6.6 Limits

- 20 ads (and 18 of 2026), 45 pairs, 33 skill–subject pairs and 15 chat questions give wide confidence intervals; differences between tiers are mostly smaller than the noise.
- Gold labels come from one annotator. A second annotator, on 20 overlap ads, agrees well on dictionary skills (kappa 0.856) and less on free-text skills outside the dictionary (0.686); on 6 ads of 2026 kappa is only 0.361. Extraction scores use the first annotator’s rows only.
- One ad row and one pair row carry an “unsure” mark that the loaders drop, so unsure labels count as gold, which slightly lowers recall.
- Retrieval can fill the top five with one subject under several codes (Machine Learning appears as 31005, 320513 and 321513 for one question), which lowers recall for other subjects. The fix belongs in `rag.py`.
- The 20 Seek ads are Data Scientist ads of 2019–22, and the 18 ATS ads of 2026 cover ten roles with one or two ads each and are not the JobsPipe ads that drive the role profiles, so the numbers show how well the methods work, not how well the app serves a particular role.
