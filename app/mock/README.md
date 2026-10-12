# Mock data for the app

The app is built against these files until the real pipeline is wired in (milestone M4, 11 Oct).
Shapes follow `docs/data_contract.md`.

| File | What |
|---|---|
| `sample_ad.txt` | Robert Walters "Data Scientist - Python, SQL", Sydney CBD, 23 Sep 2026 (the poster's block 5 ad) |
| `sample_resume.txt` | Synthetic early-career MDSI resume from Phuong Nhi's notebook; not a real person |
| `gap_job_seeker.json` | Gap result for that ad vs that resume: 8 technical skills, 6 missing |
| `gap_role_data_scientist.json` | Gap result for the role (15 most-asked skills in 3,204 Seek ads) vs the same resume |
| `subject_layers.csv` | 1,016 rows of Handbook text for the 70 subjects, by layer |
| `build_mock.py` | Rebuilds all of the above: `python app/mock/build_mock.py` (needs `data/raw/data-eda/`) |

How the mock is made: dictionary match (`skills_seed_v2.csv`) for skills, keyword match over the
Handbook text for subject evidence, MDSI subjects preferred, greedy learning path. It is a
baseline, not the method: Phuong Nhi's embeddings replace the subject matching.

Known weak spot, kept on purpose as an error-analysis example: keyword matching cannot tell
"teaches" from "mentions". 32130's learning objective "collaboration with AI tools" is counted
as evidence for the skill "artificial intelligence".
