# 7 Ethics and limitations

> Draft by Akash, updated 15 Oct with Quan's answers (#52, #89 reviews) and the data merged on 14 Oct (#81, #87, #95, #99) and the 2026 ads of 16 Oct (#134, #136, #138). The one **[CHECK]** left is the user test, run on 16 Oct.

## 7.1 Ethical considerations

### Privacy of uploaded CVs
A CV contains personal information: name, contact details, employment history and sometimes age or visa status. Skillabus needs the CV only to extract skills, so it keeps nothing else.

- **Third-party processing.** The CV is sent to the OpenAI API (GPT-4o-mini) only when the tier-3 extractor is switched on, that is, when an API key is configured. Emails, phone numbers and URLs are masked before the call (`mask_pii`). Person names are not yet masked, so a student's name can still reach a provider outside Australia; this is listed as a limitation (7.2) and a next step. The chat never receives the resume.
- **Retention.** The resume is held in session memory only; its text is never written to disk. When tier 3 runs, the list of skills the model returns for the masked CV is cached under `data/cache/llm_extract/`, keyed by a hash of the text (`llm_extract.py`). The upload screen tells the user: "Your resume stays in memory for this session and is never stored."
- **Feedback data.** Each thumbs up/down vote stores only `timestamp, subject_code, skill_label, vote, has_taken_subject` in `data/runtime/feedback.csv` (not in git). Nothing from the CV is kept with a vote.

### Consent in user testing
Classmates who tested the app were told what the test was for, that taking part was voluntary, and that their notes would be reported anonymously. They used a sample CV or their own, at their choice. **[CHECK, Quan]** Confirm this matches how the user test on 16 Oct was run.

