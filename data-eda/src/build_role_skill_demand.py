"""One demand table: role x skill x source x period, counted with the one vocabulary (plan D6).

Writes data/2_demand/role_skill_demand.csv, long format, one row per role, skill, source and period
(plan docs/notes/data_it_scope_2026-10-14.md, 4.3):

  role, role_family   one of the 11 roles of role_occupations.csv, or "Data roles (mixed)" (below)
  skill_id, skill     the skill's id and label in skills_vocabulary.csv; every row's skill is in it
  source, period      seek_2019_22 / 2019-22, data_jobs_2023 / 2023, recent_2024_26 / 2024-01 or 2026,
                      esco_occupation / v1.2.1, onet / v31.0 (for a taxonomy the period is its release)
  text_type           full_text (ad text), tool_list (a list of tool names, no text), taxonomy (no counts)
  n_ads, total_ads    ads naming the skill at least once; the ads of that role, source and period
  pct, pct_low, pct_high   100 * n_ads / total_ads (1 decimal) and its 95% Wilson interval
                      (recount_recent.wilson); blank for taxonomy rows
  importance          essential / optional (ESCO), in_demand (O*NET); blank for counted rows

Sources:
  seek_2019_22    Data Scientist, the 3,204 Seek ads (2_demand/ads/, cleaned text). Every vocabulary row
                  used for detection (used_for has extract) is matched with extract.py's tier-1 matcher
                  through build_vocabulary.skill_hits, so counting follows the app's matching rules.
  data_jobs_2023  The 7 roles of build_role_profiles.py from data/raw/jobs_au_datajobs_2023.parquet (or
                  data_jobs_hf/data_jobs.csv): the same Australian rows, de-duplication and title map.
                  Each tool name -> a vocabulary label: the dictionary rows exactly as build_role_profiles.py
                  maps them (canonical name, alias, TOKEN_MAP), then the vocabulary's other tool rows by
                  label or alias, then EXTRA_TOKEN_MAP. "go", "flow" and the bare letter "c" are not counted.
                  The denominator is the role's ads naming at least one tool, as in role_profiles.csv.
  recent_2024_26  The in-sample full-text rows of 2_demand/ads/jobs_au_recent_2024-2026_clean.csv,
                  by period (2024-01 = LinkedIn January 2024; 2026 = the September-October 2026 job-board
                  fetches) and by the file's role_group. A role_group that names one of the 11 roles is
                  its own block only with at least MIN_ROLE_ADS ads (plan D15); every other ad of the
                  period (role_group "data role", or a role below the floor) is counted under
                  "Data roles (mixed)". No role is guessed for an ad the file does not classify.
  esco_occupation The ESCO essential and optional skills of each role's occupation (occupation_skills.csv,
                  plan D4). ESCO concept URI -> vocabulary skill_id "esco:<uri>"; the vocabulary holds every
                  essential skill, and the optional skills it does not hold are left out (they stay in
                  occupation_skills.csv).
  onet            O*NET in-demand tools per role, mapped to a label with onet_tool_map.csv; several tools
                  can map to one label (one row); a tool mapped to no label (eMASS) is left out.

Not in this table: pct_required (plan D14), which waits for the required / preferred flag under
review in #109; the ASC rows of occupation_skills.csv (the plan's sources are ESCO and O*NET); the
raw 2026 ATS fetches, until they are classified by role (plan D2).

Usage (from the repo root):
    python data-eda/src/build_role_skill_demand.py
    python data-eda/src/build_role_skill_demand.py --raw "C:/path/to/another/checkout/data/raw"
    python data-eda/src/build_role_skill_demand.py --check     # exit 1 if the committed CSV is out of date
"""

from __future__ import annotations

import argparse
import logging
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

from build_vocabulary import read_table, read_table_text, skill_hits, to_csv_text
from build_role_profiles import ROLES as DATA_JOBS_ROLES, TOKEN_MAP, UNRELIABLE, australian_postings, parse_skills
from recount_recent import wilson

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))  # repo src/, for skillabus.paths
from skillabus import paths  # noqa: E402

log = logging.getLogger("build_role_skill_demand")

OUT = paths.ROLE_SKILL_DEMAND
COLUMNS = ["role", "role_family", "skill_id", "skill", "source", "period", "text_type",
           "n_ads", "total_ads", "pct", "pct_low", "pct_high", "importance"]
SOURCES = ("seek_2019_22", "data_jobs_2023", "recent_2024_26", "esco_occupation", "onet")
TEXT_TYPE = {"seek_2019_22": "full_text", "data_jobs_2023": "tool_list", "recent_2024_26": "full_text",
             "esco_occupation": "taxonomy", "onet": "taxonomy"}
