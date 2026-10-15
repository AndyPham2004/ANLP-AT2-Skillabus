"""One skill vocabulary: ESCO as the base, plus the skills ESCO lacks (plan D5).

Writes data/1_knowledge/skills/skills_vocabulary.csv, one row per skill. The plan is
docs/notes/data_it_scope_2026-10-14.md, section 3. Parts, in this order:

  1. The 148 dictionary skills (skills_seed_v2.csv), used to detect skills in ads (used_for extract).
     Each one's ESCO link was judged by hand in esco_link_review.csv; this script only copies it.
  3. IT skills beyond the dictionary (added_skills.csv, by hand: ad-style aliases, ESCO link, origin).
     A row is used for detection only if it is named in at least 3 of our Australian ads from at least
     2 employers (vocabulary_ad_counts.csv). An O*NET in-demand tool below that rule is kept as a
     core skill without aliases; any other row below it is left out.
  2. ESCO's essential skills of the 11 roles' occupations (occupation_skills.csv, plan D4) that no row
     above already is (used_for core_skill, no aliases: ESCO labels are never used for detection).
  +  Certifications (plan D11, learning_resources/certifications.csv), once that file exists.

A skill of part 1 or 3 is also a core skill (used_for extract;core_skill) when it is the exact ESCO
concept of an essential skill, or an O*NET in-demand tool of a role maps to it (onet_tool_map.csv).

Columns:
  skill_id      esco:<uri> only when esco_match = exact (the data contract's form); otherwise
                skillabus:<slug>, so two tools under one wide ESCO concept (Tableau, Power BI ->
                "data visualisation software") keep different ids and match.py never confuses them
  label         display name; for part 1 the dictionary's canonical name, unchanged
  category      the dictionary's group; "ESCO core skill" for part 2; "Certification"
  source        esco (esco_match = exact) or added (ESCO lacks the skill, or has only a wider concept)
  esco_uri, esco_label   the related ESCO concept, also when it is wider (empty for none)
  esco_match    exact / close / broad (the ESCO concept is wider) / none, as in SKOS
                (exactMatch, closeMatch, broadMatch), the mapping relations ESCO itself uses
  reviewed_by   who checked the ESCO link
  aliases_ads   how ads write the skill, "|"-joined. Only rows with aliases are used for detection
  strict        1 = aliases match case-sensitively (R, SAS, SAP, React)
  used_for      extract, core_skill, extract;core_skill, or certification
  why_added     why the row is ours: ESCO's nearest concept, origin, and the Australian ads naming it

To change a link or add a skill: edit esco_link_review.csv or added_skills.csv, rerun (and after
adding a skill, recount first). The script checks each link against the committed ESCO table (the
URI exists and carries the label written next to it), refuses links known to be wrong, and refuses
a new alias that would take mentions from another skill's alias. skills_seed_v2.csv and
skill_to_esco.csv stay as they are until the pipeline reads this file (plan C2).

Usage (from the repo root):
    python data-eda/src/build_vocabulary.py
    python data-eda/src/build_vocabulary.py --check      # exit 1 if the CSV is out of date
    python data-eda/src/build_vocabulary.py --recount    # rewrite vocabulary_ad_counts.csv; needs the
        raw ATS ads (data/raw/jobs_au_ats_2026.csv, ats_ads_2026-*.csv); --raw <folder> reads them elsewhere
"""

from __future__ import annotations

import argparse
import csv
import io
import logging
import re
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))  # repo src/, for skillabus.paths
from skillabus import extract, paths  # noqa: E402
from skillabus.normalise import BLOCKED_ESCO  # noqa: E402
from skillabus.text import read_csv_skipping_notes, slug  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger("build_vocabulary")

SEED = paths.SKILLS_SEED
REVIEW = paths.ESCO_LINK_REVIEW
ADDED = paths.ADDED_SKILLS
ONET_MAP = paths.ONET_TOOL_MAP
COUNTS = paths.VOCAB_AD_COUNTS
OCCUPATION_SKILLS = paths.OCCUPATION_SKILLS
ESCO = paths.ESCO_SKILLS_CLEAN
# Plan D11 adds this file (and maybe its own constant in paths.py); until then part "+" is empty.
CERTIFICATIONS = getattr(paths, "CERTIFICATIONS", paths.LEARNING_RESOURCES / "certifications.csv")
OUT = paths.SKILLS_VOCABULARY

