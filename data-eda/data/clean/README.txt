================================================================================
 CLEANED DATA  --  Skillabus (36118 AT2B)          Van Thong, 9 Oct 2026
 Five files, 44 MB. Every one is rebuilt by a script in data-eda/src/.
================================================================================

 WHO NEEDS WHAT

   Akash        seek_label_sample_200.csv       label all 200, batches of 50
   Hoai Thuong  seek_label_sample_200.csv       label the 20 with double_label = y
                resumes_us_2021_clean.csv       pick the 50 CV-JD pairs from here
   Phuong Nhi   jobs_au_seek_datascientist_2019-2022_clean.csv   run extraction on this
   Quan         esco_label_lookup.csv           normalise(): surface form -> ESCO URI

 Resumes are de-identified (names, emails, phones, URLs masked), not anonymous.


--------------------------------------------------------------------------------
seek_label_sample_200.csv                       200 ads     src/make_label_sample.py
--------------------------------------------------------------------------------
 batch          1-4, fifty ads each
 double_label   y on the first 20 (all in batch 1). Both Akash and Hoai Thuong
                label these, so Cohen's kappa is on ads you both saw.
 ad_id          the key. Copy it exactly into data/labels/ad_skills.csv.
 Drawn with a fixed seed (36118): re-running gives the same 200 ads.
 No two ads share the same text. The 9 Oct version had 4 re-listings drawn
 twice; on 10 Oct those 4 were swapped for unused ads, in place. The other 196
 rows, the batches and the 20 double-label rows did not change.
 If anyone already started labelling other ads, keep those and tell the group.


--------------------------------------------------------------------------------
jobs_au_seek_datascientist_2019-2022_clean.csv  3,204 ads   src/clean_seek.py
--------------------------------------------------------------------------------
 The primary corpus with the ad text repaired. ad_id and title are unchanged.

 Re-listings: 697 ads repeat another ad's text exactly (same employer, posted
 again on a later date or in another city), so there are 2,507 unique ads among
 the 3,204 listings. All counts are per listing, as on the poster. Counting
 unique ads instead changes no skill by more than 2.1 points (rank correlation
 0.998), so the ranking does not depend on the choice.

 What was wrong: the Kaggle dataset stripped HTML without putting spaces back,
 so 80% of ads had words welded together - "...Power BI and TableauSuperior
 analytical skills...". An extractor with word boundaries misses those.

 What was done: the dataset carries two renderings of every ad (mobile and
 desktop). A glued word is split only where the OTHER rendering of the same ad
 shows a break. 13,181 joins split; 11,574 left alone, which are mostly real
 words (PhD, TensorFlow, NoSQL, PySpark, JavaScript) that must not be split.
 Bullets are one per line, so sentence splitting works.

 Effect on skill counts: Python 82.8% -> 84.5%, Communication 28.3 -> 30.0,
 no skill goes down, top 15 identical, rank correlation 0.9996 with the old text.
 The poster and data/processed/ still use the old text. LABELS MUST BE MADE ON
 THIS FILE, and extraction for evaluation must run on this file too, so the
 extractor and the labeller see the same words.


--------------------------------------------------------------------------------
jobs_au_recent_2024-2026_clean.csv              179 roles   src/build_recent_sample.py
--------------------------------------------------------------------------------
 Recent Australian data roles, one row per role, same title filter for all.
   period 2026-09  22 full text (job-board APIs) + 33 Adzuna (text cut at 500
                   characters: full_text = False)
   period 2024-01  124 full text (LinkedIn, Kaggle asaniczka, ODC-By)
 For skill shares use full_text == True only, and never pool the two periods.
 The 2026 full-text sample is 22 roles from 8 employers, 12 of them from
 Canva: report a direction, not a precise percentage. The title filter keeps AI-titled
 engineering roles ("AI Video Lead"), which raises LLM mentions in 2026.


--------------------------------------------------------------------------------
resumes_us_2021_clean.csv                       2,481 resumes   src/clean_resumes.py
--------------------------------------------------------------------------------
 resume_id, category, resume_text, n_data_skills

 Masked: emails (19 resumes), phone numbers incl. international (62),
 URLs (101), and person names (1,146 in 551 resumes: 1,069 by spaCy NER, 2 by
 the 'Summary <Name> is' rule, 75 by the title / credential rule) -> [NAME].
 14 Oct 2026 (#53): phone numbers with spaces around the dash ("(281) 491 - 3225")
 and 75 more names: after Dr./Mr./Ms./Mrs./Prof., or before RN, LVN, LPN, CCM,
 NP, PhD (referees whose first name the name list lacks). 39 resumes changed;
 n_data_skills unchanged; none of them is in the CV-JD pairs.
 Employer names were already "Company Name" in the source.

 How names were found: spaCy NER tags 16,451 "PERSON" spans, but most are
 resume words ("Developed", "Dean") or skills ("Java", "Oracle", "MS Word").
 A span is masked only if it is two or more capitalised words, starts with a
 known first name, appears in at most two resumes, and is not a skill or an
 O*NET tool name. Skill counts are unchanged after masking (Java 301 -> 301,
 Oracle 577 -> 577, Spring Boot 2 -> 2). About half the masked spans are real
 names; the rest are harmless phrases ("Dean List").
 STILL NOT ANONYMOUS: a name in capitals or a lone first name can survive. The
 app must still mask with spaCy before any LLM call (ethics section).

 THERE IS NO DATA-SCIENCE CATEGORY among the 24 (IT, chef, advocate, ...).
 n_data_skills = how many of python, sql, machine learning, statistics, data
 analysis, tableau/power bi the resume mentions:
     >= 2   125 resumes
     >= 3    37 resumes
     >= 4    11 resumes
 For CV-JD pairs against Data Scientist ads, draw from n_data_skills >= 2.
 Using a chef resume against a data ad tests nothing.


--------------------------------------------------------------------------------
esco_skills_clean.csv                           13,960 concepts   src/clean_esco.py
esco_label_lookup.csv                           100,886 rows
--------------------------------------------------------------------------------
 skills_clean   one row per ESCO skill; alt_labels pipe-separated (the source
                file uses newlines inside a cell, which most tools mangle)
 label_lookup   label (lowercase), concept_uri, preferred_label,
                label_type (preferred / alt / hidden), ambiguous (True/False)

 Ambiguity: 716 labels (0.7%) point at more than one concept. The one that
 matters for us: "sql" -> both "SQL" and "database management systems".
 Lookup alone cannot settle those; that is the honest answer to the marker's
 "how are ambiguous skills handled?".

 Gaps: "data visualisation" is NOT an ESCO label; "tableau" maps to the
 generic "data visualisation software". Only 36% of our dictionary maps.

 Size: the lookup is 14.3 MB, over the repo's 5 MB limit. For the deployed
 app, filter it to the labels our dictionary can produce before committing.


--------------------------------------------------------------------------------
 REBUILD EVERYTHING (from data-eda/)
--------------------------------------------------------------------------------
   python src/clean_seek.py
   python src/clean_resumes.py
   python src/clean_esco.py
   python src/make_label_sample.py      (needs the clean Seek file first)
   python src/build_recent_sample.py