COUNTED = ("seek_2019_22", "data_jobs_2023", "recent_2024_26")
IMPORTANCE = ("essential", "optional", "in_demand")
SEEK_ROLE, SEEK_PERIOD = "Data Scientist", "2019-22"
DATA_JOBS_PERIOD = "2023"
TAXONOMY_PERIOD = {"esco_occupation": "v1.2.1", "onet": "v31.0"}
MIXED_ROLE, MIXED_FAMILY = "Data roles (mixed)", "Data & AI"
MIN_ROLE_ADS = 30  # plan D15: a role's trend is shown only when each period has at least this many of its ads

# Vocabulary rows a tool name may map to: the skills and tools, not the ESCO core skills ("apply for
# research funding", no aliases) or certificate names, which never appear in a tool list.
NOT_TOOLS = ("ESCO core skill", "Certification")
# Bare names of tools the vocabulary has, written another way in the 2023 lists (as TOKEN_MAP does).
EXTRA_TOKEN_MAP = {
    "no-sql": "NoSQL",
    "redhat": "Linux", "centos": "Linux", "debian": "Linux", "suse": "Linux",   # Linux distributions
}
# Like "go": a bare letter the dataset's keyword matcher also finds in ordinary text (likely "C-level",
# "C-suite"): Business Analyst ads name it (1.9%) about as often as Data Scientist ads (2.4%), and the
# vocabulary itself never matches a bare C (its aliases are "C programming", "C/C++", ...).
EXTRA_UNRELIABLE = {"c"}


# ---------------------------------------------------------------- inputs
def detection_rows(vocab: pd.DataFrame) -> pd.DataFrame:
    """The vocabulary rows used to find skills in ad text (used_for has extract)."""
    return vocab[vocab.used_for.str.contains("extract")].reset_index(drop=True)


def role_families(role_occupations: pd.DataFrame) -> dict[str, str]:
    return dict(role_occupations[["role", "role_family"]].drop_duplicates().itertuples(index=False))


def load_data_jobs(raw: Path) -> pd.DataFrame:
    """The data_jobs postings as strings, empty cells "" (as build_role_profiles.py reads the CSV)."""
    parquet = raw / paths.DATA_JOBS_AU_RAW.name
    csv_file = raw / paths.DATA_JOBS_RAW.relative_to(paths.RAW)
    if parquet.exists():
        df = pd.read_parquet(parquet)
        for col in df.columns:
            if not pd.api.types.is_bool_dtype(df[col]) and not pd.api.types.is_numeric_dtype(df[col]):
                df[col] = df[col].fillna("").astype(str)
        return df
    if csv_file.exists():
        return pd.read_csv(csv_file, dtype=str, keep_default_na=False)
    raise SystemExit(f"neither {parquet} nor {csv_file} found: copy the data_jobs download into --raw "
                     "(https://huggingface.co/datasets/lukebarousse/data_jobs)")


# ---------------------------------------------------------------- counted rows
def share_rows(counts: Counter, total: int, *, role: str, family: str, source: str, period: str,
               by_label: dict[str, str]) -> list[dict]:
    """One row per skill named in at least one of `total` ads."""
    rows = []
    for label, n in counts.items():
        if n < 1:
            continue
        low, high = wilson(n, total)
        rows.append({"role": role, "role_family": family, "skill_id": by_label[label], "skill": label,
                     "source": source, "period": period, "text_type": TEXT_TYPE[source], "n_ads": n,
                     "total_ads": total, "pct": round(100 * n / total, 1), "pct_low": low, "pct_high": high,
                     "importance": ""})
    return rows


def count_hits(hits: list[set[str]]) -> Counter:
    counts = Counter()
    for found in hits:
        counts.update(found)
    return counts


def seek_rows(vocab: pd.DataFrame, seek: pd.DataFrame, family: str) -> list[dict]:
    """Data Scientist over the Seek ads: ads naming each detection row at least once."""
    det = detection_rows(vocab)
    counts = count_hits(skill_hits(det, seek.description.fillna("")))
    log.info("seek_2019_22: %d ads, %d of %d detection rows found", len(seek), len(counts), len(det))
    return share_rows(counts, len(seek), role=SEEK_ROLE, family=family, source="seek_2019_22",
                      period=SEEK_PERIOD, by_label=dict(zip(vocab.label, vocab.skill_id)))


