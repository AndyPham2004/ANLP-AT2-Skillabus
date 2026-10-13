"""Find emerging skills: phrases that rise in the 2026 ads and that neither our dictionary nor ESCO
knows. Owner: Phuong Nhi. Ideas doc 4.10 B.

Today "large language models" and "generative AI" are found only because we added them to the
dictionary by hand. This module looks for the next ones automatically, three ways, from the
traditional to the newer, so the report can compare them on the same ads:

    "ngram"   every 1-3 word sequence (count-based; the traditional baseline)
    "spacy"   the tier-2 candidates of extract(method="ner"): noun phrases after a cue
              ("experience with ...") and PRODUCT entities (linguistic rules)
    "llm"     the tier-3 skills GPT-4o-mini returns (extract_llm, cached; needs OPENAI_API_KEY)

Every method only proposes phrases. All three are then scored the same way, so the comparison is
about what each method proposes, not how it is scored:

    df_new, df_2019_22  number of ads naming the phrase in a requirement line, i.e. a sentence that
                      names a dictionary skill (the recent ads; the 3,204 Seek ads 2019-22)
    z                 weighted log-odds of 2026 vs 2019-22 with an informative Dirichlet prior
                      (Monroe, Colaresi & Quinn, 2008): how surely the phrase is more common now,
                      with small counts shrunk towards the pooled rate
    kept              rising (z >= MIN_Z), in >= MIN_ADS ads from >= MIN_EMPLOYERS employers
                      (12 of the 22 ads are Canva's, so one employer's boilerplate cannot win),
                      not a dictionary skill or alias, and not an ESCO label

The recent sample is the 22 full-text 2026 ads (8 employers) by default. That is too few for a
phrase to reach 3 ads from 2 employers unless it is everywhere, so `--with-2024` adds the 124
LinkedIn ads of January 2024 (mostly data engineers and analysts: the role mix differs, say so).
Rerun when Van Thong's 2026 sample grows (ideas doc 4.6).

Output: emerging_candidates.csv, one row per method and phrase, best first, with an empty
`is_skill` column to judge the top 20 of each method by hand (precision@20 for section 6).

Run (from the repo root):
    python -m skillabus.emerging                     # n-gram and spaCy, 2026 ads
    python -m skillabus.emerging --with-2024         # 2024-01 + 2026 ads
    python -m skillabus.emerging --methods ngram spacy llm   # needs OPENAI_API_KEY in .env
"""

from __future__ import annotations

import argparse
import csv
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from .extract import load_dictionary

ROOT = Path(__file__).resolve().parents[2]
CLEAN = ROOT / "data-eda" / "data" / "clean"
OLD_CSV = CLEAN / "jobs_au_seek_datascientist_2019-2022_clean.csv"
NEW_CSV = CLEAN / "jobs_au_recent_2024-2026_clean.csv"
ESCO_CSV = CLEAN / "esco_label_lookup.csv"
OUT_CSV = ROOT / "data" / "processed" / "emerging_candidates.csv"

METHODS = ("ngram", "spacy", "llm")
MAX_N = 3              # longest n-gram
MIN_ADS = 3            # a candidate must appear in at least this many 2026 ads
MIN_EMPLOYERS = 2      # ... from at least this many employers
MIN_Z = 1.96           # and be more common in 2026 at about the 95% level
PRIOR = 10.0           # strength of the Dirichlet prior (pseudo-ads)
TOP = 30               # rows kept per method

# Words that never start or end a skill phrase. Small on purpose: the scoring and the employer
# filter remove most boilerplate; this only stops "with python" and "data and".
EDGE_STOP = set("""a an and are as at be been but by can could do for from has have how i if in
into is it its may more most must not of on or our over per so such than that the their them
there these they this those to up us via was we were what when where which while who will with
within without would you your you're we're it's they're plus etc e.g eg i.e ie also""".split())
_TOKEN = re.compile(r"[a-z0-9][a-z0-9+#]*(?:[.\-/'][a-z0-9+#]+)*")


@dataclass(frozen=True)
class Ad:
    ad_id: str
    employer: str
    text: str

    @property
    def skill_text(self) -> str:
        """Only the sentences that name a dictionary skill: the requirement lines. The 2026 ads come
        from company career sites with long benefits and hiring sections the 2019-22 Seek ads lack,
        so on whole ads almost any boilerplate word looks "rising"."""
        return _skill_text(self.text)


@lru_cache(maxsize=None)
def _skill_text(text: str) -> str:
    from .extract import _dictionary_hits, split_sentences
    return "\n".join(s for s in split_sentences(text) if _dictionary_hits(s))


# ----------------------------------------------------------------------------- corpora

def _read(path: Path) -> list[dict]:
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def load_ads(period: str = "2026") -> list[Ad]:
    """period "2026" or "2024-01": the full-text ads of jobs_au_recent (Adzuna rows are cut at 500
    characters, so left out); "2019-22": the 3,204 Seek Data Scientist ads."""
    if period == "2019-22":
        return [Ad(r["ad_id"], r.get("advertiser") or r.get("company") or "", r["description"] or "")
                for r in _read(OLD_CSV)]
    rows = _read(NEW_CSV)
    return [Ad(r["ad_id"], r.get("company") or "", r["description"] or "")
            for r in rows if r.get("period", "").startswith(period) and r.get("full_text") in ("True", "true", "1")]


