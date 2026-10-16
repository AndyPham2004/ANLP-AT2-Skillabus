"""Compare ad skills with resume skills: have / partial / missing. Owner: Phuong Nhi.

    match(ad_skills, resume_skills)  ->  the `skills` list of the gap result (data contract section 2)

Both inputs are skill mentions from extract(), with or without normalise().

have     the resume names the same skill (same dictionary name or same skill_id)
partial  the resume does not name it, but the ad asks for the umbrella skill of a dictionary
         category and the resume shows a part of it (ad "machine learning", resume "scikit-learn")
missing  neither

Substitute tools (ad "Tableau", resume "Power BI") are not counted as partial. We tried
embedding similarity between skill names (notebooks/pn_calibrate_matching.py, 8 Oct): true
substitutes scored lower than unrelated pairs (Tableau~Power BI 0.30, AWS~Azure 0.44, but
Airflow~MLflow 0.54, machine learning~artificial intelligence 0.70), so no threshold works.

Also here: soft_skills() for the skills left out of the gap list, roles(), role_profile() and
match_role() so a role (Data Scientist, Data Engineer, ...) can be matched like an ad, rank_evidence() to rank the resume sentences for one skill (the
P@5 / MRR evaluation on the CV-JD pairs), and score_matrix() to rank ads for a resume.

Demand comes from one table, data/2_demand/role_skill_demand.csv (plan C2): each role takes the block
of the first source in DEMAND_PRIORITY that counted its ads, so `demand_pct` is the share of that
block's ads naming the skill and `demand_pct_2026` the share in the role's 2026 block. Data Scientist
(and a pasted ad) keeps the 3,204 Seek ads 2019-22 for `demand_pct`, with the poster's own counts for
its 148 skills (_blocks), so the poster gap chart and the sample ad's path stay as they were.
"""

from __future__ import annotations

import csv
import re
from functools import lru_cache
from pathlib import Path

from . import paths
from .extract import _dictionary_hits, load_dictionary, split_sentences
from .similarity import embed_documents, similarity, tfidf_similarity

ROOT = paths.ROOT
DEMAND_CSV = paths.ROLE_SKILL_DEMAND   # role x skill x source x period (plan D6; data/2_demand/README.md)
# The poster counted the Seek ads on their raw text; the table recounts them on the cleaned text, 0.2 to
# 1.7 points higher for 26 skills (Python 82.8 -> 84.5). Its 148 shares replace the table's in _blocks().
POSTER_COUNTS_CSV = paths.SKILL_COUNTS
DEFAULT_ROLE = "Data Scientist"
N_ADS = 3204
DEFAULT_SOURCE, DEFAULT_PERIOD = "seek_2019_22", "2019-22"   # the full-text Data Scientist ads behind _demand()
# A role's demand_pct: the first of these sources with a block for the role ...
DEMAND_PRIORITY = ("jobspipe_2026", "adzuna_2026", "ats_2026", "data_jobs_2023", "seek_2019_22")
# ... except Data Scientist, which keeps the Seek ads (the poster numbers, the Robert Walters sample).
PINNED = {DEFAULT_ROLE: DEFAULT_SOURCE}
# demand_pct_2026: the first 2026 source, in the same order (JobsPipe, for every role today)
TREND_PRIORITY = tuple(s for s in DEMAND_PRIORITY if s.endswith("_2026"))
# recommend._weight's 2026 floor for a skill new since 2022: the 22 in-sample data roles of 2026, as
# skill_counts_2026.csv's pct_2026_all_low was, so the weights did not move with C2.
FLOOR_BLOCK = ("Data roles (mixed)", "recent_2024_26", "2026")
COUNTED = ("full_text", "tool_list", "search_count")   # text types with a share; taxonomy rows have none
MIXED = "(mixed)"                                      # "Data roles (mixed)": ads of several roles, not a role
# For captions: source -> (its name in a sentence, when its ads were posted or counted)
SOURCE_NAMES = {
    "seek_2019_22": ("Seek", "2019-22"),
    "jobspipe_2026": ("JobsPipe", "Sep-Oct 2026"),     # posted 23 Sep to 16 Oct
    "adzuna_2026": ("Adzuna", "16 Oct 2026"),          # live ads on the day of the search
    "ats_2026": ("job-board", "Aug-Oct 2026"),         # posted within 60 days of the 13 and 16 Oct fetches
    "data_jobs_2023": ("data_jobs", "2023"),
}
TEXT_KINDS = {"full_text": "full text", "tool_list": "the tools each ad lists",
              "search_count": "live ads, one phrase search per skill"}