COLUMNS = ["skill_id", "label", "category", "source", "esco_uri", "esco_label", "esco_match",
           "reviewed_by", "aliases_ads", "strict", "used_for", "why_added"]
REVIEW_COLUMNS = ["canonical", "old_esco_uri", "old_esco_label", "esco_uri", "esco_label",
                  "esco_match", "note", "reviewed_by"]
ADDED_COLUMNS = ["label", "category", "aliases_ads", "strict", "esco_uri", "esco_label", "esco_match",
                 "note", "origin", "reviewed_by"]
AD_SOURCES = ("seek_2019_22", "recent_2024_26", "ats_2026")
SOURCE_NAMES = {"seek_2019_22": "Seek 2019-22", "recent_2024_26": "recent 2024-26", "ats_2026": "ATS 2026"}
COUNT_COLUMNS = ["label", "n_ads", "n_employers", *AD_SOURCES]
MATCHES = ("exact", "close", "broad", "none")
MIN_ADS, MIN_EMPLOYERS = 3, 2
ONET_ORIGIN = "O*NET in-demand tool"  # an added_skills.csv origin; why_added then names the roles instead
CORE_CATEGORY = "ESCO core skill"
_E = "http://data.europa.eu/esco/skill/"
# Links found wrong on 14 Oct 2026 (ESCO alt labels that share a word with a data skill). The concepts
# themselves are fine for other skills ("computer vision" is the exact link for Computer vision).
KNOWN_WRONG = {
    ("Transformers", _E + "f0ab5d57-4be7-411b-afce-b4a76a142302"),   # electrical machines
    ("TensorFlow", _E + "7b0d5000-00da-4864-b776-6de49a87a669"),     # computer vision
    ("Keras", _E + "7b0d5000-00da-4864-b776-6de49a87a669"),          # computer vision
}


def read_table(path: Path) -> pd.DataFrame:
    """A committed CSV as strings, empty cells as "" (never NaN), leading "# ..." notes skipped."""
    return read_csv_skipping_notes(path, dtype=str, keep_default_na=False)


def read_table_text(text: str) -> pd.DataFrame:
    return pd.read_csv(io.StringIO(text), dtype=str, keep_default_na=False)


def vocab_slug(label: str) -> str:
    """skillabus:<slug> part. Keeps + and # apart, so C++ and C# can never share an id."""
    return slug(label.replace("+", " plus ").replace("#", " sharp "))


def skill_id(label: str, esco_match: str, esco_uri: str) -> str:
    return f"esco:{esco_uri}" if esco_match == "exact" else f"skillabus:{vocab_slug(label)}"


def aliases(cell: str) -> list[str]:
    return [a.strip() for a in cell.split("|") if a.strip()]


# ---------------------------------------------------------------- checks
def check_link(name: str, r, label_of: dict) -> list[str]:
    """Problems with one hand-judged ESCO link (a row of the review or the added file)."""
    where = f"{name}:"
    if r.esco_match not in MATCHES:
        return [f"{where} esco_match {r.esco_match!r} is not one of {MATCHES}"]
    errors = []
    if r.esco_match == "none":
        if r.esco_uri or r.esco_label:
            errors.append(f"{where} esco_match none but an ESCO link is filled in")
    elif not r.esco_uri:
        errors.append(f"{where} esco_match {r.esco_match} needs an esco_uri")
    elif r.esco_uri not in label_of:
        errors.append(f"{where} {r.esco_uri} is not in {ESCO.name}")
    elif label_of[r.esco_uri] != r.esco_label:
        errors.append(f"{where} esco_label {r.esco_label!r} but ESCO calls {r.esco_uri} {label_of[r.esco_uri]!r}")
    if r.esco_uri in BLOCKED_ESCO or (name, r.esco_uri) in KNOWN_WRONG:
        errors.append(f"{where} {r.esco_uri} ({r.esco_label}) is a known wrong link")
    if r.esco_match != "exact" and not r.note.strip():
        errors.append(f"{where} a {r.esco_match} link needs a note saying why it is not exact")
    if not r.reviewed_by.strip():
        errors.append(f"{where} reviewed_by is empty")
    return errors


