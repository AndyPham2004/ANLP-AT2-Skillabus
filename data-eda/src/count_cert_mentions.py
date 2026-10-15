"""Count how many of our local Australian ads name each certification; fill `local_ads_mentions`.

Reads the aliases in data/1_knowledge/learning_resources/certifications.csv (`aliases_ads`, how ads
write each certificate) and counts the ads whose title or description names at least one alias.
One ad counts once per certificate, however often it repeats the name.

Ads read (each source once, duplicates across files dropped by ad id):
    seek_2019_22   data/2_demand/ads/jobs_au_seek_datascientist_2019-2022_clean.csv   (committed)
    recent_2024_26 data/2_demand/ads/jobs_au_recent_2024-2026_clean.csv               (committed)
    ats_2026       data/raw/jobs_au_ats_2026.csv + data/raw/ats_ads_2026-*.csv         (not in git; used
                   when present, or pass --ats with the files)

Matching rules (see certifications.md):
    - an alias matches as a whole phrase: not inside a longer word ("CKA" does not match "CKAD");
      spaces, hyphens, dashes and colons between its words are interchangeable;
    - an alias with no lower-case letter (CISSP, AZ-104, PSM I) is case-sensitive; the rest are not;
    - longest match wins: "CCNA" inside "CCNA Cybersecurity" counts for CCNA Cybersecurity only.

Usage (from the repo root):
    python data-eda/src/count_cert_mentions.py                    # count and write the column
    python data-eda/src/count_cert_mentions.py --dry-run          # print only
    python data-eda/src/count_cert_mentions.py --ats ../other/data/raw/ats_ads_2026-10-13.csv --breakdown out.csv
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))  # repo src/, for skillabus.paths
from skillabus import paths  # noqa: E402

SEPT_ATS = paths.RAW / "jobs_au_ats_2026.csv"
ATS_GLOB = "ats_ads_2026-*.csv"
WORD_SEP = r"[\s\-‐-―:]+"   # what may stand between two words of an alias


def is_acronym(alias: str) -> bool:
    """CISSP, AZ-104, PSM I, ISC2 CC: no lower-case letter, so match case-sensitively."""
    return not any(ch.islower() for ch in alias)


def alias_pattern(alias: str) -> re.Pattern:
    words = [w for w in re.split(WORD_SEP, alias.strip()) if w]
    body = WORD_SEP.join(re.escape(w) for w in words)
    flags = 0 if is_acronym(alias) else re.IGNORECASE
    return re.compile(rf"(?<![A-Za-z0-9]){body}(?![A-Za-z0-9+])", flags)


def split_list(value: str) -> list[str]:
    return [x.strip() for x in str(value).split(";") if x.strip()]


def compile_aliases(certs: pd.DataFrame) -> list[tuple[str, re.Pattern]]:
    """(cert, pattern) for every alias of every certificate."""
    return [(row.cert, alias_pattern(a)) for row in certs.itertuples() for a in split_list(row.aliases_ads)]


def find_mentions(text: str, patterns: list[tuple[str, re.Pattern]]) -> set[str]:
    """The certificates a text names, after dropping matches that sit inside a longer match of another cert."""
    if not text:
        return set()
    spans = [(m.start(), m.end(), cert) for cert, pat in patterns for m in pat.finditer(text)]
    kept = set()
    for s, e, cert in spans:
        inside_longer = any(c2 != cert and s2 <= s and e <= e2 and (e2 - s2) > (e - s) for s2, e2, c2 in spans)
        if not inside_longer:
            kept.add(cert)
    return kept


def ad_key(ad_id: str) -> str:
    """The recent sample prefixes job-board ids with 'ats-'; the raw files do not."""
    return re.sub(r"^ats-", "", str(ad_id))


def load_ads(seek: Path, recent: Path, ats_files: list[Path]) -> pd.DataFrame:
    """One row per distinct ad: source, key, text (title + description)."""
    frames = []
    for source, files in (("seek_2019_22", [seek]), ("recent_2024_26", [recent]), ("ats_2026", ats_files)):
        for path in files:
            if not Path(path).exists():
                print(f"  skip {source}: {path} not found")
                continue
            d = pd.read_csv(path, dtype=str, keep_default_na=False)
            frames.append(pd.DataFrame({
                "source": source,
                "key": d["ad_id"].map(ad_key),
                "text": d.get("title", "") + "\n" + d["description"],
            }))
    ads = pd.concat(frames, ignore_index=True)
    return ads.drop_duplicates(subset="key", keep="first").reset_index(drop=True)


def count_mentions(ads: pd.DataFrame, certs: pd.DataFrame) -> pd.DataFrame:
    """cert x source table of ad counts, plus a `total` column."""
    patterns = compile_aliases(certs)
    hits = ads["text"].map(lambda t: find_mentions(t, patterns))
    rows = [(cert, src) for cs, src in zip(hits, ads["source"]) for cert in cs]
    table = pd.DataFrame(rows, columns=["cert", "source"])
    out = pd.crosstab(table["cert"], table["source"]) if len(table) else pd.DataFrame()
    out = out.reindex(index=certs["cert"], columns=sorted(ads["source"].unique()), fill_value=0)
    out["total"] = out.sum(axis=1)
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--certs", type=Path, default=paths.CERTIFICATIONS)
    parser.add_argument("--seek", type=Path, default=paths.SEEK_ADS)
    parser.add_argument("--recent", type=Path, default=paths.RECENT_ADS)
    parser.add_argument("--ats", type=Path, nargs="*",
                        help=f"raw job-board files; default: {SEPT_ATS.name} and every {ATS_GLOB} in data/raw/")
    parser.add_argument("--breakdown", type=Path, help="also write the cert x source table here")
    parser.add_argument("--dry-run", action="store_true", help="print the counts, do not write the CSV")
    args = parser.parse_args(argv)

    ats_files = args.ats if args.ats is not None else [SEPT_ATS] + sorted(paths.RAW.glob(ATS_GLOB))
    certs = pd.read_csv(args.certs, dtype=str, keep_default_na=False)
    ads = load_ads(args.seek, args.recent, ats_files)
    print("Ads read:", ads["source"].value_counts().to_dict(), f"({len(ads)} distinct)")

    table = count_mentions(ads, certs)
    shown = table[table["total"] > 0].sort_values("total", ascending=False)
    print(shown.to_string() if len(shown) else "No certificate named in any ad.")
    print(f"{(table['total'] > 0).sum()} of {len(certs)} certificates named at least once.")

    if args.breakdown:
        table.to_csv(args.breakdown, encoding="utf-8", lineterminator="\n")
    if not args.dry_run:
        certs["local_ads_mentions"] = certs["cert"].map(table["total"]).astype(int).astype(str)
        certs.to_csv(args.certs, index=False, encoding="utf-8", lineterminator="\n")
        print(f"Wrote local_ads_mentions to {args.certs}")
    return table


if __name__ == "__main__":
    main()
