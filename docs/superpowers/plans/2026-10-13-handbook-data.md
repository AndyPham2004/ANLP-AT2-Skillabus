# Handbook data: more courses, prerequisites, sessions, assessment probe, ATS probe

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give the app the subject data it lacks tonight: 6 more UTS courses (Master of IT in full, 5 bachelor degrees), a prerequisite rule and teaching sessions for every subject, an assessment layer if the handbook serves it to a browser, and a count of how many 2026 Australian data-scientist ads the public ATS APIs can reach.

**Architecture:** Everything is a script under `data-eda/src/` that writes a CSV under `data/processed/` (committed, small) from raw pages under `data-eda/data/raw/` (gitignored). `scrape_handbook.py` already parses the `__NEXT_DATA__` payload of a handbook page; it gains a `sessions` column. A new `scrape_requisites.py` reads the access-conditions page per subject. `build_subject_profiles.py` rebuilds `subject_profiles.csv` as before. A new `probe_ats.py` tries ~100 employer slugs on five ATS job-board APIs and counts data-scientist ads in Australia.

**Tech Stack:** Python 3.12 (`.venv`), requests, pandas, pytest; Playwright MCP for the one browser probe.

**Spec:** `docs/plan/ideas_2026-10-12.md` sections 4.3 (item 5), 4.6, 4.8 and 7 (row "12 tối"). Issues #62, #64 (Van Thong) consume the outputs; this plan produces them on branch `qp/handbook-scrape` with Van Thong as reviewer.

## Global Constraints

- Handbook year is `2026` (`--year current` resolves to 2027).
- Requests to UTS sites: `User-Agent: Mozilla/5.0 (UTS 36118 student project)`, at least 0.5 s between requests.
- Job boards: public ATS job-board APIs only (Greenhouse, Lever, SmartRecruiters, Ashby, Workable). Never Seek, LinkedIn, Indeed, CareerHub.
- Raw downloads stay under `data-eda/data/raw/` (gitignored). Only small processed CSVs are committed; nothing over 5 MB.
- Processed CSVs have no leading `#` comment line (a literal `C#` in the dictionary breaks `comment="#"` readers).
- All 110 tests in `tests/` keep passing; `test_learning_path_for_the_poster_ad` is Phuong Nhi's (#68) and may change expectation, not ours.
- Commit messages: plain summary line, body optional, end with `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`.

## Review Focus

1. A subject whose access-conditions page has no "Requisite rule" line (36100) must yield one row with an empty rule, not be dropped, so the app can say "no prerequisites". Test in Task 2.
2. A rule that mixes admission items and academic codes (`((1 OR 1a ... OR 1e) AND 2)`, 36120) must keep every item with its type, so the app can treat "Admission into C04372" as satisfied for an MDSI student. Test in Task 2.
3. A subject in two courses scraped in one run (36106 in C04372 and C04379) must appear once with `courses = "C04372|C04379"`, otherwise `subject_profiles.csv` doubles its rows. Test in Task 1.
4. An ATS slug that returns HTTP 200 with an empty job list (company exists, no openings) must count as reachable with 0 ads, distinct from HTTP 404, so the company stays in `ats_companies.csv` for the daily rerun. Test in Task 5.
5. The rebuilt `subject_profiles.csv` must keep every one of the 1,039 existing rows (same `subject_code, layer, text`), so Phuong Nhi's calibration and the 110 tests see no regression. Check in Task 4.

---

### Task 1: Scrape six more courses and record teaching sessions

**Files:**
- Modify: `data-eda/src/scrape_handbook.py:112-136` (`parse_subject`) and the module docstring
- Create: `tests/test_scrape_handbook.py`
- Create: `tests/fixtures/handbook_payload_36118.json` (the `pageContent` dict of one subject, trimmed to the keys used)
- Output (gitignored): `data-eda/data/raw/uts_subjects_2026.csv`

**Interfaces:**
- Produces: `uts_subjects_2026.csv` with the 15 existing columns plus `sessions` (pipe-joined, e.g. `Autumn Session|Spring Session`) and `modes` (pipe-joined, e.g. `On campus - Weekly`). Task 2 and Task 4 read it.

- [ ] **Step 1: Save a payload fixture**

Run from the repo root:

```bash
.venv/Scripts/python.exe -I - <<'EOF'
import json, re, requests
h = requests.get("https://coursehandbook.uts.edu.au/subject/2026/36118",
                 headers={"User-Agent": "Mozilla/5.0 (UTS 36118 student project)"}, timeout=30).text
pc = json.loads(re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', h, re.S).group(1))["props"]["pageProps"]["pageContent"]
keep = ["code", "title", "credit_points", "academic_org", "study_level_ref", "implementation_year",
        "unit_learning_outcomes", "description", "learning_approach", "teaching_strategies", "requisite_detail", "offering"]
json.dump({k: pc.get(k) for k in keep}, open("tests/fixtures/handbook_payload_36118.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
EOF
```

Expected: file written, under 60 KB (`offering` holds ~4 entries).

- [ ] **Step 2: Write the failing tests**

```python
# tests/test_scrape_handbook.py
"""Tests for data-eda/src/scrape_handbook.py: the payload parser. Run: pytest tests/test_scrape_handbook.py"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "data-eda" / "src"))

from scrape_handbook import parse_subject  # noqa: E402

PAYLOAD = json.loads((ROOT / "tests/fixtures/handbook_payload_36118.json").read_text(encoding="utf-8"))


def test_sessions_are_the_unique_teaching_periods_sorted():
    row = parse_subject(PAYLOAD, "2026")
    assert row["sessions"] == "Autumn Session|Spring Session"


def test_modes_come_from_the_offerings():
    row = parse_subject(PAYLOAD, "2026")
    assert "On campus - Weekly" in row["modes"].split("|")


def test_no_offerings_gives_empty_strings():
    row = parse_subject({**PAYLOAD, "offering": None}, "2026")
    assert row["sessions"] == "" and row["modes"] == ""
```