def check_review(seed: pd.DataFrame, review: pd.DataFrame, esco: pd.DataFrame) -> list[str]:
    """Every problem in the review file, as readable lines (empty list = fine)."""
    if list(review.columns) != REVIEW_COLUMNS:
        return [f"columns must be {REVIEW_COLUMNS}, got {list(review.columns)}"]
    errors = [f"listed twice: {d}" for d in review.canonical[review.canonical.duplicated()]]
    errors += [f"dictionary skill with no review row: {m}" for m in sorted(set(seed.canonical) - set(review.canonical))]
    errors += [f"review row for a skill not in the dictionary: {x}" for x in sorted(set(review.canonical) - set(seed.canonical))]
    label_of = dict(zip(esco.concept_uri, esco.preferred_label))
    for r in review.itertuples():
        errors += check_link(r.canonical, r, label_of)
    return errors


def check_added(added: pd.DataFrame, seed: pd.DataFrame, esco: pd.DataFrame) -> list[str]:
    """Every problem in added_skills.csv."""
    if list(added.columns) != ADDED_COLUMNS:
        return [f"columns must be {ADDED_COLUMNS}, got {list(added.columns)}"]
    errors = [f"listed twice: {d}" for d in added.label[added.label.duplicated()]]
    taken = {c.casefold() for c in seed.canonical}
    errors += [f"{x}: already a dictionary skill" for x in added.label if x.casefold() in taken]
    label_of = dict(zip(esco.concept_uri, esco.preferred_label))
    for r in added.itertuples():
        errors += check_link(r.label, r, label_of)
        if not aliases(r.aliases_ads):
            errors.append(f"{r.label}: needs at least one alias the way ads write it")
        if r.strict not in ("0", "1"):
            errors.append(f"{r.label}: strict must be 0 or 1")
        if not r.origin.strip():
            errors.append(f"{r.label}: origin is empty")
    return errors


def _contains(longer: str, shorter: str, flags) -> bool:
    """Would `shorter` be found inside `longer` by extract's lookarounds (a whole-word hit)?"""
    return re.search(rf"(?<![A-Za-z0-9]){re.escape(shorter)}(?![A-Za-z0-9])", longer, flags) is not None


def check_new_aliases(rows: pd.DataFrame, new_labels: set[str]) -> list[str]:
    """A new alias must not repeat another skill's alias, or contain one: extract() tries the longest
    alias first, so 'github actions' would take every 'GitHub Actions' mention away from Git."""
    errors = []
    for strict in ("0", "1"):
        same = rows[rows.strict == strict]
        flags = 0 if strict == "1" else re.IGNORECASE
        owned = [(a if strict == "1" else a.lower(), r.label) for r in same.itertuples() for a in aliases(r.aliases_ads)]
        for a, label in owned:
            if label not in new_labels:
                continue
            for b, other in owned:
                if other == label:
                    continue
                if a == b:
                    errors.append(f"{label}: alias {a!r} is also an alias of {other}")
                elif _contains(a, b, flags):
                    errors.append(f"{label}: alias {a!r} contains {other}'s alias {b!r} and would hide it")
    return errors


# ---------------------------------------------------------------- text of why_added
def esco_phrase(esco_match: str, esco_label: str) -> str:
    return {"exact": f"ESCO has it ('{esco_label}')", "broad": f"ESCO has only the wider '{esco_label}'",
            "close": f"ESCO's nearest concept '{esco_label}' is not the same skill", "none": "not in ESCO"}[esco_match]


def ads_phrase(c) -> str:
    by = ", ".join(f"{SOURCE_NAMES[s]} {int(c[s])}" for s in AD_SOURCES)
    n, m = int(c["n_ads"]), int(c["n_employers"])
    return f"in {n} AU ad{'s' * (n != 1)} from {m} employer{'s' * (m != 1)} ({by})"


def passes(c) -> bool:
    return int(c["n_ads"]) >= MIN_ADS and int(c["n_employers"]) >= MIN_EMPLOYERS