### De-identification of the resume dataset
The test resumes come from a public Kaggle dataset (US, 2021): 2,481 resumes in 24 job categories. Van Thong masked emails, phone numbers, URLs and person names before any use (#44; 1,146 names after the follow-up fix, `data/README.md`). A review found 7 phone numbers in an unusual format and three referees' names still in clear in two resumes; the cleaning script was corrected and re-run (#95). Recruiter emails and phone numbers in the 2026 job ads are masked too (#87), although two landline numbers in ads were flagged as still surviving. The data is de-identified, not anonymous: free-text work histories can still point to a person, so it is used only for testing and is not shown in the app.

### Bias in the data
- **Job ads.** The Seek ads (2019-22) cover data scientists only; the 2026 ads (JobsPipe, 65 employers' job boards, Adzuna counts) cover 11 IT roles but only what is advertised online. Roles advertised elsewhere, through recruiters or by word of mouth, are missing, so "market demand" means demand as visible in online ads.
- **Employer and agency concentration.** The 392 job-board ads come from 65 employers that use a modern applicant-tracking system, mostly technology companies in Sydney and Melbourne. In the 793 JobsPipe ads, 209 are from recruitment agencies, which repeat skill lists across clients (`data/2_demand/README.md`). Either can tilt a role's skill shares.
- **Gendered and exclusionary language.** Ad wording can carry gender-coded language and inflated requirements. Skillabus extracts skills, not wording, which limits how much of this passes through. Requirements copied from ads are still treated as genuine demand.
- **Resumes.** The test resumes are American and come from a 2021 dataset, so they may not reflect Australian students or current skills.
- **Taxonomy bias.** ESCO is a European framework. Australian job titles and skill phrasing do not always map cleanly to it, and the gap is largest for new skills (see 7.2).

### Over-reliance and the limits of advice
A recommendation such as "take 36118 to close your LLM gap" can read as authoritative. Skillabus is not academic advice. Showing the ad sentence and the subject sentence side by side is our main safeguard: the student can see why a subject was suggested and judge whether the evidence holds. The start and results screens say "Results are suggestions, not advice." (`app/Home.py`). There is no sentence telling students to confirm enrolment with their course coordinator; adding one is a next step.

### Data sources and terms of use
Seek and Indeed forbid scraping, so no ads were scraped from them: the Seek ads come from an existing public dataset, recent ads from public employer job-board APIs (#46, #136), and the JobsPipe ads from a commercial aggregator of Indeed and LinkedIn postings, used through its API within its quota (#138). JobsPipe's terms forbid redistributing its data in bulk, so the ad text is never committed: only each ad's link, metadata and the skills found in it at fetch time. Adzuna is used for search counts only, never text (#134). Subject profiles use only the public UTS Handbook, including the assessment summaries it publishes for each offering. No subject outline or assessment brief from UTS Canvas is in the app or the repository. The 56 external courses (`external_courses.csv`, 1,167 rows from 42 providers) quote each provider's own public course page with its `source_url` and `date_checked`; the text was collected by an AI assistant (`collected_by = Claude (web)`) and the links were then checked by hand (#96). All data is used for non-commercial academic work.

## 7.2 Limitations

1. **Subject data is uneven.** Subject profiles cover 360 subjects in 44 UTS courses, 6,853 rows in four layers: learning objectives 1,516, assessment tasks 1,015 (326 subjects), weekly topics 2,769 and descriptions 1,553 (`data/1_knowledge/uts/subject_profiles.md`). Profiles are still short (median 479 words per subject; 218 for the 19 MDSI subjects), and 33 subjects, 9 of them in MDSI, have no weekly topics. A missing match may therefore mean missing data rather than a skill the subject does not teach: 54 of 126 technical skills matched no UTS subject (`data/2_demand/skills_not_taught_by_uts.csv`), although 36118's weekly materials cover spaCy, BERT and RAG that the Handbook does not list. For those 54 skills the app falls back to external courses, which carry no UTS credit. Student-reported taught skills for 9 MDSI subjects (`data/1_knowledge/uts/taught_skills_student_reported.csv`, #126, #144) add some of what the Handbook misses, but they are what two students remember, not official course content.

2. **Emerging skills.** ESCO has no concept for many GenAI skills (LLMs, prompt engineering, RAG). The pipeline is designed to send skills ESCO lacks to a Lightcast lookup and tag anything still unmatched "emerging"; without Lightcast API credentials, every non-ESCO skill is tagged emerging in practice. These skills are counted and shown, but they have no taxonomy ID, so near-duplicates (e.g. "LLMs" vs "large language models") may be counted separately.

3. **Small test sets.** Test sets were reduced to fit the deadline (`data/labels/`): 20 labelled ads instead of 200, each labelled by two annotators (534 skill labels; Cohen's kappa rests on these 20); 33 skill-subject pairs; 15 chat questions instead of 30; and 45 CV-JD pairs (287 skill rows, 16 ads, 10 resumes). The results show whether the pipeline works and where it fails, but the confidence intervals are wide.

4. **Recent demand rests on a few weeks of ads.** The 2026 shares the app shows come from 793 JobsPipe ads posted 23 Sep-16 Oct 2026, 63 to 79 per role (`data/2_demand/role_skill_demand.csv`, source `jobspipe_2026`). With about 70 ads per role, one ad moves a share by about 1.4 points, and a single month cannot show seasonality. The skills in those ads were found by the tier-1 matcher at fetch time, so they share its recall limits. The 2019-22 Seek ads remain the trend baseline for Data Scientist only; the earlier 22-ad 2026 sample (9 data scientists) is kept for the trend in section 3 and must not be added to the JobsPipe or job-board counts, because the sources overlap.

5. **LLM extraction.** The tier-3 code keeps a skill only if it appears word for word in the text, and the evidence sentence is cut from the text, so the model cannot invent skills or quotes. Its limits are recall (it can miss skills) and run-to-run variation, reduced by temperature 0 and a response cache.

6. **Votes can be lost.** Feedback votes are written to a file on the app server. Streamlit Community Cloud resets that disk whenever the app restarts, so votes collected there are lost unless exported first.

7. **Person names reach the LLM.** As noted in 7.1, names in a CV are not masked before the tier-3 call.

8. **Demand is not outcome.** Weighting gaps by how often a skill appears in ads measures what employers ask for, not what gets candidates hired. Learning-path rankings are a proxy.

9. **Scope.** The prototype covers 11 Australian IT roles and 360 UTS subjects in 44 courses (data, IT, AI, analytics, maths, cybersecurity), bachelor courses included. It has not been tested on other faculties, universities or job families.

10. **Validation of recommendations.** Whether a subject really teaches a skill was checked against the Handbook for a small set of pairs and through tester votes. Neither replaces confirmation from subject coordinators, which would be the next step.