- [ ] **Step 3: Run the tests to verify they fail**

Run: `.venv/Scripts/python.exe -m pytest tests/test_scrape_handbook.py -q -p no:cacheprovider`
Expected: 3 failed with `KeyError: 'sessions'`.

- [ ] **Step 4: Add `sessions` and `modes` to `parse_subject`**

In `data-eda/src/scrape_handbook.py`, replace the `return {` block of `parse_subject` with:

```python
    offerings = [o for o in (payload.get("offering") or []) if str(o.get("offered", "true")).lower() != "false"]
    sessions = sorted({o.get("teaching_period", "") for o in offerings if o.get("teaching_period")})
    modes = sorted({o.get("mode", "") for o in offerings if o.get("mode")})

    return {
        "subject_code": payload.get("code", ""),
        "subject_name": payload.get("title", ""),
        "credit_points": payload.get("credit_points", ""),
        "faculty": payload.get("academic_org", ""),
        "study_level": payload.get("study_level_ref", ""),
        "year": payload.get("implementation_year", year),
        "n_outcomes": len(ordered),
        "learning_outcomes": outcome_text,
        "description": clean(payload.get("description")),
        "topics": clean(payload.get("learning_approach")),
        "teaching_strategies": clean(payload.get("teaching_strategies")),
        "requisites": clean(payload.get("requisite_detail")),
        "sessions": "|".join(sessions),
        "modes": "|".join(modes),
        "handbook_url": f"{BASE}/subject/{year}/{payload.get('code', '')}",
    }
```

Add to the docstring, after the Output line: `Columns added 13 Oct 2026: sessions, modes (from the offering list).`

- [ ] **Step 5: Run the tests to verify they pass**

Run: `.venv/Scripts/python.exe -m pytest tests/test_scrape_handbook.py -q -p no:cacheprovider`
Expected: 3 passed.

- [ ] **Step 6: Put the existing raw file where the scripts expect it**

```bash
mkdir -p data-eda/data/raw
cp "data/raw/data-eda/data/raw/uts_subjects_2026.csv" data-eda/data/raw/uts_subjects_2026_vanthong_25sep.csv
```

(`data-eda/data/*` is gitignored except `clean/`; nothing here is committed.)

- [ ] **Step 7: Scrape all twelve courses in one run**

```bash
cd data-eda && ../.venv/Scripts/python.exe src/scrape_handbook.py \
  --course C04372 C04379 C04380 C04295 C04373 C04443 C10148 C10474 C10476 C10471 C10457 C10143 \
  --year 2026 --delay 0.7 --out data/raw/uts_subjects_2026.csv; cd ..
```

Expected: `Wrote N subjects` with N well above 70 (roughly 150-220); `FAILED` list empty or a handful. If a course yields 0 subjects, note it and continue; do not retry more than once.

- [ ] **Step 8: Check the merge of the old and new scrape**

```bash
.venv/Scripts/python.exe - <<'EOF'
import pandas as pd
old = pd.read_csv("data-eda/data/raw/uts_subjects_2026_vanthong_25sep.csv", dtype=str)
new = pd.read_csv("data-eda/data/raw/uts_subjects_2026.csv", dtype=str)
missing = sorted(set(old.subject_code) - set(new.subject_code))
print("old", len(old), "new", len(new), "old codes missing from new:", missing)
print("duplicate codes in new:", new.subject_code.duplicated().sum())
print(new.groupby(new.courses.str.split("|").str[0]).size().to_string())
print("36106 courses:", new.loc[new.subject_code == "36106", "courses"].tolist())
print("sessions empty:", (new.sessions.fillna("") == "").sum())
EOF
```

Expected: `old codes missing from new: []`, duplicates 0, 36106 lists both C04372 and C04379. If any old code is missing, append its row from the old file: `--codes <code>` run, then concatenate.

- [ ] **Step 9: Commit**

```bash
git switch -c qp/handbook-scrape
git add data-eda/src/scrape_handbook.py tests/test_scrape_handbook.py tests/fixtures/handbook_payload_36118.json
git commit -m "$(cat <<'EOF'
Handbook scraper records teaching sessions and modes

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
EOF
)"
```

---

### Task 2: Prerequisite rules and offerings for every subject

**Files:**
- Create: `data-eda/src/scrape_requisites.py`
- Create: `tests/test_scrape_requisites.py`
- Create: `tests/fixtures/evop_36118.html` (copy of `C:\Users\phamm\AppData\Local\Temp\claude\...\scratchpad\evop.html` saved on 12 Oct; re-fetch if gone)
- Output (committed): `data/processed/prerequisites.csv`, `data/processed/offerings.csv`

**Interfaces:**
- Produces `parse_requisites(html: str) -> dict` with keys `rule: str` (e.g. `"(1 AND 2 AND 3)"`, `""` when none) and `items: list[dict]`, each `{"item": "1a", "type": "academic"|"admission"|"other", "code": "36100"|"", "text": "..."}`.
- Produces `data/processed/prerequisites.csv`, long format, one row per item (and one row with empty item for a subject with no rule): `subject_code, rule, item, type, requisite_code, requisite_text, source_url`.
- Produces `data/processed/offerings.csv`: `subject_code, teaching_period, mode` from the `sessions`/`modes` columns of Task 1 (one row per session × mode).
- App plan Task B2 reads both files.

