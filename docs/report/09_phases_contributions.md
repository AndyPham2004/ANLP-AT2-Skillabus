# 9 Phases, contributions and challenges

## 9.1 Phases

The first pull request merged on 12 October; the deadline is 17 October. The week had five phases.

| **Dates** | **Phase** | **Result** |
|----|----|----|
| 11–12 Oct | Contract and baseline | Data contract and mock gap data; first app on the baseline; extraction tiers 1–2, matching and evidence ranking; evaluation harness; first report drafts |
| 14 Oct | Data and labels | Handbook data (360 subjects, 44 courses); four-layer subject profiles; 2026 ad sample; labels for 20 ads and a second annotator; CV–JD pairs, skill–subject pairs and chat questions; related work |
| 15 Oct | One vocabulary | Data folders reorganised; ESCO base plus 145 skills; occupation skills and certifications for 11 roles; self-study store; one demand table; prerequisites in recommendations |
| 16 Oct | Scale to 11 roles | JobsPipe 2026 ads (1,932); extractors read the vocabulary; outside courses; app for all 11 roles; evaluation run |
| 17 Oct | Report | Evaluation re-run with 2026 labels; app finished (start page, course and role rankings); sections cut and checked, report assembled |

## 9.2 Contributions by member

Counts are merged pull requests on `main` at 21:50 on 17 October (106 in total).

- **Quan (55)**: Streamlit app and its redesign; data layout and `paths.py`; Handbook data; one skills vocabulary; self-study store; demand table; JobsPipe 2026 ads; evaluation re-runs; label kits; report integration.
- **Phuong Nhi (19)**: dictionary and spaCy extraction; matching; evidence ranking; recommendation with prerequisites and outside courses; emerging-skill detection; normalisation error table; methods section.
- **Van Thong (22)**: data cleaning; subject profiles; 2026 ad samples and skill counts; FAISS retrieval; second-annotator labels; role profiles; external courses; Adzuna counts; data section.
- **Hoai Thuong (8)**: evaluation harness and Cohen’s kappa; CV–JD pairs; ad labels; skill–subject pairs and chat questions; evaluation run and section 6.
- **Akash (2)**: ethics and limitations draft; related-work section with its comparison table.

## 9.3 Challenges and solutions

1.  **Data for eleven roles.** The first sources covered mainly Data Scientist. We added the JobsPipe 2026 feed, Seek 2020–21 and Adzuna counts, then cleaned and sampled to 89–216 ads per role.
2.  **One bare word, two meanings.** A bare “AI” counted as the skill and “R” matched everywhere. We matched only the phrases ads use (#148, \#149) and kept “R” out unless written as “R programming”.
3.  **One vocabulary for everything.** Dictionary, extraction, demand and subjects each had their own skill list. We merged them into one file and switched every stage to it (#104, \#109), then re-ran the evaluation.
4.  **Coordination in one week.** Five people worked in one repository. One task per issue, branch and pull request, a review on each, and a freeze before the final run kept merges manageable.