# ---------------------------------------------------------------- parts
def part1(seed: pd.DataFrame, review: pd.DataFrame, counts: dict) -> list[dict]:
    """The dictionary skills, in dictionary order, with their reviewed ESCO links."""
    links = review.set_index("canonical")
    rows = []
    for s in seed.itertuples():
        r = links.loc[s.canonical]
        why = ""
        if r.esco_match != "exact":
            why = f"Dictionary skill; {esco_phrase(r.esco_match, r.esco_label)}"
            if s.canonical in counts:
                why += f"; in {int(counts[s.canonical]['n_ads'])} AU ads"
        rows.append({"skill_id": skill_id(s.canonical, r.esco_match, r.esco_uri), "label": s.canonical,
                     "category": s.category, "source": "esco" if r.esco_match == "exact" else "added",
                     "esco_uri": r.esco_uri, "esco_label": r.esco_label, "esco_match": r.esco_match,
                     "reviewed_by": r.reviewed_by, "aliases_ads": s.aliases, "strict": s.strict,
                     "used_for": "extract", "why_added": why})
    return rows


def part3(added: pd.DataFrame, counts: dict, onet_roles: dict) -> list[dict]:
    """Rows of added_skills.csv that pass the ad rule, plus O*NET in-demand tools that do not (as core skills)."""
    rows = []
    for r in added.itertuples():
        if r.label not in counts:
            raise ValueError(f"{r.label} has no ad count: run python data-eda/src/build_vocabulary.py --recount")
        c = counts[r.label]
        origin = r.origin
        if r.label in onet_roles:
            onet = f"O*NET in-demand for {', '.join(onet_roles[r.label])}"
            origin = onet if origin == ONET_ORIGIN else f"{origin}; {onet}"
        why = f"{origin}; {esco_phrase(r.esco_match, r.esco_label)}; {ads_phrase(c)}"
        if passes(c):
            used, alias_cell = "extract", r.aliases_ads
        elif r.label in onet_roles:
            used, alias_cell = "core_skill", ""
            why += f", below the rule for detection ({MIN_ADS} ads, {MIN_EMPLOYERS} employers)"
        else:
            log.info("left out, below the ad rule: %s (%s ads, %s employers)", r.label, c["n_ads"], c["n_employers"])
            continue
        rows.append({"skill_id": skill_id(r.label, r.esco_match, r.esco_uri), "label": r.label,
                     "category": r.category, "source": "esco" if r.esco_match == "exact" else "added",
                     "esco_uri": r.esco_uri, "esco_label": r.esco_label, "esco_match": r.esco_match,
                     "reviewed_by": r.reviewed_by, "aliases_ads": alias_cell, "strict": r.strict,
                     "used_for": used, "why_added": why})
    return rows


def esco_essentials(occupation_skills: pd.DataFrame) -> dict[str, list[str]]:
    """ESCO essential skill URI -> the roles whose occupation lists it (plan D4)."""
    e = occupation_skills[(occupation_skills.source == "esco") & (occupation_skills.importance == "essential")]
    return {uri: sorted(set(g.role)) for uri, g in e.groupby("skill_ref")}


def onet_in_demand(occupation_skills: pd.DataFrame, onet_map: pd.DataFrame, labels: set[str]) -> tuple[dict, list[str]]:
    """Vocabulary label -> roles for which O*NET marks a tool of it In Demand; and the problems found."""
    tools = occupation_skills[occupation_skills.source == "onet"]
    mapping = dict(zip(onet_map.onet_tool, onet_map.label))
    errors = [f"O*NET tool not in {ONET_MAP.name}: {t}" for t in sorted(set(tools.skill) - set(mapping))]
    errors += [f"{ONET_MAP.name}: {t} -> {lab!r} is not a vocabulary label" for t, lab in mapping.items()
               if lab and lab not in labels]
    errors += [f"{ONET_MAP.name}: {t} is dropped without a reason" for t, lab, note
               in onet_map[["onet_tool", "label", "note"]].itertuples(index=False) if not lab and not note.strip()]
    roles = defaultdict(set)
    for t in tools.itertuples():
        if mapping.get(t.skill):
            roles[mapping[t.skill]].add(t.role)
    return {k: sorted(v) for k, v in roles.items()}, errors


