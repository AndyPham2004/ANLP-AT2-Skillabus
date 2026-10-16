# role_outlook.csv: the official Australian signal per role (plan D13, #118)

One row per role (two for Network/Systems Administrator, which spans two ANZSCO occupations): is the
occupation in national shortage, and how many online vacancies its occupation group had in the latest
month against a year earlier. Both come from Jobs and Skills Australia (JSA), read on 16 Oct 2026.
Collected by Claude for Quan; the role-to-occupation mapping is the project's (`role_occupations.csv`).

| Column | Meaning |
|---|---|
| `role` | One of the 11 roles of `data/1_knowledge/taxonomies/role_occupations.csv` |
| `anzsco_code`, `anzsco_title` | The ANZSCO 2022 occupation the role is read as, with the title as the JSA file spells it |
| `shortage_2025` | The 2025 Occupation Shortage List national rating: `Shortage`, `No shortage` (the list also has `Regional shortage` and `Metro shortage`) |
| `vacancies_latest`, `vacancies_latest_month`, `vacancies_12m_ago` | Internet Vacancy Index, Australia, the role's **4-digit unit group**, 3-month moving average, August 2026 and August 2025 |
| `source_osl_url`, `source_ivi_url` | The two JSA files the numbers were read from |
| `date_checked`, `note` | When; state exceptions, the OSCA 2024 row where it differs, and what the unit group is |

## Sources

- **2025 Occupation Shortage List**, JSA, released 15 October 2025: `2025 Occupation Shortage List - 6 digit
  ANZSCO and OSCA.xlsx`, sheet "2025 OSL (ANZSCO 2022)" (916 occupations). Ratings: S shortage, NS no
  shortage, R regional, M metro. The headline list is on OSCA 2024; the ANZSCO 2022 sheet is its Appendix A,
  used here because the project's codes are ANZSCO. Landing page: https://www.jobsandskills.gov.au/data/occupation-shortage
- **Internet Vacancy Index**, August 2026 data, released 23 September 2026: `Internet Vacancies, ANZSCO4
  Occupations, States and Territories - August 2026.xlsx`, sheet "4 digit 3 month average". JSA publishes
  the IVI to the 4-digit unit group only, not per occupation, and the series is a 3-month moving average, not
  seasonally adjusted (the file's own note). Landing page: https://www.jobsandskills.gov.au/data/internet-vacancy-index

## Read with care

- **Four roles share one unit group** (2613 Software and Applications Programmers: Software Engineer,
  Machine Learning Engineer, QA/Test Engineer, DevOps/SRE), three share 2621, two share 2631 and two share
  2241. The vacancy figures are the group's, so they must never be summed across roles; show them as
  "its occupation group".
- **The mapping is a judgement** for roles ANZSCO 2022 has no occupation for: Machine Learning Engineer and
  DevOps/SRE are read as Software Engineer / Devops Engineer, Data Engineer as Database Administrator, Cloud
  Engineer as Computer Network and Systems Engineer. The OSCA 2024 sheet of the same list has direct rows for
  Data Engineer (no shortage) and **Cloud Engineer (shortage nationally)**, so Cloud Engineer's rating depends
  on the classification shown; the `note` says so.
- Cyber Security Analyst is ANZSCO 2022 code 262116 in the JSA file; the project's ANZSCO 2013 code 262112
  ICT Security Specialist no longer exists there. Other cyber occupations (engineer, architect, operations
  coordinator, GRC specialist) are in shortage nationally; the analyst is not.
- All five IT unit groups had fewer online vacancies in August 2026 than in August 2025 (2613 down 19%),
  while total vacancies rose 4.8% seasonally adjusted. The OSL is a point-in-time, employer-side assessment;
  its own methodology lists the lags and the binary rating as limits.

## Licence

JSA's copyright page (https://www.jobsandskills.gov.au/copyright-and-disclaimer): "All content on the Jobs
and Skills Australia website is provided under a Creative Commons Attribution 4.0 International Licence with
the exception of: content supplied by third parties; the Commonwealth Coat of Arms; material protected by a
trade mark; any images and/or photographs", and "Use of all or part of any material on this website must
include the following attribution: © Commonwealth of Australia". Neither dataset carries its own licence
note, so the site-wide licence is what applies. Attribution to use in the app and the report:

> © Commonwealth of Australia. Source: Jobs and Skills Australia, 2025 Occupation Shortage List (released
> 15 October 2025) and Internet Vacancy Index, August 2026 (released 23 September 2026), CC BY 4.0. Vacancy
> figures are unit-group level, 3-month moving averages; the role-to-occupation mapping is Skillabus's.

A 2026 Occupation Shortage List and the September 2026 IVI are due in October 2026, after the submission date.
