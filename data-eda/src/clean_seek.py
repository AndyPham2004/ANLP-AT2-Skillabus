"""Clean the primary Seek corpus: repair glued words, tidy whitespace, keep ad_id.

The Kaggle dataset ships each ad twice, as `mobileAdTemplate` and
`desktopAdTemplate`, both with the HTML already stripped - and stripped without
putting whitespace back where block tags were, so list items weld together:

    "...Experience with SAS, R, PythonExcellent verbal and written..."

That hides real skill mentions from any extractor with word boundaries: 365 of
them on our 14 audited tools (see validate_against_authorflags.py).

Splitting every lower->Upper join is not an option: it would break JavaScript,
TensorFlow, PySpark, NoSQL, PhD and a few hundred more. So this script only
splits a join when the *other* rendering of the same ad has a break there. The
mobile text is the base (it is the longer of the two in most ads); the desktop
text is the evidence. Where both renderings are glued, the join is left alone.

Output keeps every ad_id and title unchanged, so labels made on the clean file
line up with everything else keyed on ad_id.

Usage:
    python src/clean_seek.py
"""

from __future__ import annotations

import argparse
import html
import logging
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ADS = ROOT / "data" / "raw" / "jobs_au_seek_datascientist_2019-2022.csv"
DEFAULT_SOURCE = ROOT / "data" / "raw" / "jobs_au_seek_datascience_2019-2022_authorflags.csv"
DEFAULT_OUT = ROOT / "data" / "clean" / "jobs_au_seek_datascientist_2019-2022_clean.csv"

# A join is a lowercase letter, closing bracket or full stop running straight
# into a capital: "PythonExcellent", "skills).You", "teams.Experience".
JOIN = re.compile(r"(?<=[a-z)\.:%])(?=[A-Z])")
LEFT_WORD = re.compile(r"[A-Za-z0-9+#.]{2,}$")
RIGHT_WORD = re.compile(r"[A-Za-z0-9+#]{2,}")
BREAK_CHARS = r"[\s •:;,.\-]+"
HTML_SCRAP = re.compile(r"<\s*/?\s*[a-zA-Z][^>]{0,80}>|<span id=\"mce[^\"]*\"?")

KEEP = ["ad_id", "title", "company", "advertiser", "listingDate", "state", "city",
        "salary_string", "description"]

log = logging.getLogger("clean_seek")


def deglue(mobile: str, desktop: str) -> tuple[str, int, int]:
    """Split glued words in `mobile` wherever `desktop` shows a break.

    Returns the repaired text, the number of joins split, and the number left
    alone for lack of evidence.
    """
    pieces, last, split, kept = [], 0, 0, 0
    for join in JOIN.finditer(mobile):
        i = join.start()
        left = LEFT_WORD.search(mobile[max(0, i - 30):i])
        right = RIGHT_WORD.match(mobile[i:i + 30])
        if not (left and right):
            continue
        pair = re.escape(left.group(0).rstrip(".")) + BREAK_CHARS + re.escape(right.group(0))
        if re.search(pair, desktop):
            pieces += [mobile[last:i], "\n"]
            last = i
            split += 1
        else:
            kept += 1
    pieces.append(mobile[last:])
    return "".join(pieces), split, kept


def tidy(text: str) -> str:
    """Whitespace and stray markup, keeping line structure for sentence splitting."""
    text = html.unescape(text)
    text = HTML_SCRAP.sub(" ", text)
    text = text.replace(" ", " ").replace("​", "")
    text = re.sub(r"\s*•\s*", "\n• ", text)   # one bullet per line
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--ads", type=Path, default=DEFAULT_ADS,
                        help="the 3,204-ad primary corpus; defines which ads are kept")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE,
                        help="file carrying mobileAdTemplate and desktopAdTemplate")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    ads = pd.read_csv(args.ads)
    src = (pd.read_csv(args.source, usecols=["jobId", "mobileAdTemplate", "desktopAdTemplate"])
             .drop_duplicates("jobId").set_index("jobId"))
    missing = (~ads.ad_id.isin(src.index)).sum()
    if missing:
        raise SystemExit(f"{missing} ads have no row in {args.source.name}; cannot clean them")

    mobile = src.mobileAdTemplate.reindex(ads.ad_id).fillna("").to_numpy()
    desktop = src.desktopAdTemplate.reindex(ads.ad_id).fillna("").to_numpy()

    cleaned, split_total, kept_total = [], 0, 0
    for m, d in zip(mobile, desktop):
        text, split, kept = deglue(m, d)
        cleaned.append(tidy(text))
        split_total += split
        kept_total += kept

    out = ads.copy()
    out["description"] = cleaned
    out = out[[c for c in KEEP if c in out.columns]]

    empty = (out.description.str.len() < 50).sum()
    if empty:
        log.warning("%d ads have under 50 characters of text after cleaning", empty)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.out, index=False, encoding="utf-8")

    before = pd.Series(ads.description.fillna("")).str.len().median()
    after = out.description.str.len().median()
    log.info("Wrote %s: %d ads, ad_id unchanged", args.out, len(out))
    log.info("  glued joins split on desktop evidence: %s", f"{split_total:,}")
    log.info("  joins left alone (real words or no evidence): %s", f"{kept_total:,}")
    log.info("  median length %d -> %d characters", before, after)


if __name__ == "__main__":
    main()
