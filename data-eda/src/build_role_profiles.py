"""Skill profiles for 7 data and IT roles, from Luke Barousse's 2023 job-postings dataset.

Source: https://huggingface.co/datasets/lukebarousse/data_jobs (Apache-2.0), 785,741 postings
collected from Google Jobs in 2023. Each posting carries `job_title_short` (a 10-class title
from the author's BERT classifier) and `job_skills`, a list of tool names the author extracted.
There is no ad text, so a profile here is about tools: concepts such as machine learning,
statistics or communication cannot appear (the Seek full-text profile covers those for
Data Scientist).

Steps:
  1. Australian postings (`job_country == "Australia"`), de-duplicated on title + company +
     location, since the same ad is often listed on several boards.
  2. Seven roles; the senior titles fold into their role:
       Data Engineer (+ Senior), Data Analyst (+ Senior), Data Scientist (+ Senior),
       Software Engineer, Business Analyst, Cloud Engineer, Machine Learning Engineer.
  3. Each tool name -> a skill of data/1_knowledge/skills/skills_seed_v2.csv: by canonical name or
     alias, or through TOKEN_MAP for the dataset's bare names ("shell", "word").
     Unmapped names are counted in the log and left out. "go" is dropped as well: the
     dataset's extractor counts the English word (Go in 9% of Data Analyst ads), so Go
     cannot be measured from this source.
  4. Per role and skill: ads naming it, share of the role's ads that name any tool, and
     the 95% Wilson interval.

Output: data/2_demand/role_profiles.csv
    role, skill, category, n_ads, pct_ads, pct_low, pct_high, total_ads, source

Usage (from the repo root):
    python data-eda/src/build_role_profiles.py
    python data-eda/src/build_role_profiles.py --data path/to/data_jobs.csv
"""

from __future__ import annotations

import argparse
import ast
import csv
import logging
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

from recount_recent import wilson

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))  # repo src/, for skillabus.paths
from skillabus import paths  # noqa: E402

DEFAULT_DATA = paths.DATA_JOBS_RAW
SEED = paths.SKILLS_SEED
OUT = paths.ROLE_PROFILES
SOURCE = "lukebarousse/data_jobs (2023, Australia)"

ROLES = {
    "Data Engineer": "Data Engineer", "Senior Data Engineer": "Data Engineer",
    "Data Analyst": "Data Analyst", "Senior Data Analyst": "Data Analyst",
    "Data Scientist": "Data Scientist", "Senior Data Scientist": "Data Scientist",
    "Software Engineer": "Software Engineer",
    "Business Analyst": "Business Analyst",
    "Cloud Engineer": "Cloud Engineer",
    "Machine Learning Engineer": "Machine Learning Engineer",
}

# The dataset's bare tool names that our aliases leave out on purpose, because in running text
# they are ordinary words ("in other words", "market outlook"). In a tool list they are tools.
TOKEN_MAP = {
    "shell": "Shell scripting", "unix": "Linux", "windows": "Windows",
    "word": "Microsoft Office", "outlook": "Microsoft Office", "sap": "SAP", "react": "React",
    "node": "JavaScript", "dax": "Power BI",
}

# Tool names the dataset's extractor also finds in ordinary English; not counted.
UNRELIABLE = {"go", "flow"}

log = logging.getLogger("build_role_profiles")


def load_dictionary(path: Path = SEED) -> tuple[dict[str, str], dict[str, str]]:
    """({lower-case name or alias: canonical}, {canonical: category})."""
    with open(path, encoding="utf-8") as f:
        rows = list(csv.DictReader(l for l in f if not l.startswith("# ")))   # never comment="#": C#
    lookup, category = {}, {}
    for r in rows:
        category[r["canonical"]] = r["category"]
        lookup[r["canonical"].casefold()] = r["canonical"]
        for alias in r["aliases"].split("|"):
            if alias:
                lookup.setdefault(alias.casefold(), r["canonical"])
    return lookup, category


def to_skill(token: str, lookup: dict[str, str]) -> str | None:
    t = token.strip().casefold()
    if t in UNRELIABLE:
        return None
    return TOKEN_MAP.get(t) or lookup.get(t)


def parse_skills(cell: str) -> list[str]:
    """"['python', 'sql']" -> ['python', 'sql']; empty or malformed -> []."""
    if not cell or not cell.startswith("["):
        return []
    try:
        return [str(x) for x in ast.literal_eval(cell)]
    except (ValueError, SyntaxError):
        return []


def australian_postings(df: pd.DataFrame) -> pd.DataFrame:
    au = df[(df.job_country == "Australia") & df.job_title_short.isin(ROLES)].copy()
    before = len(au)
    au = au.drop_duplicates(["job_title", "company_name", "job_location"])
    log.info("Australian postings in the 7 roles: %d, %d after de-duplication", before, len(au))
    au["role"] = au.job_title_short.map(ROLES)
    return au


def profiles(au: pd.DataFrame, lookup: dict[str, str], category: dict[str, str]) -> tuple[pd.DataFrame, Counter]:
    rows, unmapped = [], Counter()
    for role, ads in au.groupby("role"):
        counts, total = Counter(), 0
        for cell in ads.job_skills:
            tokens = parse_skills(cell)
            if not tokens:
                continue
            total += 1
            skills = set()
            for t in tokens:
                s = to_skill(t, lookup)
                if s:
                    skills.add(s)
                elif t.casefold() not in UNRELIABLE:
                    unmapped[t.casefold()] += 1
            counts.update(skills)
        log.info("%-26s %5d ads, %5d name at least one tool", role, len(ads), total)
        for skill, n in counts.items():
            low, high = wilson(n, total)
            rows.append({"role": role, "skill": skill, "category": category[skill], "n_ads": n,
                         "pct_ads": round(100 * n / total, 1), "pct_low": low, "pct_high": high,
                         "total_ads": total, "source": SOURCE})
    out = pd.DataFrame(rows).sort_values(["role", "n_ads", "skill"], ascending=[True, False, True])
    return out.reset_index(drop=True), unmapped


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    if not args.data.exists():
        raise SystemExit(f"{args.data} not found. Download data_jobs.csv from "
                         "https://huggingface.co/datasets/lukebarousse/data_jobs into that folder.")

    lookup, category = load_dictionary()
    df = pd.read_csv(args.data, dtype=str, keep_default_na=False)
    out, unmapped = profiles(australian_postings(df), lookup, category)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.out, index=False, encoding="utf-8")
    log.info("Wrote %s: %d rows, %d roles", args.out.name, len(out), out.role.nunique())
    total = sum(unmapped.values())
    log.info("Tool names not in the dictionary: %d distinct, %d mentions; most frequent: %s",
             len(unmapped), total, ", ".join(f"{t} {n}" for t, n in unmapped.most_common(15)))


if __name__ == "__main__":
    main()