def tokens(text: str) -> list[str]:
    return _TOKEN.findall((text or "").lower().replace("’", "'"))


def ngrams(toks: list[str], max_n: int = MAX_N) -> set[tuple[str, ...]]:
    """Every 1..max_n word sequence that does not start or end with a stop word or a number."""
    out = set()
    for n in range(1, max_n + 1):
        for i in range(len(toks) - n + 1):
            gram = tuple(toks[i:i + n])
            if gram[0] in EDGE_STOP or gram[-1] in EDGE_STOP or gram[0].isdigit() or gram[-1].isdigit():
                continue
            if n == 1 and len(gram[0]) < 2:
                continue
            out.add(gram)
    return out


def document_frequency(ads: list[Ad], max_n: int = MAX_N) -> tuple[Counter, dict]:
    """(phrase -> number of ads, phrase -> set of employers), over word sequences of the ads."""
    df: Counter = Counter()
    employers: dict = defaultdict(set)
    for ad in ads:
        for gram in ngrams(tokens(ad.skill_text), max_n):
            df[gram] += 1
            employers[gram].add(ad.employer)
    return df, employers


# --------------------------------------------------------------------------- proposals

def propose_ngram(ads: list[Ad]) -> dict[tuple, str]:
    """Every n-gram of the 2026 ads (the phrase as it is written is the n-gram itself)."""
    out = {}
    for ad in ads:
        for gram in ngrams(tokens(ad.skill_text)):
            out.setdefault(gram, " ".join(gram))
    return out


def propose_spacy(ads: list[Ad]) -> dict[tuple, str]:
    """The non-dictionary candidates of the spaCy tier (extract.py, method="ner")."""
    from .extract import extract
    out = {}
    for ad in ads:
        for m in extract(ad.text, "ner"):
            if m.get("canonical"):
                continue
            key = tuple(tokens(m["text"]))
            if key and len(key) <= MAX_N + 1:
                out.setdefault(key, m["text"])
    return out


def propose_llm(ads: list[Ad]) -> dict[tuple, str]:
    """The skills GPT-4o-mini returns (hard skills only), cached on disk by llm_extract."""
    from .llm_extract import extract_llm
    out, failed = {}, 0
    for ad in ads:
        try:
            mentions = extract_llm(ad.text)
        except Exception:                      # no key and no cached answer for this ad
            failed += 1
            continue
        for m in mentions:
            if m.get("kind") == "soft":
                continue
            key = tuple(tokens(m["text"]))
            if key and len(key) <= MAX_N + 1:
                out.setdefault(key, m["text"])
    if failed:
        print(f"llm: {failed} of {len(ads)} ads had no answer (no OPENAI_API_KEY and no cache)")
    return out


PROPOSERS = {"ngram": propose_ngram, "spacy": propose_spacy, "llm": propose_llm}


# ----------------------------------------------------------------------------- filters

@lru_cache(maxsize=1)
def known_phrases() -> frozenset[tuple[str, ...]]:
    """Dictionary names and aliases, as token tuples."""
    known = set()
    for skill in load_dictionary():
        for name in (skill["canonical"], *skill["aliases"]):
            known.add(tuple(tokens(name)))
            known.add(tuple(tokens(name)) + ("s",))          # crude plural guard for "llms"
    return frozenset(known)


@lru_cache(maxsize=1)
def esco_phrases() -> frozenset[tuple[str, ...]]:
    """Every ESCO skill label (preferred and alternative), as token tuples; empty without the file."""
    if not ESCO_CSV.exists():
        return frozenset()
    return frozenset(tuple(tokens(r["label"])) for r in _read(ESCO_CSV))


def _singular(key: tuple[str, ...]) -> tuple[str, ...]:
    last = key[-1]
    if len(last) > 3 and last.endswith("s") and not last.endswith("ss"):
        return key[:-1] + (last[:-1],)
    return key


def known_as(key: tuple[str, ...]) -> str:
    """"dictionary", "esco" or "" (new to both)."""
    for k in {key, _singular(key)}:
        if k in known_phrases():
            return "dictionary"
    for k in {key, _singular(key)}:
        if k in esco_phrases():
            return "esco"
    return ""


# ----------------------------------------------------------------------------- scoring

def log_odds_z(y_new: int, n_new: int, y_old: int, n_old: int, prior: float = PRIOR) -> float:
    """Weighted log-odds that a phrase is more common in the new ads, informative Dirichlet prior
    (Monroe et al. 2008) on document counts: the prior is the pooled rate times `prior` pseudo-ads."""
    pooled = (y_new + y_old) / (n_new + n_old)
    a, b = max(prior * pooled, 1e-3), max(prior * (1 - pooled), 1e-3)    # pseudo-ads with / without

    def logit(y, n):
        return math.log((y + a) / (n - y + b))

    delta = logit(y_new, n_new) - logit(y_old, n_old)
    var = 1 / (y_new + a) + 1 / (n_new - y_new + b) + 1 / (y_old + a) + 1 / (n_old - y_old + b)
    return delta / math.sqrt(var)


