# Technical report, one file per section

**Submitted version:** `Skillabus_report.pdf` (and its source `Skillabus_report.docx`), 17 Oct 2026, A4.
Sections 1–9 and the references take 15 pages; the appendix (A–D) follows. The section files below
were regenerated from that Word file (`pandoc -t gfm --wrap=none`), so they hold the same text; edit
the Word file first if the report changes again. The app it describes is `main` at bb2f366 (#191).

| File | Section | Owner | Due |
|---|---|---|---|
| `01_introduction.md` | Problem, users, innovation | Quan | 12 Oct |
| `02_related_work.md` | Existing systems and what they lack | Quan (from Akash's table) | 12 Oct |
| `03_data.md` | Sources, cleaning, subject profiles, 2026 demand per role | Van Thong | 17 Oct |
| `04_methods.md` | Pipeline, why each method | Phuong Nhi | 11 Oct |
| `05_system.md` | Architecture diagram, app screens | Quan | 12 Oct |
| `06_evaluation.md` | Metrics, results, error analysis | Hoai Thuong | 12 Oct |
| `07_ethics_limitations.md` | Ethics, limitations | Akash (draft), Van Thong (final) | 17 Oct |
| `08_conclusion.md` | Takeaways, future work | Quan | 12 Oct |
| `09_phases_contributions.md` | Phases, contributions by member, challenges | Hoai Thuong | 17 Oct |
| `10_appendix.md` | References (one list for the whole report), then Appendix A: links and QR, data sources and licences, ads per role, rank agreement, subject layers | Van Thong | 17 Oct |
| `11_appendix_evaluation.md` | Appendix B: evaluation tables | Hoai Thuong | 17 Oct |
| `12_appendix_reference.md` | Appendix C data dictionary, Appendix D glossary (after `11_appendix_evaluation.md`, Appendix B) | Akash, Van Thong | 17 Oct |

Figures in `figures/`: `05_architecture.png` (Figure 5.1, drawn for the final app; source `05_architecture.html`, screenshot of `#fig` at 1560 px), `05_results_skills.png`,
`05_results_path.png`, `05_evidence.png` (Figures 5.2–5.3, the sample Robert Walters ad and sample resume on
`main` at bb2f366) and `qr_app.png` (`python src/make_qr.py https://skillabus.streamlit.app`). Figure 3.1 is
`../figures/fig4_ds_2019_vs_2026.png`.