def tool_lookup(vocab: pd.DataFrame, dictionary_labels: set[str]) -> dict[str, str]:
    """{lower-case tool name: vocabulary label}.

    The dictionary rows first, built exactly as build_role_profiles.load_dictionary builds them (a
    canonical name overrides an earlier alias), so every tool it mapped maps to the same skill here.
    Then the vocabulary's other tool rows, by label or alias, never overriding a dictionary name.
    """
    tools = vocab[~vocab.category.isin(NOT_TOOLS)]
    lookup: dict[str, str] = {}
    first = tools[tools.label.isin(dictionary_labels)]
    for r in first.itertuples():
        lookup[r.label.casefold()] = r.label
        for alias in r.aliases_ads.split("|"):
            if alias:
                lookup.setdefault(alias.casefold(), r.label)
    for r in tools[~tools.label.isin(dictionary_labels)].itertuples():
        for name in (r.label, *r.aliases_ads.split("|")):
            if name.strip():
                lookup.setdefault(name.strip().casefold(), r.label)
    return lookup


def to_label(token: str, lookup: dict[str, str]) -> str | None:
    t = token.strip().casefold()
    if t in UNRELIABLE or t in EXTRA_UNRELIABLE:
        return None
    return TOKEN_MAP.get(t) or lookup.get(t) or EXTRA_TOKEN_MAP.get(t)


def data_jobs_rows(vocab: pd.DataFrame, postings: pd.DataFrame, families: dict[str, str],
                   dictionary_labels: set[str]) -> tuple[list[dict], Counter, dict[str, int]]:
    """The 7 roles' tool shares; also the unmapped tool names (mentions) and each role's denominator."""
    lookup = tool_lookup(vocab, dictionary_labels)
    labels = set(vocab.label)
    bad = sorted({v for v in (*TOKEN_MAP.values(), *EXTRA_TOKEN_MAP.values()) if v not in labels})
    if bad:
        raise ValueError(f"token maps name labels that are not in the vocabulary: {bad}")
    by_label = dict(zip(vocab.label, vocab.skill_id))
    au = australian_postings(postings)
    rows, unmapped, totals = [], Counter(), {}
    for role, ads in au.groupby("role"):
        counts, total = Counter(), 0
        for cell in ads.job_skills:
            tokens = parse_skills(cell)
            if not tokens:
                continue
            total += 1
            found = set()
            for t in tokens:
                label = to_label(t, lookup)
                if label:
                    found.add(label)
                elif t.strip().casefold() not in UNRELIABLE | EXTRA_UNRELIABLE:
                    unmapped[t.strip().casefold()] += 1
            counts.update(found)
        totals[role] = total
        rows += share_rows(counts, total, role=role, family=families[role], source="data_jobs_2023",
                           period=DATA_JOBS_PERIOD, by_label=by_label)
    return rows, unmapped, totals


def recent_period(period: str) -> str:
    """2024-01 stays; 2026-09 and 2026-10 (the job-board fetches) are one period, 2026."""
    return "2026" if str(period).startswith("2026") else str(period)


def recent_rows(vocab: pd.DataFrame, recent: pd.DataFrame, families: dict[str, str]) -> tuple[list[dict], list[str]]:
    """The recent sample by period and role group; groups below MIN_ROLE_ADS fold into MIXED_ROLE."""
    keep = (recent.full_text.astype(str).str.lower() == "true") & (recent.in_sample.astype(str).str.lower() == "true")
    ads = recent[keep].reset_index(drop=True)
    ads["block_period"] = ads.period.map(recent_period)
    hits = skill_hits(detection_rows(vocab), ads.description.fillna(""))
    role_of = {r.casefold(): r for r in families}
    by_label = dict(zip(vocab.label, vocab.skill_id))
    rows, notes = [], []
    for period, in_period in ads.groupby("block_period", sort=True):
        mixed = []
        for group, sub in in_period.groupby("role_group", sort=True):
            role = role_of.get(str(group).strip().casefold())
            if role and len(sub) >= MIN_ROLE_ADS:
                rows += share_rows(count_hits([hits[i] for i in sub.index]), len(sub), role=role,
                                   family=families[role], source="recent_2024_26", period=period, by_label=by_label)
                notes.append(f"{period}: {role}, {len(sub)} ads, its own block")
            else:
                mixed += list(sub.index)
                why = (f"below {MIN_ROLE_ADS} ads" if role else "not one role")
                notes.append(f"{period}: role_group '{group}', {len(sub)} ads, {why} -> {MIXED_ROLE}")
        if mixed:
            rows += share_rows(count_hits([hits[i] for i in mixed]), len(mixed), role=MIXED_ROLE,
                               family=MIXED_FAMILY, source="recent_2024_26", period=period, by_label=by_label)
    return rows, notes


