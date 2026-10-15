# 3_tuning: which number was set on which data

Every threshold, weight and cap the pipeline uses, where it lives, and how it was chosen. Rule: no
threshold or prompt is tuned on the test sets in `data/4_evaluation/labels/` (the 200 labelled ads,
the 50 CV-JD pairs, the 30 skill-subject pairs, the 30 chat questions). A number tuned later goes here
with the data it was tuned on, the date and who did it. Owner: Quan (table); each row's owner is the
person in "Who".

"Judgement" means set by reading examples, not fitted on data. Line numbers are as of 15 Oct 2026.

| Parameter | Value | Where | Set on | Date | Who |
|---|---|---|---|---|---|
| `ESCO_MIN_SIM`: nearest ESCO label counts if cosine at least | 0.82 (env `SKILLABUS_ESCO_MIN_SIM`) | `src/skillabus/normalise.py:42` | Judgement, not tuned. If tuned: a held-out set of ads, not the labelled test ads (plan T3) | 4 Oct | Quan |
| `FUZZY_MIN`: the fuzzy-string mapper of the normalisation error table counts a match at | difflib ratio 0.85 | `notebooks/pn_normalisation_errors.py:53` | Judgement, set before the table was built and not changed since; a comparison baseline only, the pipeline does not use it | 14 Oct | Phuong Nhi |
| Lightcast name must be this close to the phrase | `SequenceMatcher` ratio 0.6, or one contains the other | `src/skillabus/normalise.py:196` | Judgement; untested (no Lightcast credentials) | 4 Oct | Quan |
| `MIN_SIM["embed"]`: an unnamed subject row counts as evidence above | 0.55 | `src/skillabus/recommend.py:46` | 22 data skills against the 429 Handbook rows of the 70-subject profiles, closest unnamed rows read by hand (`notebooks/pn_calibrate_matching.py`); at 0.50 about half were generic. Rechecked for 12 IT skills over all 6,853 rows (plan T1, `--it`): the 55 closest unnamed rows judged by hand (`data/3_tuning/t1_it_unnamed_rows.csv`), precision 7/7 at 0.55, 17/19 judged at 0.50 (at most 15 rows per skill, so 8 more Data security rows at 0.50-0.55 are unjudged); kept at 0.55 | 8 Oct; T1 15 Oct | Phuong Nhi |
| `MIN_SIM["tfidf"]` | 0.35 | `src/skillabus/recommend.py:46` | Same reading: above it only rows sharing the skill's words | 8 Oct | Phuong Nhi |
| `LAYER_WEIGHT`: learning objective / assessment / weekly topic / description | 1.0 / 0.9 / 0.8 / 0.5 | `src/skillabus/recommend.py:39` (same in `app/baseline.py:35`) | Judgement: taught and assessed > graded > covered in class > mentioned | 8 Oct | Phuong Nhi |
| `EXTRA_ROW_BONUS`, `MAX_EXTRA_ROWS`: per further row about the skill | 0.15, at most 3 rows | `src/skillabus/recommend.py:47-48` | Judgement | 8 Oct | Phuong Nhi |
| `TITLE_BONUS`: the subject's name names the skill | 0.40 | `src/skillabus/recommend.py:49` | Judgement ("94691 Deep Learning" must beat a passing mention) | 8 Oct | Phuong Nhi |
| `HOME_BONUS`: MDSI (C04372) subjects win ties | 0.10 | `src/skillabus/recommend.py:51` | Judgement | 8 Oct | Phuong Nhi |
| `COVER_RATIO`, `SUBJECTS_PER_SKILL`: a subject covers a skill if at least this share of the best subject's strength and in the top n | 0.60, top 5 | `src/skillabus/recommend.py:52-53` | Judgement | 8 Oct | Phuong Nhi |
| `MAX_PATH`, `MAX_SUBJECTS`: subjects in the path, recommendations shown | 3, 10 | `src/skillabus/recommend.py:54-55` | Judgement (one or two semesters of electives) | 8 Oct | Phuong Nhi |
| `NEW_SKILL_PCT`: below this 2019-22 share a skill is "new" and weighted by its 2026 lower bound | 1.0% | `src/skillabus/recommend.py:163` | Judgement (LLMs and generative AI are 0% in 2019-22) | 12 Oct | Quan |
| `MIN_SCORE`: chat passages below this score are dropped | embed 0.30, TF-IDF 0.05 | `src/skillabus/rag.py:56` | Judgement on example questions; an off-topic question must return nothing (`tests/test_rag.py`) | 10 Oct | Van Thong |
| Partial credit in the ad-resume score | have 1, partial 0.5, missing 0 | `src/skillabus/match.py:244` | Judgement | 8 Oct | Phuong Nhi |
| `UMBRELLA`, `NOT_TRANSFERABLE`: which categories give partial credit | 7 umbrella skills; Programming and Professional never | `src/skillabus/match.py:41-51` | Judgement; skill-name embeddings could not separate substitutes (`notebooks/pn_calibrate_matching.py`, 8 Oct) | 8 Oct | Phuong Nhi |
| Emerging skills: `MIN_ADS`, `MIN_EMPLOYERS`, `MIN_Z` | 3 ads, 2 employers, z 1.96 (about 95%) | `src/skillabus/emerging.py:60-62` | Judgement; one employer posts many 2026 ads, so 2 employers | 14 Oct | Phuong Nhi |
| Emerging skills: `PRIOR`, `PRIOR_FLOOR`, `MAX_N`, `TOP` | 10 pseudo-ads, 0.5 (Jeffreys), 3-grams, 50 rows | `src/skillabus/emerging.py:59-65` | Monroe, Colaresi and Quinn (2008); floor and `TOP` read off the 2026 run | 14 Oct | Phuong Nhi |
| Emerging skills: `BOILERPLATE` words | about 60 words | `src/skillabus/emerging.py:76` | Read off the n-gram output, not a test set | 14 Oct | Phuong Nhi |
| GPT extraction: `PROMPT_VERSION`, temperature, `MAX_CHARS` | v3, 0, 12,000 characters | `src/skillabus/llm_extract.py:27-28`, `:87` | Prompt checked on the Robert Walters ad, the sample resume and a CBA Sept 2026 ad (none in the test sets) | 10 Oct | Quan |
| Chat answer temperature | 0.2 | `app/chat.py:86` | Judgement | 4 Oct | Quan |
| Baseline (fallback) MDSI bonus | +0.2 | `app/baseline.py:130` | Judgement | 4 Oct | Quan |
| spaCy candidate length (tier 2) | 1-4 tokens | `src/skillabus/extract.py:296` | Judgement | 8 Oct | Phuong Nhi |

Nothing is stored here yet. When a parameter is tuned, put the held-out data (or a pointer to it) and
the sweep output in this folder and update its row.
