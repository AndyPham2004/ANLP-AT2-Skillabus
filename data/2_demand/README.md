# 2_demand: what employers ask for

Market demand by role and skill (`role_skill_demand.csv`, one table for every source), plus the cleaned ads
it is counted on and the lists used to collect them. Code takes these paths from `src/skillabus/paths.py`. Commands run
from the repo root.

| File | What | Made by | Rebuild |
|---|---|---|---|
| `role_skill_demand.csv` | **The one demand table** (plan D6): role x skill x source x period, every source counted with the one vocabulary; **the app reads it** (plan C2, `match.py`). Section below | Claude for Quan, 15 Oct | `python data-eda/src/build_role_skill_demand.py` (needs the raw data_jobs file; `--check` says if it is stale) |
| `skill_counts_v2.csv` | **Superseded by `role_skill_demand.csv`; only the fallback engine `app/baseline.py` reads it.** Every dictionary skill (148) over the 3,204 Seek Data Scientist ads 2019-22, counted on the raw text as on the poster; `match.py` read `pct_ads` as `demand_pct` until C2 | Quan 25 Sep (poster), Van Thong 14 Oct (10 new rows) | `python data-eda/src/extract_skills.py --input data/raw/jobs_au_seek_datascientist_2019-2022.csv --text-col description --id-col ad_id --seed data/1_knowledge/skills/skills_seed_v2.csv`; keep the columns `skill, category, n_ads, pct_ads` of `data/runtime/extract_skills/skill_counts.csv` |
| `skill_counts_2026.csv` | **Superseded by `role_skill_demand.csv`; the app no longer reads it** (C2). Every dictionary skill in 2019-22, Jan 2024 and 2026 with 95% Wilson intervals (see below) | Van Thong | `python data-eda/src/recount_recent.py` |
| `top_skills.csv` | **Superseded by `role_skill_demand.csv`; only the fallback engine `app/baseline.py` reads it.** The 15 most-asked technical skills of Data Scientist; `match.role_profile` gives the same 15 from the table | Quan, 25 Sep | From `skill_counts_v2.csv`, technical categories only |
| `role_profiles.csv` | **Superseded by `role_skill_demand.csv`; the app no longer reads it** (C2). Tool profiles of 7 data and IT roles (data_jobs 2023, Apache-2.0), 441 rows; notes in `role_profiles.md` | Van Thong | `python data-eda/src/build_role_profiles.py` |
| `role_outlook.csv` (+ `.md`) | **Official Australian signal per role** (plan D13): 2025 Occupation Shortage List rating and Internet Vacancy Index (Aug 2026 vs Aug 2025, unit-group level) from Jobs and Skills Australia, 12 rows; CC BY 4.0, attribution in `role_outlook.md` | Claude for Quan, 16 Oct | By hand from the two JSA files named in the rows |
| `skills_not_taught_by_uts.csv` | 73 skills: 54 that no UTS subject names, plus 19 named but asked for in 10%+ of 2026 ads (was `uncovered_skills_2026-10-13.csv`) | Quan's session, 13 Oct | Recompute after the vocabulary (D5) and the IT subjects (D8) |
| `ads/jobs_au_seek_datascientist_2019-2022_clean.csv` | 3,204 Seek Data Scientist ads, glued words split | Van Thong | `python data-eda/src/clean_seek.py` |
| `ads/jobs_au_recent_2024-2026_clean.csv` | 192 Australian data roles: job boards 2026, Adzuna 2026 (500 characters), LinkedIn Jan 2024 | Van Thong | `python data-eda/src/build_recent_sample.py` |
| `ads/ats_2026_clean.csv` | **The 2026 job-board ads with a role** (plan D2): 392 Australian ads from the 65 boards (fetches of 13 and 16 Oct 2026, all professions) posted within 60 days of their fetch, one row per company and title, each given one of the 11 roles or `other` from its title; 85 have a role (Software Engineer 33, Data Scientist 11, Machine Learning Engineer 11, Cybersecurity Analyst 9, DevOps/SRE 7, Network/Systems Administrator 6, Business Analyst 3, Data Analyst 3, Cloud Engineer 1, Data Engineer 1). Contacts masked. Section below | Claude for Quan, 16 Oct | `python data-eda/src/classify_ats_roles.py` (needs the raw fetches in `data/raw/`) |
| `ads/jobspipe_2026_skills.csv` | **The JobsPipe 2026 ads, without their text**: 793 Australian ads posted 23 Sep to 16 Oct 2026, fetched 16 Oct from the JobsPipe API (Indeed 183, LinkedIn 576, ATS boards the rest), 85 per role by title query, kept when the title is that role; per ad: id, role, title, company, location, date, employer type (209 agencies), seniority, link, the vocabulary skills its text names (tier-1 matcher) and JobsPipe's own ESCO tags. Business Analyst 79, Data Analyst 78, QA/Test Engineer 78, Network/Systems Administrator 77, Software Engineer 73, Data Scientist 71, Data Engineer 70, Machine Learning Engineer 69, Cybersecurity Analyst 68, DevOps/SRE 67, Cloud Engineer 63. Section below | Claude for Quan, 16 Oct | `python data-eda/src/fetch_jobspipe.py` (one-off: the free key has 1,000 credits once; `--rehit` recomputes the skills from the raw file without calls) |
| `collection/jobspipe_totals_2026-10-16.csv` | Per role: the JobsPipe title query, its total live Australian ads in the 60-day window on 16 Oct (170 Data Scientist to 1,450 Software Engineer), fetched and kept | Claude for Quan | same script |
| `ads/CLEANING_NOTES.txt` | What each cleaned file is, who uses it, how it was cleaned (was `data-eda/data/clean/README.txt`) | Van Thong | Text |
| `adzuna_counts_2026-10.csv` | Live Adzuna search counts per skill x role, 11 roles (plan D12): `role, role_query, skill, skill_query, count, role_total, date`. Section below | Van Thong, 16 Oct | `python data-eda/src/count_role_skills_adzuna.py` (needs an Adzuna key; 173 calls) |
| `collection/adzuna_queries.csv` | The title query of each role and the phrase searched for each of its 15 priority skills, with a note wherever the phrase is a judgement | Van Thong, 16 Oct | `count_role_skills_adzuna.py --write-queries`, then by hand |
| `collection/ats_companies.csv` | The 65 job boards `fetch_ats.py` reads | Van Thong, Quan | Edited by hand |
| `collection/ats_candidates.csv` | 206 candidate employers with a slug guess per platform | Quan, 13 Oct | Edited by hand |
| `collection/ats_probe_2026-10-13.csv` | Which boards answered, with how many Australian data roles | Quan, 13 Oct | `python data-eda/src/probe_ats.py` (writes `ats_probe_<date>.csv`) |
| `emerging/emerging_candidates.csv` | Phrases rising in the 2026 ads that neither the dictionary nor ESCO knows, n-gram and spaCy | Phuong Nhi | `python -m skillabus.emerging` (with `PYTHONPATH=src`) |
| `emerging/emerging_candidates_2024-2026.csv` | The same with the Jan 2024 LinkedIn ads added | Phuong Nhi | `python -m skillabus.emerging --with-2024 --out data/2_demand/emerging/emerging_candidates_2024-2026.csv` |