SOFT_CATEGORIES = {"Professional"}        # real skills, but they do not map to subjects
# Left out of a role's 15 skills: soft skills, and certifications (the role page lists those itself;
# no subject teaches one). An ad that names one still shows it.
NOT_IN_PROFILE = SOFT_CATEGORIES | {"Certification"}
# The skill that names its whole category: asking for it is met in part by any skill in it.
UMBRELLA = {
    "Machine learning": "Machine learning",
    "Deep learning": "Deep learning",
    "Natural language processing": "NLP",
    "Cloud platforms": "Cloud",
    "Statistics": "Statistics",
    "Data visualisation": "Visualisation",
    "Computer vision": "Computer vision",
}
# A programming language is a named requirement: knowing Java is not partly knowing Python.
NOT_TRANSFERABLE = {"Programming"} | SOFT_CATEGORIES
# Dictionary skills ESCO has no concept for (normalise.py keeps the same list).
EMERGING_SEED = {"Large language models", "Generative AI"}


# --------------------------------------------------------------------------- lookups

def _rows(path: Path) -> list[dict]:
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(line for line in f if not line.startswith("#")))


@lru_cache(maxsize=1)
def _category() -> dict[str, str]:
    return {skill["canonical"]: skill["category"] for skill in load_dictionary()}


# --------------------------------------------------------------------------- demand

@lru_cache(maxsize=1)
def _blocks() -> dict[tuple[str, str, str], dict]:
    """(role, source, period) -> one counted block of role_skill_demand.csv: role, source, period,
    text_type, total_ads, shares {skill: pct} and lows {skill: pct_low}. Taxonomy rows have no share
    and are left out. The Data Scientist Seek block takes the poster's shares for its 148 skills
    (POSTER_COUNTS_CSV) and keeps the table's for the rest (Teradata, C#, ...)."""
    blocks: dict[tuple[str, str, str], dict] = {}
    for row in _rows(DEMAND_CSV):
        if row["text_type"] not in COUNTED or not row["pct"]:
            continue
        block = blocks.setdefault((row["role"], row["source"], row["period"]), {
            "role": row["role"], "source": row["source"], "period": row["period"], "text_type": row["text_type"],
            "total_ads": int(float(row["total_ads"])), "shares": {}, "lows": {}})
        block["shares"][row["skill"]] = float(row["pct"])
        if row["pct_low"]:
            block["lows"][row["skill"]] = float(row["pct_low"])
    seek = blocks.get((DEFAULT_ROLE, DEFAULT_SOURCE, DEFAULT_PERIOD))
    if seek and POSTER_COUNTS_CSV.exists():
        seek["shares"].update({row["skill"]: float(row["pct_ads"]) for row in _rows(POSTER_COUNTS_CSV)})
    return blocks


def _pick(role: str, sources: tuple[str, ...]) -> dict | None:
    """The role's block of the first of `sources` that has one (its latest period), or None."""
    for source in sources:
        found = [b for (r, s, _), b in _blocks().items() if r == role and s == source]
        if found:
            return max(found, key=lambda b: b["period"])
    return None


def demand_block(role: str = DEFAULT_ROLE, source: str | None = None, period: str | None = None) -> dict | None:
    """The block behind a role's `demand_pct`: Data Scientist's Seek ads, any other role's first source in
    DEMAND_PRIORITY. With `source` (and `period`), that block instead. None when there is none: the
    app then shows the role's core skills."""
    if source:
        return _pick(role, (source,)) if period is None else _blocks().get((role, source, period))
    pinned = (PINNED[role],) if role in PINNED else ()
    return _pick(role, pinned + DEMAND_PRIORITY)


def trend_block(role: str = DEFAULT_ROLE) -> dict | None:
    """The block behind `demand_pct_2026`: the role's first 2026 source. For every role but Data
    Scientist it is the demand block itself, so the two shares are equal."""
    return _pick(role, TREND_PRIORITY)


def block_meta(block: dict | None = None) -> dict:
    """The fields every gap row carries for its caption; default the Data Scientist Seek block."""
    block = block or demand_block() or {"source": DEFAULT_SOURCE, "period": DEFAULT_PERIOD,
                                        "total_ads": N_ADS, "text_type": "full_text"}
    return {"demand_source": block["source"], "demand_period": block["period"],
            "total_ads": block["total_ads"], "text_type": block["text_type"]}


