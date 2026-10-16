"""Live Adzuna counts per skill x role for the 11 IT roles (plan D12, issue #115).

For each role: one call for the role total (live Australian ads whose TITLE has the role's words,
Adzuna's `title_only`), then one call per priority skill with the same title filter plus the
skill's phrase (`what_phrase`). Only Adzuna's `count` is kept; no ad text is stored.

What a count means (checked 16 Oct 2026 on three phrases): `what_phrase` searches the whole ad, not
only the title and the 500-character snippet the API returns. Of 50 ads returned for "stakeholder
management", 11 show the phrase in title or snippet; the rest match further down the ad. So a share
here is "ads with this title that mention the skill anywhere", comparable to the full-text counts.

Two files, both reviewable by hand:
    data/2_demand/collection/adzuna_queries.csv   role, title_query, skill, what_phrase, note
    data/2_demand/adzuna_counts_2026-10.csv       role, role_query, skill, skill_query, count, role_total, date

`--write-queries` (re)builds the queries file from priority_skills.csv and the vocabulary: the
phrase is the skill's first ad alias, else its label, except where PHRASE below says otherwise; a
skill in ESCO's wording that no ad uses gets no phrase and is not counted (count left blank).

Adzuna allows 25 calls a minute and 250 a day: 11 role totals + about 160 skills, 2.5 s apart.

Usage (from the repo root; credentials as in count_cert_adzuna.py):
    python data-eda/src/count_role_skills_adzuna.py --write-queries     # no calls
    python data-eda/src/count_role_skills_adzuna.py --limit 3 --dry-run   # first 3 rows, writes nothing
    python data-eda/src/count_role_skills_adzuna.py                     # all rows, writes the counts file
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import sys
import time
from pathlib import Path

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from count_cert_adzuna import count_ads  # noqa: E402
from skillabus import paths  # noqa: E402

QUERIES = paths.DEMAND / "collection" / "adzuna_queries.csv"
COUNTS = paths.DEMAND / "adzuna_counts_2026-10.csv"
COLUMNS = ["role", "role_query", "skill", "skill_query", "count", "role_total", "date"]

# Title words per role, chosen on live counts on 16 Oct (title_only keeps ads with all the words).
TITLE = {
    "Data Scientist": "data scientist",
    "Data Analyst": "data analyst",
    "Data Engineer": "data engineer",
    "Machine Learning Engineer": "machine learning engineer",
    "Software Engineer": "software engineer",
    "QA/Test Engineer": "test analyst",            # "tester" (910) also catches penetration and non-IT testers
    "Cloud Engineer": "cloud engineer",
    "DevOps/SRE": "devops",                         # "site reliability" adds 78 more; one query per role
    "Network/Systems Administrator": "systems administrator",   # "network engineer" also catches telecom roles
    "Cybersecurity Analyst": "security analyst",    # "cyber security" (358) also catches managers and engineers
    "Business Analyst": "business analyst",
}
# Where the first ad alias is a poor search phrase. "" = ESCO wording no ad uses: not counted.
PHRASE = {
    "Artificial intelligence": ("ai", "ads write AI far more often than the full name"),
    "C": ("c", "bare letter; within these titles mostly the language (c 130, c# 160, c++ 210 for software engineer)"),
    "Excel": ("excel", "also a verb ('excel in a team'): may over-count"),
    "Firewalls": ("firewall", "the singular, the more common form in ads"),
    "MITRE ATT&CK": ("mitre", "the & splits the name"),
    "Natural language processing": ("nlp", "ads write NLP more often than the full name"),
    "Oracle": ("oracle", "also the company name"),
    "Predictive modelling": ("predictive modelling", "Australian spelling; 'modeling' not counted"),
    "R": ("r programming", "a bare R matches R&D and initials: under-counts R"),
    "React": ("react", "also a verb: may over-count"),
    "Spark": ("spark", "also a verb: may over-count"),
    "Windows": ("windows", "the first alias 'microsoft windows' is rare in ads"),
    "administer ICT system": ("", "ESCO wording, not an ad phrase: not counted"),
    "collect cyber defence data": ("", "ESCO wording, not an ad phrase: not counted"),
    "cyber attack counter-measures": ("", "ESCO wording, not an ad phrase: not counted"),
}


def write_queries() -> pd.DataFrame:
    vocab = pd.read_csv(paths.SKILLS_VOCABULARY, dtype=str, keep_default_na=False).set_index("label")
    prio = pd.read_csv(paths.PRIORITY_SKILLS, dtype=str, keep_default_na=False)
    rows = []
    for r in prio.itertuples():
        aliases = [a.strip() for a in vocab.loc[r.skill].aliases_ads.split("|") if a.strip()]
        phrase, note = PHRASE.get(r.skill, ((aliases[0] if aliases else r.skill).lower(), ""))
        rows.append({"role": r.role, "title_query": TITLE[r.role], "skill": r.skill, "what_phrase": phrase, "note": note})
    q = pd.DataFrame(rows)
    QUERIES.parent.mkdir(parents=True, exist_ok=True)
    q.to_csv(QUERIES, index=False, lineterminator="\n")
    return q


def main(argv=None) -> None:
    from dotenv import load_dotenv
    load_dotenv(paths.ENV_FILE)
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--write-queries", action="store_true", help="rebuild the queries file, make no calls")
    p.add_argument("--limit", type=int, default=None, help="only the first N query rows")
    p.add_argument("--dry-run", action="store_true", help="print, write nothing")
    p.add_argument("--delay", type=float, default=2.5)
    p.add_argument("--app-id", default=os.environ.get("ADZUNA_APP_ID"))
    p.add_argument("--app-key", default=os.environ.get("ADZUNA_APP_KEY"))
    a = p.parse_args(argv)
    if a.write_queries:
        q = write_queries()
        print(f"wrote {QUERIES.name}: {len(q)} rows, {(q.what_phrase == '').sum()} not counted")
        return
    if not (a.app_id and a.app_key):
        raise SystemExit("Missing credentials: ADZUNA_APP_ID and ADZUNA_APP_KEY (see .env.example)")
    q = pd.read_csv(QUERIES, dtype=str, keep_default_na=False)
    if a.limit:
        q = q.head(a.limit)
    keys = dict(app_id=a.app_id, app_key=a.app_key)
    session, today = requests.Session(), dt.date.today().isoformat()
    totals = {}
    for role, title in q[["role", "title_query"]].drop_duplicates().itertuples(index=False):
        totals[role] = count_ads(session, "", title_only=title, **keys)
        print(f"{totals[role]!s:>6}  {role} (title: {title!r})")
        time.sleep(a.delay)
    out = []
    for r in q.itertuples():
        n = None
        if r.what_phrase:
            n = count_ads(session, r.what_phrase, title_only=r.title_query, **keys)
            if n is not None and totals[r.role] is not None and n > totals[r.role]:
                raise SystemExit(f"{r.role} x {r.skill}: {n} > role total {totals[r.role]}; the title filter was ignored")
            time.sleep(a.delay)
        print(f"{n!s:>6}  {r.role:30} {r.skill}")
        out.append({"role": r.role, "role_query": r.title_query, "skill": r.skill, "skill_query": r.what_phrase,
                    "count": n, "role_total": totals[r.role], "date": today})
    df = pd.DataFrame(out, columns=COLUMNS).astype({"count": "Int64", "role_total": "Int64"})
    if a.dry_run:
        print(df.to_string(index=False))
        return
    df.to_csv(COUNTS, index=False, lineterminator="\n")
    print(f"wrote {COUNTS.name}: {len(df)} rows, {df['count'].notna().sum()} counted")


if __name__ == "__main__":
    main()
