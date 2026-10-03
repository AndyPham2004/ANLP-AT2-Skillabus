# How we work

Rules for the AT2B sprint (3-14 Oct 2026). Short on purpose; read it once.
Tasks and dates: `docs/team_plan.md`. Data formats: `docs/data_contract.md`.

## 1. One task = one issue = one branch = one pull request

1. Pick your issue on the project board, move it to **In progress**.
2. Branch from an up-to-date `main`, named `<initials>/<short-task>`:
   `qp/app-skeleton`, `vt/subject-profiles`, `pn/extraction`, `ht/eval-harness`, `ak/ad-labels-batch1`.
3. Open a pull request early (draft is fine). Write `Closes #<issue>` in the description.
4. Ask the reviewer named in the plan. **Never push straight to `main`.**
5. After approval: the author merges, except for `app/` and `docs/report/`, which Quan merges.

```bash
git checkout main && git pull
git checkout -b pn/extraction
# ... work, commit ...
git push -u origin pn/extraction
gh pr create --fill --draft
```

## 2. Folders: what goes where

| Folder | What | Owner |
|---|---|---|
| `app/` | Streamlit app | Quan |
| `src/skillabus/` | Reusable pipeline code (extract, normalise, match, recommend, rag, evaluate) | Phuong Nhi, Van Thong, Hoai Thuong |
| `notebooks/` | Exploration only, named `<initials>_<topic>.ipynb` | anyone |
| `data/processed/` | Small derived CSVs the app reads | Van Thong |
| `data/labels/` | Hand-made test sets, one file per set, templates included | Akash, Hoai Thuong |
| `docs/report/` | One Markdown file per report section | section owner |
| `data/raw/` | Never committed | |

Code that two people need goes in `src/skillabus/`, not in a notebook.

## 3. Data

- **Never commit `data/raw/`**, resumes, or anything with names, emails or phone numbers.
- Committed files stay under 5 MB. Bigger: share on the team drive and say where in `data/README.md`.
- Label files follow the templates in `data/labels/` exactly: same columns, same order, UTF-8.
  Do not edit someone else's label file; open an issue instead.
- Every number in the report names the file and script that produced it.

## 4. Secrets

- The OpenAI key lives in `.env` (copy `.env.example`). `.env` is gitignored.
- If a key is ever committed, tell Quan at once; we rotate it. Deleting the commit is not enough.

## 5. Code

- Python 3.12 in a venv: `py -3.12 -m venv .venv`, then `pip install -r requirements.txt`.
- Functions in `src/skillabus/` follow the shapes in `docs/data_contract.md`.
  **Changing the contract needs a PR reviewed by Quan and Phuong Nhi**, because the app depends on it.
- Clear notebook outputs before committing (Kernel → Restart & Clear Output).
- Commit messages: one plain line saying what changed (`Add three-tier skill extractor`).

## 6. Deadlines and being stuck

- Post a three-line update in the group chat each evening: done / next / blocked.
- If you will miss a date, say so **24 hours before**, in the issue, and add the `blocked` label.
  Late is fine if we know early; late without notice is not.
- Decisions go in the issue comments, not only in chat, so they are findable.

## 7. Review checklist

Reviewer, before approving:
- [ ] Does it do what the issue asked?
- [ ] Does it run on a fresh clone (no paths like `C:\Users\...`)?
- [ ] Data formats match `docs/data_contract.md`?
- [ ] No raw data, personal data or keys in the diff?
- [ ] Numbers that will go in the report are reproducible?