def demand_caption(block: dict) -> str:
    """Where a block's shares come from: "71 JobsPipe Data Scientist ads, Sep-Oct 2026, full text"."""
    name, when = SOURCE_NAMES.get(block["source"], (block["source"], block["period"]))
    kind = TEXT_KINDS.get(block["text_type"], block["text_type"])
    return f"{block['total_ads']:,} {name} {block['role']} ads, {when}, {kind}"


def _demand() -> dict[str, float]:
    """Share of the 3,204 Seek Data Scientist ads 2019-22 naming each skill (the poster's 148 shares)."""
    block = _blocks().get((DEFAULT_ROLE, DEFAULT_SOURCE, DEFAULT_PERIOD))
    return block["shares"] if block else {}


def _trend(role: str) -> dict[str, float]:
    """skill -> share of the role's 2026 ads (trend_block). A full-text block looked for every dictionary
    skill, so one that no ad names is 0.0 there, not unknown."""
    block = trend_block(role)
    if block is None:
        return {}
    zeros = dict.fromkeys(_category(), 0.0) if block["text_type"] == "full_text" else {}
    return zeros | block["shares"]


def _demand_2026() -> dict[str, float]:
    """The 2026 share for an ad and for Data Scientist: the Data Scientist ads of the 2026 block (71 JobsPipe ads)."""
    return _trend(DEFAULT_ROLE)


def demand_2026_low() -> dict[str, float]:
    """Lower end of the 95% Wilson interval of the 2026 share over all 22 in-sample data roles
    (FLOOR_BLOCK, the numbers of skill_counts_2026.csv's `pct_2026_all_low`), not the 9 data
    scientists: one ad moves a share of 9 by 11 points. Even over 22 a share carries about +-20
    points; recommend() weights gaps by this conservative value. Kept on these 22 ads by C2 so the
    weights stay put: JobsPipe's 71 Data Scientist ads would raise Generative AI's floor from 4.7 to 14.4."""
    block = _blocks().get(FLOOR_BLOCK)
    return dict(block["lows"]) if block else {}


@lru_cache(maxsize=1)
def _aliases() -> dict[str, tuple[str, ...]]:
    return {skill["canonical"]: skill["aliases"] for skill in load_dictionary()}


def skill_query(label: str) -> str:
    """The text a skill is compared by: its name plus its dictionary aliases."""
    return ", ".join(dict.fromkeys([label, *_aliases().get(label, ())]))


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def _key(mention: dict) -> str:
    """What makes two mentions the same skill: dictionary name, else skill_id, else the words."""
    return mention.get("canonical") or mention.get("skill_id") or f"text:{slug(mention['text'])}"


def _group(mentions: list[dict]) -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = {}
    for mention in mentions:
        groups.setdefault(_key(mention), []).append(mention)
    return groups


def _evidence(mentions: list[dict]) -> str:
    """The sentence to show: the first full sentence, not a title line such as 'Data Scientist - Python, SQL'."""
    sentences = [m["sentence"] for m in mentions]
    return next((s for s in sentences if len(s.split()) >= 7), sentences[0])


def _is_soft(mention: dict) -> bool:
    return _category().get(mention.get("canonical")) in SOFT_CATEGORIES or mention.get("kind") == "soft"


# ----------------------------------------------------------------------------- match

def _related(skill: str, resume: dict[str, list[dict]], demand: dict[str, float] | None = None) -> str | None:
    """The resume skill that partly meets an umbrella skill (the most in-demand one), or None."""
    category = _category().get(skill)
    if category is None or category in NOT_TRANSFERABLE or UMBRELLA.get(skill) != category:
        return None
    demand = _demand() if demand is None else demand
    parts = [k for k in resume if k != skill and _category().get(k) == category]
    return max(parts, key=lambda k: demand.get(k, 0.0), default=None)