def part2(essentials: dict, covered: set[str], label_of: dict) -> list[dict]:
    """ESCO essential skills that no row above is exactly, sorted by label."""
    rows = [{"skill_id": f"esco:{uri}", "label": label_of[uri], "category": CORE_CATEGORY, "source": "esco",
             "esco_uri": uri, "esco_label": label_of[uri], "esco_match": "exact",
             "reviewed_by": "ESCO v1.2.1 (its own concept)", "aliases_ads": "", "strict": "0",
             "used_for": "core_skill", "why_added": ""} for uri in essentials if uri not in covered]
    return sorted(rows, key=lambda r: (r["label"].casefold(), r["esco_uri"]))


def part_certifications(path: Path) -> list[dict]:
    """Certifications from plan D11 (cert, vendor, ...). Listed, not detected: ads rarely name them."""
    if not path.exists():
        log.info("no %s yet (plan D11): no Certification rows", path.name)
        return []
    certs = read_table(path)
    if "cert" not in certs:
        raise ValueError(f"{path.name} needs a 'cert' column")
    rows = []
    for r in certs.drop_duplicates("cert").itertuples():
        vendor = getattr(r, "vendor", "")
        rows.append({"skill_id": f"skillabus:{vocab_slug(r.cert)}", "label": r.cert, "category": "Certification",
                     "source": "added", "esco_uri": "", "esco_label": "", "esco_match": "none",
                     "reviewed_by": getattr(r, "collected_by", "") or "plan D11", "aliases_ads": "", "strict": "0",
                     "used_for": "certification",
                     "why_added": f"Certification{' by ' + vendor if vendor else ''} (plan D11); not in ESCO"})
    return rows


# ---------------------------------------------------------------- build
def load_counts(path: Path) -> dict:
    if not path.exists():
        return {}
    c = read_table(path)
    return {r["label"]: r for r in c.to_dict("records")}


def build(seed_path: Path = SEED, review_path: Path = REVIEW, esco_path: Path = ESCO,
          added_path: Path = ADDED, counts_path: Path = COUNTS, occupation_path: Path = OCCUPATION_SKILLS,
          onet_map_path: Path = ONET_MAP, certs_path: Path = CERTIFICATIONS) -> pd.DataFrame:
    seed, review, added = read_table(seed_path), read_table(review_path), read_table(added_path)
    esco = pd.read_csv(esco_path, usecols=["concept_uri", "preferred_label"], dtype=str)
    label_of = dict(zip(esco.concept_uri, esco.preferred_label))
    errors = check_review(seed, review, esco) + check_added(added, seed, esco)
    if errors:
        raise ValueError(f"{len(errors)} problem(s) in the hand files:\n  " + "\n  ".join(errors))
    counts = load_counts(counts_path)
    occupation_skills = read_table(occupation_path)
    onet_roles, errors = onet_in_demand(occupation_skills, read_table(onet_map_path),
                                        set(seed.canonical) | set(added.label))
    rows = part1(seed, review, counts) + part3(added, counts, onet_roles)
    vocab = pd.DataFrame(rows, columns=COLUMNS)
    errors += [f"{lab}: O*NET maps a tool to it, but it is left out (below the ad rule, not O*NET-origin)"
               for lab in onet_roles if lab not in set(vocab.label)]
    # Every candidate, kept or not: the recount matches them all together with the dictionary.
    every = pd.concat([vocab[vocab.label.isin(seed.canonical)], added], ignore_index=True)
    errors += check_new_aliases(every[["label", "strict", "aliases_ads"]], set(added.label))
    essentials = esco_essentials(occupation_skills)
    errors += [f"ESCO essential skill not in {ESCO.name}: {u}" for u in essentials if u not in label_of]
    if errors:
        raise ValueError(f"{len(errors)} problem(s):\n  " + "\n  ".join(errors))

    core = vocab.label.isin(onet_roles) | ((vocab.esco_match == "exact") & vocab.esco_uri.isin(essentials))
    vocab.loc[core & (vocab.used_for == "extract"), "used_for"] = "extract;core_skill"
    covered = set(vocab.esco_uri[vocab.esco_match == "exact"])
    vocab = pd.concat([vocab, pd.DataFrame(part2(essentials, covered, label_of) + part_certifications(certs_path),
                                           columns=COLUMNS)], ignore_index=True)
    for col, key in (("skill_id", vocab.skill_id), ("label", vocab.label.str.casefold())):
        clash = vocab.label[key.duplicated(keep=False)].tolist()
        if clash:
            raise ValueError(f"rows share a {col}: {clash}")
    return vocab


