# 3 Data

> Draft by Van Thong (with Claude), 10 Oct 2026. Every number below comes from
> `notebooks/vt_eda.ipynb`, which runs on committed files only. The script behind each
> file is named in `data-eda/data/clean/README.txt` and `data/README.md`.

## 3.1 Sources

Skillabus needs four kinds of data: job ads for demand, subject text for supply, resumes
to test the input side, and a skills vocabulary that ties them together. Table 3.1 lists
every source and what it is used for.

**Table 3.1.** Data sources.

| Source | What we use | Period | Role in Skillabus |
|---|---|---|---|
| Seek Australia Data Scientist ads (nomilk, 2022) | 3,204 listings, full text | Feb 2019 – Jan 2022 | demand: every `demand_pct` |
| Job-board APIs (Greenhouse, Lever, SmartRecruiters) | 22 Australian data roles, full text | Sep 2026 | recent demand: `demand_pct_2026` |
| Adzuna API | 33 Australian data roles, text cut at 500 characters | Sep 2026 | counted as roles, not for skill shares |
| LinkedIn data-science postings (asaniczka, 2024) | 124 Australian data roles | Jan 2024 | midpoint for the trend |
| LinkedIn job postings (arshkon, 2024) | 247 US Data Scientist ads | 2023–24 | validation |
| Glassdoor Australia (nadzmiagthomas, 2022) | 193 data roles | Aug – Dec 2022 | validation |
| UTS Handbook 2026 (University of Technology Sydney, 2026) | 70 subjects in six courses, 19 of them MDSI | 2026 | subject profiles |
| Resume Dataset (snehaanbhawal, 2021) | 2,481 resumes, 24 categories | 2021 | test inputs, CV–JD pairs |
| ESCO v1.2.1 (European Commission, 2025) | 13,960 skills, 100,135 labels | 2025 | normalisation vocabulary |
| O\*NET 31.0 (National Center for O\*NET Development, 2026) | 8,753 tool names | 2026 | tools ESCO lacks |

Skills are first found with a 138-skill dictionary (`data/processed/skills_seed_v2.csv`)
written from the way ads phrase things, so "power bi", "powerbi" and "Power BI" are one skill.

## 3.2 Collection and ethics

We scraped none of Seek, LinkedIn, Indeed or Glassdoor: their terms forbid automated
access. Every job ad comes from a published Kaggle dataset or a public job-board API built
to be read by software. Indeed was in the plan and was dropped for this reason; it has no
public search API. The UTS Handbook's `robots.txt` disallows crawling, so the 70 subjects
were read with about 90 targeted, rate-limited requests rather than a crawl, and
assessment details are being collected by hand. Resumes are de-identified (section 3.3)
before any use, and the app masks them again before any text reaches a language model.

## 3.3 Cleaning

**Welded words in the Seek ads.** The source dataset stripped HTML without putting spaces
back, so list items ran together ("…Power BI and TableauSuperior analytical skills…") in
80.4% of ads, and a dictionary with word boundaries misses those mentions. Each ad is
stored twice in the dataset, as a mobile and a desktop page. We split a join only where
the other version of the same ad shows a break: 13,181 joins were split and 11,574 left
alone, almost all genuine product names such as PhD, TensorFlow, PySpark and JavaScript.
Python rose from 82.8% to 84.5% of ads, no skill fell, and the ranking barely moved (rank
correlation 0.9996 with the uncleaned counts).

**Re-listings.** 697 listings repeat another listing's text exactly. In 99% of cases the
employer is the same and the ad was posted again on a later date (81%) or in another city
(19%), so there are 2,507 unique ads. We count per listing, as on the poster; counting per
unique ad moves no skill by more than 2.1 points (rank correlation 0.997). The 200-ad
labelling sample is drawn so that no text appears twice.

**Resumes.** Emails (in 19 resumes), phone numbers (61) and URLs (100) are masked with
patterns. Names are harder: spaCy's named-entity recogniser (Honnibal et al., 2020) tags
16,451 spans as people, but most are resume vocabulary ("Developed") or skills ("Java",
"Oracle"). A span is masked only if it is two or more capitalised words, starts with a known
first name, occurs in at most two resumes, and is not a dictionary skill or an O\*NET tool.
That masks 1,071 names and leaves every skill count unchanged (Java 301 before and after).
The result is de-identified, not anonymous.

