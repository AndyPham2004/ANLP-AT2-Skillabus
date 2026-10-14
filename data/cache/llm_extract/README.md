# GPT-4o-mini extraction cache

One file per input text, named `sha256("gpt-4o-mini|v3|<masked text>")[:24].json` (see `_cache_path` in
`src/skillabus/llm_extract.py`). Each file holds the model's list of skill mentions, `{"text", "kind"}`;
the input text itself is not stored.

The 30 files were written on 14 Oct 2026 by `python -m skillabus.evaluate --all --methods llm` over the
20 labelled ads (`seek_label_sample_200.csv`, `double_label = y`) and the 10 resumes used in
`data/labels/cv_jd_pairs.csv`. With them the LLM tier of the evaluation reruns without an API key; any other
text still needs `OPENAI_API_KEY`. To regenerate, delete the files and rerun with a key (a few cents).

`data/cache/` stays in `.gitignore`, because the app writes a file here for every ad and resume a user
pastes. The 30 files above are tracked anyway (`git add -f`); after a rerun, add the new ones the same way
and never `git add` the whole folder.
