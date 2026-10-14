# 2 Related work

> Quan's draft (4 Oct) merged with Akash's table (#30). Checked on 14 Oct: Schlippe and Bothmer (2023) and
> Karakolis et al. (2022) against their full texts; UniSkill against the ACL Anthology entry; SEEK and the
> industry rows against their public pages. References in APA 7.

## 2.1 Comparison

Columns: **CV gap**: finds a person's missing skills from their CV. **Subject rec.**: recommends specific
university subjects. **Evidence**: shows why a subject matches a skill. **Demand**: ranks gaps by labour-market
demand. **Beyond description**: uses subject text other than the description (objectives, weekly topics,
assessments). **Emerging**: handles skills absent from the taxonomy.

| System | For whom | What it does | What it lacks for our users | CV gap | Subject rec. | Evidence | Demand | Beyond description | Emerging |
|---|---|---|---|---|---|---|---|---|---|
| LinkedIn (Skills Match, LinkedIn Learning) | Job seekers | Shows which of a job's top skills a profile lists; suggests LinkedIn Learning courses from job title and profile skills | Matches self-declared profile skills, not CV text; recommends its own short courses, not university subjects; no evidence for a match | ✓ | ✗ | ✗ | Partial | n/a | Own taxonomy |
| SEEK (in-demand skills, SEEK Profile, SEEK Learning) | Job seekers (AU) | Publishes top skills by industry from SEEK ads; links to courses at TAFEs and universities | Industry-level only, no comparison with a specific job; course links at program level; no evidence | ✗ | ✗ (program level) | ✗ | Aggregate only | ✗ | Not reported |
| Jobscan and similar ATS checkers | Job seekers | Keyword match between a resume and a job description; top skills by job title | Stops at "add this keyword"; never says where to learn a skill; lexical matching | ✓ | ✗ | Keywords highlighted | ✗ | n/a | ✗ |
| University handbooks and course planners | Students | List subjects, learning outcomes and requisites | No labour-market signal; electives listed, not ranked by career value | ✗ | Rules only | ✗ | ✗ | ✗ | ✗ |
| Lightcast Skillabi (Lightcast, 2025) | Program leaders, L&D | Maps curriculum text (descriptions, learning outcomes, syllabi) to the Lightcast taxonomy and scores program-occupation alignment 0-100 | Program level, not student level; no CV; proprietary and licensed | ✗ | ✗ (program audit) | ✗ | ✓ | Syllabi if supplied | ✓ (Lightcast) |
| UniSkill (Musazade et al., 2026) | Researchers | Dataset pairing graduate course sentences with ESCO skills; a BERT baseline reaches 87% F1 on course-skill matching | No job ads, no student, no recommendation | ✗ | ✗ | Sentence-level | ✗ | ✗ | ✗ |
| SkillSpan and weak supervision (Zhang, Jensen, Sonniks et al., 2022; Zhang, Jensen, van der Goot et al., 2022) | Researchers | Expert-annotated skill spans in English job ads; spans linked to ESCO skills by embedding similarity | Extraction only; both note that fixed inventories like ESCO miss new skills | ✗ | ✗ | n/a | ✗ | n/a | Identified, not solved |
| Skill Scanner (Schlippe & Bothmer, 2023) | Employers, job seekers, institutions | Sentence-BERT embeddings of 2,633 data-scientist ads (Indeed, Kaggle), CVs and one data-science master's curriculum, clustered with UMAP, DBSCAN and K-means; reports which market skills a document covers | Coverage reports, not subject recommendations for one student; no taxonomy; clusters labelled by bigrams, no evidence sentences; evaluated by silhouette score and a user survey, not against labelled ground truth | Partial (vs. market) | ✗ | ✗ | Partial | Not stated | Partial (clusters, no taxonomy) |
| Karakolis et al. (2022) | Students, professors | ~1,500 posts from Greek job sites; ESCO-based extraction; recommends skills and NTUA courses from the learner's CV, plus curriculum updates via association rules | Gap is to a job specialisation, not a target ad; course skills from descriptions only; relevance scores rather than evidence sentences; frequency threshold drops rare skills; evaluated by a survey of 31 early users | Partial (vs. specialisation) | ✓ | Scores only | ✓ | ✗ | ✗ |
| Frej et al. (2024), JCRec | Researchers | LLM few-shot skill extraction from resumes, ads and course descriptions; reinforcement learning picks course sequences that maximise jobs a learner qualifies for | Explainability is a goal, not a feature; description-only course text; optimises job count, not gaps to one role; simulated users | ✓ | ✓ (sequence) | ✗ | ✓ | ✗ | Partial (LLM) |
| **Skillabus (ours)** | UTS students | CV and one ad or role → gaps → UTS subjects with evidence → demand-weighted learning path | | ✓ | ✓ (subject level) | Ad and subject sentence | ✓ | ✓ (objectives, weekly topics, assessments) | ✓ (Lightcast, then "emerging") |

## 2.2 What is new

Existing tools each cover part of the problem. LinkedIn and Jobscan find what a CV lacks against a job but stop
at a keyword or point to their own short courses. SEEK and Skillabi measure demand, but for an industry or a
whole program, not one student. Handbooks know the subjects but not the job market. The two research systems
closest to ours connect CVs, ads and courses, but in different ways: Skill Scanner reports coverage at the level
of skill clusters and recommends no subjects, and Karakolis et al. recommend courses from a CV but use course
descriptions only and show relevance scores rather than evidence. Neither evaluates its recommendations against
labelled ground truth; both rely on user surveys.

Skillabus combines the steps for one student and one target ad or role. It links each gap to a specific UTS
subject; shows the ad sentence and the subject sentence side by side, with the layer the match came from;
draws on objectives, weekly topics and assessments, not only the description (the marker's 36118 example);
weights gaps by Australian ad demand and picks the 2-3 subjects that close the most of it; and keeps skills
missing from ESCO, such as GenAI, through a Lightcast lookup and an explicit "emerging" class. Each stage is
measured against a baseline on hand-labelled test sets (section 6).

**Closest system.** Skillabi is the nearest in spirit: it compares "taught" with "sought" skills. Skillabus
differs in the unit of analysis (one student, not a program), in showing evidence for every recommendation, in
using an open taxonomy with an emerging class, and in producing a short list of electives. The similar names are
a coincidence; we note it so a reader does not assume a link.

**What we take from the literature.** UniSkill shows that sentence-level course-skill matching works with
fine-tuned encoders, which supports sentence embeddings over keyword matching for subject ranking (section 4).
SkillSpan and its weak-supervision follow-up motivate a dictionary-plus-ESCO pipeline with a fallback for skills
the inventory lacks. Retrieval-augmented generation (Lewis et al., 2020) grounds the chat in Handbook text
instead of the model's memory.

## References

Frej, J., Dai, A., Montariol, S., Bosselut, A., & Käser, T. (2024). Course recommender systems need to consider
the job market. In *Proceedings of the 47th International ACM SIGIR Conference on Research and Development in
Information Retrieval*. https://arxiv.org/abs/2404.10876

Jobscan. (2023). *Resume skills: Top resume skills by job title*. https://jobscan.co/skills

Karakolis, E., Kapsalis, P., Skalidakis, S., Kontzinos, C., Kokkinakos, P., Markaki, O., & Askounis, D. (2022).
Bridging the gap between technological education and job market requirements through data analytics and
decision support services. *Applied Sciences, 12*(14), Article 7139. https://doi.org/10.3390/app12147139

Lewis, P., Perez, E., Piktus, A., Petroni, F., Karpukhin, V., Goyal, N., Küttler, H., Lewis, M., Yih, W.,
Rocktäschel, T., Riedel, S., & Kiela, D. (2020). Retrieval-augmented generation for knowledge-intensive NLP
tasks. In *Advances in Neural Information Processing Systems* (Vol. 33, pp. 9459–9474).

Lightcast. (2025, June 3). *Lightcast addresses higher education's relevance crisis with real-time skills
alignment technology* [Press release]. https://lightcast.io/resources/blog/skillabi-press-release-june-3-2025

LinkedIn. (n.d.). *LinkedIn Learning Hub: Skill building*. Retrieved October 14, 2026, from
https://learning.linkedin.com/skill-building

Musazade, N., Mezei, J., & Zhang, M. (2026). UniSkill: A dataset for matching university curricula to
professional competencies. In *Proceedings of the Fifteenth Language Resources and Evaluation Conference*
(pp. 456–469). https://aclanthology.org/2026.lrec-1.31/

Schlippe, T., & Bothmer, K. (2023). Skill Scanner: An AI-based recommendation system for employers, job seekers
and educational institutions. *International Journal of Advanced Corporate Learning, 16*(1), 55–64.
https://doi.org/10.3991/ijac.v16i1.34779

SEEK. (2025, October 23). *Most in-demand skills in your industry right now*.
https://www.seek.com.au/career-advice/article/in-demand-skills

Zhang, M., Jensen, K. N., Sonniks, S. D., & Plank, B. (2022). SkillSpan: Hard and soft skill extraction from
English job postings. In *Proceedings of the 2022 Conference of the North American Chapter of the Association
for Computational Linguistics: Human Language Technologies* (pp. 4962–4984).
https://doi.org/10.18653/v1/2022.naacl-main.366

Zhang, M., Jensen, K. N., van der Goot, R., & Plank, B. (2022). Skill extraction from job postings using weak
supervision. In *Proceedings of the 2nd Workshop on Recommender Systems for Human Resources (RecSys-in-HR 2022)*
(CEUR Workshop Proceedings, Vol. 3218). https://ceur-ws.org/Vol-3218/RecSysHR2022-paper_10.pdf