def match(ad_skills: list[dict], resume_skills: list[dict], include_soft: bool = False,
          demand: dict[str, float] | None = None, demand_2026: dict[str, float] | None = None,
          block: dict | None = None) -> list[dict]:
    """Return the `skills` list of the gap result (data contract section 2), most in-demand first.

    demand          skill -> share of ads, for `demand_pct`; default: the 3,204 Seek Data Scientist ads.
                    match_role() passes the role's own shares.
    demand_2026     skill -> 2026 share, for `demand_pct_2026`; default: the Data Scientist 2026 ads
                    when `demand` is the default too, else none.
    block           the demand block `demand` comes from (demand_block()); its source, period, number of
                    ads and text type are copied to every row for the app's caption. Default: Seek.
    """
    if demand_2026 is None:
        demand_2026 = _demand_2026() if demand is None else {}
    demand = _demand() if demand is None else demand
    meta = block_meta(block)
    resume = _group(resume_skills)
    resume_ids = {m["skill_id"]: key for key, ms in resume.items() for m in ms if m.get("skill_id")}
    out = []

    for key, mentions in _group(ad_skills).items():
        first = mentions[0]
        if not include_soft and _is_soft(first):
            continue
        canonical = first.get("canonical")
        label = canonical or first.get("skill_label") or first["text"]
        skill_id = first.get("skill_id") or (f"seed:{slug(canonical)}" if canonical
                                             else f"emerging:{slug(first['text'])}")
        vocab = first.get("vocab")
        emerging = vocab in ("emerging", "lightcast") if vocab else (canonical is None or canonical in EMERGING_SEED)

        # A shared skill_id counts only for a skill outside the dictionary: several dictionary skills
        # share one broad ESCO concept (PyTorch and matplotlib, Tableau and Power BI), so a resume
        # naming one must not count as having the other.
        same = key if key in resume else (None if canonical else resume_ids.get(first.get("skill_id")))
        related = None if same else (_related(canonical, resume, demand) if canonical else None)
        skill = {
            "skill_id": skill_id,
            "skill_label": label,
            "status": "have" if same else "partial" if related else "missing",
            "demand_pct": round(demand.get(canonical, 0.0), 1),
            "demand_pct_2026": demand_2026.get(canonical),
            **meta,
            "emerging": emerging,
            "ad_evidence": _evidence(mentions),
            "resume_evidence": _evidence(resume[same or related]) if (same or related) else None,
        }
        if related:
            skill["related_skill"] = related
        if all(m.get("method") == "llm" for m in mentions):
            skill["found_by"] = "llm"
        out.append(skill)
    return sorted(out, key=lambda s: -s["demand_pct"])


def soft_skills(ad_skills: list[dict], demand: dict[str, float] | None = None) -> list[str]:
    """Professional skills the ad names (communication, teamwork): shown, but not part of the gap list,
    most in-demand first by `demand` (default: the Seek Data Scientist ads; a role passes its own)."""
    demand = _demand() if demand is None else demand
    names = {m.get("canonical") or m["text"] for m in ad_skills if _is_soft(m)}
    return sorted(names, key=lambda k: (-demand.get(k, 0.0), k))


def _block(role: str) -> dict:
    """demand_block(role), or KeyError for a role with no counted block (unknown, or taxonomy rows only)."""
    block = demand_block(role)
    if block is None:
        raise KeyError(role)
    return block


def roles() -> list[dict]:
    """The roles with ad counts (all 11 since C2): name, number of ads behind the shares, source, period,
    text type. Data Scientist first, then most ads first."""
    names = {role for role, _, _ in _blocks() if not role.endswith(MIXED)}
    out = []
    for name in names:
        block = demand_block(name)
        if block:
            out.append({"role": name, "n_ads": block["total_ads"], "source": block["source"],
                        "period": block["period"], "text_type": block["text_type"]})
    return sorted(out, key=lambda r: (r["role"] != DEFAULT_ROLE, -r["n_ads"], r["role"]))


def role_demand(role: str = DEFAULT_ROLE) -> dict[str, float]:
    """skill -> share of the role's ads that ask for it: every skill of its demand block, not only the
    profile's 15, so _related() can rank the resume's part skills (Excel over Microsoft Office) as in
    ad mode. Data Scientist: the Seek shares of _demand()."""
    return _block(role)["shares"]


def role_profile(role: str = DEFAULT_ROLE, top_n: int = 15) -> list[dict]:
    """A role as skill mentions, ready for match(): its most-asked technical skills.

    Only dictionary skills (the table is counted with the same vocabulary) outside NOT_IN_PROFILE,
    most asked first (ties in the table's order). Raises KeyError for a role with no counted block.
    """
    block = _block(role)
    name, when = SOURCE_NAMES.get(block["source"], (block["source"], block["period"]))
    category = _category()
    mentions = []
    for skill, pct in sorted(block["shares"].items(), key=lambda kv: -kv[1]):
        if skill not in category or category[skill] in NOT_IN_PROFILE:
            continue
        mentions.append({
            "text": skill, "canonical": skill, "method": "dictionary",
            "sentence": f"Asked for in {pct:.0f}% of {block['total_ads']:,} {name} {role} ads ({when}).",
        })
        if len(mentions) == top_n:
            break
    return mentions