`skill_counts_2026.csv` columns: `pct_2019_22` (3,204 Seek listings, clean text, counted per listing as
on the poster), `pct_2024_01` (122 Australian LinkedIn data roles), `n_2026` / `pct_2026` (the 9
data-scientist ads of the 2026 sample) and `n_2026_all` / `pct_2026_all` (all 22 sample roles), each
with a 95% Wilson interval. Until C2 `match.py` read `pct_2026` as `demand_pct_2026` (trend column) and
`pct_2026_all_low` as the 2026 floor of the gap weight in `recommend._weight`; since C2 the bars are the 2026
JobsPipe shares themselves and the floor is gone. **Read with care:** 22 ads from 12 employers, 9 of them data scientists from
5, so one ad moves a data-scientist share by 11 points. Show 2026 as "n of 9", not as a bare percentage.

## Adzuna search counts (plan D12): `adzuna_counts_2026-10.csv`

A **search count** is the number of live ads on Adzuna Australia on `date` whose title has all the words of
`role_query` (Adzuna's `title_only`) and whose text has `skill_query` as an exact phrase (`what_phrase`);
`role_total` is the same without the phrase, so the share is `count / role_total`. Only the numbers are
kept, never ad text. Checked on 16 Oct before the run: `what_phrase` searches the **whole ad**, not only the
title and the 500-character snippet the API returns (of 50 ads returned for "stakeholder management", 11
show the phrase in title or snippet). So a share here is comparable to the full-text counts, with three
differences: it is one phrase per skill, not every alias (`adzuna_queries.csv` notes where that under- or
over-counts: R, Excel, React, Spark); a role is one set of title words (DevOps/SRE is "devops", QA/Test
Engineer is "test analyst"); and the ads are whatever is live on Adzuna that day, re-listings included.
Three skills in ESCO's wording that no ad uses have no phrase and a blank count.

Owner of the folder: Van Thong. Planned here (plan D1): `roles.csv`. The app reads `role_skill_demand.csv`
since plan C2; `skill_counts_*`, `top_skills.csv` and `role_profiles.*` go to `archive/demand_files_v1/`
once the fallback engine and the poster check stop reading them.

**How the app reads the table** (`src/skillabus/match.py`, C2). A *block* is one role, source and period
with a share (`full_text`, `tool_list`, `search_count`); `taxonomy` rows and the `(mixed)` blocks are not a
role's demand.

- `demand_pct` = the role's block of the first source in `jobspipe_2026` > `adzuna_2026` > `ats_2026` >
  `data_jobs_2023` > `seek_2019_22`: today JobsPipe 2026 for all 11 roles, Data Scientist included; a pasted
  ad is weighed by the Data Scientist ads. Quan, 16 Oct: the 2019-22 Seek ads predate ChatGPT (LLMs 0%,
  AI 22%, Hadoop 17%; in 2026 34%, 73%, 1%), so they are no longer the main number.
- `demand_pct_2019_22` = the trend column: the Seek Data Scientist block (the table's count, same matcher as
  the 2026 ads), for Data Scientist and a pasted ad only.
- `demand_pct_2026` = the role's first 2026 block, the same order (equal to `demand_pct` today).
- `recommend._weight` = `demand_pct + 1`; the 2026 floor for skills new since 2022 is gone, the 2026 shares
  name them. The sample ad's path went from 36106 -> 36121 -> 32130 (87.9% of demand, 2019-22 weights) to
  36121 -> 36106 -> 32130 (84.9%; LLMs now weigh 34% and no subject teaches them).
- A role's 15 skills leave out soft skills and certifications. Every gap row carries `demand_source`,
  `demand_period`, `total_ads` and `text_type`; the caption reads "70 JobsPipe Data Engineer ads, Sep-Oct
  2026, full text."

## The demand table (plan D6): `role_skill_demand.csv`

One table for every demand source, long format, one row per role, skill, source and period. Rebuild with
`python data-eda/src/build_role_skill_demand.py` (reads `data/raw/jobs_au_datajobs_2023.parquet`, or
`data/raw/data_jobs_hf/data_jobs.csv`; `--raw <folder>` reads another checkout's; `--check` exits 1 if the
committed file is out of date). The build log prints a per-role, per-source summary, the role_profiles
comparison and every unmapped tool name.

| Column | Meaning |
|---|---|
| `role`, `role_family` | One of the 11 roles of `1_knowledge/taxonomies/role_occupations.csv` and its family, or `Data roles (mixed)` (`Data & AI`, below) |
| `skill_id`, `skill` | The skill's id and label in `1_knowledge/skills/skills_vocabulary.csv`; every row's skill is in the vocabulary |
| `source`, `period` | Where the row comes from, and when (for a taxonomy: its release) |
| `text_type` | `full_text` (ad text), `tool_list` (a list of tool names, no text), `search_count` (live Adzuna search counts), `taxonomy` (no counts) |
| `n_ads`, `total_ads` | Ads naming the skill at least once; the ads of that role, source and period. Blank for `taxonomy` |
| `pct`, `pct_low`, `pct_high` | `100 * n_ads / total_ads` (1 decimal) and its 95% Wilson interval (`recount_recent.wilson`). Blank for `taxonomy` |
| `importance` | `essential` / `optional` (ESCO), `in_demand` (O\*NET); blank for counted rows |

Not in it yet: **`pct_required`** (plan D14, required vs preferred), which waits for the flag under review in
#109; ASC rows.

| `source` | `period` | `text_type` | Roles | Ads | Rows | A share is |
|---|---|---|---|---|---|---|
| `seek_2019_22` | `2019-22` | full_text | Data Scientist | 3,204 | 197 | Seek Data Scientist ads whose cleaned text names the skill |
| `data_jobs_2023` | `2023` | tool_list | the 7 roles of `role_profiles.csv` | 263 (ML Engineer) to 4,438 (Data Engineer) | 576 | the role's Australian ads whose tool list names the tool |
| `recent_2024_26` | `2024-01`, `2026` | full_text | `Data roles (mixed)` | 122, 22 | 149 + 74 | in-sample full-text ads of `ads/jobs_au_recent_2024-2026_clean.csv` naming the skill |
| `ats_2026` | `2026-10` | full_text | `Software Engineer`; `Data roles (mixed)`; `IT roles (mixed)` | 33; 26; 26 | 244 | ads of `ads/ats_2026_clean.csv` with that role (or folded into a mixed block) naming the skill |
| `jobspipe_2026` | `2026-10` | full_text | all 11 | 63 to 79 | 1006 | ads of `ads/jobspipe_2026_skills.csv` with that role whose text named the skill (found at fetch time) |
| `adzuna_2026` | `2026-10` | search_count | all 11 | 62 (ML Engineer) to 1,171 (Software Engineer) | 153 | live Adzuna AU ads on 16 Oct whose title has the role's words and whose text has the skill's phrase; only each role's 15 priority skills searched (section on Adzuna counts) |
| `esco_occupation` | `v1.2.1` | taxonomy | all 11 | | 456 | (no share) ESCO lists the skill as essential or optional for the role's occupation |
| `onet` | `v31.0` | taxonomy | all 11 | | 207 | (no share) O\*NET marks the tool In Demand for the role's occupation |

How each source is counted:

- **Full text** (`seek_2019_22`, `recent_2024_26`): every vocabulary row used for detection (`used_for` has
  `extract`, 281 rows: the 148 dictionary skills, 84 added IT skills, 49 certifications) is matched with
  `extract.py`'s tier-1 matcher (`build_vocabulary.skill_hits`), so the table follows the app's matching
  rules. One of them: the longest alias at each place wins, so "SQL Server" counts as SQL Server and not
  also as SQL, "Google Cloud" not also as Cloud platforms, "Azure ML" not also as Azure, "Generative AI" not
  also as AI. Van Thong's `extract_skills.py`, which made the superseded files, counted both.
- **`recent_2024_26`: one role at a time only with 30 ads (plan D15).** The file's `role_group` is
  `data scientist` or `data role` (a mix of engineers and analysts). A role group that names one of the 11
  roles gets its own block for a period only with at least 30 ads; every other ad of the period is counted
  under `Data roles (mixed)`. Today no block qualifies (January 2024: 11 data scientists, 111 other data
  roles; 2026: 9 and 13), so each period is one mixed block, the same ads as `skill_counts_2026.csv`'s
  `pct_2024_01` (122) and `pct_2026_all` (22). Its 9-ad Data Scientist share (`pct_2026`) has no row here.
  `2026` = the September and October 2026 job-board fetches together. No role is guessed for an ad.
- **`ats_2026`: the job-board ads by role (plan D2), one role at a time only with 30 ads (plan D15).** The role
  comes from the title (`classify_ats_roles.py`, rules in the script; the 30-ad hand check is in `ads/CLEANING_NOTES.txt`).
  Only ads posted within 60 days of their fetch count, one per company and title: job boards keep evergreen ads open
  for years, and the same rule makes this source consistent with `recent_2024_26` (#64, #87). A role with at least
  30 ads gets its own block; a smaller role folds into `Data roles (mixed)` when its family is Data & AI, else into
  `IT roles (mixed)`; the 307 ads with role `other` (sales, marketing, management, pre-sales engineers) are not
  counted. Today: Software Engineer 33, Data Scientist 11, Machine Learning Engineer 11, Cybersecurity Analyst 9, DevOps/SRE 7, Network/Systems Administrator 6, Business Analyst 3, Data Analyst 3, Cloud Engineer 1, Data Engineer 1. The period is `2026-10`, not `2026`, because the 22 in-sample 2026 ads of
  `recent_2024_26` are among these ads (same boards): the two sources overlap and must never be added together.
  Bias to state: 65 employers that use a modern ATS, mostly technology companies, mostly Sydney and Melbourne.
- **`jobspipe_2026`: the JobsPipe ads by role, every role its own block.** 85 ads per role were fetched on 16 Oct
  (`fetch_jobspipe.py`): country AU, posted in the last 60 days, active, title containing one of the role's phrases
  (`collection/jobspipe_totals_2026-10-16.csv`), management words excluded; the title is then checked with the
  job-board rules (`classify_ats_roles.role_of`) and one row kept per company and title: 793 ads, 63
  to 79 per role. The text is not committed (JobsPipe's terms forbid redistributing the data in bulk and
  the text belongs to the employers), so the skills each ad names were found at fetch time with the same tier-1
  matcher and committed per ad; `fetch_jobspipe.py --rehit` recomputes them from the raw file after a vocabulary
  change. JobsPipe aggregates Indeed and LinkedIn postings itself; we used its API within its quota and keep the
  link to every posting, as its terms ask. 209 of the 793 ads are from recruitment agencies
  (`employer_type`), which repeat skill lists across clients. Overlaps with `ats_2026` are possible (ATS boards are
  among JobsPipe's sources) and the two are never added together.
- **`data_jobs_2023`**: the Australian rows, de-duplication and title map of `build_role_profiles.py`
  (senior titles fold into their role), and its denominator: the role's ads naming at least one tool (9,234
  of 10,925 ads). Each tool name maps to a vocabulary label: the 148 dictionary rows exactly as
  `build_role_profiles.py` maps them (name, alias, its `TOKEN_MAP`), then the vocabulary's other tool rows by
  label or alias (Confluence, Splunk, DynamoDB, Angular, Spring, HTML, ...), then five spellings in
  `EXTRA_TOKEN_MAP` (`no-sql` -> NoSQL; `redhat`, `centos`, `debian`, `suse` -> Linux). Not counted:
  `go`, `flow` (as before) and the bare letter `c`, which the dataset's matcher also finds in ordinary text
  (Business Analyst ads "name" it nearly as often as Data Scientist ads; likely "C-level"). **Unmapped:**
  74 names, 1,222 mentions, none of them a vocabulary skill: express 126, vmware 116, atlassian 96 (Jira
  counts only Jira), perl 81, chef 67, sheets 50, notion 39, aurora 34, slack 33, unity 32, yarn 27,
  spreadsheet 25, unify 25, vb.net 21, asp.net 21, ... (all in the build log). VMware and Perl are real
  tools the vocabulary lacks (candidates for `added_skills.csv`); Express, Chef, Unity, Notion, Slack are as
  likely English words as tools.
- **`esco_occupation`**: each role's ESCO occupation (`role_occupations.csv`), its essential and optional
  skills from `occupation_skills.csv`. The ESCO concept URI is the vocabulary's `skill_id` (`esco:<uri>`);
  the vocabulary holds every essential skill (plan D5, part 2), so all 317 essential rows are here, and 139
  of the 399 optional ones; the other 260 optional skills are not in the vocabulary and stay only in
  `occupation_skills.csv`.
- **`onet`**: the In Demand tools of each role's O\*NET occupation, mapped to a label with
  `1_knowledge/skills/onet_tool_map.csv`. Several tools can map to one label (Excel, Outlook, PowerPoint ->
  Microsoft Office) and give one row: 229 tool rows -> 207. eMASS is dropped there (a US defence system).
  Software Engineer and DevOps/SRE share one O\*NET occupation (15-1252.00), so their rows are the same.

**Shares from different sources are not comparable**, even for the same role and skill. Compare a skill's
rank within one source; across sources compare ranks (plan D7), not percentages, and caption every number
with source, period, n and text type.

- *What is read.* A full-text share counts every way an ad names a skill, concepts included (machine learning,
  communication). A tool-list share counts only the tool names another extractor (the dataset author's)
  pulled out: no concept ever appears, and each tool is matched by different rules. R is the clearest case:
  12% of Seek Data Scientist ads (the vocabulary only accepts "R" in context, "R programming", "Python and
  R") against 32% of data_jobs Data Scientist ads (the bare token "r").
- *What is divided by.* Seek counts every ad; data_jobs only ads with a tool list (an empty list means the
  extractor found nothing, not that the ad asks for nothing).
- *Who is counted.* The recent blocks mix data engineers, analysts and scientists; Seek is Data Scientist
  titles only.
- *When and where.* 2019-22 Seek, 2023 Google Jobs, January 2024 LinkedIn, 2026 public job boards of tech
  employers.
- *Taxonomy rows are not demand.* They say what a classification lists for the occupation (ESCO is
  European, O\*NET American), with no count; the app showed them as "core skills" for the four roles without
  Australian ads until JobsPipe counted them (C2); `backend.core_skills` stays as the fallback for a role
  with no counted block.

Checks (`tests/test_role_skill_demand.py`; numbers of 15 Oct):

- **data_jobs against `role_profiles.csv`**: the 7 denominators are equal (Data Engineer 4,438, Data
  Analyst 1,362, Software Engineer 1,198, Data Scientist 1,047, Business Analyst 576, Cloud Engineer 350,
  ML Engineer 263). 435 of its 441 role x skill rows have the same count; the other 6 gain a few ads from
  `EXTRA_TOKEN_MAP`: Linux (Cloud Engineer 60 -> 62, Data Engineer 305 -> 306, Software Engineer 184 -> 187)
  and NoSQL (Data Engineer 339 -> 350, Data Scientist 43 -> 44, Software Engineer 53 -> 56); at most 0.6
  point. 135 role x skill rows are new: vocabulary tools the dictionary lacked, the largest Angular 5.7%,
  Confluence 5.1%, Spring 4.9% and HTML 4.2% of Software Engineer ads.
- **Seek against `skill_counts_v2.csv`** (148 dictionary skills, Data Scientist). Rule: within 0.1 point;
  or, if not, equal within 0.1 to `skill_counts_2026.csv`'s `pct_2019_22` (the same ads, cleaned, the same
  aliases) and higher, so the gap is the text cleaning; or lower because of the longest-alias rule above.
  Result: 120 within 0.1; 26 higher by 0.2 to 1.7 points because `skill_counts_v2.csv` was counted on the raw
  text with welded words ("TableauSuperior"): Python 82.8 -> 84.5, Communication 28.3 -> 30.0, Scala 15.1 ->
  16.4, Predictive modelling 30.1 -> 31.1, Data visualisation 25.3 -> 26.2, AWS 21.7 -> 22.3, Tableau 18.9
  -> 19.4, Spark 25.6 -> 26.1, and 18 more by 0.2 to 0.4; 2 lower by the longest-alias rule: SQL 56.8 -> 56.3,
  Cloud platforms 25.1 -> 23.6. None because of the vocabulary: its 148 dictionary aliases are unchanged, and
  counting with only those 148 rows gives the same numbers, so the new rows take no mention from them.
- **recent against `skill_counts_2026.csv`**: 2026, all 148 within 0.1; January 2024, 145, and SQL -4.1,
  Cloud platforms -1.6, Artificial intelligence -0.8 points (longest alias).
- The committed Seek, recent and taxonomy rows equal a rebuild from the committed files; the data_jobs rows
  too when `data/raw/` has the data_jobs file (else that test skips; `--check` covers it).
