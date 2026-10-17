# 7 Ethics and limitations

## 7.1 Ethics

**Data collection.** Seek, LinkedIn, Indeed and Glassdoor forbid scraping, so older ads come from
published Kaggle datasets and 2026 ads from APIs. JobsPipe aggregates LinkedIn and Indeed postings
under its own licence, which forbids redistributing their text and allows one free account per
person: we store only the skills found in each ad and its link, and used three members' own
accounts. How JobsPipe collects postings from platforms that forbid scraping is outside our
control. The UTS Handbook's `robots.txt` disallows crawling; we read its public pages one request
at a time, at least 1.2 seconds apart. Students reported their subjects' skills by name only; no
Canvas material is stored.

**Privacy.** A pasted resume stays in memory and is never written to disk. Before the GPT-4o-mini
tier, emails, URLs and phone numbers are masked, but names are not, a gap the upload screen should
state. The response cache keeps only skill lists, and a feedback vote never links to a resume. The
test resumes are de-identified, not anonymous.

**Bias and over-reliance.** "Demand" means demand visible in online ads: 408 of the 1,932 JobsPipe
ads are from recruitment agencies, and the job boards we read belong mostly to technology
companies. ESCO is European and maps Australian phrasing unevenly. The app checks prerequisites
and teaching sessions but not credit-point rules, and its results screen does not yet tell
students to confirm choices with their course coordinator.

## 7.2 Limitations

1. **Small test sets:** 20 labelled ads, 45 CV–JD pairs, 33 skill–subject pairs and 15 chat
   questions, one annotator (kappa 0.856 on 20 shared ads, but only 0.361 on 6 ads of 2026; section 6.6).
2. **Small samples:** 89–216 ads per role in 2026 (up to ±10 points); the pre-2022 trend rests on
   3,204 Seek ads of 2019–22 for Data Scientist but on 43–944 ads of 2020–21 for nine other roles,
   and Machine Learning Engineer has none; shares from different sources are not comparable.
3. **The "AI" trade-off:** counting Artificial intelligence only in phrases such as "AI models"
   drops recruiter tools and company names but misses ads that write only "AI": on Adzuna, 12% of
   Data Scientist ads say "artificial intelligence" and 66% "AI".
4. **Uneven subject text:** nine MDSI subjects have no topic list, two students reported, and
   "named" is not "taught in depth".
5. **Course level:** reading the role paths (section 6) found Bachelor-only subjects in an MDSI
   student's paths; they are now closed to postgraduates, so IT roles get fewer UTS subjects.
6. **No user test:** the planned test with five classmates did not happen, so ease of use is
   judged by the team only (section 8).
7. **Demand is not outcome:** ads show what employers ask for, not who is hired.
