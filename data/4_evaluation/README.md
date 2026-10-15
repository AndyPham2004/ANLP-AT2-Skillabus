# 4_evaluation: test sets, their inputs, results

Everything the evaluation (report section 6) scores against. Never tune a threshold or a prompt on
these files (`data/3_tuning/README.md`). Code takes these paths from `src/skillabus/paths.py`.

| File | What | Made by | Rebuild |
|---|---|---|---|
| `labels/ad_skills.csv` | Skills in 20 labelled Seek ads, two annotators (534 rows); rules in `labels/README.md` | Hoai Thuong, Van Thong | Hand-labelled, one PR per batch |
| `labels/cv_jd_pairs.csv` | Ad skills checked against resumes: have / partial / missing, with the resume sentence (287 rows) | Hoai Thuong (with Claude) | Hand-labelled |
| `labels/skill_subject_pairs.csv` | Does this subject teach this skill: y / partly / n (33 rows) | Hoai Thuong | Hand-labelled |
| `labels/chat_questions.csv` | Chat questions with reference answers (15 rows) | Hoai Thuong | Hand-written |
| `labels/*_TEMPLATE.csv` | The column templates for the four files above | Quan, Claude | Templates |
| `inputs/seek_label_sample_200.csv` | The 200 Seek ads drawn for labelling (seed 36118; 20 with `double_label = y`) | Van Thong | `python data-eda/src/make_label_sample.py` |
| `inputs/resumes_us_2021_clean.csv` | 2,481 de-identified resumes (Kaggle, 2021), the CV side of the CV-JD pairs | Van Thong | `python data-eda/src/clean_resumes.py` |
| `llm_cache/*.json` | 30 GPT-4o-mini answers for the 20 double-labelled ads and 10 resumes, so the LLM tier reruns without a key; read only (`llm_cache/README.md`) | Quan, 14 Oct | Rerun the evaluation with a key, copy the new files from `data/runtime/cache/llm_extract/` |
| `results/` | Scores for report section 6 (empty until the evaluation PR #56 lands) | Hoai Thuong | The evaluation run |

Owner of the folder: Hoai Thuong (evaluation); labels by their annotators. Planned here: 20-30
labelled IT ads (E1, Akash), about 10 IT skill-subject pairs and 5 chat questions (E2, E3).
