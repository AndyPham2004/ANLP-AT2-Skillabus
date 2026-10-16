"""Give each 2026 job-board ad one of the 11 roles, or "other", from its title (plan D2 / D15, issue #116).

Input: the raw fetches of fetch_ats.py in data/raw/ (ats_ads_2026-10-13.csv, ats_ads_2026-10-16.csv, ...):
every Australian posting of the 65 public job boards, all professions. Output: the committed
data/2_demand/ads/ats_2026_clean.csv: one row per unique ad (same company, title and text counted once),
contact details masked as in build_recent_sample.py, and a `role` column that build_role_skill_demand.py
counts skills by (source = ats_2026).

The role comes from the title alone, so the rule is reviewable: RULES below is tried in order and the
first match wins. Management titles ("Engineering Manager - Data", "Head of Engineering") and pre-sales,
consulting or support engineers are "other". A title must name an individual-contributor noun (engineer,
developer, scientist, analyst, administrator, architect, tester); "engineering" alone never counts.
When the title says "Software Engineer" that wins over a qualifier ("Senior Software Engineer, AI Tooling"
is Software Engineer; "Senior Engineer - ML Systems" is Machine Learning Engineer).

Usage (from the repo root):
    python data-eda/src/classify_ats_roles.py                         # write data/2_demand/ads/ats_2026_clean.csv
    python data-eda/src/classify_ats_roles.py --titles                # every distinct title with its role, by role
    python data-eda/src/classify_ats_roles.py --sample 30 --seed 1    # random ads with the text head, for the hand check
"""
from __future__ import annotations

import argparse
import logging
import re
import sys
from pathlib import Path

import pandas as pd

from build_recent_sample import posted_date, snapshot_date, tidy

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))  # repo src/, for skillabus.paths
from skillabus import paths  # noqa: E402

log = logging.getLogger("classify_ats_roles")

RAW_GLOB = "ats_ads_2026-10-*.csv"           # the October fetches (the September file holds data roles only)
OUT = paths.ATS_2026_ADS
MIN_TEXT = 200                               # an ad with less text than this is a stub, not an ad
COLUMNS = ["ad_id", "source", "company", "title", "role", "location", "posted", "snapshot", "description", "url"]
OTHER = "other"

ENG = r"engineers?\b"                        # "engineer", "engineers"; never "engineering"
RULES: list[tuple[str, re.Pattern]] = [
    # Management titles are not individual-contributor roles.
    (OTHER, re.compile(r"\b(?:managers?|director|head of|chief|vp|vice president|officer|team lead|engineering lead)\b", re.I)),
    # Pre-sales, consulting, enablement and support "engineers" and "architects".
    (OTHER, re.compile(
        rf"\b(?:sales|solutions?|customer success|customer|support|services?|escalations?|enablement|onboarding|"
        rf"commercial|implementation|consulting|field)\b[^,]*\b{ENG}"
        r"|\b(?:solutions?|consulting|partner|delivery|specialist|enablement|customer)\b.*\barchitects?\b", re.I)),
    ("Machine Learning Engineer", re.compile(
        rf"machine learning {ENG}|\bML {ENG}|\bAI {ENG}|applied ai {ENG}|\b(?:AI|ML) platform {ENG}|mlops", re.I)),
    ("Software Engineer", re.compile(
        rf"software (?:{ENG}|developers?\b)|\bdevelopers?\b|programmer|full[- ]?stack|front[- ]?end|back[- ]?end"
        rf"|\b(?:mobile|web|android|ios|java|python|\.net|c#|react|search|language|forward deployed|deployment|salesforce) {ENG}"
        r"|\bengineers?\s*[-–(]\s*(?:salesforce|c#|\.net)", re.I)),
    ("Cybersecurity Analyst", re.compile(
        rf"security (?:{ENG}|analysts?\b|archi\w*|specialists?\b|consultants?\b|operations|researchers?\b)|cyber|infosec"
        r"|information security|penetration|\bsoc\b|identity (?:&|and) access|\biam engineer|devsecops|\bsiem\b", re.I)),
    ("Cloud Engineer", re.compile(rf"\bcloud\b.*\b(?:{ENG}|architects?\b)|\b(?:aws|azure|gcp) (?:engineer|architect)", re.I)),
    ("DevOps/SRE", re.compile(
        rf"devops|site reliability|\bsre\b|(?:platform|production|infrastructure|reliability|release|build|observability) {ENG}"
        r"|compute (?:foundation|platform)", re.I)),
    ("Network/Systems Administrator", re.compile(
        rf"network (?:{ENG}|administrators?\b|operations|analysts?\b|tech)|systems? (?:administrators?\b|{ENG})|sysadmin"
        rf"|\bit support|service desk|desktop support|\bit operations|infrastructure (?:administrators?|analysts?)\b"
        rf"|\b(?:datacenter|data center)\b.*\b{ENG}|\b{ENG}.*\b(?:datacenter|data center)", re.I)),
    ("QA/Test Engineer", re.compile(
        rf"\bqa\b|quality assurance|test(?:ing)? (?:{ENG}|analysts?\b|automation|lead)|software tester|\bsdet\b|automation (?:{ENG}|testers?\b)", re.I)),
    ("Data Engineer", re.compile(rf"(?:data|analytics) {ENG}|data platform|\betl\b|data pipeline|database (?:{ENG}|developers?\b)", re.I)),
    ("Data Analyst", re.compile(
        r"data analysts?\b|analytics (?:senior )?analysts?\b|\banalysts?\b.*\banalytics|analytics\b.*\banalysts?\b|business intelligence"
        r"|\bbi (?:analyst|developer)|(?:reporting|insights?) analysts?\b", re.I)),
    ("Business Analyst", re.compile(
        r"business analysts?\b|business (?:and|&) process analysts?\b|functional analysts?\b|business systems analysts?\b|systems analysts?\b"
        r"|process analysts?\b|product owners? (?:&|and) business analysts", re.I)),
    ("Data Scientist", re.compile(
        r"\b(?:data|applied|research|decision|ai|ml|machine learning) scientists?\b|\bscientists?\b.*\b(?:ai|ml|data|machine learning|analytics)\b"
        r"|\b(?:ai|ml|data)\b.*\bscientists?\b", re.I)),
    ("Machine Learning Engineer", re.compile(
        rf"\b(?:ai|ml|machine learning|agentic|llms?|genai|deep learning|nlp)\b.*\b(?:{ENG}|architects?\b)"
        rf"|\b(?:{ENG}|architects?\b).*\b(?:ai|ml|machine learning|agentic|llms?|genai)\b", re.I)),
    ("Software Engineer", re.compile(rf"\b{ENG}", re.I)),
]


