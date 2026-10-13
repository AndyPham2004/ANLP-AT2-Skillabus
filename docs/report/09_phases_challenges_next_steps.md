# 9. Project phases, contributions, challenges and next steps

> Draft by Akash (#78), for Quan to edit and place at assembly. Sources: issues, pull requests and their review comments, `docs/team_plan.md` and `docs/plan/ideas_2026-10-12.md` section 7. Items marked **[CHECK]** need confirming before submission.

## 9.1 Project phases

| Phase | Dates | What happened | Main outputs |
|---|---|---|---|
| 0. Poster (AT2A) | to late Sep | Baseline pipeline on 3,204 Seek Data Scientist ads (2019-22) and the UTS Handbook; poster submitted. Marker feedback: innovation not stated, subject data too thin, methods not validated. | Poster, `docs/handoffs/` |
| 1. Re-plan | 3-4 Oct | Plan rebuilt around the three feedback points. One task = one issue = one branch = one reviewed pull request; Quan approves every merge. Data contract agreed between pipeline and app. | `docs/team_plan.md`, `docs/data_contract.md` (#35) |
| 2. Build | 3-11 Oct | Each stage built and tested on its own branch: cleaning and four-layer subject profiles, extraction tiers 1-3, ESCO/Lightcast normalisation, matching, recommendation with evidence, learning path, FAISS retrieval, Streamlit app, evaluation harness. | PRs #35-#51 |
| 3. Integrate and review | 11-12 Oct | Stack merged in dependency order; 16 PRs merged on 12 Oct, 110 tests passing, all three app flows running end to end. Report drafts for sections 1-5 and 7 in `main`. | `main` at dcbfd3e |
| 4. Deepen | 12-16 Oct | Deadline moved to 17 Oct. Second plan (ideas doc section 7): full Handbook scrape (360 subjects, prerequisites, sessions, assessment layer), prerequisite-aware recommendation, external courses for skills UTS does not teach, larger 2026 sample, role profiles, emerging-skill detection, full evaluation. | PRs #80-#87 **[CHECK: update with what is merged by 16 Oct]** |
| 5. Assemble and submit | 16-17 Oct | User test, report assembly, demo, submission. | Report PDF, app link |

## 9.2 Contributions by team member

| Member | Role | Main contributions |
|---|---|---|
| Quan Pham | Tech lead, app | Data contract (#35); Streamlit app and wireframes (#36); GPT-4o-mini extraction tier and ESCO/Lightcast normalisation (#37); deployment and QR code (#38); report sections 1, 2, 5 and 8 (#39); review and integration of every PR; Handbook scrape of 360 subjects with prerequisites, sessions and assessments (#81); user testing; report assembly and submission. |
| Van Thong (tompham9016) | Data | Cleaning of Seek ads, resumes and ESCO, including the glued-word repair and resume de-identification (#44); four-layer subject profiles (#45); 2026 Australian ad sample and three-period skill counts (#46, #47, #87); FAISS retrieval (#48); report section 3 (#49); second-annotator labels for kappa (#85); role profiles for 7 data and IT roles (#86). |
| Phuong Nhi (nhinguyenuts) | Pipeline | Extraction tiers 1-2: dictionary and spaCy (#40); matching with TF-IDF and embeddings, subject recommendation with ranked evidence, greedy demand-weighted learning path (#43, #51); report section 4 (#50); prerequisite- and session-aware recommendation (#82, #83); emerging-skill detection (#84). |
| Hoai Thuong (hoaithuongnguyen-uts) | Evaluation | Evaluation harness for the four stages and Cohen's kappa (#41); CV-JD pair template and labelling rules (#42); ad skill labels for the 20 overlap ads (#55); evaluation runs and report section 6 (#54, #56); skill-subject pairs and chat test questions. |
| Akash Tomar (Akashtom98) | Related work, ethics, report | Related-work comparison of nine systems and the innovation statement (#30); ethics and limitations section (#31, #52); this section on phases, challenges and next steps (#78); external-course list review (#77); appendix and proofreading (#79). |

Every pull request was reviewed by a second member before Quan approved the merge, so each stage was checked by someone other than its author.

## 9.3 Challenges and how we solved them

| Challenge | Effect | Solution |
|---|---|---|
| **Wrong ESCO concept.** ESCO has no Apache Spark; the closest label, "SPARK", is a Java web framework. | Spark gaps were linked to the wrong skill. | The link is blocked in normalisation and dropped from the mock data (#37); recorded for error analysis. |
| **Broad ESCO concepts.** Several tools share one ESCO id (e.g. NumPy, scikit-learn, PyTorch, matplotlib). | A resume with matplotlib counted as "having" PyTorch; Power BI as having Tableau. | `match()` compares dictionary skills by name before falling back to the shared ESCO id (#43). |
| **No LLM skills in ESCO.** GenAI, LLMs, RAG and prompt engineering have no ESCO concept. | The newest skills would be dropped. | Lightcast lookup, then an "emerging" tag shown in the app; automatic detection of new phrases in the 2026 ads (#37, #84). |
| **PII masking too greedy.** The phone pattern masked year ranges and salaries ("2019-2022" became `[PHONE]`). | `[PHONE]` appeared inside evidence quotes. | Phones need 8+ digits and plain ranges are skipped, with tests (#37). Some resume phone formats and referee names were also missed, fixed in a follow-up (#53). |
| **`C#` read as a comment.** Reading the skill dictionary with `comment="#"` cut "C#" to "C". | C# demand was lost. | Comment lines skipped explicitly; C# keeps its 2.6% demand (#37). |
| **Seek and Indeed forbid scraping.** | The plan's 150 fresh 2026 ads could not be collected legitimately. | Public ATS job APIs and LinkedIn Jan 2024 data instead: 22 full-text 2026 ads plus a 2024 middle point; Indeed dropped (#46). 2026 counts are used only for skills under 1% before 2023, so the small sample cannot swing demand weights (#43). |
| **Thin Handbook data.** Learning objectives miss what subjects teach (the marker's 36118 example); 73 of 126 technical skills matched no subject. | Many gaps had no subject recommendation. | Four-layer profiles, then a full Handbook scrape adding an assessment layer (#45, #81); external courses for skills no UTS subject teaches (#77). |
| **Prerequisites.** 43023 Emerging Topics in AI ranked second on the poster ad but needs a subject outside MDSI; 36118 needs three earlier subjects. | The learning path recommended subjects a student cannot enrol in. | `recommend()` adds missing prerequisites, respects sessions and drops closed subjects with a reason (#82). |
| **Light deployment.** Streamlit Community Cloud runs without PyTorch. | The app silently fell back to the baseline on every request; the LLM tier never ran. | Embedding steps skip cleanly when unavailable, and the pipeline path calls tier 3 (#37, #38). |
| **Many dependent branches.** Stages built in parallel depended on each other. | Merge conflicts and tests failing on single branches. | Agreed merge order (#35 → #36 → #37 → #38 → #43), shared data contract, 110 tests run on the merged stack. |
| **Team coordination.** Five members, one remote, several tasks late. | Test sets risked holding up evaluation. | Every task had a backup owner, late test sets shrank instead of blocking (e.g. 20 overlap ads, 15 skill-subject pairs), and work was redistributed in the 12 Oct plan. |

## 9.4 Recommendations and next steps

1. **Career paths.** Take a student's background and target role and propose a chain of 2-3 roles (e.g. supply-chain graduate → supply-chain data analyst → data scientist), each step with its missing skills and subjects.
2. **Course and session planning.** Compare whole courses by the share of demand they cover, and lay out a semester-by-semester plan that follows course rules, not only prerequisites.
3. **All disciplines.** Extend beyond data roles and MDSI to every UTS faculty, using the 360-subject scrape as the base.
4. **Browse current jobs.** Let students pick live Australian ads instead of pasting one, and compare two ads side by side.
5. **Resume suggestions.** Point out skills a student has but does not state clearly in their CV.
6. **Stronger validation.** Ask subject coordinators to confirm skill-subject links, and collect more labelled ads and pairs to narrow the confidence intervals.
7. **Privacy and persistence.** Mask person names before any text goes to an external model, and store feedback votes in a database so they survive app restarts.
8. **Larger 2026 sample.** Keep collecting Australian ads over time so demand weights can move from 2019-22 data to current data.
