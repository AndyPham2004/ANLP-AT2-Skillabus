# archive: frozen, read only

Old work kept as evidence, not used by the app. Nothing here is edited; a file that comes back into
use is moved out with `git mv`. Everything was also in git history before it moved here (15 Oct 2026).

| Folder | What | Why kept |
|---|---|---|
| `poster_AT2A/poster/` | The AT2A poster as submitted on 26 Sep: HTML (single source), A0 PDF, PNG preview, `figures/uts_logo.png` | The submitted deliverable; the HTML still opens in a browser (its `figures/` path is unchanged) |
| `poster_AT2A/tools/` | `export_poster.py`: HTML to vector A0 PDF and PNG with headless Chrome or Edge | To rebuild the PDF: `python archive/poster_AT2A/tools/export_poster.py` |
| `poster_AT2A/data/` | `gap.csv` (block 5 hero), `skill_counts.csv`, `skill_counts_wide.csv`, `ad_skill_long.csv`, `BLOCKS_B.md`, `FOR_A_blocks_3_and_5.md`, the block 3 and block 5 PNGs | The numbers on the poster. `tests/test_extract.py` and `tests/test_match.py` still check the pipeline reproduces `gap.csv`; `validate_against_authorflags.py` reads `ad_skill_long.csv` |
| `poster_AT2A/scripts/` | `chart_sources.py` (block 3 cards), `chart_top15.py` (block 5 chart), `source_counts.py` (block 3 counts). Their partner `extract_skills.py` is still imported by live scripts, so it stays in `data-eda/src/` | How the poster charts were made. Their default paths point at the old `data-eda/` layout; pass paths as arguments to rerun |
| `poster_AT2A/handoffs/` | What Van Thong (B), Phuong Nhi (C) and Hoai Thuong (D) delivered for the poster, with figures | The source of every poster number (was `docs/handoffs/`) |
| `mock_2026-10-03/` | The app's first mock: `subject_layers.csv` (70 subjects, Handbook only), two example gap results, `build_mock.py` | The app was designed against it; `tests/fixtures/subject_profiles_sample.csv` was cut from it. Replaced by `data/1_knowledge/uts/subject_profiles.csv` |
| `eda_2026-09/` | `au_vs_us_comparison.csv`, `source_counts.csv`, `esco_absent.csv`, `esco_verbphrase.csv`: outputs of the September EDA notebook (was `data/5_crosscheck/`) | Evidence for the September numbers; no code reads them. ESCO coverage per skill is now `data/1_knowledge/skills/esco_link_review.csv` (D5) |
| `oneoff_2026-10/` | `ht_run_evaluation.py` (a shortcut for `python -m skillabus.evaluate --all --methods <m>`) and `jsontitles.py` (printed the titles embedded in the saved outside-course pages while building `external_courses.csv`) | Nothing reads or runs them any more (18 Oct cleanup); their `sys.path` lines assume their old folders (`notebooks/`, `data-eda/src/external/`) |
| `templates_2026-10/` | Empty column templates: the four label sets (`ad_skills`, `cv_jd_pairs`, `skill_subject_pairs`, `chat_questions`) and `subject_content` | Copy one to start a new hand-made set; the filled sets are in `data/4_evaluation/labels/` |

To come (plan section 2): `dictionary_v1/` (the 133-row dictionary and its ESCO links, once
`skills_vocabulary.csv` replaces them) and `demand_files_v1/` (the skill-count files, once
`role_skill_demand.csv` replaces them).