def to_csv_text(df: pd.DataFrame) -> str:
    buf = io.StringIO()
    df.to_csv(buf, index=False, lineterminator="\n", quoting=csv.QUOTE_MINIMAL)
    return buf.getvalue()


def headline(vocab: pd.DataFrame, counts: dict) -> dict:
    """The numbers for the report: skills ESCO lacks (broad or none) that our ads name by the ad rule."""
    detect = vocab[vocab.used_for.str.contains("extract")]
    lacks = detect[detect.esco_match.isin(["broad", "none"])]
    seen = lacks[[lab in counts and passes(counts[lab]) for lab in lacks.label]]
    part3_labels = set(read_table(ADDED).label)
    return {"n": len(seen), "dictionary": int((~seen.label.isin(part3_labels)).sum()),
            "added": int(seen.label.isin(part3_labels).sum())}


def summary(vocab: pd.DataFrame) -> str:
    m = vocab.esco_match.value_counts()
    u = vocab.used_for.value_counts()
    return (f"{len(vocab)} skills; esco_match " + ", ".join(f"{k} {m.get(k, 0)}" for k in MATCHES)
            + "; used_for " + ", ".join(f"{k} {v}" for k, v in sorted(u.items()))
            + f"; source esco {int((vocab.source == 'esco').sum())}, added {int((vocab.source == 'added').sum())}")


# ---------------------------------------------------------------- ad counts
def ad_files(raw: Path = paths.RAW) -> dict[str, list[Path]]:
    """Our Australian full-text ads by source. The ATS ads are raw downloads (data/raw/, not in git)."""
    return {"seek_2019_22": [paths.SEEK_ADS], "recent_2024_26": [paths.RECENT_ADS],
            "ats_2026": [raw / paths.ATS_SEPT_RAW.name, *sorted(raw.glob(paths.ATS_RAW_PATTERN))]}


def load_corpus(files: dict[str, list[Path]]) -> pd.DataFrame:
    """One row per distinct ad: source, title, employer, text.

    An ad fetched twice is kept once, under the first source in AD_SOURCES order: same text after
    folding case and spaces, or (outside Seek, whose employer field is mostly the recruiter) the same
    title and employer. The recent sample copied some 2026 ATS ads; the two ATS fetches overlap.
    """
    frames = []
    for source in AD_SOURCES:
        for f in files.get(source, []):
            df = pd.read_csv(f, dtype=str, keep_default_na=False)
            employer = df["company"] if "company" in df else pd.Series("", index=df.index)
            if "advertiser" in df:
                employer = employer.where(employer.str.strip() != "", df["advertiser"])
            frames.append(pd.DataFrame({"source": source, "title": df.get("title", ""),
                                        "employer": employer.str.strip(), "text": df["description"]}))
    ads = pd.concat(frames, ignore_index=True)
    ads = ads[ads.text.str.strip() != ""]
    ads = ads[~ads.text.str.lower().str.replace(r"\s+", " ", regex=True).str.strip().duplicated()]
    named = ads[(ads.source != "seek_2019_22") & (ads.employer != "")]
    again = named[pd.DataFrame({"t": named.title.str.lower(), "e": named.employer.str.lower()}).duplicated()]
    return ads.drop(index=again.index).reset_index(drop=True)