def role_of(title: str) -> str:
    """The first rule the title matches, else "other"."""
    t = re.sub(r"\s+", " ", title or "").strip()
    for role, rx in RULES:
        if rx.search(t):
            return role
    return OTHER


def read_raw(files: list[Path]) -> pd.DataFrame:
    """The fetches as one table: one row per unique ad (ad_id, then company + title + text), earliest fetch kept."""
    parts = []
    for path in sorted(files):
        a = pd.read_csv(path, dtype=str, keep_default_na=False)
        created = a.created.map(posted_date)
        snap = snapshot_date(path, created)
        parts.append(pd.DataFrame({
            "ad_id": "ats-" + a.ad_id.astype(str), "source": a.source, "company": a.company.str.strip(),
            "title": a.title.map(lambda s: re.sub(r"\s+", " ", s or "").strip()), "location": a.location,
            "posted": created.dt.strftime("%Y-%m-%d").fillna(""), "snapshot": snap.strftime("%Y-%m-%d"),
            "description": a.description.map(tidy), "url": a.redirect_url,
        }))
        log.info("%s: %d ads, fetched %s", path.name, len(a), snap.date())
    ads = pd.concat(parts, ignore_index=True)
    before = len(ads)
    ads = ads.drop_duplicates("ad_id").drop_duplicates(["company", "title", "description"])
    ads = ads[ads.description.str.len() >= MIN_TEXT].reset_index(drop=True)
    log.info("%d rows -> %d unique ads with text (%d dropped)", before, len(ads), before - len(ads))
    return ads


def classify(ads: pd.DataFrame) -> pd.DataFrame:
    out = ads.copy()
    out["role"] = out.title.map(role_of)
    return out[COLUMNS].sort_values(["role", "company", "title", "ad_id"]).reset_index(drop=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--raw", type=Path, default=paths.RAW, help="folder with the ats_ads_2026-10-*.csv fetches")
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument("--titles", action="store_true", help="print every distinct title with its role and stop")
    parser.add_argument("--sample", type=int, default=0, help="print this many random ads for the hand check and stop")
    parser.add_argument("--seed", type=int, default=1)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s", force=True)

    files = sorted(args.raw.glob(RAW_GLOB))
    if not files:
        sys.exit(f"no {RAW_GLOB} in {args.raw}; run data-eda/src/fetch_ats.py --australia-only first")
    table = classify(read_raw(files))
    counts = table.role.value_counts()
    log.info("ads per role:\n%s", counts.to_string())

    if args.titles:
        for role, group in table.groupby("role"):
            print(f"\n## {role} ({len(group)} ads)")
            for title, n in group.title.value_counts().sort_index().items():
                print(f"  {n:2d}  {title}")
        return
    if args.sample:
        for row in table.sample(args.sample, random_state=args.seed).itertuples():
            head = re.sub(r"\s+", " ", row.description)[:300]
            print(f"\n[{row.ad_id}] {row.role} | {row.title} | {row.company}\n    {head}")
        return
    args.out.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(args.out, index=False, encoding="utf-8", lineterminator="\n")
    log.info("wrote %s: %d ads, %d with one of the 11 roles", args.out, len(table), int((table.role != OTHER).sum()))


if __name__ == "__main__":
    main()
