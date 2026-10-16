"""The IT roles in the PromptCloud Seek Australia samples of 2020-21: a pre-2022 full-text baseline per role.

Why: the Seek 2019-22 file holds Data Scientist titles only, so the trend "then vs now" exists for one role.
PromptCloud published Seek Australia samples of every category on Kaggle under CC0 (public domain):
    Seek Australia Job Listing      Oct-Dec 2020    https://www.kaggle.com/datasets/promptcloud/seek-australia-job-listing
    Seek Job Listing Australia      Jan-Mar 2021    https://www.kaggle.com/datasets/promptcloud/seek-job-listing-australia
(and the small Jan 2020 file already in data/raw/). About one ad in twenty has an IT title, enough for a
2020-21 block of every role that reaches MIN_ROLE_ADS.

What this writes (the raw CSVs stay in data/raw/, 30,000 rows each; CC0 allows committing them, but the IT
subset with text would exceed the 5 MB file limit, so the committed file has no text, like the JobsPipe one):
    data/2_demand/ads/seek_2020_21_skills.csv   one row per IT ad: id, role, title, company, state, post_date,
                                                url, n_chars, skills (the vocabulary skills the text names,
                                                tier-1 matcher) — what build_role_skill_demand.py counts as
                                                source seek_2020_21, period 2020-21
Role from the title with the job-board rules (classify_ats_roles.role_of) plus two guards for an all-professions
board (NON_IT, IT_WORDS below); one row per company + title + text head (PromptCloud re-crawls); ads under 200
characters dropped.

Usage (from the repo root):
    python data-eda/src/build_seek_it_2020_21.py                       # reads data/raw/jobs_au_seek_allcategories_*.csv
    python data-eda/src/build_seek_it_2020_21.py --dry-run             # counts only, writes nothing
    python data-eda/src/build_seek_it_2020_21.py --convert <sample.ldjson> data/raw/jobs_au_seek_allcategories_2021Q1.csv
The two Kaggle files come as .ldjson (download with kagglehub.dataset_download("promptcloud/<slug>")).
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import re
import sys
from pathlib import Path

import pandas as pd

from build_recent_sample import mask_contacts
from build_vocabulary import read_table, skill_hits
from classify_ats_roles import OTHER, RULES, role_of

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))  # repo src/, for skillabus.paths
from skillabus import paths  # noqa: E402

log = logging.getLogger("build_seek_it_2020_21")

RAW_GLOB = "jobs_au_seek_allcategories_*.csv"
OUT = paths.SEEK_2020_21_SKILLS
MIN_TEXT = 200
COLUMNS = ["ad_id", "role", "title", "company", "state", "post_date", "period_file", "url", "n_chars", "skills"]
CONVERT_KEEP = ["uniq_id", "crawl_timestamp", "url", "job_title", "category", "company_name", "city", "state",
                "inferred_state", "country", "post_date", "job_description", "job_type"]

# Seek lists every profession, so the job-board rules (written for tech employers' boards) need two guards:
# engineers and analysts of other fields are not IT roles, and the catch-all "engineer" rule only counts
# when the title names something IT. Help-desk titles are left out of Network/Systems Administrator, as the
# JobsPipe and Adzuna queries for that role left them out.
_B = r"\b"
NON_IT = re.compile(_B + r"(?:civil|mechanical|electrical|structural|chemical|process|mining|geotechnical|environmental|"
                    r"hvac|mechatronic|maintenance|field service|fire|hydraulic|drainage|traffic|rail|signalling|marine|"
                    r"aerospace|automotive|construction|piping|tailings|bms|cnc|manufactur\w*|agri\w*|finance|financial|"
                    r"food|laboratory|biomedical|clinical|pharma\w*|plant|estimat\w*|surveyor|cadet|acoustic|water|energy|"
                    r"solar|telecom\w*|radio|rf|audio|broadcast|quality assurance|service desk|desktop support|help ?desk|"
                    r"it support|support analyst|support technician|support officer|control systems?|safety|medical|defence|defense|"
                    r"weapons?|combat|underwater)" + _B, re.I)
IT_WORDS = re.compile(r"software|developer|programmer|" + _B + r"it" + _B + r"|ict|application|system|web|cloud|devops|"
                      r"data|digital|" + _B + r"qa" + _B + r"|tester|test (?:analyst|engineer|lead|automation)|automation test|"
                      r"testing|" + _B + r"uat" + _B + r"|sdet|selenium|" + _B + r"api" + _B + r"|platform|backend|back end|"
                      r"frontend|front end|full ?stack|mobile|java|python|\.net|c#|react|node|sql|database|linux|windows|"
                      r"network|security|cyber|salesforce|" + _B + r"sap" + _B + r"|dynamics|erp|crm|integration|"
                      r"infrastructure|storage|" + _B + r"ml" + _B + r"|" + _B + r"ai" + _B, re.I)
GENERIC_RULES = RULES[:-1]                   # all but the catch-all "engineer" rule


def it_role(title: str) -> str:
    """role_of() with the two guards above."""
    t = re.sub(r"\s+", " ", title or "").strip()
    if NON_IT.search(t):
        return OTHER
    role = role_of(t)
    if role == OTHER:
        return OTHER
    specific = next((r for r, rx in GENERIC_RULES if rx.search(t)), None)
    if specific is None and not IT_WORDS.search(t):      # only the catch-all matched: "Project Engineer"
        return OTHER
    if role == "QA/Test Engineer" and not IT_WORDS.search(t):
        return OTHER
    return role


def convert(ldjson: Path, out: Path) -> int:
    """A PromptCloud .ldjson sample -> CSV with the columns we use."""
    with open(ldjson, encoding="utf-8", errors="replace") as f:
        first = json.loads(f.readline())
    cols = [k for k in CONVERT_KEEP if k in first]
    n = 0
    with open(ldjson, encoding="utf-8", errors="replace") as f, open(out, "w", encoding="utf-8", newline="") as g:
        w = csv.DictWriter(g, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            w.writerow({k: rec.get(k) if not isinstance(rec.get(k), (list, dict)) else json.dumps(rec.get(k)) for k in cols})
            n += 1
    return n


def read_promptcloud(path: Path) -> pd.DataFrame:
    """One PromptCloud Seek file -> the columns we keep, text tidied and contacts masked."""
    a = pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8", encoding_errors="replace")
    title = next(c for c in a.columns if c.lower() in ("title", "job_title"))
    desc = next(c for c in a.columns if c.lower() in ("description", "job_description", "html_job_description"))
    company = next((c for c in a.columns if c.lower() in ("company", "company_name")), None)
    state = next((c for c in a.columns if c.lower() in ("state", "inferred_state")), None)
    date = next((c for c in a.columns if c.lower() in ("post_date", "postdate_yyyymmdd", "posted")), None)
    url = next((c for c in a.columns if c.lower() in ("url", "job_url")), None)
    ad_id = next((c for c in a.columns if c.lower() in ("ad_id", "uniq_id", "id")), None)
    text = a[desc].map(lambda s: re.sub(r"\s+", " ", mask_contacts(str(s))).strip())
    tag = re.search(r"allcategories_(\w+)", path.stem)
    return pd.DataFrame({
        "ad_id": ("seek-" + a[ad_id].astype(str)) if ad_id else ("seek-" + path.stem + "-" + a.index.astype(str)),
        "title": a[title].map(lambda s: re.sub(r"\s+", " ", str(s)).strip()),
        "company": a[company].str.strip() if company else "", "state": a[state] if state else "",
        "post_date": a[date].astype(str).str[:10] if date else "", "period_file": tag.group(1) if tag else path.stem,
        "url": a[url] if url else "", "description": text,
    })


def build(files: list[Path]) -> pd.DataFrame:
    parts = [read_promptcloud(p) for p in files]
    for p, part in zip(files, parts):
        log.info("%s: %d ads", p.name, len(part))
    ads = pd.concat(parts, ignore_index=True)
    before = len(ads)
    ads = ads[ads.description.str.len() >= MIN_TEXT]
    ads["head"] = ads.description.str[:300]
    ads = ads.drop_duplicates("ad_id").drop_duplicates(["company", "title", "head"]).drop(columns="head")
    ads["role"] = ads.title.map(it_role)
    it = ads[ads.role != OTHER].reset_index(drop=True)
    log.info("%d rows -> %d unique ads with text -> %d with an IT role", before, len(ads), len(it))
    vocab = read_table(paths.SKILLS_VOCABULARY)
    detection = vocab[vocab.used_for.str.contains("extract")].reset_index(drop=True)
    hits = skill_hits(detection, it.description)
    it["skills"] = ["|".join(sorted(h)) for h in hits]
    it["n_chars"] = it.description.str.len()
    return it[COLUMNS].sort_values(["role", "company", "title", "ad_id"]).reset_index(drop=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--raw", type=Path, default=paths.RAW)
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--convert", type=Path, nargs=2, metavar=("LDJSON", "CSV"), help="convert a Kaggle .ldjson sample to CSV and stop")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s", force=True)
    if args.convert:
        n = convert(args.convert[0], args.convert[1])
        log.info("wrote %s: %d rows", args.convert[1], n)
        return
    files = sorted(args.raw.glob(RAW_GLOB))
    if not files:
        sys.exit(f"no {RAW_GLOB} in {args.raw}: download the PromptCloud Seek samples from Kaggle (see the docstring)")
    table = build(files)
    log.info("ads per role:\n%s", table.role.value_counts().to_string())
    if args.dry_run:
        return
    args.out.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(args.out, index=False, encoding="utf-8", lineterminator="\n")
    log.info("wrote %s: %d ads", args.out, len(table))


if __name__ == "__main__":
    main()
