# 2 Related work

**Skill extraction.** ESCO (European Commission, 2017) gives a shared, multilingual skill inventory that most research
systems map to. SkillSpan (Zhang, Jensen, Sonniks & Plank, 2022) annotated skill spans in English job ads, and a
weak-supervision follow-up linked spans to ESCO by embedding similarity (Zhang, Jensen, van der Goot & Plank, 2022).
Both note that a fixed inventory misses new skills. Large language models now extract skills from ads, resumes and
course descriptions with few examples (Frej et al., 2024); an LLM can, however, return skills that are not in the text. This
motivates our design: a vocabulary lookup as the precise backbone, spaCy and GPT-4o-mini for what it misses (with every
skill checked against the text), and an explicit class for skills ESCO lacks.

**Job–resume matching.** LinkedIn's Skills Match and resume checkers such as Jobscan compare a profile or resume with a
job. They stop at "add this keyword" or point to their own short courses, never to a university subject, and they show
no evidence for a match.

**Course recommendation.** Karakolis et al. (2022) recommend university courses from a learner's CV using ESCO, but read
course descriptions only and show relevance scores instead of evidence. Skill Scanner (Schlippe & Bothmer, 2023) embeds
ads, CVs and one master's curriculum and reports which market skill clusters a document covers, without recommending
subjects. JCRec (Frej et al., 2024) uses reinforcement learning to choose course sequences that maximise the jobs a
learner qualifies for, evaluated on simulated users. UniSkill (Musazade, Mezei & Zhang, 2026) shows that sentence-level
course–skill matching works with fine-tuned encoders, which supports sentence embeddings over keywords for subject
evidence. None of these evaluates recommendations against labelled ground truth.

**Closest system.** Lightcast Skillabi (Lightcast, 2025) maps curriculum text to the Lightcast taxonomy and scores how
well a program aligns with occupations: it compares "taught" with "sought" skills, as we do. It works at program level for
program leaders, is proprietary, and shows no evidence sentences. The similar names are a coincidence.

**The gap Skillabus fills.** No system we found does all of the following for one student and one target ad or role:
finds the gaps in their resume, links each gap to a specific UTS subject with the Handbook sentence that justifies it
(from learning objectives, assessments and weekly topics, not only the description), ranks gaps by Australian ad
demand, chooses the two or three subjects the student can actually enrol in, and keeps skills that ESCO lacks. Each
stage is measured against a baseline on hand-labelled data (section 6).

## References

European Commission. (2017). *ESCO: European Skills, Competences, Qualifications and Occupations*. https://esco.ec.europa.eu

Frej, J., Dai, A., Montariol, S., Bosselut, A., & Käser, T. (2024). Course recommender systems need to consider
the job market. In *Proceedings of the 47th International ACM SIGIR Conference on Research and Development in
Information Retrieval*. https://arxiv.org/abs/2404.10876

Jobscan. (2023). *Resume skills: Top resume skills by job title*. https://jobscan.co/skills

Karakolis, E., Kapsalis, P., Skalidakis, S., Kontzinos, C., Kokkinakos, P., Markaki, O., & Askounis, D. (2022).
Bridging the gap between technological education and job market requirements through data analytics and
decision support services. *Applied Sciences, 12*(14), Article 7139. https://doi.org/10.3390/app12147139

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

Zhang, M., Jensen, K. N., Sonniks, S. D., & Plank, B. (2022). SkillSpan: Hard and soft skill extraction from
English job postings. In *Proceedings of the 2022 Conference of the North American Chapter of the Association
for Computational Linguistics: Human Language Technologies* (pp. 4962–4984).
https://doi.org/10.18653/v1/2022.naacl-main.366

Zhang, M., Jensen, K. N., van der Goot, R., & Plank, B. (2022). Skill extraction from job postings using weak
supervision. In *Proceedings of the 2nd Workshop on Recommender Systems for Human Resources (RecSys-in-HR 2022)*
(CEUR Workshop Proceedings, Vol. 3218). https://ceur-ws.org/Vol-3218/RecSysHR2022-paper_10.pdf