def score(proposals: dict[tuple, str], new: list[Ad], old: list[Ad],
          new_df=None, old_df=None) -> list[dict]:
    """Score every proposed phrase on both corpora; return the kept ones, best first."""
    new_df, new_emp = new_df or document_frequency(new, MAX_N + 1)
    old_df, _ = old_df or document_frequency(old, MAX_N + 1)
    rows = []
    for key, text in proposals.items():
        y_new, y_old = new_df.get(key, 0), old_df.get(key, 0)
        employers = len(new_emp.get(key, ()))
        if y_new < MIN_ADS or employers < MIN_EMPLOYERS:
            continue
        z = log_odds_z(y_new, len(new), y_old, len(old))
        if z < MIN_Z:
            continue
        known = known_as(key)
        if known:
            continue
        rows.append({
            "phrase": text, "df_new": y_new, "pct_new": round(100 * y_new / len(new), 1),
            "df_2019_22": y_old, "pct_2019_22": round(100 * y_old / len(old), 2),
            "employers_new": employers, "z": round(z, 2),
        })
    rows.sort(key=lambda r: (-r["z"], -r["df_new"], -len(r["phrase"].split()), r["phrase"]))   # longer phrase first on ties
    return _drop_nested(rows)


def _drop_nested(rows: list[dict]) -> list[dict]:
    """Keep "prompt engineering" and drop "prompt" or "engineering prompt" when they are in the
    same ads: a shorter or longer phrase with the same 2026 count adds nothing."""
    kept: list[dict] = []
    for row in rows:
        words = f" {row['phrase'].lower()} "
        if any(row["df_new"] == k["df_new"] and (words in f" {k['phrase'].lower()} " or
                                                   f" {k['phrase'].lower()} " in words) for k in kept):
            continue
        kept.append(row)
    return kept


def detect(methods=("ngram", "spacy"), new: list[Ad] | None = None, old: list[Ad] | None = None,
           top: int = TOP) -> list[dict]:
    """The candidate table: for each method, its `top` rising phrases new to dictionary and ESCO."""
    new = new if new is not None else load_ads("2026")
    old = old if old is not None else load_ads("2019-22")
    new_df, old_df = document_frequency(new, MAX_N + 1), document_frequency(old, MAX_N + 1)
    table = []
    for method in methods:
        found = score(PROPOSERS[method](new), new, old, new_df, old_df)[:top]
        table += [{"method": method, "rank": i, **row, "is_skill": ""} for i, row in enumerate(found, 1)]
    return table


def overlap(table: list[dict]) -> dict[tuple[str, str], int]:
    """How many phrases each pair of methods share (lower-cased)."""
    by = defaultdict(set)
    for row in table:
        by[row["method"]].add(row["phrase"].lower())
    methods = sorted(by)
    return {(a, b): len(by[a] & by[b]) for i, a in enumerate(methods) for b in methods[i + 1:]}


def main() -> None:
    import os

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--methods", nargs="+", default=["ngram", "spacy"], choices=METHODS)
    parser.add_argument("--with-2024", action="store_true", help="add the 124 LinkedIn ads of January 2024")
    parser.add_argument("--top", type=int, default=TOP)
    parser.add_argument("--out", type=Path, default=OUT_CSV)
    args = parser.parse_args()
    methods = list(args.methods)
    if "llm" in methods:
        try:
            from dotenv import load_dotenv
            load_dotenv(ROOT / ".env")
        except ImportError:
            pass
        if not os.getenv("OPENAI_API_KEY"):
            print("No OPENAI_API_KEY: skipping the llm method (cached answers are still used if present).")
            from .llm_extract import CACHE_DIR
            if not CACHE_DIR.exists():
                methods.remove("llm")

    new = load_ads("2026") + (load_ads("2024-01") if args.with_2024 else [])
    sample = "2024-01+2026" if args.with_2024 else "2026"
    old = load_ads("2019-22")
    print(f"recent ads ({sample}): {len(new)} from {len({a.employer for a in new})} employers; "
          f"2019-22 ads: {len(old)}")
    table = [{"sample": sample, **row} for row in detect(methods, new, old, args.top)]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(table[0]) if table else ["sample", "method"])
        writer.writeheader()
        writer.writerows(table)
    for method in methods:
        rows = [r for r in table if r["method"] == method]
        print(f"\n{method}: {len(rows)} candidates")
        for r in rows[:15]:
            print(f"  {r['rank']:>2}. {r['phrase']:<30} {r['df_new']:>3} ads ({r['pct_new']:>5}%), "
                  f"{r['employers_new']:>3} employers | 2019-22 {r['pct_2019_22']:>5}% | z {r['z']}")
    print("\nshared between methods:", overlap(table))
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
