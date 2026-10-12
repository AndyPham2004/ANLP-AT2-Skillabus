# 2 Related work

> Draft by Quan (with Claude), 4 Oct 2026. Akash's related-work table (due 8 Oct) will add rows;
> every claim marked **[verify]** needs a source checked before submission.

| System | For whom | What it does | Vocabulary | What it lacks for our users |
|---|---|---|---|---|
| Job platforms (LinkedIn, Seek) | Job seekers | Show how a profile matches a job's listed skills **[verify feature names]** | Platform's own | No link to university subjects; no evidence for a match |
| Lightcast Skillabi (2025) | Program leaders, L&D | Scrapes program descriptions and learning outcomes, maps them to the Lightcast Open Skills taxonomy, scores program-to-occupation alignment 0-100 | Lightcast (proprietary) | Program level, not student level; no resume; licence cost |
| UniSkill (LREC 2026) | Researchers | Dataset of university course sentences paired with ESCO skills; BERT baseline reaches 87% F1 on course-skill matching | ESCO | No job ads, no student profile, no recommendation interface |
| University handbooks and course planners | Students | List subjects, learning outcomes, requisites | Free text | No labour-market signal |
| Skill extraction research (e.g. ESCO tagging of job ads) **[Akash: add 2-3 papers]** | Researchers | Extract and normalise skills from ads | ESCO | Extraction only; no subject recommendation |

**Closest system.** Skillabi is the nearest in spirit: it compares "taught" with "sought" skills.
Skillabus differs in the unit of analysis (one student and one ad or role, not a program), in
showing the evidence sentence and its layer for every recommendation, in using an open taxonomy
with an explicit emerging class, and in turning the comparison into a short, demand-weighted list
of electives. The similar names are a coincidence; we note it so a reader does not assume a link.

**What we take from the literature.** UniSkill shows sentence-level course-skill matching is
feasible with fine-tuned encoders, which supports our choice of sentence embeddings over keyword
matching for subject ranking (section 4). Retrieval-augmented generation (Lewis et al., 2020)
grounds the chat in Handbook text instead of the model's memory.

## Sources

- Lightcast (2025). *Lightcast addresses higher education's relevance crisis with real-time skills
  alignment technology* [press release, 3 June 2025]. https://lightcast.io/resources/blog/skillabi-press-release-june-3-2025
- Lightcast. *Skillabi*. https://lightcast.io/solutions/software/skillabi
- *UniSkill: A Dataset for Matching University Curricula to Professional Competencies* (2026).
  Musazade, Mezei and Zhang. LREC 2026. https://aclanthology.org/2026.lrec-1.31/ (arXiv 2603.03134)
- Lewis, P. et al. (2020). Retrieval-augmented generation for knowledge-intensive NLP tasks. NeurIPS.