- [ ] **Step 1: Save the fixture**

```bash
cp "C:/Users/phamm/AppData/Local/Temp/claude/c--MDSI-03-Applied-NLP-assessments-at2/9c48fc1f-7d99-40b0-bf2a-28c53c3d9323/scratchpad/evop.html" tests/fixtures/evop_36118.html \
  || curl -s -A "Mozilla/5.0 (UTS 36118 student project)" "https://studentforms.uts.edu.au/evop/access/search.cfm?subjectcode=36118" -o tests/fixtures/evop_36118.html
ls -la tests/fixtures/evop_36118.html
```

Expected: about 10 KB.

- [ ] **Step 2: Write the failing tests**

```python
# tests/test_scrape_requisites.py
"""Tests for data-eda/src/scrape_requisites.py. Run: pytest tests/test_scrape_requisites.py"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "data-eda" / "src"))

from scrape_requisites import parse_requisites  # noqa: E402

HTML = (ROOT / "tests/fixtures/evop_36118.html").read_text(encoding="utf-8", errors="replace")

MIXED = """<html><body>Requisite rule: ((1 OR 1a) AND 2) Item Type Details
1 Admission requisite Admission into C04372 Master of Data Science and Innovation
1a Academic requisite Must have completed at least 48 credit points in 48.0000000000 Credit Points spk(s): C04379 - Master of Business Analytics (Extension)
2 Academic requisite 36106 Machine Learning Algorithms and Applications
Note: See also the information</body></html>"""

NONE = "<html><body>36100 Data Science for Innovation Note: See also the information</body></html>"


def test_36118_needs_three_subjects():
    out = parse_requisites(HTML)
    assert out["rule"] == "(1 AND 2 AND 3)"
    assert [i["code"] for i in out["items"]] == ["36100", "36103", "36106"]
    assert {i["type"] for i in out["items"]} == {"academic"}


def test_mixed_rule_keeps_item_types_and_ids():
    out = parse_requisites(MIXED)
    assert out["rule"] == "((1 OR 1a) AND 2)"
    assert out["items"][0] == {"item": "1", "type": "admission", "code": "",
                               "text": "Admission into C04372 Master of Data Science and Innovation"}
    assert out["items"][1]["item"] == "1a" and out["items"][1]["type"] == "academic" and out["items"][1]["code"] == ""
    assert out["items"][2] == {"item": "2", "type": "academic", "code": "36106",
                               "text": "36106 Machine Learning Algorithms and Applications"}


def test_no_rule_gives_empty_rule_and_no_items():
    assert parse_requisites(NONE) == {"rule": "", "items": []}
```

- [ ] **Step 3: Run the tests to verify they fail**

Run: `.venv/Scripts/python.exe -m pytest tests/test_scrape_requisites.py -q -p no:cacheprovider`
Expected: ImportError `No module named 'scrape_requisites'`.

- [ ] **Step 4: Write the scraper**