def skill_hits(skills: pd.DataFrame, texts) -> list[set[str]]:
    """The labels of `skills` each text names, with the tier-1 dictionary matcher of extract.py.

    `skills` needs label, category, aliases_ads, strict, like the vocabulary. The rows are written to
    a temporary file in the dictionary's format, so counting follows exactly the matching rules of
    extract(): longest alias first, case-sensitive strict aliases, URLs and e-mails blanked out.
    """
    with tempfile.TemporaryDirectory() as tmp:
        seed = Path(tmp) / "candidates.csv"
        pd.DataFrame({"canonical": skills.label, "category": skills.category, "strict": skills.strict,
                      "aliases": skills.aliases_ads}).to_csv(seed, index=False, lineterminator="\n")
        return [{c for sentence in extract.split_sentences(text)
                 for _, _, c in extract._dictionary_hits(sentence, str(seed))} for text in texts]


def count_ads(skills: pd.DataFrame, texts) -> Counter:
    """Texts naming each skill: label -> n."""
    counts = Counter()
    for found in skill_hits(skills, texts):
        counts.update(found)
    return counts


def self_mention(employer: str, label: str, alias_cell: str) -> bool:
    """Is the employer named after the skill (Datadog's own ads naming Datadog)? Such ads do not count."""
    names = [label, *aliases(alias_cell)]
    return any(len(n) >= 3 and _contains(employer, n, re.IGNORECASE) for n in names)


def count_corpus(skills: pd.DataFrame, corpus: pd.DataFrame) -> pd.DataFrame:
    """Per skill: ads naming it, distinct employers among them, and ads per source."""
    hits = skill_hits(skills, corpus.text)
    rows = []
    for s in skills.itertuples():
        idx = [i for i, found in enumerate(hits) if s.label in found
               and not self_mention(corpus.employer.iat[i], s.label, s.aliases_ads)]
        sub = corpus.iloc[idx]
        by_source = sub.source.value_counts()
        rows.append({"label": s.label, "n_ads": len(sub),
                     "n_employers": sub.employer[sub.employer != ""].str.lower().nunique(),
                     **{src: int(by_source.get(src, 0)) for src in AD_SOURCES}})
    return pd.DataFrame(rows, columns=COUNT_COLUMNS)


def recount(raw: Path, out: Path = COUNTS) -> pd.DataFrame:
    """Count every dictionary skill and every added_skills.csv row over our Australian ads, in one matcher."""
    files = ad_files(raw)
    missing = [str(f) for fs in files.values() for f in fs if not f.exists()]
    if missing or len(files["ats_2026"]) < 2:
        raise SystemExit(f"--recount needs the raw ATS ads; missing: {missing or 'ats_ads_2026-*.csv'}")
    seed, added = read_table(SEED), read_table(ADDED)
    skills = pd.concat([pd.DataFrame({"label": seed.canonical, "category": seed.category, "strict": seed.strict,
                                      "aliases_ads": seed.aliases}),
                        added[["label", "category", "strict", "aliases_ads"]]], ignore_index=True)
    corpus = load_corpus(files)
    log.info("%d distinct ads: %s", len(corpus), corpus.source.value_counts().to_dict())
    counts = count_corpus(skills, corpus)
    out.write_text(to_csv_text(counts), encoding="utf-8", newline="")
    log.info("wrote %s", out)
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument("--check", action="store_true", help="do not write; exit 1 if --out differs")
    parser.add_argument("--recount", action="store_true", help=f"rewrite {COUNTS.name} from the ads first")
    parser.add_argument("--raw", type=Path, default=paths.RAW, help="folder with the raw ATS ads")
    args = parser.parse_args()

    if args.recount:
        recount(args.raw)
    vocab = build()
    log.info(summary(vocab))
    h = headline(vocab, load_counts(COUNTS))
    log.info("Skillabus extends ESCO with %d skills the Australian IT market asks for but ESCO lacks "
             "(%d from the dictionary, %d added for IT)", h["n"], h["dictionary"], h["added"])

    text = to_csv_text(vocab)
    if args.check:
        if not args.out.exists() or not read_table(args.out).equals(read_table_text(text)):
            log.error("%s is out of date: run python data-eda/src/build_vocabulary.py", args.out)
            sys.exit(1)
        log.info("%s is up to date", args.out)
        return
    args.out.write_text(text, encoding="utf-8", newline="")
    log.info("wrote %s", args.out)


if __name__ == "__main__":
    main()
