# role_profiles.csv

Tool profiles for 7 data and IT roles, so the app can offer roles other than Data Scientist
(ideas doc 4.7, issue #65).

| | |
|---|---|
| Rows | 441: one per role and dictionary skill named in at least one ad |
| Roles | Data Engineer, Data Analyst, Data Scientist, Software Engineer, Business Analyst, Cloud Engineer, Machine Learning Engineer |
| Built by | `python data-eda/src/build_role_profiles.py` |
| Source | [`lukebarousse/data_jobs`](https://huggingface.co/datasets/lukebarousse/data_jobs) on Hugging Face, Apache-2.0; postings collected from Google Jobs in 2023. Raw file in `data-eda/data/raw/data_jobs_hf/` (not committed) |
| Built | 14 Oct 2026 |

## Columns

| Column | Meaning |
|---|---|
| `role` | One of the 7 roles. Senior titles fold into their role (Senior Data Engineer is Data Engineer) |
| `skill`, `category` | A skill of `skills_seed_v2.csv`, its category |
| `n_ads` | Ads of the role whose tool list names the skill |
| `pct_ads` | `n_ads / total_ads`, in % |
| `pct_low`, `pct_high` | 95% Wilson interval of `pct_ads` |
| `total_ads` | The role's ads that name at least one tool (the denominator) |
| `source` | `lukebarousse/data_jobs (2023, Australia)` |

## How it is built

1. **12,955 Australian postings** (`job_country == "Australia"`) in the 7 roles; **10,925** after
   dropping repeats of the same title, company and location (one ad is often listed on several boards).
2. The dataset gives each posting a list of tool names its author extracted (`job_skills`) and a
   standardised title (`job_title_short`, a 10-class BERT classifier). There is no ad text.
3. Each tool name maps to a dictionary skill by canonical name or alias. A few bare names map
   through `TOKEN_MAP` (`shell` -> Shell scripting, `unix` -> Linux, `word` -> Microsoft Office,
   `dax` -> Power BI); in running text our aliases leave them out because they are ordinary words.
4. The denominator is the role's ads that name at least one tool (9,234 of 10,925 ads in all); an empty list
   means the extractor found nothing, not that the ad asks for nothing.

## Top 10 per role

| Rank | Data Engineer (n=4,438) | Data Analyst (n=1,362) | Data Scientist (n=1,047) | Software Engineer (n=1,198) | Business Analyst (n=576) | Cloud Engineer (n=350) | Machine Learning Engineer (n=263) |
|---|---|---|---|---|---|---|---|
| 1 | SQL 69% | SQL 60% | Python 59% | AWS 40% | SQL 46% | Azure 42% | Python 85% |
| 2 | Python 57% | Python 34% | SQL 59% | Python 37% | Excel 39% | AWS 38% | SQL 40% |
| 3 | Azure 43% | Power BI 30% | R 32% | Java 29% | Power BI 27% | Python 29% | AWS 29% |
| 4 | AWS 42% | Excel 28% | AWS 22% | SQL 25% | Python 22% | SQL 25% | PyTorch 28% |
| 5 | Spark 30% | Tableau 27% | Azure 22% | Azure 24% | Tableau 22% | Terraform 20% | TensorFlow 22% |
| 6 | Databricks 22% | R 22% | Tableau 19% | JavaScript 22% | Microsoft Office 14% | Shell scripting 18% | Java 22% |
| 7 | Java 17% | Azure 12% | Power BI 16% | Git 22% | AWS 11% | Linux 17% | Azure 20% |
| 8 | SQL Server 17% | SQL Server 10% | Spark 12% | Linux 15% | Azure 9% | Windows 16% | Google Cloud 20% |
| 9 | Snowflake 17% | AWS 9% | Excel 12% | Kubernetes 15% | R 8% | Kubernetes 15% | Linux 19% |
| 10 | Git 15% | Snowflake 8% | Git 9% | React 15% | SAP 8% | Git 13% | Git 19% |

## Dictionary rows added for this file

Ten tools the 2023 lists name often and the dictionary lacked were added to `skills_seed_v2.csv`
(now 148 skills), with aliases that are safe in running text: **Kafka, Linux** (with Unix),
**Windows** (only "Microsoft Windows", "Windows Server"), **Jira** (not Confluence), **SAP**
(case-sensitive), **Microsoft Office** (Word, PowerPoint, Visio; not "Outlook", which is also an
ordinary word), **React** (case-sensitive), **Ruby, Alteryx, Ansible**. Their 2019-22 shares were
added to `skill_counts_v2.csv`, counted on the raw Seek text like the other 138 rows (which
are unchanged): Microsoft Office 4.4%, Linux 3.7%, Jira 2.4%, Kafka 2.3%, Alteryx 1.8%, SAP 1.6%,
React 1.0%, Ruby 0.3%, Ansible 0.1%, Windows 0.0%. Jira counts only Jira since 14 Oct (#86
review): Confluence and Atlassian are other products.

## Limits (say these wherever the numbers appear)

- **Tools only.** The lists hold tool names, so concepts never appear: no machine learning,
  statistics, data modelling or communication. For Data Scientist the app should keep the Seek
  full-text profile (3,204 ads, which has those) and use this file for the other six roles.
- **2023**, and collected through Google Jobs, so the mix of boards is the search engine's.
- **The author's extractor, not ours.** It counts the English word "go" as the language
  (Go would be 9% of Data Analyst ads), so `go` is dropped and Go is counted only from `golang`.
  For the same reason `flow` is dropped. 112 tool names stay unmapped (3,261 mentions; most
  frequent Confluence, DynamoDB, C, Express, HTML, Splunk), listed in the build log.
- **Titles come from a classifier.** `job_title_short` is the author's BERT model; a mislabelled
  title moves an ad between roles.
- No AI Engineer: the 2023 classes do not have it, and the 2026 sample holds only a few such ads.