```python
# data-eda/src/scrape_requisites.py
"""Prerequisite rules and teaching sessions for every subject in uts_subjects_2026.csv.

The handbook's `requisite_detail` field is boilerplate that links to the access-conditions
page on studentforms.uts.edu.au, which lists the actual rule, e.g. for 36118:

    Requisite rule: (1 AND 2 AND 3)
    1 Academic requisite 36100 Data Science for Innovation
    2 Academic requisite 36103 Statistical Thinking for Data Science
    3 Academic requisite 36106 Machine Learning Algorithms and Applications

Item types: Academic (a subject code, or a credit-point condition), Admission (into a
course), Other. The rule is a boolean expression over item ids (1, 1a, 2 ...).

Usage (from the repo root):
    python data-eda/src/scrape_requisites.py                # all subjects in uts_subjects_2026.csv
    python data-eda/src/scrape_requisites.py --codes 36118  # a few

Writes data/processed/prerequisites.csv (one row per rule item) and
data/processed/offerings.csv (one row per session x mode, from the subjects file).
"""

from __future__ import annotations

import argparse
import html as html_lib
import logging
import re
import time
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]           # data-eda/
REPO = ROOT.parent
SUBJECTS = ROOT / "data" / "raw" / "uts_subjects_2026.csv"
OUT_PREREQ = REPO / "data" / "processed" / "prerequisites.csv"
OUT_OFFER = REPO / "data" / "processed" / "offerings.csv"
EVOP = "https://studentforms.uts.edu.au/evop/access/search.cfm?subjectcode={code}"
HEADERS = {"User-Agent": "Mozilla/5.0 (UTS 36118 student project)"}

RULE = re.compile(r"Requisite rule:\s*(.+?)\s*Item\s+Type\s+Details")
# "1a Academic requisite 36100 Data Science ..." up to the next item id or "Note:"
ITEM = re.compile(r"(?:(?<=\s)|^)(\d+[a-z]?)\s+(Academic|Admission|Other)\s+requisite\s+(.+?)(?=\s+\d+[a-z]?\s+(?:Academic|Admission|Other)\s+requisite\s|\s*Note:|$)",
                  re.S)
CODE = re.compile(r"^(\d{5})\b")
PREREQ_COLUMNS = ["subject_code", "rule", "item", "type", "requisite_code", "requisite_text", "source_url"]

log = logging.getLogger("scrape_requisites")


def page_text(html: str) -> str:
    text = re.sub(r"(?s)<(script|style).*?</\1>", " ", html)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", html_lib.unescape(text)).strip()


def parse_requisites(html: str) -> dict:
    """The rule and its items from an access-conditions page; {"rule": "", "items": []} when none."""
    text = page_text(html)
    m = RULE.search(text)
    if not m:
        return {"rule": "", "items": []}
    rule = m.group(1).strip()
    body = text[m.end():]
    body = body[:body.find("Note:")] if "Note:" in body else body
    items = []
    for item, kind, detail in ITEM.findall(body):
        detail = detail.strip()
        code = CODE.match(detail)
        items.append({"item": item, "type": kind.lower(), "code": code.group(1) if code else "", "text": detail})
    return {"rule": rule, "items": items}


def fetch(session: requests.Session, code: str) -> str | None:
    r = session.get(EVOP.format(code=code), headers=HEADERS, timeout=30)
    if r.status_code != 200:
        log.warning("%s -> HTTP %s", code, r.status_code)
        return None
    return r.text


def offerings_from_subjects(subjects: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for s in subjects.itertuples(index=False):
        sessions = [x for x in str(getattr(s, "sessions", "") or "").split("|") if x and x != "nan"]
        modes = [x for x in str(getattr(s, "modes", "") or "").split("|") if x and x != "nan"] or [""]
        for period in sessions:
            for mode in modes:
                rows.append({"subject_code": s.subject_code, "teaching_period": period, "mode": mode})
    return pd.DataFrame(rows, columns=["subject_code", "teaching_period", "mode"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--subjects", type=Path, default=SUBJECTS)
    parser.add_argument("--codes", nargs="*", default=None)
    parser.add_argument("--delay", type=float, default=0.6)
    parser.add_argument("--out", type=Path, default=OUT_PREREQ)
    parser.add_argument("--offerings-out", type=Path, default=OUT_OFFER)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    subjects = pd.read_csv(args.subjects, dtype=str)
    codes = args.codes or sorted(subjects.subject_code.dropna().unique())
    session = requests.Session()
    rows, failed = [], []
    for i, code in enumerate(codes, 1):
        html = fetch(session, code)
        if html is None:
            failed.append(code)
        else:
            out = parse_requisites(html)
            url = EVOP.format(code=code)
            if not out["items"]:
                rows.append({"subject_code": code, "rule": out["rule"], "item": "", "type": "",
                             "requisite_code": "", "requisite_text": "", "source_url": url})
            for it in out["items"]:
                rows.append({"subject_code": code, "rule": out["rule"], "item": it["item"], "type": it["type"],
                             "requisite_code": it["code"], "requisite_text": it["text"], "source_url": url})
            log.info("[%d/%d] %s rule=%s items=%d", i, len(codes), code, out["rule"] or "-", len(out["items"]))
        time.sleep(args.delay)

    df = pd.DataFrame(rows, columns=PREREQ_COLUMNS)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False, encoding="utf-8")
    offers = offerings_from_subjects(subjects[subjects.subject_code.isin(codes)])
    offers.to_csv(args.offerings_out, index=False, encoding="utf-8")
    print(f"\nWrote {args.out}: {len(df)} rows, {df.subject_code.nunique()} subjects, "
          f"{(df.rule != '').groupby(df.subject_code).any().sum()} with a rule")
    print(f"Wrote {args.offerings_out}: {len(offers)} rows, {offers.subject_code.nunique()} subjects")
    if failed:
        print(f"FAILED ({len(failed)}): {', '.join(failed)}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `.venv/Scripts/python.exe -m pytest tests/test_scrape_requisites.py -q -p no:cacheprovider`
Expected: 3 passed. If `test_36118_needs_three_subjects` fails on item boundaries, print `page_text(HTML)[:1200]` and adjust `ITEM` so each item ends where the next `<id> <Type> requisite` begins.

- [ ] **Step 6: Run the scraper on every subject**

Run: `.venv/Scripts/python.exe data-eda/src/scrape_requisites.py --delay 0.6`
Expected: about 150-220 subjects in 2-3 minutes; `FAILED` empty. Spot-check:

```bash
.venv/Scripts/python.exe - <<'EOF'
import pandas as pd
p = pd.read_csv("data/processed/prerequisites.csv", dtype=str).fillna("")
for c in ["36100", "36118", "43023", "36120", "94693"]:
    print(c, "|", p[p.subject_code == c].rule.iloc[0], "|", p[p.subject_code == c].requisite_code.tolist())
o = pd.read_csv("data/processed/offerings.csv", dtype=str)
print(o[o.subject_code.isin(["36118", "94691", "36120"])].to_string(index=False))
EOF
```

Expected: 36100 rule empty; 36118 `(1 AND 2 AND 3)` with `['36100','36103','36106']`; 43023 `((1 OR 1a))` with `['42172','41040']`; 36120 ends `AND 2` with `36106`; 94693 `(1)` with `36100`; 94691 only Autumn, 36120 only Spring.

- [ ] **Step 7: Commit**

```bash
git add data-eda/src/scrape_requisites.py tests/test_scrape_requisites.py tests/fixtures/evop_36118.html data/processed/prerequisites.csv data/processed/offerings.csv
git commit -m "$(cat <<'EOF'
Prerequisite rules and teaching sessions for every scraped subject