# ---------------------------------------------------------------- taxonomy rows
def taxonomy_rows(vocab: pd.DataFrame, occupation_skills: pd.DataFrame, onet_map: pd.DataFrame,
                  families: dict[str, str]) -> tuple[list[dict], dict[str, Counter]]:
    """ESCO essential/optional and O*NET in-demand rows per role, as vocabulary skills; and what was left out."""
    label_of_id = dict(zip(vocab.skill_id, vocab.label))
    id_of_label = dict(zip(vocab.label, vocab.skill_id))
    tool_label = dict(zip(onet_map.onet_tool, onet_map.label))
    rows, left_out = [], {"esco_occupation": Counter(), "onet": Counter()}

    def row(role, sid, source, importance):
        return {"role": role, "role_family": families[role], "skill_id": sid, "skill": label_of_id[sid],
                "source": source, "period": TAXONOMY_PERIOD[source], "text_type": "taxonomy", "n_ads": None,
                "total_ads": None, "pct": None, "pct_low": None, "pct_high": None, "importance": importance}

    esco = occupation_skills[occupation_skills.source == "esco"]
    for r in esco.itertuples():
        sid = f"esco:{r.skill_ref}"
        if sid in label_of_id:
            rows.append(row(r.role, sid, "esco_occupation", r.importance))
        else:
            left_out["esco_occupation"][f"{r.importance} skill not in the vocabulary"] += 1
    onet_seen = set()
    for r in occupation_skills[occupation_skills.source == "onet"].itertuples():
        if r.skill not in tool_label:
            raise ValueError(f"O*NET tool {r.skill!r} is not in {paths.ONET_TOOL_MAP.name}")
        label = tool_label[r.skill]
        if not label:
            left_out["onet"][f"{r.skill} (dropped in {paths.ONET_TOOL_MAP.name})"] += 1
            continue
        if (r.role, label) in onet_seen:   # several O*NET tools -> one label (Outlook, PowerPoint -> Microsoft Office)
            continue
        onet_seen.add((r.role, label))
        rows.append(row(r.role, id_of_label[label], "onet", "in_demand"))
    return rows, left_out


# ---------------------------------------------------------------- build
def sort_table(df: pd.DataFrame) -> pd.DataFrame:
    """Source order, role, period, most ads first, essential before optional, then label."""
    key = pd.DataFrame({
        "s": df.source.map({s: i for i, s in enumerate(SOURCES)}), "r": df.role, "p": df.period,
        "n": -df.n_ads.fillna(0).astype(int), "i": df.importance.map({"": 0, **{v: i + 1 for i, v in enumerate(IMPORTANCE)}}),
        "k": df.skill.str.casefold(), "id": df.skill_id})
    order = key.sort_values(list(key.columns), kind="mergesort").index
    return df.loc[order].reset_index(drop=True)


def to_frame(rows: list[dict]) -> pd.DataFrame:
    """Rows -> the table: the columns in order, counts as integers (blank for taxonomy rows), sorted."""
    table = pd.DataFrame(rows, columns=COLUMNS)
    for col in ("n_ads", "total_ads"):
        table[col] = table[col].astype("Int64")
    for col in ("pct", "pct_low", "pct_high"):
        table[col] = table[col].astype(float)
    return sort_table(table)


def committed_inputs() -> dict:
    """Every input that is in git (all but the raw data_jobs file)."""
    families = role_families(read_table(paths.ROLE_OCCUPATIONS))
    missing_roles = sorted(set(DATA_JOBS_ROLES.values()) - set(families))
    if missing_roles:
        raise ValueError(f"data_jobs roles not in {paths.ROLE_OCCUPATIONS.name}: {missing_roles}")
    return {"vocab": read_table(paths.SKILLS_VOCABULARY), "families": families,
            "dictionary_labels": set(read_table(paths.SKILLS_SEED).canonical),
            "seek": pd.read_csv(paths.SEEK_ADS, dtype=str, keep_default_na=False),
            "recent": pd.read_csv(paths.RECENT_ADS, dtype=str, keep_default_na=False),
            "occupation_skills": read_table(paths.OCCUPATION_SKILLS), "onet_map": read_table(paths.ONET_TOOL_MAP)}