def match_role(resume_skills: list[dict], role: str = DEFAULT_ROLE, top_n: int = 15) -> list[dict]:
    """match() against a role instead of an ad: `demand_pct` is the share of the role's ads (demand_block),
    `demand_pct_2026` the share of its 2026 ads (trend_block), equal to `demand_pct` for every role
    whose demand block is already from 2026 (all but Data Scientist)."""
    return match(role_profile(role, top_n), resume_skills, demand=role_demand(role),
                 demand_2026=_trend(role), block=_block(role))


# ------------------------------------------------------ ranking resume evidence for a skill

RANK_METHODS = ("skills", "tfidf", "embed")


def rank_evidence(skill_label: str, resume_text: str, method: str = "skills") -> list[str]:
    """The resume's sentences, best evidence for `skill_label` first. For P@5 and MRR on the CV-JD pairs.

    "tfidf"   cosine of the skill (name + aliases) and each sentence, TF-IDF (baseline)
    "embed"   the same with sentence embeddings
    "skills"  what match() uses: sentences that name the skill first, then sentences that name a
              part of an umbrella skill (scikit-learn for machine learning), then the rest by TF-IDF
    Ties keep the order of the resume.
    """
    if method not in RANK_METHODS:
        raise ValueError(f"method must be one of {RANK_METHODS}, got {method!r}")
    sentences = list(dict.fromkeys(split_sentences(resume_text or "")))
    if not sentences:
        return []
    sims = similarity([skill_query(skill_label)], sentences, "tfidf" if method == "skills" else method)[0]
    if method == "skills":
        category = _category().get(skill_label)
        is_umbrella = category is not None and UMBRELLA.get(skill_label) == category
        phrase = re.compile(rf"(?<![A-Za-z0-9]){re.escape(skill_label)}(?![A-Za-z0-9])", re.IGNORECASE)

        def tier(sentence: str) -> int:
            named = {canonical for _, _, canonical in _dictionary_hits(sentence)}
            if skill_label in named or (skill_label not in _category() and phrase.search(sentence)):
                return 2
            if is_umbrella and any(_category().get(k) == category for k in named):
                return 1
            return 0
        tiers = [tier(s) for s in sentences]
        order = sorted(range(len(sentences)), key=lambda i: (-tiers[i], -sims[i], i))
    else:
        order = sorted(range(len(sentences)), key=lambda i: (-sims[i], i))
    return [sentences[i] for i in order]


# ----------------------------------------------------------- ranking ads for a resume

def skill_overlap(ad_skills: list[dict], resume_skills: list[dict]) -> float:
    """Demand-weighted share of the ad's skills the resume covers (have = 1, partial = 0.5), in [0, 1]."""
    skills = match(ad_skills, resume_skills)
    weights = [s["demand_pct"] + 1 for s in skills]          # +1 so 0% skills still count
    credit = [{"have": 1.0, "partial": 0.5, "missing": 0.0}[s["status"]] for s in skills]
    return sum(w * c for w, c in zip(weights, credit)) / sum(weights) if weights else 0.0


def score_matrix(resume_texts: list[str], ad_texts: list[str], method: str = "tfidf",
                 extract_method: str = "dictionary"):
    """How well each ad fits each resume: array [len(resume_texts), len(ad_texts)].

    "tfidf"   cosine of the two whole texts under TF-IDF (baseline)
    "embed"   cosine of mean sentence embeddings
    "skills"  skill_overlap() of the extracted skills (what the app shows)
    Rank a row to get the best ads for that resume; score it with P@5 and MRR.
    """
    import numpy as np

    from .extract import extract, split_sentences

    if method == "tfidf":
        return tfidf_similarity(list(resume_texts), list(ad_texts))
    if method == "embed":
        resumes = embed_documents([split_sentences(t) for t in resume_texts])
        ads = embed_documents([split_sentences(t) for t in ad_texts])
        return resumes @ ads.T
    if method == "skills":
        resumes = [extract(t, extract_method) for t in resume_texts]
        ads = [extract(t, extract_method) for t in ad_texts]
        return np.array([[skill_overlap(ad, resume) for ad in ads] for resume in resumes])
    raise ValueError(f'method must be "tfidf", "embed" or "skills", got {method!r}')