From the access-conditions page (studentforms.uts.edu.au) and the handbook
offering list. 36118 = 36100 AND 36103 AND 36106; 43023 needs 42172 or
41040, which MDSI does not offer.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
EOF
)"
```

---

### Task 3: Assessment table probe (spike, 30 minutes cap)

**Files:**
- Create if the probe succeeds: `data-eda/src/scrape_assessments.py`, output `data/processed/assessments_scraped.csv` (columns of `subject_profiles.csv`, `layer = assessment`, `collected_by = "script (handbook)"`)
- Modify if the probe succeeds: `data-eda/src/build_subject_profiles.py:215-216` so `--assessments` takes several paths (`nargs="+"`) and `load_assessments` concatenates them
- Always: a paragraph in `data/processed/subject_profiles.md` under "The assessment layer" stating what the probe found

**Interfaces:**
- Produces (success case) rows for Task 4's rebuild; otherwise nothing, and issue #62 keeps the manual fallback.

- [ ] **Step 1: Load the Playwright tools**

`ToolSearch` with `select:mcp__plugin_playwright_playwright__browser_navigate,mcp__plugin_playwright_playwright__browser_snapshot,mcp__plugin_playwright_playwright__browser_click,mcp__plugin_playwright_playwright__browser_network_requests,mcp__plugin_playwright_playwright__browser_close`.

- [ ] **Step 2: Open 36118 and trigger the availability selector**

Navigate to `https://coursehandbook.uts.edu.au/subject/2026/36118`; snapshot; click the element whose text is "Select availability"; snapshot; click the first offering (e.g. "City campus - Autumn Session - On campus - Weekly"); snapshot and confirm an "Assessment" heading with task rows now appears.

- [ ] **Step 3: Find where the table came from**

Call `browser_network_requests`; list requests made after the click whose URL contains `assessment`, `offering`, `courseloop`, `api` or ends in `.json`. For the most likely one, replay it without browser cookies:

```bash
curl -s -o /dev/null -w "%{http_code}\n" -A "Mozilla/5.0 (UTS 36118 student project)" "<url>"
```

- [ ] **Step 4a: If a public JSON endpoint returns 200**

Write `data-eda/src/scrape_assessments.py` modelled on `scrape_requisites.py`: for each subject code and each offering id from the handbook payload (`offering[].off_id`), GET the endpoint, take each assessment task's title and description, and emit rows `{subject_code, subject_name, course, layer: "assessment", text: f"{title}: {description}", source_url, collected_by: "script (handbook)"}` de-duplicated on `(subject_code, text)` (the same task repeats per offering). Write `data/processed/assessments_scraped.csv`. Change `build_subject_profiles.py` so `--assessments` is `nargs="+"` and `load_assessments` concatenates every existing path. Run it on 5 codes first, then all. Commit with message `Assessment layer scraped from the handbook offering pages`.

- [ ] **Step 4b: If it is 401/403 or the table is rendered without a separate request**

Try once more with `browser_network_requests` filtered to the page's own origin (`coursehandbook.uts.edu.au`); if the assessment text is present in the initial `__NEXT_DATA__` under a different key, grep the saved page for the first task's title and record the key. If still nothing within 30 minutes, stop. Add to `data/processed/subject_profiles.md`:

