# Mock data of 3 Oct 2026 (frozen)

The app was built against these files before the pipeline and Van Thong's subject profiles existed.
Moved here from `app/mock/` on 15 Oct 2026; the app now reads `data/1_knowledge/uts/subject_profiles.csv`.

| File | What |
|---|---|
| `gap_job_seeker.json` | Gap result for the sample ad vs the sample resume: 8 technical skills, 6 missing |
| `gap_role_data_scientist.json` | Gap result for the role (15 most-asked skills in 3,204 Seek ads) vs the same resume |
| `subject_layers.csv` | 1,016 rows of Handbook text for the 70 subjects, by layer |
| `build_mock.py` | Rebuilt all of the above (`python app/mock/build_mock.py` when it lived there; needed `data/raw/data-eda/`) |

How the mock was made: dictionary match (`skills_seed_v2.csv`) for skills, keyword match over the
Handbook text for subject evidence, MDSI subjects preferred, greedy learning path. It was a
baseline, not the method.

Known weak spot, kept on purpose as an error-analysis example: keyword matching cannot tell
"teaches" from "mentions". 32130's learning objective "collaboration with AI tools" is counted
as evidence for the skill "artificial intelligence".
