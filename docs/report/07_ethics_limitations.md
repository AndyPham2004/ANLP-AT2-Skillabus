# 7 Ethics and limitations

## 7.1 Ethics

**Data collection.** Seek, LinkedIn, Indeed and Glassdoor forbid scraping, so older ads come from
published Kaggle datasets (CC0, ODC-By) and 2026 ads from APIs. JobsPipe aggregates LinkedIn and
Indeed postings under its own licence and forbids redistributing their text, so we store only the
skills found in each ad and its link. The UTS Handbook's `robots.txt` disallows crawling; we read
its public pages one request at a time, at least 1.2 seconds apart. Students reported what their
subjects taught as skill names only; no Canvas material is stored.

**Privacy.** A pasted resume stays in memory and is never written to disk. For the GPT-4o-mini
tier, emails, URLs and phone numbers are masked before the text goes to OpenAI, but names are not,
a gap the upload screen should state. The response cache keeps only skill lists, and a feedback
vote stores the subject, skill and vote, never the resume. The test resumes are de-identified, not
anonymous.

**Bias and over-reliance.** "Demand" means demand visible in online ads: 209 of the 793 JobsPipe
ads come from recruitment agencies, and the job boards we read belong mostly to technology
companies. ESCO is European, and Australian phrasing maps to it unevenly. The app checks
prerequisites and teaching sessions but not credit-point rules or interests, and its results
screen does not yet tell students to confirm choices with their course coordinator.

## 7.2 Limitations

1. **Small test sets:** 20 labelled ads (planned 200), 45 CV–JD pairs, 33 skill–subject pairs and
   15 chat questions, labelled by one annotator (kappa 0.856 on 20 shared ads; section 6.6).
2. **Small samples per role:** about 70 ads per role in 2026 (±11 points); the 2019–22 trend
   exists for Data Scientist only, and shares from different sources are not comparable.
3. **The "AI" trade-off:** counting Artificial intelligence only in phrases such as "AI models"
   drops recruiter tools and company names but misses ads that write only "AI". On Adzuna, 12% of
   Data Scientist ads say "artificial intelligence" and 66% say "AI"; the true share lies between.
4. **Uneven subject text:** nine MDSI subjects have no topic list, student reports come from two
   students, and "named" is not "taught in depth".
5. **No user test:** the planned test with five classmates did not happen, so ease of use is
   judged by the team only (section 8).
6. **Demand is not outcome:** ad frequency measures what employers ask for, not who is hired.
