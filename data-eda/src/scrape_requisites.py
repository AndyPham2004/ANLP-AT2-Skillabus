"""Prerequisite rules and teaching sessions for every subject in uts_subjects_2026.csv.

The handbook's `requisite_detail` field is boilerplate that links to the access-conditions
page on studentforms.uts.edu.au, which lists the actual rule, e.g. for 36118:

    Requisite rule: (1 AND 2 AND 3)
    1 Academic requisite 36100 Data Science for Innovation
    2 Academic requisite 36103 Statistical Thinking for Data Science
    3 Academic requisite 36106 Machine Learning Algorithms and Applications

Item types: Academic (a subject code, or a credit-point condition), Admission (into a
course), Other, and corequisite ("1d corequisite ..." or "2 Academic corequisite 25741 ...": may be
taken in the same session). The rule is a boolean expression over item ids (1, 1a, 2 ...).

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
# The page also lists anti-requisites ("you cannot take this if you took ..."), same table shape.
ANTI = re.compile(r"Anti-requisite rule:\s*(.+?)\s*Item\s+(?:Type\s+)?Details", re.S)
# Some anti-requisite tables have no Type column: "1 31250 Introduction to Data Analytics 2 321130 ..."
ANTI_ITEM = re.compile(r"(?:(?<=\s)|^)(\d+[a-z]?)\s+(\d{5,6})\s+(.+?)(?=\s+\d+[a-z]?\s+\d{5,6}\s|\s*Note:|$)", re.S)
NOT_FOUND = "There are no access restrictions enforced for this subject"
# "1a Academic requisite 36100 Data Science ..." up to the next item id or "Note:"
ITEM = re.compile(
    r"(?:(?<=\s)|^)(\d+[a-z]?)\s+(?:(Academic|Admission|Other)\s+)?(requisite|corequisite)\s+(.+?)"
    r"(?=\s+\d+[a-z]?\s+(?:(?:Academic|Admission|Other)\s+)?(?:requisite|corequisite)\s|\s*Note:|$)",
    re.S)
CODE = re.compile(r"^(\d{5,6})\b")   # 36118, and six-digit codes such as 090014
PREREQ_COLUMNS = ["subject_code", "kind", "rule", "item", "type", "requisite_code", "requisite_text", "evop_found",
                  "source_url"]
# kind: requisite (must hold before enrolling) or antirequisite (cannot be taken together with);
# evop_found: n when the access-conditions site has no record of the code, so "no rule" is unverified.

log = logging.getLogger("scrape_requisites")


def page_text(html: str) -> str:
    text = re.sub(r"(?s)<(script|style).*?</\1>", " ", html)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", html_lib.unescape(text)).strip()


def _items(body: str) -> list[dict]:
    body = body[:body.find("Note:")] if "Note:" in body else body
    items = []
    for item, kind, keyword, detail in ITEM.findall(body):
        detail = detail.strip()
        code = CODE.match(detail)
        # "corequisite" (bare, or "Academic corequisite") may be taken in the same session: its own type
        kind = "corequisite" if keyword == "corequisite" else (kind or "other").lower()
        items.append({"item": item, "type": kind, "code": code.group(1) if code else "", "text": detail})
    return items


def parse_requisites(html: str, code: str | None = None) -> dict:
    """The rule and its items from an access-conditions page.

    Returns rule, items, anti_rule, anti_items and found. `found` is False when the page is the
    generic "no access restrictions" page without the subject's own heading (EVOP has no record of
    the code), which must not be read as "confirmed: no prerequisites".
    """
    text = page_text(html)
    found = True if code is None else (f"{code} " in text and NOT_FOUND not in text) or ("Requisite rule" in text)
    out = {"rule": "", "items": [], "anti_rule": "", "anti_items": [], "found": found}
    m = RULE.search(text)
    if m:
        out["rule"] = m.group(1).strip()
        after = text[m.end():]
        cut = after.find("Anti-requisite")
        out["items"] = _items(after if cut < 0 else after[:cut])
    a = ANTI.search(text)
    if a:
        out["anti_rule"] = a.group(1).strip()
        body = text[a.end():]
        body = body[:body.find("Note:")] if "Note:" in body else body
        out["anti_items"] = _items(body) or [
            {"item": item, "type": "academic", "code": code, "text": f"{code} {name.strip()}"}
            for item, code, name in ANTI_ITEM.findall(body)]
    return out


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
            out = parse_requisites(html, code)
            url = EVOP.format(code=code)
            found = "y" if out["found"] else "n"
            if not out["items"]:
                rows.append({"subject_code": code, "kind": "requisite", "rule": out["rule"], "item": "", "type": "",
                             "requisite_code": "", "requisite_text": "", "evop_found": found, "source_url": url})
            for it in out["items"]:
                rows.append({"subject_code": code, "kind": "requisite", "rule": out["rule"], "item": it["item"],
                             "type": it["type"], "requisite_code": it["code"], "requisite_text": it["text"],
                             "evop_found": found, "source_url": url})
            for it in out["anti_items"]:
                rows.append({"subject_code": code, "kind": "antirequisite", "rule": out["anti_rule"], "item": it["item"],
                             "type": it["type"], "requisite_code": it["code"], "requisite_text": it["text"],
                             "evop_found": found, "source_url": url})
            log.info("[%d/%d] %s rule=%s items=%d anti=%d found=%s", i, len(codes), code, out["rule"] or "-",
                     len(out["items"]), len(out["anti_items"]), found)
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
