# 6 Evaluation and error analysis

> Draft, 12 Oct 2026. Numbers come from `notebooks/ht_run_evaluation.py` (saved in `data/processed/eval_results.json`).
> **[TODO]** marks what is not run yet. Scripts: `src/skillabus/evaluate.py` (metrics), the notebook above (the run).

## 6.1 What was run

Section 4.7 lists four stages. Only the first two have labelled test sets in the repo today, and only the dictionary tier
runs without spaCy or an API key. The table says what the numbers below cover.

| Stage | Test set (as labelled) | Tiers run | Status |
|---|---|---|---|
| Extraction | 20 Seek ads, 217 skill labels | Dictionary (tier 1) | Done |
| Extraction | same | spaCy (tier 2), GPT-4o-mini (tier 3) | **[TODO]** needs spaCy and the cached LLM responses |
| Matching | 45 CV–JD pairs, 287 skill rows (81 have, 6 partial, 200 missing) | `match()` and `rank_evidence()` | Done |
| Subjects P@3 | **[TODO]** | | |
| Chat judge | **[TODO]** | | |
| Annotator agreement | 20 overlap ads, two annotators | Cohen's kappa | **[TODO]** needs the second annotator's file |

The test sets are much smaller than planned (200 ads, 50 pairs). Five of the 50 selected pairs have no scored skills, because
their ads name only soft skills, which `match()` leaves out. Every figure below is therefore a small-sample estimate.

**[Hoai Thuong: add one paragraph here on how the labels were made and who made them, as you decide to declare it.]**

## 6.2 Extraction

On the 20 ads, the dictionary tier finds 154 of the 217 labelled skills and adds 19 that were not labelled.

| Tier | Precision | Recall | F1 | TP / FP / FN |
|---|---|---|---|---|
| Dictionary | 0.890 | 0.710 | 0.790 | 154 / 19 / 63 |
| spaCy | **[TODO]** | | | |
| GPT-4o-mini | **[TODO]** | | | |

All labelled skills come from the dictionary, so scoring on dictionary skills alone gives the same figures.

**Where it fails.** Of the 63 misses, 25 are soft skills (communication, teamwork, stakeholder management), 13 are
programming skills and 11 are machine-learning skills. Eleven of the 13 programming misses are the bare letter "R". This is
by design, as section 4.1 explains: the dictionary matches only aliases such as "R programming", never the ambiguous bare
"R". The 19 false positives are mostly Statistics (7) and Professional skills (4): skills the dictionary found in the ad text but that were not in the labelled list. **[TODO: check these 19 against the ads to see which are label gaps and which are real errors.]** The next two tiers are meant to recover the soft skills
and the bare "R".

## 6.3 Matching

We ran `match()` two ways. In *end to end*, the ad skills come from the dictionary extractor. In *matching only*, the ad
skills are the gold labels, so the score does not include extraction misses.

| Setting | Accuracy | Macro F1 | have P / R | partial P / R | missing P / R |
|---|---|---|---|---|---|
| End to end | 0.913 | 0.749 | 0.98 / 0.79 | 0.38 / 0.50 | 0.91 / 0.97 |
| Matching only | 0.930 | 0.777 | 0.97 / 0.84 | 0.36 / 0.67 | 0.95 / 0.97 |

In the end-to-end run, 61 of the 287 labelled skills were never extracted from the ad, so they get no status. We count
them as "missing"; 45 of them really are missing, which is why accuracy stays high.

**Read partial with care.** There are only six partial rows, so one row moves partial recall by 17 points. We report the
counts and put the weight on accuracy and on the have and missing classes.

**Confusion (matching only).** Of 287 rows, 195 missing and 68 have are right. The errors are:

| Gold → predicted | Rows | What happened |
|---|---|---|
| have → missing | 11 | Eight are the bare "R" in the resume, which tier 1 does not extract; two are "predictive modelling" and one is "ETL" |
| missing → partial | 5 | See below |
| have → partial | 2 | Data visualisation (CVJD06), Statistics (CVJD24): the resume has a related tool but not the named skill |
| partial → have | 2 | Statistics (CVJD26, CVJD28) |

**The five false partials.** In four of them (CVJD37–40, "machine learning") the resume is an economics resume with a
line about *forecasting* money supply. The umbrella rule treats "time series forecasting" as part of machine learning, so it
credits a partial. Under the labelling rules this is wrong, because the resume shows no machine-learning method. In the fifth
(CVJD38, "data visualisation") the credit comes from "Proficient in Excel". Whether Excel is a visualisation tool is
debatable, and our labels say no. A stricter umbrella rule (for example, a method or library from the category, not
forecasting as a topic) would remove four of the five.

## 6.4 Evidence ranking

For each have or partial row, `rank_evidence()` ranks the resume's sentences, and the gold evidence is the labelled phrase.
A sentence counts as correct when it contains the phrase.

| Metric | Value (k = 5, n = 87) |
|---|---|
| P@5 | 0.189 |
| Hit@5 | 0.885 |
| MRR | 0.756 |

Each row has one gold phrase, so P@5 cannot exceed 0.2. Hit@5 says the right sentence is in the top five for 88.5% of
rows, and MRR of 0.756 says it is usually first or second. The baselines (TF-IDF and embedding ranking) are **[TODO]**.

## 6.5 Limits of these numbers

- 20 ads and 45 pairs are small; the confidence intervals are wide, and results from different tiers will differ by less
  than the noise unless the gap is large.
- Gold labels come from one annotator. Kappa on the 20 overlap ads (**[TODO]**) will show how far another person agrees.
- Matching and ranking use the dictionary tier. Tier 2 and tier 3 will change which skills reach `match()`.