**ESCO and the Handbook.** ESCO keeps alternative labels as a newline-separated list
inside one cell; we reshaped it into a lookup of 100,886 label–concept rows. 716 labels
(0.7%) point at more than one concept, including `sql` ("SQL" and "database management
systems"), so a lookup alone cannot normalise them. In the Handbook text, 40 broken
punctuation sequences in 13 subjects were repaired and course-level outcome codes were
removed.

## 3.4 Subject profiles

The poster feedback pointed out that learning objectives alone miss what a subject
teaches. Each subject is therefore split into one row per piece of text, labelled by layer
(Table 3.2), so a recommendation can quote the exact sentence and say where it came from.

**Table 3.2.** Subject profiles (`data/processed/subject_profiles.csv`, 1,039 rows).

| Layer | Rows | Subjects | Source |
|---|---|---|---|
| Learning objective | 289 | 67 | one row per objective |
| Weekly topic | 444 | 58 | one row per listed topic |
| Description | 306 | 70 | one row per sentence |
| Assessment | 0 | 0 | collected by hand; merged automatically when it arrives |

The extra layers matter. Subject 36118 Applied NLP lists "Large Language Models (LLMs)" as
a weekly topic, which its learning objectives never mention. The poster said it mentioned
LLMs only in its description, which understated what it teaches, exactly as the feedback
suspected. Coverage is uneven, though: 9 of the 19 MDSI subjects have no topic list,
including 36106 Machine Learning and 94691 Deep Learning, and three have no learning
objectives. Those subjects can rank low for lack of text rather than lack of content.

## 3.5 What the market asks for

![Top technical skills](../../data-eda/outputs/figures/fig1_top_skills.png)

*Figure 3.1. Share of the 3,204 Seek ads naming each technical skill.*

Four skills dominate: Python (84%), machine learning (73%), SQL (57%) and statistics (56%).
After them only predictive modelling passes 30%, and 24 technical skills appear in at least
10% of ads. A typical ad names eight technical skills (interquartile range 5–11), and 32% ask
for all of Python, SQL and statistics. Communication appears in 30% of ads, more often than
any technical skill outside the top five.

## 3.6 Can the counts be trusted?

**An independent extractor.** The Kaggle dataset includes its author's own flags for 25
tools on the same ads. On the 14 tools both extractors cover, agreement across all 3,204 ads
gives a median Cohen's kappa (Cohen, 1960) of 0.637, with 8 of 14 at 0.60 or above. The two
mostly disagree in one direction: for 3,348 of the author's 3,734 extra positives, the tool
does not appear in the ad at all (their R flag fires on 70% of ads). Our own misses were
mainly the welded words fixed in section 3.3. This measures agreement, not accuracy;
accuracy comes from the hand-labelled test set in section 6.

**Other platforms and markets.** If the ranking were an artefact of how Seek ads are
written, other sources would rank skills differently. Table 3.3 compares them, using the
Spearman rank correlation over technical skills that appear in both corpora.

**Table 3.3.** Skill ranking compared with Seek Australia, 2019–22.

| Compared with | Ads | What differs | Rank correlation |
|---|---|---|---|
| Glassdoor Australia, 2022 | 193 | platform | 0.75 |
| LinkedIn US, 2023–24, Data Scientist titles | 247 | country and years | 0.82 |
| LinkedIn Australia, Jan 2024, data roles | 124 | years and role mix | 0.61 |

The ranking holds across platforms and countries. It is weakest where the role mix
changes: the January 2024 sample is mostly data engineers and analysts.

## 3.7 Recent ads and the LLM shift

The plan asked for about 150 Australian ads from 2026. The legitimate sources yielded 22
with full text, from 8 employers, 12 of them Canva. Adzuna adds 33 more, but its API cuts
every description at 500 characters, so they are excluded from skill shares. The 124
Australian LinkedIn ads from January 2024 give the trend a midpoint in the same country.
All three periods use the same dictionary, cleaning and code
(`data/processed/skill_counts_2026.csv`).

![LLM-era skills over time](../../data-eda/outputs/figures/fig2_llm_trend.png)

*Figure 3.2. Australian data ads naming an LLM-era skill, with 95% Wilson intervals.*

LLM-era skills went from one ad in 3,204 (a mention of "Transformer models for NLP") to 3 of
124 in early 2024 (2.4%) and 11 of 22 in 2026 (50%; 95% Wilson interval 31–69%; Wilson,
1927). Part of that jump is the role mix, since the 2026 ads include AI-titled engineering
roles. But the rise appears within both groups: from 1 of 108 to 3 of 10 for data roles
without AI in the title, and from 2 of 16 to 8 of 12 for AI and machine-learning titles.
The direction is clear. Per-skill 2026 shares are not reliable, with intervals of about 20
points either side, so the app shows them as counts ("8 of 22 recent ads") rather than
percentages. Five LLM tools appear only in the 2026 ads and are not in our dictionary:
LangSmith, LangGraph, GraphRAG, DeepSpeed and Claude. These are the skills normalisation
tags as emerging (section 4).

## 3.8 Market against curriculum

![Market demand against the UTS curriculum](../../data-eda/outputs/figures/fig3_subject_coverage.png)

*Figure 3.3. The 25 most-demanded technical skills, coloured by whether any of the 70 UTS
subjects names them.*

21 of the 25 most-demanded technical skills are named by at least one of the 70 subjects,
and 13 by an MDSI subject. Scala, Power BI, Azure and Java are named by none; vendor tools
rarely appear in a handbook, so the app says so instead of forcing a weak match. The LLM
toolchain is the clearest gap: large language models appear as weekly topics in 36118 and
43023 and generative AI once (32130), but prompt engineering, retrieval-augmented generation
and transformers appear in none of the 70 subjects.

On the input side, only 125 of the 2,481 resumes name two or more of six core data skills,
and none of the 24 categories is data science. The CV–JD test pairs are drawn from those
125, and the app's demonstration uses a synthetic MDSI resume.

## 3.9 Limitations

- The main corpus is Data Scientist titles only, ends in January 2022, and is 22% re-listings.
- The 2026 sample is 22 ads from 8 employers, 12 of them from Canva. It supports a direction,
  not precise shares.
- The resumes are US, from 2021, mostly outside data roles, and de-identified rather than anonymous.
- Subject profiles come from the public Handbook. They have no assessment layer yet, and
  topic lists are uneven.
- Only 36% of our dictionary maps to ESCO by exact label, and some ESCO labels are ambiguous.
- A dictionary misses new tools until someone adds them, and it under-counts R and Go on
  purpose (a bare "R" matches "R&D").

## References

arshkon. (2024). *LinkedIn job postings (2023–2024)* [Data set]. Kaggle. https://www.kaggle.com/datasets/arshkon/linkedin-job-postings

asaniczka. (2024). *Data science job postings & skills (2024)* [Data set]. Kaggle. https://www.kaggle.com/datasets/asaniczka/data-science-job-postings-and-skills

Cohen, J. (1960). A coefficient of agreement for nominal scales. *Educational and Psychological Measurement, 20*(1), 37–46. https://doi.org/10.1177/001316446002000104

European Commission. (2025). *ESCO: European skills, competences, qualifications and occupations* (Version 1.2.1) [Data set]. https://esco.ec.europa.eu/en/use-esco/download

Honnibal, M., Montani, I., Van Landeghem, S., & Boyd, A. (2020). *spaCy: Industrial-strength natural language processing in Python*. Zenodo. https://doi.org/10.5281/zenodo.1212303

nadzmiagthomas. (2022). *Australia data science jobs* [Data set]. Kaggle. https://www.kaggle.com/datasets/nadzmiagthomas/australia-data-science-jobs

National Center for O\*NET Development. (2026). *O\*NET 31.0 database* [Data set]. https://www.onetcenter.org/database.html

nomilk. (2022). *Data science job listings – Australia – 2019–2021* [Data set]. Kaggle. https://www.kaggle.com/datasets/nomilk/data-science-job-listings-australia-20192020

snehaanbhawal. (2021). *Resume dataset* [Data set]. Kaggle. https://www.kaggle.com/datasets/snehaanbhawal/resume-dataset

University of Technology Sydney. (2026). *UTS handbook 2026*. https://coursehandbook.uts.edu.au

Wilson, E. B. (1927). Probable inference, the law of succession, and statistical inference. *Journal of the American Statistical Association, 22*(158), 209–212. https://doi.org/10.1080/01621459.1927.10502953