> Probe 13 Oct (Claude): the assessment table loads after "Select availability" from `<url>`, which returns HTTP `<code>` without a browser session, so it stays hand-collected (issue #62, Van Thong, 19 MDSI subjects).

and comment on issue #62 with the same sentence.

- [ ] **Step 5: Close the browser and commit whatever was produced**

`browser_close`; `git add -A data-eda/src data/processed/subject_profiles.md data/processed/assessments_scraped.csv 2>/dev/null; git commit` with the message from 4a or `Record the assessment-table probe result`.

---

### Task 4: Rebuild the subject profiles and check nothing regressed

**Files:**
- Modify (data): `data/processed/subject_profiles.csv`, `data/processed/subject_profiles.md`
- Run: `data-eda/src/build_subject_profiles.py`, `tests/`

**Interfaces:**
- Produces the new `subject_profiles.csv` that `recommend()`, `rag.py`, `app/baseline.py` and the chat load by path; same columns, more rows.

- [ ] **Step 1: Keep the old file for comparison**

```bash
cp data/processed/subject_profiles.csv "C:/Users/phamm/AppData/Local/Temp/claude/c--MDSI-03-Applied-NLP-assessments-at2/9c48fc1f-7d99-40b0-bf2a-28c53c3d9323/scratchpad/subject_profiles_old.csv"
```

- [ ] **Step 2: Rebuild**

```bash
cd data-eda && ../.venv/Scripts/python.exe src/build_subject_profiles.py; cd ..
```

If Task 3 produced `assessments_scraped.csv`: `src/build_subject_profiles.py --assessments ../data/labels/subject_content.csv ../data/processed/assessments_scraped.csv`.

Expected: `Wrote ... rows from N subjects` with N equal to the Task 1 count; the per-layer summary printed.

- [ ] **Step 3: Verify every old row survived (Review Focus 5)**

```bash
.venv/Scripts/python.exe - <<'EOF'
import pandas as pd
S = "C:/Users/phamm/AppData/Local/Temp/claude/c--MDSI-03-Applied-NLP-assessments-at2/9c48fc1f-7d99-40b0-bf2a-28c53c3d9323/scratchpad/subject_profiles_old.csv"
old = pd.read_csv(S, dtype=str); new = pd.read_csv("data/processed/subject_profiles.csv", dtype=str)
key = ["subject_code", "layer", "text"]
lost = old.merge(new[key], on=key, how="left", indicator=True).query("_merge == 'left_only'")
print("old rows", len(old), "new rows", len(new), "lost", len(lost))
print(lost[key].head(10).to_string(index=False)) if len(lost) else None
print(new.groupby("layer").agg(rows=("text", "size"), subjects=("subject_code", "nunique")))
print("courses:", new.course.str.split("|").explode().value_counts().to_dict())
EOF
```

Expected: `lost 0`. If a row differs only by the mojibake repair or whitespace, accept it and note the count; if whole subjects are lost, go back to Task 1 Step 8.

- [ ] **Step 4: Run the full test suite and the poster path**

```bash
env -u OPENAI_API_KEY .venv/Scripts/python.exe -m pytest -q -p no:cacheprovider
.venv/Scripts/python.exe - <<'EOF'
import sys; sys.path.insert(0, "src")
from pathlib import Path
from skillabus.extract import extract; from skillabus.match import match; from skillabus.recommend import recommend
ad = Path("tests/fixtures/ad_rw_2026-09-23.txt").read_text(encoding="utf-8"); cv = Path("tests/fixtures/resume_synthetic.txt").read_text(encoding="utf-8")
gaps = [s for s in match(extract(ad), extract(cv)) if s["status"] != "have"]
r = recommend(gaps); print(r["learning_path"]); print([(x["subject_code"], x["covers"]) for x in r["recommendations"][:5]])
EOF
```

Expected: 110 passed (tests read `tests/fixtures/subject_profiles_sample.csv`, not the rebuilt file, so they must not change). The poster path prints; record it in the PR body (it may now include a bachelor or Master of IT subject: say so, that is for Phuong Nhi's #68 to rank by course).

- [ ] **Step 5: Update `subject_profiles.md`**

Replace the header table (Rows, Subjects, Built) and the "Rows per layer" table with the numbers from Step 3, add a "Courses" line listing the twelve codes with subject counts, add under "Known gaps": `Bachelor subjects (C10xxx) are shown to MDSI students with a "bachelor" tag; most cannot be enrolled in postgraduate study (ideas doc 4.3 item 5).` Keep the rest.

- [ ] **Step 6: Commit and open the PR**

```bash
git add data/processed/subject_profiles.csv data/processed/subject_profiles.md
git commit -m "$(cat <<'EOF'
Subject profiles rebuilt over twelve courses, with sessions and prerequisites alongside

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
EOF
)"
git push -u origin qp/handbook-scrape
gh pr create --base main --title "Handbook: 12 courses, prerequisites, sessions, assessment probe" --reviewer tompham9016 --body "$(cat <<'EOF'
Closes part of #62 (Van Thong: review, then the manual assessment rows if Task 3 failed).

## What changed
- `scrape_handbook.py` records `sessions` and `modes`; scraped C04372 C04379 C04380 C04295 C04373 C04443 C10148 C10474 C10476 C10471 C10457 C10143.
- New `scrape_requisites.py` -> `data/processed/prerequisites.csv` (rule + items per subject) and `offerings.csv`.
- `subject_profiles.csv` rebuilt: <rows> rows, <subjects> subjects; every previous row kept.
- Assessment probe: <result sentence from Task 3>.

## How to check it
`pytest tests/test_scrape_handbook.py tests/test_scrape_requisites.py`; `python data-eda/src/build_subject_profiles.py` reproduces the CSV from `data-eda/data/raw/uts_subjects_2026.csv` (not committed; ask Quan).
Poster path now: <path>.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

---

### Task 5: Probe ~100 Australian employers on the public ATS APIs

**Files:**
- Create: `data-eda/config/ats_candidates.csv` (`company,greenhouse,lever,smartrecruiters,ashby,workable` slug guesses, blank when unknown)
- Create: `data-eda/src/probe_ats.py`
- Create: `tests/test_probe_ats.py`
- Output (committed, small): `data-eda/data/clean/ats_probe_2026-10-13.csv`
- Modify: `data-eda/config/ats_companies.csv` (append reachable companies with AU data roles)

**Interfaces:**
- Produces `count_roles(rows: list[dict]) -> dict` with `total`, `au`, `data_au`, `ds_au` using `AU_PATTERN` from `fetch_ats` and `DATA_TITLE` from `build_recent_sample`, plus `DS_TITLE = re.compile(r"data scien|applied scien|research scien|machine learning|\bML\b|AI scientist", re.I)`.
- Produces `probe(session, platform, slug) -> dict` with `status` (`ok`, `empty`, `missing`, `error`), `rows`.
- Van Thong's #64 consumes `ats_probe_2026-10-13.csv` and the appended `ats_companies.csv`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_probe_ats.py
"""Tests for data-eda/src/probe_ats.py counting rules. Run: pytest tests/test_probe_ats.py"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "data-eda" / "src"))

from probe_ats import classify, count_roles  # noqa: E402


def row(title, location):
    return {"title": title, "location": location, "description": "x"}


def test_counts_split_by_country_and_title():
    rows = [row("Data Scientist", "Sydney"), row("Senior Data Scientist", "Melbourne, VIC"),
            row("Data Engineer", "Sydney"), row("Data Scientist", "London"), row("Graphic AI Designer", "Sydney")]
    assert count_roles(rows) == {"total": 5, "au": 4, "data_au": 3, "ds_au": 2}


def test_empty_board_is_reachable_but_empty():
    assert classify(200, []) == "empty"
    assert classify(200, [row("x", "y")]) == "ok"
    assert classify(404, None) == "missing"
    assert classify(500, None) == "error"
```

Note the fifth row: "Graphic AI Designer" must not count as a data role (the bare `\bAI\b` in `DATA_TITLE` is what #64 tightens; `count_roles` applies `DS_TITLE` for `ds_au` and `DATA_TITLE` minus bare AI for `data_au`).

- [ ] **Step 2: Run the test to verify it fails**

Run: `.venv/Scripts/python.exe -m pytest tests/test_probe_ats.py -q -p no:cacheprovider`
Expected: ImportError.

- [ ] **Step 3: Write the probe**

```python
# data-eda/src/probe_ats.py
"""Which Australian employers can we reach through a public ATS job-board API, and how many
data-scientist ads do they have open right now?

Reads config/ats_candidates.csv (one row per company, a slug guess per platform; blank = not
tried), hits each platform's public listing endpoint, and writes data/clean/ats_probe_<date>.csv
with one row per (company, platform): status, total ads, Australian ads, Australian data roles,
Australian data-scientist roles. No key, no login; these endpoints exist to render the
companies' own careers pages (see fetch_ats.py).

Usage (from data-eda/):
    python src/probe_ats.py
    python src/probe_ats.py --only canva atlassian
"""

from __future__ import annotations

import argparse
import logging
import re
import time
from datetime import date
from pathlib import Path

import pandas as pd
import requests

from build_recent_sample import DATA_TITLE
from fetch_ats import AU_PATTERN, HEADERS, fetch_greenhouse, fetch_lever, fetch_smartrecruiters, to_text

ROOT = Path(__file__).resolve().parents[1]
ASHBY = "https://api.ashbyhq.com/posting-api/job-board/{slug}"
WORKABLE = "https://apply.workable.com/api/v1/widget/accounts/{slug}"
DS_TITLE = re.compile(r"data scien|applied scien|research scien|machine learning|\bML\b|AI scientist", re.I)
BARE_AI = re.compile(r"\bAI\b", re.I)
PLATFORMS = ("greenhouse", "lever", "smartrecruiters", "ashby", "workable")

log = logging.getLogger("probe_ats")


def classify(status_code: int, rows: list | None) -> str:
    if status_code == 404:
        return "missing"
    if status_code != 200:
        return "error"
    return "ok" if rows else "empty"


def is_data_title(title: str) -> bool:
    """DATA_TITLE without the bare 'AI' match that lets 'Graphic AI Designer' through."""
    t = title or ""
    if DS_TITLE.search(t):
        return True
    return bool(DATA_TITLE.search(t)) and not (BARE_AI.search(t) and not re.search(r"data|analy|engineer|scien|learning|intelligence", t, re.I))


def count_roles(rows: list[dict]) -> dict:
    au = [r for r in rows if AU_PATTERN.search(r.get("location") or "")]
    return {"total": len(rows), "au": len(au),
            "data_au": sum(is_data_title(r.get("title")) for r in au),
            "ds_au": sum(bool(DS_TITLE.search(r.get("title") or "")) for r in au)}


def fetch_ashby(session, slug):
    r = session.get(ASHBY.format(slug=slug), headers=HEADERS, timeout=30)
    rows = [] if r.status_code != 200 else [
        {"ad_id": f"as-{j.get('id')}", "source": "ashby", "title": j.get("title", ""), "company": slug,
         "location": j.get("location", ""), "created": j.get("publishedAt", ""),
         "description": to_text(j.get("descriptionHtml") or j.get("descriptionPlain")), "redirect_url": j.get("jobUrl", "")}
        for j in r.json().get("jobs", [])]
    return r.status_code, rows


def fetch_workable(session, slug):
    r = session.get(WORKABLE.format(slug=slug), params={"details": "true"}, headers=HEADERS, timeout=30)
    rows = [] if r.status_code != 200 else [
        {"ad_id": f"wk-{j.get('shortcode')}", "source": "workable", "title": j.get("title", ""), "company": slug,
         "location": ", ".join(filter(None, [j.get("city"), j.get("state"), j.get("country")])),
         "created": j.get("published_on", ""), "description": to_text(j.get("description")), "redirect_url": j.get("url", "")}
        for j in r.json().get("jobs", [])]
    return r.status_code, rows


def probe(session, platform: str, slug: str) -> dict:
    try:
        if platform == "greenhouse":
            r = session.get(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs", headers=HEADERS, timeout=30)
            rows = fetch_greenhouse(session, slug, slug, False) if r.status_code == 200 else []
            code = r.status_code
        elif platform == "lever":
            r = session.get(f"https://api.lever.co/v0/postings/{slug}", params={"mode": "json"}, headers=HEADERS, timeout=30)
            rows = fetch_lever(session, slug, slug, False) if r.status_code == 200 else []
            code = r.status_code
        elif platform == "smartrecruiters":
            r = session.get(f"https://api.smartrecruiters.com/v1/companies/{slug}/postings", params={"limit": 1}, headers=HEADERS, timeout=30)
            code = r.status_code
            rows = []
            if code == 200 and (r.json().get("totalFound") or 0) > 0:
                rows = fetch_smartrecruiters(session, slug, slug, False, au_only=True, delay=0.25)
        elif platform == "ashby":
            code, rows = fetch_ashby(session, slug)
        else:
            code, rows = fetch_workable(session, slug)
    except (requests.RequestException, ValueError) as exc:
        log.warning("%s/%s -> %s", platform, slug, exc)
        return {"status": "error", "rows": []}
    return {"status": classify(code, rows), "rows": rows}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--candidates", type=Path, default=ROOT / "config" / "ats_candidates.csv")
    parser.add_argument("--only", nargs="*", default=None, help="company names to probe")
    parser.add_argument("--delay", type=float, default=0.8)
    parser.add_argument("--out", type=Path, default=ROOT / "data" / "clean" / f"ats_probe_{date.today().isoformat()}.csv")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    cands = pd.read_csv(args.candidates, dtype=str).fillna("")
    if args.only:
        cands = cands[cands.company.str.lower().isin([o.lower() for o in args.only])]
    session = requests.Session()
    out = []
    for c in cands.itertuples(index=False):
        for platform in PLATFORMS:
            slug = getattr(c, platform, "")
            if not slug:
                continue
            res = probe(session, platform, slug)
            counts = count_roles(res["rows"])
            out.append({"company": c.company, "platform": platform, "slug": slug, "status": res["status"], **counts})
            log.info("%-28s %-15s %-8s total=%3d au=%3d data_au=%2d ds_au=%2d", c.company, platform, res["status"],
                     counts["total"], counts["au"], counts["data_au"], counts["ds_au"])
            time.sleep(args.delay)
    df = pd.DataFrame(out)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False, encoding="utf-8")
    hit = df[df.status == "ok"]
    print(f"\nWrote {args.out}: {len(df)} probes, {len(hit)} reachable boards, "
          f"{int(hit.au.sum())} AU ads, {int(hit.data_au.sum())} AU data roles, {int(hit.ds_au.sum())} AU data-scientist roles")
    print(hit.sort_values('ds_au', ascending=False)[['company', 'platform', 'au', 'data_au', 'ds_au']].head(30).to_string(index=False))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `.venv/Scripts/python.exe -m pytest tests/test_probe_ats.py -q -p no:cacheprovider`
Expected: 2 passed.

- [ ] **Step 5: Write the candidate list**

Create `data-eda/config/ats_candidates.csv` with the header `company,greenhouse,lever,smartrecruiters,ashby,workable` and about 100 rows. Slugs are lower-case company names with spaces removed; put the same guess in every column you cannot rule out (the probe tolerates misses). Include the 12 already in `ats_companies.csv` (they confirm the probe works), then: Atlassian, REA Group, Xero, Airwallex, Rokt, SafetyCulture, Linktree, Employment Hero, Go1, Zip, Tyro, Afterpay, Block, Up, Brighte, Nearmap, Propeller Aero, Harrison.ai, Annalise.ai, Displayr, Pet Circle, Cover Genius, Shippit, Buildkite, Secure Code Warrior, Mr Yum, SiteMinder, Ansarada, Bugcrowd, Lendi, Finder, Hnry, Zeller, Swyftx, CoinJar, Hatch, Stake, Spaceship, Honey Insurance, Open, Amber Electric, Dovetail, Vow, Loam Bio, Hivery, Relevance AI, Leonardo.ai, Fleet Space, Q-CTRL, Morse Micro, Sonder, Envato, Kogan, Koala, Who Gives A Crap, Culture Amp, Canva, SEEK, Judo Bank, Eucalyptus, hipages, Prospa, Athena, Octopus Deploy, Mable, Deputy, Immutable, Stripe, Datadog, Databricks, Cloudflare, Twilio, MongoDB, Elastic, HashiCorp, GitLab, Dropbox, Figma, Airbnb, DoorDash, Squarespace, Zendesk, Snowflake, Okta, Wise, Revolut, Deliveroo, Uber, Shopify, Intercom, Miro, Notion, Anthropic, OpenAI, Scale AI, Cohere, ServiceNow, Workday, Salesforce, Adobe, Autodesk, Atlassian (lever), Amazon (none), Microsoft (none), Google (none).

- [ ] **Step 6: Run the probe**

```bash
cd data-eda && ../.venv/Scripts/python.exe src/probe_ats.py --delay 0.8 2>&1 | tail -40; cd ..
```

Expected: 3-8 minutes; a table of reachable boards sorted by `ds_au`. Record the three totals.

- [ ] **Step 7: Append the reachable companies and refetch**

```bash
.venv/Scripts/python.exe - <<'EOF'
import pandas as pd
from datetime import date
p = pd.read_csv(f"data-eda/data/clean/ats_probe_{date.today().isoformat()}.csv", dtype=str)
hit = p[(p.status == "ok") & (p.data_au.astype(int) > 0)][["platform", "slug", "company"]].assign(verified="yes")
cur = pd.read_csv("data-eda/config/ats_companies.csv", dtype=str)
new = hit[~hit.slug.isin(cur.slug)]
allc = pd.concat([cur, new[cur.columns]], ignore_index=True)
allc.to_csv("data-eda/config/ats_companies.csv", index=False)
print("added", len(new), "->", len(allc), "companies"); print(new.to_string(index=False))
EOF
cd data-eda && ../.venv/Scripts/python.exe src/fetch_ats.py --australia-only --out data/raw/ats_ads_2026-10-13.csv | tail -15; cd ..
```

Expected: `fetch_ats.py` prints `Wrote N ads`; N is the new 2026 full-text pool before title filtering. Do not run `build_recent_sample.py` (Van Thong's #64 decides the filter and the cap).

- [ ] **Step 8: Commit and hand over**

```bash
git add data-eda/src/probe_ats.py tests/test_probe_ats.py data-eda/config/ats_candidates.csv data-eda/config/ats_companies.csv data-eda/data/clean/ats_probe_*.csv
git commit -m "$(cat <<'EOF'
Probe ~100 employers on public ATS job-board APIs; add the reachable ones

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
EOF
)"
git push
gh issue comment 64 --body "Probe run 13 Oct (branch qp/handbook-scrape, data-eda/data/clean/ats_probe_2026-10-13.csv): <reachable> boards reachable, <au> AU ads, <data_au> AU data roles, <ds_au> AU data-scientist roles. Companies with AU data roles were appended to ats_companies.csv; fetch_ats.py --australia-only now returns <N> ads (raw file not committed). Title filter and the 3-per-company cap are yours in build_recent_sample.py."
```
