# 7. Ethics and limitations

> Draft by Akash, updated with Quan's answers and corrections from the #52 review. Items still marked **[CHECK]** depend on work not yet merged; confirm at assembly and delete the tag.

## 7.1 Ethical considerations

### Privacy of uploaded CVs
A CV contains personal information: name, contact details, employment history and sometimes age or visa status. Skillabus needs the CV only to extract skills, so it keeps nothing else.

- **Third-party processing.** The CV is sent to the OpenAI API (GPT-4o-mini) only when the tier-3 extractor is switched on, that is, when an API key is configured. Emails, phone numbers and URLs are masked before the call (`mask_pii`). Person names are not yet masked, so a student's name can still reach a provider outside Australia; this is listed as a limitation (7.2) and a next step. The chat never receives the resume.
- **Retention.** The resume is held in session memory only and is never written to disk. The upload screen tells the user: "Your resume stays in memory for this session and is never stored."
- **Feedback data.** Each thumbs up/down vote stores only `timestamp, subject_code, skill_label, vote, has_taken_subject` in `data/processed/feedback.csv`. Nothing from the CV is kept with a vote.

### Consent in user testing
Classmates who tested the app were told what the test was for, that taking part was voluntary, and that their notes would be reported anonymously. They used a sample CV or their own, at their choice. **[CHECK, Quan]** Confirm this matches how the user test on 16 Oct was run.

### De-identification of the resume dataset
The test resumes come from a public Kaggle dataset (US, 2021): 2,481 resumes in 24 job categories. Van Thong masked emails, phone numbers, URLs and person names (1,071 spans) before any use (#44). A review found 7 phone numbers in an unusual format and three referees' names still in clear in two resumes; the cleaning script was corrected and re-run (#53). **[CHECK, Van Thong]** Confirm #53 is merged. The data is de-identified, not anonymous: free-text work histories can still point to a person, so it is used only for testing and is not shown in the app.

### Bias in the data
- **Job ads.** The Seek ads (2019-22) and the recent samples cover Australian data roles on a few platforms. Roles advertised elsewhere, through recruiters or by word of mouth, are missing, so "market demand" means demand as visible in online ads.
- **Employer concentration.** The 2026 sample has 22 full-text ads from 8 employers, 12 of them from Canva. One employer's wording can dominate the newest skill counts.
- **Gendered and exclusionary language.** Ad wording can carry gender-coded language and inflated requirements. Skillabus extracts skills, not wording, which limits how much of this passes through. Requirements copied from ads are still treated as genuine demand.
- **Resumes.** The test resumes are American and come from a 2021 dataset, so they may not reflect Australian students or current skills.
- **Taxonomy bias.** ESCO is a European framework. Australian job titles and skill phrasing do not always map cleanly to it, and the gap is largest for new skills (see 7.2).

### Over-reliance and the limits of advice
A recommendation such as "take 36118 to close your LLM gap" can read as authoritative. Skillabus is not academic advice. Showing the ad sentence and the subject sentence side by side is our main safeguard: the student can see why a subject was suggested and judge whether the evidence holds. The start and results screens say "Results are suggestions, not advice." **[CHECK, Quan]** A sentence telling students to confirm enrolment with the course coordinator was planned for the results screen (#38); confirm it is there.

### Data sources and terms of use
Seek and Indeed forbid scraping, so no ads were scraped from them: the Seek ads come from an existing public dataset, and recent ads come from public employer job APIs (#46). Subject profiles use only the public UTS Handbook. No subject outline or assessment brief from UTS Canvas is in the app or the repository. All data is used for non-commercial academic work.

## 7.2 Limitations

1. **Subject data is uneven.** On `main`, subject profiles have three layers, not four: learning objectives (289 rows, 67 subjects), weekly topics (444 rows, 58 subjects) and descriptions (306 rows, 70 subjects). The assessment layer had 0 rows. **[CHECK, Quan]** If #81 is merged, update to its figures: 6,848 rows, 360 subjects, four layers including 1,015 assessment tasks. Profiles are also short (median 184 words per subject), and 12 subjects, including 36106, have no weekly topics. A missing match may therefore mean missing data rather than a skill the subject does not teach: 73 of 126 technical skills matched no UTS subject, although 36118's weekly materials cover spaCy, BERT and RAG that the Handbook does not list.

2. **Emerging skills.** ESCO has no concept for many GenAI skills (LLMs, prompt engineering, RAG). Skills ESCO lacks go to a Lightcast lookup, and anything still unmatched is tagged "emerging". These skills are counted and shown, but they have no taxonomy ID, so near-duplicates (e.g. "LLMs" vs "large language models") may be counted separately.

3. **Small test sets.** Test sets were reduced to fit the deadline. **[CHECK, Hoai Thuong]** Final numbers: labelled ads __ (planned 200); skill-subject pairs __ (planned 30); chat questions __ (planned 30); CV-JD pairs __. Cohen's kappa rests on 20 ads labelled by two annotators. The results show whether the pipeline works and where it fails, but the confidence intervals are wide.

4. **Small recent sample.** The trend compares 3,204 Seek ads (2019-22) with 124 Australian LinkedIn data roles (January 2024) and 22 full-text ads from 2026; 33 further Adzuna ads count as roles only, because their text is cut at 500 characters (#46, #47). 2026 counts are used only for skills under 1% of ads before 2023 (#43). Changes in individual skill shares, especially rare ones, may be noise: the 2026 LLM share of 11 of 22 ads has a 95% interval of 31-69%.

5. **LLM extraction.** The tier-3 code keeps a skill only if it appears word for word in the text, and the evidence sentence is cut from the text, so the model cannot invent skills or quotes. Its limits are recall (it can miss skills) and run-to-run variation, reduced by temperature 0 and a response cache.

6. **Votes can be lost.** Feedback votes are written to a file on the app server. Streamlit Community Cloud resets that disk whenever the app restarts, so votes collected there are lost unless exported first.

7. **Person names reach the LLM.** As noted in 7.1, names in a CV are not masked before the tier-3 call.

8. **Demand is not outcome.** Weighting gaps by how often a skill appears in ads measures what employers ask for, not what gets candidates hired. Learning-path rankings are a proxy.

9. **Scope.** The prototype covers data roles in Australia and UTS postgraduate data subjects. It has not been tested on other degrees, universities or job families.

10. **Validation of recommendations.** Whether a subject really teaches a skill was checked against the Handbook for a small set of pairs and through tester votes. Neither replaces confirmation from subject coordinators, which would be the next step.
