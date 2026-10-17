# Appendix

**Repository:** https://github.com/AndyPham2004/ANLP-AT2-Skillabus · **App:** [link and QR code: Quan adds]

## Appendix A. Data

**Table A.1.** Every data source, what Skillabus uses it for, and its licence.

| Source | What we use | Period | Role in Skillabus | Licence or terms |
|---|---|---|---|---|
| JobsPipe API (aggregates LinkedIn, Indeed, Workday and 11 job-board platforms) | 1,932 Australian ads, 89–216 per role, 11 roles; skills found and link only | 1 Sep – 16 Oct 2026 | main demand for every role | API terms: ad text not redistributed, link kept; one free account per person (three members' own accounts) |
| Adzuna API | live search counts: 11 role totals, 162 skill × role counts | 16 Oct 2026 | second 2026 view; rank check | API terms (counts only) |
| Public job boards of 65 employers (Greenhouse, Lever, SmartRecruiters, Ashby, Workable) | 392 ads posted within 60 days, 85 with a role | Oct 2026 | third 2026 view | employers' public ads |
| Seek Australia, Data Scientist (nomilk, 2022) | 3,204 listings, full text | Feb 2019 – Jan 2022 | Data Scientist trend | CC0 |
| Seek Australia samples (PromptCloud, 2021) | 2,366 IT ads out of 65,840, 10 roles | 2020–21 | pre-2022 baseline per role | CC0 |
| data_jobs (Barousse, 2025) | 10,925 Australian postings in 7 roles, tool lists | 2023 | cross-check | Apache-2.0 |
| LinkedIn data-science postings (asaniczka, 2024) | 122 Australian data roles | Jan 2024 | trend midpoint | ODC-By |
| LinkedIn job postings (arshkon, 2024) | 247 US Data Scientist ads | 2023–24 | validation | CC BY-SA 4.0 |
| Glassdoor Australia (nadzmiagthomas, 2022) | 193 data roles | Aug – Dec 2022 | validation | CC BY-NC 4.0 |
| ESCO v1.2.1 | 13,960 skills, 100,135 labels; essential and optional skills of each role's occupation | 2025 | base of the vocabulary; core skills | free reuse with attribution |
| O\*NET 31.0 | 8,753 software products (Technology Skills); the "In Demand" ones per occupation | 2026 | in-demand tools per role | CC BY 4.0 |
| Australian Skills Classification v1.0 | core competencies and tool categories per ANZSCO occupation | 2021 | Australian taxonomy | CC BY 4.0 |
| Jobs and Skills Australia | 2025 Occupation Shortage List; Internet Vacancy Index | 2025–26 | shortage label per role | CC BY 4.0 |
| UTS Handbook 2026 | 360 subjects in 44 courses, 19 of them MDSI | 2026 | subject profiles, prerequisites, sessions | public pages; text kept for matching |
| Students' Canvas reports | 305 skill rows for 9 MDSI subjects, 2 students | 2025–26 | what subjects taught | our own data |
| Official course, tutorial and certification pages | 56 outside courses, 250 self-study resources, 49 certifications (19 vendors) | Oct 2026 | outside courses, self-study, certifications | links and our own summaries |
| Resume Dataset (snehaanbhawal, 2021) | 2,481 resumes, 24 categories | 2021 | test inputs, CV–JD pairs | CC0 |

**Table A.2.** Ads per role and source in `data/2_demand/role_skill_demand.csv` (4,494 rows; notebook section 10). The app
reads the first source that has the role, in the order JobsPipe 2026, Adzuna 2026, job boards 2026, data_jobs 2023,
Seek 2019–22 (`match.DEMAND_PRIORITY`); today that is JobsPipe for all 11 roles. The 2026 job-board ads form three blocks
of 30+ ads: Software Engineer 33, data roles (mixed) 26 and IT roles (mixed) 26.

| Family | Role | JobsPipe 2026 | Adzuna 2026 | Seek 2020–21 | data_jobs 2023 | Seek 2019–22 |
|---|---|---|---|---|---|---|
| Data & AI | Data Scientist | 89 | 171 | 30 | 1,047 | 3,204 |
| Data & AI | Data Analyst | 205 | 290 | 145 | 1,362 | – |
| Data & AI | Data Engineer | 188 | 811 | 59 | 4,438 | – |
| Data & AI | Machine Learning Engineer | 204 | 62 | – | 263 | – |
| Software | Software Engineer | 195 | 1,171 | 944 | 1,198 | – |
| Software | QA/Test Engineer | 212 | 105 | 174 | – | – |
| Cloud & infrastructure | Cloud Engineer | 101 | 395 | 43 | 350 | – |
| Cloud & infrastructure | DevOps/SRE | 187 | 330 | 130 | – | – |
| Cloud & infrastructure | Network/Systems Administrator | 203 | 210 | 269 | – | – |
| Security | Cybersecurity Analyst | 132 | 139 | 179 | – | – |
| Business analysis | Business Analyst | 216 | 876 | 389 | 576 | – |

**Table A.3.** Do skill rankings agree across sources? Spearman rank correlation over the skills both name
(`data/5_crosscheck/`; notebook section 5).

| Compared | What differs | Skills | Rank correlation |
|---|---|---|---|
| Seek 2019–22 vs Glassdoor Australia 2022 (193 ads) | platform | 95 | 0.75 |
| Seek 2019–22 vs LinkedIn US 2023–24 (247 Data Scientist ads) | country and years | 100 | 0.82 |
| Seek 2019–22 vs LinkedIn Australia Jan 2024 (122 data roles) | years and role mix | 84 | 0.61 |
| Adzuna 2026 vs data_jobs 2023, per role (7 roles) | years and kind of source | 6–15 | 0.40 (Business Analyst) to 0.97 (Data Scientist); 0.50 Machine Learning Engineer; 0.69–0.77 the other four |
| Adzuna 2026 vs Seek 2019–22, Data Scientist | years and kind of source | 15 | 0.57 |

Only each role's 15 priority skills were searched on Adzuna, and they were picked from the older sources, so the Adzuna
rows test the order within that top group (`role_rank_agreement.csv`).

**Table A.4.** Subject profiles (`data/1_knowledge/uts/subject_profiles.csv`, 6,853 rows, 360 subjects in 44 courses).

| Layer | Rows | Subjects | Source |
|---|---|---|---|
| Learning objective | 1,516 | 354 | one row per objective |
| Assessment | 1,015 | 326 | one row per task: name, type, weight, group or individual, description |
| Weekly topic | 2,769 | 327 | one row per listed topic |
| Description | 1,553 | 360 | one row per sentence |

Alongside them, `prerequisites.csv` holds 2,200 requisite items for 290 subjects, 70 empty rules and 301 anti-requisite
rows for 172 subjects, and `offerings.csv` the teaching sessions of 330 subjects. Tables A.5 and A.6 give the layers per
course and per MDSI subject.

Rows per layer in `data/1_knowledge/uts/subject_profiles.csv`: 6,853 rows for 360 subjects in 44 courses, one row per
learning objective, assessment task, weekly topic or description sentence (UTS Handbook 2026, scraped 13 Oct 2026;
`data/1_knowledge/uts/subject_profiles.md`). A dash means the Handbook has no text for that layer.

**Table A.5.** Courses. A subject in several courses is counted in each, so columns do not add up to the total.

| Course | Level | Name | Subjects | Obj. | Assess. | Topics | Desc. |
|---|---|---|---|---|---|---|---|
| C04256 | Master | AI (Online) | 11 | 50 | 12 | 89 | 43 |
| C04265 | Master | Science (Extension) | 18 | 74 | 45 | 145 | 69 |
| C04277 | Master | Engineering (Extension) | 11 | 42 | 33 | 84 | 43 |
| C04295 | Master | Information Technology | 10 | 44 | 33 | 79 | 39 |
| C04296 | Master | Information Technology | 5 | 22 | 13 | 28 | 17 |
| C04370 | Master | Executive MDSI | 3 | 15 | 9 | 17 | 15 |
| C04372 | Master | MDSI | 19 | 76 | 46 | 75 | 91 |
| C04373 | Master | Quantitative Finance | 9 | 36 | 25 | 71 | 36 |
| C04379 | Master | Business Analytics | 31 | 137 | 99 | 200 | 150 |
| C04380 | Master | Business Analytics | 11 | 44 | 35 | 80 | 45 |
| C04430 | Master | Cybersecurity | 15 | 58 | 52 | 151 | 64 |
| C04431 | Master | Cybersecurity | 15 | 58 | 52 | 151 | 64 |
| C04434 | Master | Technology Management | 18 | 72 | 53 | 150 | 57 |
| C04435 | Master | Technology Management | 12 | 49 | 35 | 112 | 40 |
| C04443 | Master | Artificial Intelligence | 20 | 82 | 56 | 148 | 78 |
| C04450 | Master | Technology Innovation | 11 | 44 | 26 | 83 | 38 |
| C04467 | Master | Business Analytics | 11 | 45 | 29 | 72 | 45 |
| C06113 | Grad. diploma | IT | 62 | 266 | 188 | 499 | 241 |
| C06124 | Grad. diploma | Data Science and Innovation | 16 | 76 | 46 | 75 | 72 |
| C06147 | Grad. diploma | AI | 17 | 68 | 49 | 131 | 67 |
| C09019 | Honours | IT | 3 | 13 | 8 | 26 | 14 |
| C09066 | Honours | Engineering | 27 | 115 | 71 | 160 | 131 |
| C09119 | Honours | Computing Science | 19 | 84 | 69 | 194 | 85 |
| C09129 | Honours | Mathematical Sciences | 10 | 39 | 24 | 51 | 33 |
| C10143 | Bachelor | Information Technology | 78 | 324 | 244 | 665 | 344 |
| C10148 | Bachelor | Information Technology | 9 | 37 | 38 | 117 | 46 |
| C10229 | Bachelor | Games Development | 20 | 83 | 73 | 195 | 90 |
| C10395 | Bachelor | Information Systems | 29 | 125 | 108 | 288 | 137 |
| C10457 | Bachelor | Mathematical Sciences | 14 | 61 | 43 | 143 | 44 |
| C10471 | Bachelor | Cybersecurity | 29 | 117 | 97 | 311 | 132 |
| C10474 | Bachelor | AI | 27 | 113 | 93 | 270 | 117 |
| C10476 | Bachelor | Computing Science | 17 | 75 | 62 | 170 | 77 |
| C11142 | Grad. certificate | IT | 56 | 242 | 173 | 442 | 219 |
| C11191 | Grad. certificate | AI | 4 | 19 | 5 | 44 | 15 |
| C11247 | Grad. certificate | IT | 4 | 18 | 16 | 45 | 19 |
| C11274 | Grad. certificate | Data Science and Innovation | 16 | 76 | 46 | 75 | 72 |
| C11280 | Grad. certificate | Business Analytics | 4 | 15 | 14 | 28 | 16 |
| C11308 | Grad. certificate | Quantitative Finance | 9 | 36 | 25 | 71 | 36 |
| C11329 | Grad. certificate | Health Analytics | 21 | 93 | 55 | 179 | 123 |
| C11339 | Grad. certificate | AI Management | 4 | 16 | 10 | 29 | 13 |
| C11340 | Grad. certificate | Cybersecurity Management | 4 | 16 | 7 | 53 | 15 |
| C11350 | Grad. certificate | Data Visualisation and Storytelling | 4 | 17 | 13 | 42 | 14 |
| C11376 | Grad. certificate | Applied AI for Finance | 4 | 19 | 12 | 28 | 24 |
| C11385 | Grad. certificate | Business Analytics | 4 | 18 | 11 | 31 | 19 |
| **All** | | 44 courses | **360** | 1,516 | 1,015 | 2,769 | 1,553 |

**Table A.6.** MDSI subjects (C04372).

| Code | Subject | Obj. | Assess. | Topics | Desc. |
|---|---|---|---|---|---|
| 36100 | Data Science for Innovation | 5 | 3 | 5 | 5 |
| 36101 | Leading Data Science Initiatives | 5 | 3 | 12 | 5 |
| 36103 | Statistical Thinking for Data Science | 5 | 3 | 12 | 5 |
| 36104 | Data Visualisation and Narratives | 4 | 3 | 1 | 4 |
| 36106 | Machine Learning Algorithms and Applications | 5 | 3 | – | 5 |
| 36118 | Applied Natural Language Processing | 5 | 3 | 9 | 3 |
| 36120 | Advanced Machine Learning Application | 5 | 3 | 5 | 4 |
| 36121 | Artificial Intelligence Principles and Applications | 5 | 3 | 5 | 8 |
| 36122 | Python Programming | 8 | 3 | 9 | 7 |
| 36123 | Research Paper 1 | 3 | 1 | 2 | 3 |
| 36124 | Applied Data Science for Innovation | – | – | – | 5 |
| 36125 | Advanced Data Science for Innovation | – | – | – | 4 |
| 36126 | Innovation Lab: Research Project | 3 | 2 | – | 3 |
| 36127 | Innovation Lab: Capstone Project | 4 | 4 | – | 6 |
| 94689 | Special Subject 1 (FTDI) | – | – | – | 10 |
| 94691 | Deep Learning | 5 | 3 | – | 3 |
| 94692 | Data Science Practice | 5 | 3 | – | 1 |
| 94693 | Big Data Engineering | 4 | 3 | 15 | 3 |
| 94699 | Innovation Lab: Internship Project | 5 | 3 | – | 7 |
| **Total** | 19 subjects | 76 | 46 | 75 | 91 |
