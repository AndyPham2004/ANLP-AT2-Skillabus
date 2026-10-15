# certifications.csv

Industry certifications for the 11 IT roles, each with a measurable "hot" signal (plan D11 in
`docs/notes/data_it_scope_2026-10-14.md`; decision 7: the outside-learning store goes deep and wide because IT people
keep learning all career long). The app can show them next to the gaps that outside courses fill.

| | |
|---|---|
| Rows | 49 certifications from 19 vendors |
| Levels | 11 foundational, 22 associate, 10 professional, 6 expert |
| Roles | the 11 of plan section 4.1; every role has at least 4 (table below) |
| Checked | 15 Oct 2026, on each vendor's own page (Claude for Quan) |
| Counts | `local_ads_mentions` filled 15 Oct 2026; `au_ads_count` blank until Van Thong runs the Adzuna count |
| Path | `paths.CERTIFICATIONS` (this note: `paths.CERTIFICATIONS_MD`) |

## Columns

| Column | Meaning |
|---|---|
| `cert`, `vendor`, `exam_code` | Current name and exam code. Google Cloud and Databricks have no public exam code (blank) |
| `level` | `foundational` / `associate` / `professional` / `expert`. AWS "Specialty" is filed as professional; CISSP, CISM, CISA and CBAP (five years' experience required) as expert |
| `roles` | Semicolon list of the 11 role names |
| `skills` | Semicolon list; the spelling of `skills_seed_v2.csv` where the dictionary has the skill (a test checks this), plain names otherwise |
| `aliases_ads` | How ads write it, semicolon list. For renamed exams the old name or code is included (AZ-204, AI-102, DP-100, CyberOps), because ads lag behind renames |
| `cost_aud`, `cost_usd` | Exam price for one attempt, list price, non-member; see Prices. `varies` = priced by country |
| `cost_basis` | Where the price comes from and what it includes |
| `official_url` | The vendor's own certification or exam page |
| `date_checked` | 2026-10-15 for every row |
| `adzuna_query` | The phrase counted on Adzuna (see How to count) |
| `au_ads_count`, `count_date` | Live Adzuna AU ads containing the phrase, and the day counted; blank for now |
| `local_ads_mentions` | Our own Australian ads naming the certificate (see Local mentions) |
| `report_signal` | A recent industry report that names the certificate (see Reports); blank otherwise |
| `hot` | `yes` / `no` by the rule below; blank until the Adzuna counts exist |
| `status_note` | Current status and recent renames or retirements, with dates |
| `au_ads_count_prev`, `count_date_prev` | The previous count, moved here by the next run (the trend) |
| `hot_reason` | Why `hot` is yes, in words the app can show |

## Certificates per role

| Role | n | Certificates (exam code, or name) |
|---|---|---|
| Data Scientist | 4 | MLA-C02, AI-103, AI-300, Google Cloud Professional Machine Learning Engineer |
| Data Analyst | 4 | PL-300, Google Cloud Associate Data Practitioner, SnowPro Core (COF-C03), Salesforce Certified Tableau Data Analyst |
| Data Engineer | 6 | SAA-C03, DEA-C01, Google Professional Data Engineer, Google Associate Data Practitioner, Databricks Data Engineer Associate, COF-C03 |
| Machine Learning Engineer | 5 | DEA-C01, MLA-C02, AI-103, AI-300, Google Professional Machine Learning Engineer |
| Software Engineer | 11 | CLF-C02, SAA-C03, DVA-C02, AZ-400, AI-200, AI-103, CKAD, KCNA, PSM I, CSM, ACS CP |
| QA/Test Engineer | 4 | ISTQB CTFL v4.0, ISTQB CTAL-TAE v2.0, PSM I, CSM |
| Cloud Engineer | 14 | CLF-C02, SAA-C03, DVA-C02, DOP-C02, SCS-C03, AZ-104, AZ-305, AI-200, Google ACE, Google PCA, Cloud+ (CV0-004), CKA, KCNA, Terraform Associate (004) |
| DevOps/SRE | 13 | CLF-C02, SAA-C03, DVA-C02, DOP-C02, AZ-104, AZ-400, Google ACE, CKA, CKAD, KCNA, RHCSA (EX200), Terraform Associate (004), ITIL Foundation (Version 5) |
| Network/Systems Administrator | 9 | AZ-104, A+ (220-1201/1202), Network+ (N10-009), Security+ (SY0-701), Cloud+, CCNA (200-301), RHCSA, ITIL, ACS CP |
| Cybersecurity Analyst | 10 | SCS-C03, SC-200, Security+, CySA+ (CS0-004), CCNA Cybersecurity (200-201 CCNACBR), ISC2 CC, CISSP, CISM, CISA, ACS CP |
| Business Analyst | 9 | PL-300, Tableau Data Analyst, PSM I, PSPO I, CSM, ECBA, CCBA, CBAP, ACS CP |

Vendors: Microsoft 8, AWS 7, Google Cloud 5, CompTIA 5, Linux Foundation / CNCF 3, IIBA 3, Cisco 2, ISC2 2, ISACA 2,
ISTQB 2, Scrum.org 2, and one each from Red Hat, HashiCorp, Databricks, Snowflake, Salesforce (Tableau), Scrum
Alliance, PeopleCert (ITIL) and the Australian Computer Society.

Frameworks are not certificates and are not listed: the ASD Essential Eight, NIST CSF, ISO/IEC 27001 (the standard),
SFIA, TOGAF (the framework), Scrum (the framework). Left out on purpose: AWS Certified Advanced Networking - Specialty
(retires 31 Dec 2026), certificates whose exam has already retired, and, to keep the list near 45, the next tier
(AWS AI Practitioner, AWS CloudOps Engineer SOA-C03, AWS Generative AI Developer - Professional AIP-C01, Azure
Fundamentals, DP-600, DP-700, SC-500, Google Cloud Digital Leader / DevOps / Security, Databricks ML and GenAI,
CompTIA Linux+ / PenTest+, LFCS, CCSP, CRISC, PMP). Each is a one-row addition if the app needs it.

## Recent changes found on 15 Oct 2026

Names and exam codes change often; these are why `date_checked` matters.

| Certificate | Change | Source |
|---|---|---|
| Microsoft Azure Data Scientist Associate (DP-100) | Retired 1 Jun 2026; Microsoft's path is now AI-300, Machine Learning Operations Engineer Associate | [Microsoft Learn, exam retirement](https://learn.microsoft.com/en-us/credentials/support/retired-certification-exams) |
| Microsoft Azure AI Engineer Associate (AI-102) | Retired 30 Jun 2026; successor AI-103, Azure AI Apps and Agents Developer Associate | same page; AI-103 page on Learn |
| Microsoft Azure AI Fundamentals (AI-900) | Exam retired 30 Jun 2026 (successor AI-901, per vladtalkstech.com) | same page |
| Microsoft Azure Developer Associate (AZ-204) | Retired 31 Jul 2026; successor AI-200, Azure AI Cloud Developer Associate | same page; AI-200 page on Learn |
| Microsoft Azure Security Engineer Associate (AZ-500) | Retired 31 Aug 2026; successor SC-500, Cloud and AI Security Engineer Associate | same page; SC-500 page on Learn |
| Microsoft Windows Server Hybrid Administrator (AZ-800/801) | Exams retired 30 Sep 2026 (one exam AZ-802 replaces them, per vladtalkstech.com) | same page |
| AWS SysOps Administrator - Associate | Renamed AWS Certified CloudOps Engineer - Associate with exam SOA-C03 | [AWS](https://aws.amazon.com/certification/certified-cloudops-engineer-associate/) |
| AWS Machine Learning Engineer - Associate | MLA-C01 in English ended 28 Sep 2026; MLA-C02 (booked as ME1-C02) in beta since 29 Sep 2026 | [AWS](https://aws.amazon.com/certification/certified-machine-learning-engineer-associate/) |
| AWS Machine Learning - Specialty | No longer on the AWS list of certifications | [AWS exams](https://aws.amazon.com/certification/exams/) |
| AWS Developer - Associate | DVA-C03 registration opens 27 Oct 2026; last DVA-C02 sitting 30 Nov 2026 | [AWS](https://aws.amazon.com/certification/certified-developer-associate/) |
| AWS Solutions Architect - Professional | SAP-C03 registration opens 27 Oct 2026; last SAP-C02 sitting 16 Nov 2026 (not listed here; SAA is) | [AWS](https://aws.amazon.com/certification/certified-solutions-architect-professional/) |
| AWS Security - Specialty | Now SCS-C03 (from 2 Dec 2025 per Tutorials Dojo; the AWS page links SCS-C03 material) | [AWS](https://aws.amazon.com/certification/certified-security-specialty/) |
| AWS Advanced Networking - Specialty | Retires 31 Dec 2026 (left out) | [AWS exams](https://aws.amazon.com/certification/exams/) |
| Cisco CyberOps Associate (200-201 CBROPS) | Now CCNA Cybersecurity, exam 200-201 CCNACBR (early 2026; the old URL redirects) | [Cisco](https://www.cisco.com/site/us/en/learn/training-certifications/exams/ccnacbr.html) |
| CompTIA CySA+ | V4 (CS0-004) launched 23 Jun 2026; V3 English exam retires 22 Dec 2026 | [CompTIA](https://www.comptia.org/en-us/certifications/cybersecurity-analyst/) |
| CompTIA Security+ | V8 expected on or around 17 Nov 2026 | [CompTIA](https://www.comptia.org/en-us/certifications/security/) |
| ITIL | ITIL (Version 5) launched 12 Feb 2026; ITIL 4 Foundation still sold, retirement reported for 31 Dec 2027 | [PeopleCert](https://www.peoplecert.org/browse-certifications/it-governance-and-service-management/ITIL-1/itil-5-foundation-version-50-4154); dates from secondary sources |
| HashiCorp Terraform Associate | Version 004 replaced 003 on 8 Jan 2026 | [HashiCorp](https://developer.hashicorp.com/certifications/terraform-associate) |
| SnowPro Core | COF-C03 is the listed exam | [Snowflake](https://learn.snowflake.com/en/certifications/) |
| Google Professional ML Engineer | Exam updated for the move from Vertex AI to Gemini Enterprise Agent Platform | [Google Cloud](https://cloud.google.com/learn/certification/machine-learning-engineer) |
| ISACA CISM | New exam content outline from 3 Nov 2026 | [ISACA](https://www.isaca.org/credentialing/cism) |
| IIBA ECBA | New English-only exam; old version kept for other languages | [IIBA](https://www.iiba.org/business-analysis-certifications/ecba/) |

## Prices

- One attempt, list price, for an individual who is not a member, exam only plus any compulsory application fee
  (IIBA CCBA and CBAP: application USD 145 + exam). Member prices are in `cost_basis`.
- `cost_aud` is the vendor's own AUD price where it publishes one: AWS (150 / 224 / 449 for foundational /
  associate / professional and specialty; AWS updates these each May), PeopleCert (AU$979 for the ITIL exam bundle,
  incl. tax; there is no exam-only price) and the ACS (membership AU$374 + application AU$346.50, incl. GST, fee
  schedule dated 1 Jun 2023).
- Vendors that price in USD only (Google Cloud, Cisco, ISC2 for Asia Pacific, ISACA, Linux Foundation, HashiCorp,
  Databricks, Snowflake, Scrum.org, IIBA, Salesforce): **AUD = USD / 0.7002**, the RBA 4 pm rate of 14 Oct 2026
  (1 AUD = 0.7002 USD, [RBA](https://www.rba.gov.au/statistics/frequency/exchange-rates.html)), rounded to cents.
  For AUD-only vendors `cost_usd` is the same conversion backwards.
- `varies` where the vendor prices by country and shows no Australian price on a public page: Microsoft (the FAQ
  says associate and expert exams "typically cost US$165" and are priced to local currency; `cost_usd` = 165),
  CompTIA (vouchers are "country and currency restricted"; the store shows no price without a region), Red Hat,
  ISTQB (ANZTB books through iSQI in local currency) and Scrum Alliance (each trainer sets the CSM course price).
- Prices exclude GST and local taxes unless `cost_basis` says otherwise (AWS: "applicable taxes may apply";
  HashiCorp: "plus locally applicable taxes"). Training, retakes and renewal fees are not included.

## Local mentions

`python data-eda/src/count_cert_mentions.py` counts the ads in our own Australian text that name each certificate:
the 3,204 Seek Data Scientist ads 2019-22 and the 192 recent ads (both committed), plus the raw job-board files
`data/raw/jobs_au_ats_2026.csv` and `data/raw/ats_ads_2026-*.csv` when present (here: 234 + 601 ads, 702 after
dropping duplicates and the 37 already in the recent file); 4,098 distinct ads. An ad counts once per certificate.
Aliases match as whole phrases; acronyms (no lower-case letter) are case-sensitive; the longest match wins, so
"CCNA" inside "CCNA Cybersecurity" counts for the second only.

Result on 15 Oct 2026: 7 of 49 certificates are named at all.

| Certificate | Job boards 2026 (702) | Recent 2024-26 (192) | Seek DS 2019-22 (3,204) | Total |
|---|---|---|---|---|
| ITIL | 0 | 2 | 3 | 5 |
| CCNA | 4 | 0 | 0 | 4 |
| CISA | 2 | 0 | 0 | 2 |
| CISSP | 1 | 0 | 0 | 1 |
| CISM | 1 | 0 | 0 | 1 |
| SnowPro Core | 1 | 0 | 0 | 1 |
| Google Professional ML Engineer | 0 | 0 | 1 | 1 |

This confirms the 14 Oct finding: our local ads rarely name a certificate (AWS, Azure and Scrum certificates: 0),
so `local_ads_mentions` cannot rank them, which is why `hot` uses the Adzuna counts. ITIL hits are partly the
framework ("ITIL compliant", "in line with ITIL"), not the certificate. Per-source table: `--breakdown out.csv`.

## Reports

`report_signal` names a report only if it was opened and published in the 12 months before 15 Oct 2026:

- **Robert Half 2027 Salary Guide** (US, released 1 Oct 2026), through Robert Half's article "27 technology
  certifications that can boost your career and salary in 2027"
  ([link](https://www.roberthalf.com/us/en/insights/career-development/which-it-certifications-are-most-valuable)).
  It names 15 of our rows: CLF, SAA, SCS, MLA, AZ-305, Google PCA, A+, Network+, Security+, Cloud+, CCNA, CISSP,
  CISM, CISA, CKA. US market, not Australian.

Opened but not used: the Skillsoft IT Skills and Salary top-paying list (published 24 Oct 2024, outside the window;
no newer edition found); the Hays Salary Guide FY26/27 coverage (names skills such as Azure ML and LLM architecture,
not certificates); Robert Half Australia's insights pages (no 2026 certification article).

## Hot rule

Computed by `apply_hot_rule()` in `data-eda/src/count_cert_adzuna.py`, after the Adzuna counts:

- **hot = yes** if any of these holds, and `hot_reason` says which:
  1. `au_ads_count` is in the top third (rounded up) of the certificates listed for at least one of its roles, and is
     at least 1;
  2. `report_signal` is not blank and `au_ads_count` is at least 1;
  3. trend: there is a previous count, and the count rose 20% or more to at least 10 ads.
- **hot = no** otherwise; **blank** while `au_ads_count` is blank.
- Rule 1 is per role so that a Business Analyst certificate is compared with Business Analyst certificates, not with
  AWS. Re-running the counter on a later day moves the old count to `au_ads_count_prev` and gives the trend.

## How to count on Adzuna (Van Thong)

1. Put the key in `.env` at the repo root (copy `.env.example`): `ADZUNA_APP_ID=...` and `ADZUNA_APP_KEY=...`.
2. Try three rows without writing: `python data-eda/src/count_cert_adzuna.py --limit 3 --dry-run`.
   The first line prints the number of all live Adzuna AU ads (the denominator). If a certificate's count equals
   it, Adzuna ignored the phrase parameter and the script stops; then rerun with `--match words`.
3. Count everything: `python data-eda/src/count_cert_adzuna.py` (49 calls + 1, 2.5 s apart, about 2 minutes; Adzuna's
   default limit is 25 calls a minute and 250 a day). It writes `au_ads_count`, `count_date`, `hot`, `hot_reason`.
4. Commit the CSV through a PR. Run it again a week later for the trend.

Options: `--category it-jobs` (only Adzuna's IT category), `--max-days-old N`, `--where Sydney`, `--hot-only`
(recompute `hot` without calls). If you change the options, say so in the PR: counts with different options do
not compare.

Caveats on the counts: each `adzuna_query` is one exact phrase, chosen to be specific to the certificate. Some still
catch job titles ("Associate Cloud Engineer", "Professional Cloud Architect", "Professional Data Engineer") or other
meanings ("CISA" is also the US Cybersecurity and Infrastructure Security Agency; "ITIL" is also the framework).
For the three new Microsoft certificates the query is the predecessor's code (AZ-204, AI-102, DP-100) and for CCNA
Cybersecurity the old name (CyberOps), because ads lag the renames; switch them once ads use the new codes. Whether
Adzuna searches the full ad or only its start is still to be checked (plan D12).

## Not verified

- Prices not shown on an official page: CompTIA (all), Microsoft in AUD, Red Hat, ISTQB/ANZTB, Scrum Alliance CSM;
  Tableau Data Analyst (USD 200 from the reseller Ascendient Learning; the Trailhead page did not render the fee);
  PSPO I (USD 200 from the store.scrum.org listing as shown in search results; scrum.org pages block scripted
  requests).
- Exam codes read from page links rather than page text: AWS CLF-C02, SAA-C03, DEA-C01, DOP-C02, SCS-C03.
  Security+ SY0-701 is inferred from "V7"; A+ 220-1201/1202 and CySA+ CS0-004 come from search results that quote
  CompTIA's pages.
- Dates from secondary sources: SCS-C03 start (Tutorials Dojo), ITIL 4 retirement (Cybiant, CertCrush), AI-901 and
  AZ-802 successors (vladtalkstech.com).
- Adzuna's `what_phrase` parameter is not in its public docs page; the script's denominator check catches it if
  Adzuna ignores it.
- The dictionary (`skills_seed_v2.csv`) does not yet have certificates as skills (`category = Certification`, plan
  D11); that belongs with the vocabulary rebuild (D5).
