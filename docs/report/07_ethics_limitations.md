# 7. Ethics and limitations

> Draft by Akash, for Quan to edit. Items marked **[CHECK]** depend on how the app was actually built; confirm each with the owner before submission and delete the tag.

## 7.1 Ethical considerations

### Privacy of uploaded CVs
A CV contains personal information: name, contact details, employment history and sometimes age or visa status. Skillabus needs the CV only to extract skills, so it should keep nothing else.

- **Third-party processing.** Tier-3 skill extraction sends CV text to the OpenAI API (GPT-4o-mini). The user is therefore sharing personal data with a provider outside Australia. The upload screen should say so plainly. **[CHECK, Quan]** Is the CV sent in full, or only after contact details are stripped? Is there a notice on the upload screen?
- **Retention.** **[CHECK, Quan]** Does the deployed app on Streamlit Community Cloud write uploaded CVs to disk or logs, or hold them only in session memory? The safe position, which this section should be able to state, is that CVs are processed in memory and discarded when the session ends.
- **Feedback data.** The thumbs up/down votes are stored for validation. They must not be linked to the CV that produced them. **[CHECK]** What exactly is stored with each vote?

### Consent in user testing
Five classmates tested the app. Each was told what the test was for, that participation was voluntary, and that their notes would be reported anonymously. Testers used a sample CV or their own, at their choice. **[CHECK, Akash]** Confirm this matches what you actually told testers.

### Bias in the data
- **Job ads.** The Seek ads (2019-22) and the 2026 sample cover Australian data roles on a few platforms. Roles advertised elsewhere, through recruiters or by word of mouth are missing, so "market demand" means demand as visible in online ads.
- **Gendered and exclusionary language.** Ad wording can carry gender-coded language and inflated requirements. Skillabus extracts skills, not wording, which limits how much of this passes through. Requirements copied from ads are still treated as genuine demand.
- **Resumes.** **[CHECK, Van Thong]** Where do the resumes come from? If it is a public dataset, note its origin and any demographic skew (e.g. mostly US or Indian candidates).
- **Taxonomy bias.** ESCO is a European framework. Australian job titles and skill phrasing do not always map cleanly to it, and the gap is largest for new skills (see 7.2).

### Over-reliance and the limits of advice
A recommendation such as "take 36118 to close your LLM gap" can read as authoritative. Skillabus is not academic advice. It does not check prerequisites, timetable availability, credit-point rules or a student's own interests. Showing the ad sentence and the subject sentence side by side is our main safeguard: the student can see why a subject was suggested and judge whether the evidence holds. The results screen should still tell students to confirm enrolment decisions with the course coordinator. **[CHECK, Quan]** Is that note on the results screen?

### Data sources and terms of use
Job ads were collected from public listings and existing datasets for non-commercial academic use. Subject content comes from the UTS Handbook and subject materials. Some of that material (weekly topics, assessment briefs) is shared with enrolled students, not the public. **[CHECK, Van Thong]** Confirm that no restricted material is published in the deployed app or the public repo. If any is, limit the app to short extracts.

## 7.2 Limitations

1. **Subject data is uneven.** Subject profiles have four layers (learning objective, assessment, weekly topic, description), but not every subject has all four. Assessment details were not collected in full for the 19 MDSI subjects. **[CHECK, Akash/Van Thong]** State how many subjects have each layer. For subjects with thin profiles, a missing match may mean missing data rather than a skill the subject does not teach. Recommendations therefore favour subjects with richer published information.

2. **Emerging skills.** ESCO does not yet contain many GenAI skills (e.g. prompt engineering, RAG, LLM fine-tuning). Skills ESCO lacks go to a Lightcast lookup, and anything still unmatched is tagged "emerging". These skills are counted and shown, but they have no taxonomy ID, so near-duplicates (e.g. "LLMs" vs "large language models") may be counted separately.

3. **Small test sets.** Test sets were reduced to fit the deadline. **[CHECK, fill in final numbers]** Labelled ads: __ (planned 200). Skill-subject pairs: __ (planned 30). Chat questions: __ (planned 30). CV-JD pairs: __. Inter-annotator agreement (Cohen's kappa) rests on 20 ads labelled by two annotators. The results show whether the pipeline works and where it fails, but the confidence intervals are wide.

4. **Small 2026 sample.** The 2019-22 vs 2026 trend compares a large historical set with about 150 recent ads (**[CHECK, Van Thong]** final count). Changes in individual skill frequencies, especially rare ones, may be noise.

5. **LLM extraction.** GPT-4o-mini output can vary between runs and can occasionally return skills that are not in the text. Tiers 1-2 (dictionary, spaCy NER) give a deterministic baseline, and tier 3's output is constrained to the same schema, but tier-3 results are not fully reproducible.

6. **Demand is not outcome.** Weighting gaps by how often a skill appears in ads measures what employers ask for, not what gets candidates hired. Learning-path rankings are a proxy.

7. **Scope.** The prototype covers data roles in Australia and the 19 MDSI subjects at UTS. It has not been tested on other degrees, universities or job families.

8. **Validation of recommendations.** Whether a subject really teaches a skill was checked against the Handbook for a small set of pairs and through tester votes. Neither is a substitute for confirmation from subject coordinators, which would be the next step.