def build(raw: Path = paths.RAW) -> tuple[pd.DataFrame, dict]:
    i = committed_inputs()
    vocab, families = i["vocab"], i["families"]
    rows = seek_rows(vocab, i["seek"], families[SEEK_ROLE])
    dj_rows, unmapped, dj_totals = data_jobs_rows(vocab, load_data_jobs(raw), families, i["dictionary_labels"])
    rec_rows, recent_notes = recent_rows(vocab, i["recent"], families)
    tax_rows, left_out = taxonomy_rows(vocab, i["occupation_skills"], i["onet_map"], families)
    table = to_frame(rows + dj_rows + rec_rows + tax_rows)
    clash = table[table.duplicated(["role", "skill_id", "source", "period"], keep=False)]
    if not clash.empty:
        raise ValueError(f"rows repeat a role, skill, source and period:\n{clash.head()}")
    no_taxonomy = sorted(set(families) - set(table.role[table.text_type == "taxonomy"]))
    if no_taxonomy:
        raise ValueError(f"roles without taxonomy rows: {no_taxonomy}")
    report = {"unmapped": unmapped, "data_jobs_totals": dj_totals, "recent_notes": recent_notes,
              "left_out": left_out}
    return table, report


# ---------------------------------------------------------------- report
def summary(table: pd.DataFrame, top: int = 5) -> str:
    lines = []
    for (source, role, period), g in table.groupby(["source", "role", "period"], sort=False):
        if source in COUNTED:
            best = ", ".join(f"{r.skill} {r.pct:.0f}%" for r in g.head(top).itertuples())
            lines.append(f"  {source:15} {period:8} {role:30} n={int(g.total_ads.iloc[0]):5}  {len(g):3} skills  {best}")
        else:
            imp = g.importance.value_counts()
            lines.append(f"  {source:15} {period:8} {role:30} {len(g):3} skills ("
                         + ", ".join(f"{k} {imp[k]}" for k in IMPORTANCE if k in imp) + ")")
    return "\n".join(lines)


def compare_role_profiles(table: pd.DataFrame) -> str:
    """data_jobs_2023 against role_profiles.csv: denominators, and shares of the skills both have."""
    rp = pd.read_csv(paths.ROLE_PROFILES)
    dj = table[table.source == "data_jobs_2023"]
    totals = dj.groupby("role").total_ads.first()
    old_totals = rp.groupby("role").total_ads.first()
    m = rp.merge(dj, left_on=["role", "skill"], right_on=["role", "skill"], how="left", suffixes=("_rp", ""))
    differ = m[(m.n_ads.fillna(0) != m.n_ads_rp)]
    lines = [f"  totals equal role_profiles.csv: {totals.reindex(old_totals.index).eq(old_totals).all()} "
             f"({', '.join(f'{r} {n}' for r, n in totals.items())})",
             f"  role x skill rows of role_profiles.csv: {len(m)}; same n_ads here: {len(m) - len(differ)}"]
    for r in differ.itertuples():
        lines.append(f"    {r.role}, {r.skill}: {r.n_ads_rp} -> {r.n_ads} ads ({r.pct_ads} -> {r.pct}%)")
    new = dj[~dj.set_index(["role", "skill"]).index.isin(rp.set_index(["role", "skill"]).index)]
    lines.append(f"  new role x skill rows (tools the dictionary lacked): {len(new)}")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--raw", type=Path, default=paths.RAW, help="folder with jobs_au_datajobs_2023.parquet")
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument("--check", action="store_true", help="do not write; exit 1 if --out is out of date")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s", force=True)
    for name in ("extract_skills", "build_role_profiles"):
        logging.getLogger(name).setLevel(logging.WARNING)

    table, report = build(args.raw)
    counts = table.groupby(["source", "text_type"]).size()
    log.info("%d rows: %s", len(table), ", ".join(f"{s} ({t}) {n}" for (s, t), n in counts.items()))
    log.info("Per role, source and period (top %d):\n%s", 5, summary(table))
    log.info("recent_2024_26 blocks:\n  %s", "\n  ".join(report["recent_notes"]))
    log.info("data_jobs_2023 against role_profiles.csv:\n%s", compare_role_profiles(table))
    unmapped = report["unmapped"]
    log.info("data_jobs tool names not in the vocabulary: %d distinct, %d mentions:\n  %s", len(unmapped),
             sum(unmapped.values()), ", ".join(f"{t} {n}" for t, n in unmapped.most_common()))
    for source, c in report["left_out"].items():
        if c:
            log.info("%s rows left out: %s", source, ", ".join(f"{k}: {n}" for k, n in sorted(c.items())))

    text = to_csv_text(table)
    if args.check:
        if not args.out.exists() or not read_table(args.out).equals(read_table_text(text)):
            log.error("%s is out of date: run python data-eda/src/build_role_skill_demand.py", args.out)
            sys.exit(1)
        log.info("%s is up to date", args.out)
        return
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(text, encoding="utf-8", newline="")
    log.info("wrote %s", args.out)


if __name__ == "__main__":
    main()
