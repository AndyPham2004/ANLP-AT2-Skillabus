# AT2B team plan: Skillabus app + technical report

Due **14 Oct 2026**. Plan agreed 3 Oct 2026. Every task is a GitHub issue with the same title;
the issue is where questions, decisions and links go. Every task has a reviewer: nothing is merged
or counted as done until someone other than the author has checked it.

## What changes after the poster feedback

The marker liked the pipeline and the evaluation plan. Three things to fix, and every task below
serves one of them:

1. **Innovation not stated.** Say what LinkedIn, Seek and university course planners do not do:
   link a skill gap to a specific subject, with evidence, weighted by market demand.
2. **Subject data too thin.** Handbook learning objectives miss what lectures, tutorials and
   assessments teach (the marker's own example: 36118 does teach LLMs). Subject profiles get four
   layers: learning objective, assessment, weekly topic, description.
3. **Validation and justification.** Why each method, how emerging skills (GenAI, absent from ESCO)
   are handled, how subject recommendations are checked, error analysis.

## Product features (in priority order)

| # | Feature | Must / should |
|---|---|---|
| 1 | Evidence for every gap and recommendation: the ad sentence and the subject sentence side by side | Must |
| 2 | Four-layer subject profiles, each match labelled by layer | Must |
| 3 | Learning path: the 2-3 electives that close the most demand-weighted gaps | Must |
| 4 | Emerging skills: not in ESCO → Lightcast lookup or "emerging" tag, with the 2019-22 vs 2026 trend | Should |
| 5 | "Does this subject really teach this?" thumbs up/down, stored for validation | Should |
| 6 | Three states: have / partial / missing | Could |

## Who does what

### Quan Pham (A): product, UI, fresh data, story, submission
| Task | Due | Reviewer |
|---|---|---|
| Agree the data contract (`docs/data_contract.md`) with Phuong Nhi | 4 Oct | Phuong Nhi |
| Fresh 2026 ads: extend Van Thong's ATS fetch, add an Indeed sample, target 150 AU data roles | 5 Oct | Van Thong |
| Check the Kaggle Glassdoor 2024 AU data-science set (full descriptions? synthetic?) | 5 Oct | Van Thong |
| Lightcast Open Skills free API key and lookup helper | 5 Oct | Phuong Nhi |
| UI design: wireframes for the three user flows and the results screen | 5 Oct | Hoai Thuong |
| Streamlit app on mock data (upload, gap chart, evidence panel, learning path) | 8 Oct | Phuong Nhi |
| Wire the app to the real pipeline; chat panel; feedback buttons | 11 Oct | Hoai Thuong |
| Deploy (Streamlit Community Cloud) and QR code | 11 Oct | Van Thong |
| Report: introduction, related work and innovation, architecture, conclusion | 12 Oct | Phuong Nhi |
| Final edit, assembly and submission | 14 Oct | all |

### Van Thong (B): data
| Task | Due | Reviewer |
|---|---|---|
| Clean Seek, resumes, ESCO; share the Seek ad file with Akash for labelling | 4 Oct | Quan |
| Build four-layer subject profiles from the collected subject content | 7 Oct | Phuong Nhi |
| Recount skills on the 2026 sample with `skills_seed_v2.csv` (trend 2019-22 vs 2026) | 7 Oct | Quan |
| RAG backend: FAISS index over subject profiles and ads, `retrieve()` function | 9 Oct | Quan |
| Report: data and EDA section | 10 Oct | Hoai Thuong |

### Phuong Nhi (C): pipeline
| Task | Due | Reviewer |
|---|---|---|
| Skill extraction, three tiers: dictionary → spaCy NER → GPT-4o-mini | 7 Oct | Hoai Thuong |
| Normalisation to ESCO with the emerging-skill fallback (Lightcast, then "emerging") | 7 Oct | Van Thong |
| Matching (TF-IDF → embeddings) and subject recommendation with evidence | 9 Oct | Hoai Thuong |
| Learning path: greedy demand-weighted cover over the gaps | 9 Oct | Quan |
| Report: methods section, with the reason for each method choice | 11 Oct | Quan |

### Hoai Thuong (D): evaluation
| Task | Due | Reviewer |
|---|---|---|
| Label 20 of the same ads as Akash, for inter-annotator agreement (Cohen's kappa) | 5 Oct | Quan |
| Build the 50 CV-JD pairs | 6 Oct | Phuong Nhi |
| Evaluation harness for the four stages (`src/skillabus/evaluate.py`) | 8 Oct | Phuong Nhi |
| Run the evaluation; error analysis with concrete failure examples | 11 Oct | Quan |
| Report: evaluation section | 12 Oct | Quan |

### Akash (E): test sets, subject content, related work, user testing, ethics
| Task | Due | Reviewer |
|---|---|---|
| Label 200 Seek ads with skills, in batches of 50 (first batch 4 Oct) | 6 Oct | Hoai Thuong |
| 30 skill-subject pairs checked against the Handbook | 6 Oct | Phuong Nhi |
| 30 chat questions with reference answers | 6 Oct | Quan |
| Collect subject content (description, assessments, weekly topics) for the 19 MDSI subjects | 6 Oct | Van Thong |
| Related-work table: 6-8 systems or papers, what each does and lacks | 8 Oct | Quan |
| Draft ethics and limitations section (add the subject-data limitation) | 10 Oct | Quan |
| User test with 5 classmates: mock app 9-10 Oct, real app 12 Oct; notes and feedback votes | 12 Oct | Quan |
| References, README user guide, report screenshots | 13 Oct | Quan |

## Milestones

| Date | Milestone | Done when |
|---|---|---|
| 4 Oct | **M0 Contract** | Data contract merged; first 50 labelled ads in |
| 6 Oct | **M1 Inputs** | All test sets and raw subject content in `data/labels/` |
| 7 Oct | **M2 Pipeline** | Ad + resume in, gap JSON out, end to end |
| 8 Oct | **M3 App on mock data** | Every screen clickable |
| 11 Oct | **M4 App on real data + evaluation** | Deployed link; metrics table filled |
| 12 Oct | **M5 Report draft** | Every section in `docs/report/` |
| 14 Oct | **M6 Submit** | Report PDF and app link on Canvas |

If a test set is late, it shrinks; nothing else waits for it.
