# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Skillabus: exploratory data analysis
#
# 36118 Applied NLP, AT2 Part B · Van Thong (Role B, data) · updated 17 Oct 2026
#
# **Runs on committed files only** (everything under `data/`; every path comes from
# `src/skillabus/paths.py`), so it works on a fresh clone. Raw downloads are not needed; each
# section names the script that built its input. Figures for the report are written to
# `docs/figures/`.
#
# Each section answers a question the app depends on:
#
# 1. What data do we have, and what is each file for?
# 2. Is the ad text clean enough to extract skills from?
# 3. What do Australian employers ask for?
# 4. Can we trust the extractor?
# 5. Does the ranking hold on other platforms and in other markets?
# 6. What changed after 2022?
# 7. What does the UTS curriculum cover?
# 8. Are the resumes usable?
# 9. How far does ESCO reach?
# 10. Where does each of the 11 IT roles get its demand from, and what changed?
# 11. What this means for the app

# %%
import logging
import math
import re
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "data-eda" / "src"))
logging.getLogger("extract_skills").setLevel(logging.WARNING)

from extract_skills import build_patterns, extract  # noqa: E402
from skillabus import paths  # noqa: E402  (every data path in one place)

FIG = paths.FIGURES
FIG.mkdir(parents=True, exist_ok=True)

pd.set_option("display.max_colwidth", 80)
pd.set_option("display.width", 140)

# Team colours: teal = market / covered, copper = gap. Checked for colour-blind
# separation (OKLab dE 9.6 protan, 15.7 deutan, 27.2 tritan) and contrast on white.
TEAL, COPPER, INK, MUTED, GRID = "#0F6E68", "#B8541F", "#1B2530", "#5C6974", "#E3E8E6"
plt.rcParams.update({
    "font.size": 10, "axes.edgecolor": GRID, "axes.labelcolor": INK,
    "xtick.color": MUTED, "ytick.color": INK, "axes.spines.top": False,
    "axes.spines.right": False, "figure.dpi": 110, "savefig.dpi": 200,
    "savefig.bbox": "tight",
})

SEED = paths.SKILLS_SEED                    # the one dictionary the app uses
patterns = build_patterns(SEED)
seed = pd.read_csv(SEED, skiprows=1)         # skiprows, not comment="#": the file contains C#
cat = seed.set_index("canonical").category


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """95% Wilson interval for k of n, in percent."""
    p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return 100 * max(0, c - h), 100 * min(1, c + h)


def skill_shares(df: pd.DataFrame, text: str = "description", pats=patterns) -> pd.Series:
    """Percent of ads in df naming each skill."""
    long = extract(df, text, "ad_id", pats)
    return (100 * long.groupby("skill").ad_id.nunique() / len(df)).sort_values(ascending=False)


def spearman(a: pd.Series, b: pd.Series) -> tuple[float, int]:
    """Rank correlation over technical skills with a non-zero share (to 0.1%) in both corpora.

    This is the poster's definition, and it reproduces the poster's 0.819. A skill in 1
    of 3,204 ads rounds to 0.0% and is left out.
    """
    a, b = a.round(1), b.round(1)
    shared = [k for k in a.index.intersection(b.index)
              if cat.get(k) != "Professional" and a[k] > 0 and b[k] > 0]
    return float(np.corrcoef(a[shared].rank(), b[shared].rank())[0, 1]), len(shared)

# %% [markdown]
# ## 1. What data do we have?

# %%
seek = pd.read_csv(paths.SEEK_ADS, parse_dates=["listingDate"])
recent = pd.read_csv(paths.RECENT_ADS)
resumes = pd.read_csv(paths.RESUMES)
esco = pd.read_csv(paths.ESCO_SKILLS_CLEAN)
lookup = pd.read_csv(paths.ESCO_LABEL_LOOKUP)
label_sample = pd.read_csv(paths.LABEL_SAMPLE)
profiles = pd.read_csv(paths.SUBJECT_PROFILES, dtype={"subject_code": str})

inventory = pd.DataFrame([
    ("Seek Data Scientist ads", len(seek), "2019-22", "demand_pct (main demand)", "clean_seek.py"),
    ("Recent AU data roles", len(recent), "Jan 2024, Sept-Oct 2026", "demand_pct_2026, trend", "build_recent_sample.py"),
    ("Subject profile rows", len(profiles), f"{profiles.subject_code.nunique()} subjects, 2026",
     "recommend(), chat", "build_subject_profiles.py"),
    ("Resumes", len(resumes), "2021", "test inputs, CV-JD pairs", "clean_resumes.py"),
    ("ESCO skill concepts", len(esco), "v1.2.1", "normalise()", "clean_esco.py"),
    ("ESCO label lookup rows", len(lookup), "v1.2.1", "normalise()", "clean_esco.py"),
    ("Label sample (ads)", len(label_sample), "2019-22", "extraction test set", "make_label_sample.py"),
    ("Skill dictionary", len(seed), "v2", "extract() tier 1", "data/1_knowledge/skills/"),
    ("Prerequisite rows", len(pd.read_csv(paths.PREREQUISITES, dtype=str)), "2026",
     "recommend(): order, anti-requisites", "scrape_requisites.py"),
    ("Teaching sessions", len(pd.read_csv(paths.OFFERINGS, dtype=str)), "2026",
     "recommend(): when a subject runs", "scrape_requisites.py"),
    ("Role profile rows", len(pd.read_csv(paths.ROLE_PROFILES)), "2023, 7 roles",
     "role picker, match()", "build_role_profiles.py"),
    ("External course rows", len(pd.read_csv(paths.EXTERNAL_COURSES, dtype=str)), "Oct 2026, 56 courses",
     "recommend() tier 2", "external/ (Quan)"),
    # Added 15 Oct for the 11 IT roles (plan D4-D11); section 10 looks at them.
    ("Skill vocabulary", len(pd.read_csv(paths.SKILLS_VOCABULARY, dtype=str)), "15 Oct 2026",
     "replaces the dictionary (D5)", "build_vocabulary.py"),
    ("Role x skill demand rows", len(pd.read_csv(paths.ROLE_SKILL_DEMAND)), "2019-26, 11 roles",
     "the one demand table (D6)", "build_role_skill_demand.py"),
    ("Role occupation rows", len(pd.read_csv(paths.ROLE_OCCUPATIONS)), "ESCO, O*NET, ASC",
     "11 roles -> occupations (D4)", "build_occupation_skills.py"),
    ("Occupation skill rows", len(pd.read_csv(paths.OCCUPATION_SKILLS)), "ESCO, O*NET, ASC",
     "core skills per role (D4)", "build_occupation_skills.py"),
    ("Certifications", len(pd.read_csv(paths.CERTIFICATIONS)), "Oct 2026", "certifications per role (D11)", "by hand"),
    ("Self-study resources", len(pd.read_csv(paths.RESOURCES)), "Oct 2026", "self-study column (D9)", "by hand"),
    ("JobsPipe 2026 ads (skills, no text)", len(pd.read_csv(paths.JOBSPIPE_SKILLS)), "Sep-Oct 2026",
     "main demand, 11 roles", "fetch_jobspipe.py"),
    ("Seek 2020-21 IT ads (skills)", len(pd.read_csv(paths.SEEK_2020_21_SKILLS)), "2020-21",
     "pre-2022 baseline, 10 roles", "build_seek_it_2020_21.py"),
    ("2026 job-board ads with a role", len(pd.read_csv(paths.ATS_2026_ADS)), "Oct 2026",
     "second 2026 view", "classify_ats_roles.py"),
    ("Adzuna search counts", len(pd.read_csv(paths.ADZUNA_COUNTS)), "16 Oct 2026",
     "live counts, 11 roles", "count_role_skills_adzuna.py"),
    ("Role outlook (JSA)", len(pd.read_csv(paths.ROLE_OUTLOOK)), "2025-26", "shortage label per role", "by hand"),
    ("Student-reported taught skills", len(pd.read_csv(paths.UTS / "taught_skills_student_reported.csv")),
     "2025-26", "what subjects taught (D10)", "by hand, from Canvas"),
], columns=["data", "rows", "period", "used by", "built by"])
inventory

# %%
# The prerequisite file mixes three kinds of row: requisite items, anti-requisites, and one empty
# row for each subject with no rule. The report cites them separately.
req = pd.read_csv(paths.PREREQUISITES, dtype=str, keep_default_na=False)
rq, anti = req[req.kind == "requisite"], req[req.kind == "antirequisite"]
print(f"requisite items: {(rq.item != '').sum():,} for {rq[rq.item != ''].subject_code.nunique()} subjects; "
      f"subjects with no rule: {(rq.item == '').sum()}; "
      f"anti-requisite rows: {len(anti)} for {anti.subject_code.nunique()} subjects")

# %% [markdown]
# ### The main corpus: 3,204 Seek Data Scientist ads
#
# A published Kaggle dataset (nomilk); we did not scrape Seek. Checks that it is
# real rather than generated: dates, geography, employers and ad length should
# look like a labour market.

# %%
print(f"listing dates: {seek.listingDate.min():%b %Y} to {seek.listingDate.max():%b %Y}")
print(f"employers: {seek.company.nunique():,}  |  advertisers: {seek.advertiser.nunique():,}")
top10 = seek.company.value_counts().head(10)
print(f"top 10 employers hold {100 * top10.sum() / len(seek):.1f}% of ads")
L = seek.description.str.len()
print(f"ad length: median {int(L.median()):,} chars, 10th-90th percentile "
      f"{int(L.quantile(.1)):,}-{int(L.quantile(.9)):,}")
print(f"exact duplicate descriptions: {seek.description.duplicated().sum()}")
display(seek.listingDate.dt.year.value_counts().sort_index().rename("ads").to_frame().T)
display(seek.state.value_counts().head(6).rename("ads").to_frame().T)

# %% [markdown]
# The ads run Feb 2019 to Jan 2022, with only 90 in 2022, and no employer dominates.
# Many share their text exactly with another ad. Are those errors or re-listings?

# %%
dup = seek[seek.description.duplicated(keep=False)].assign(
    employer=lambda d: d.company.fillna(d.advertiser))   # recruiter ads often leave company blank
groups = dup.groupby("description").agg(company=("employer", "nunique"), date=("listingDate", "nunique"),
                                        city=("city", "nunique"))
print(f"unique ad texts: {seek.description.nunique():,} of {len(seek):,} listings")
print(f"duplicate groups: {len(groups):,} | same employer in {100 * (groups.company == 1).mean():.0f}% | "
      f"posted on another date in {100 * (groups.date > 1).mean():.0f}% | in another city in "
      f"{100 * (groups.city > 1).mean():.0f}%")

# %% [markdown]
# Every repeat comes from the same employer, re-posted later or in another city:
# ordinary job-board behaviour, not a data error. Counts below are per listing, as on
# the poster; section 3 checks that counting unique ads instead changes nothing.

# %% [markdown]
# ## 2. Is the ad text clean enough?
#
# The source dataset stripped HTML without putting spaces back, so list items
# welded together ("...Power BI and TableauSuperior..."). `clean_seek.py` repairs
# this using the dataset's second rendering of each ad as evidence: a join is split
# only where the desktop text shows a break, which leaves real words like
# JavaScript alone. The joins still left in the clean text should be real words:

# %%
joins = pd.Series([w for t in seek.description for w in re.findall(r"\b\w*[a-z][A-Z]\w*\b", t)])
print("most common remaining lower-to-upper joins:")
print(joins.value_counts().head(15).to_dict())

# %% [markdown]
# They are product names, not damage. What the repair changed, using the same
# 133-skill dictionary as the poster so the comparison is like for like:

# %%
poster = pd.read_csv(paths.SKILL_COUNTS_PRIMARY).set_index("skill").pct_ads   # raw text, Sept
clean_133 = skill_shares(seek.assign(ad_id=seek.ad_id), pats=build_patterns(paths.SKILLS_SEED_V1))
delta = (clean_133.reindex(poster.index).fillna(0) - poster).round(1)
rho, n = spearman(poster, clean_133)
print(f"rank correlation raw vs clean: {rho:.4f} over {n} skills")
print(f"skills that went down: {(delta < -0.05).sum()}  |  largest rise: {delta.max():.1f} pts ({delta.idxmax()})")
delta.sort_values(ascending=False).head(6).rename("change, pts").to_frame().T

# %% [markdown]
# ## 3. What do Australian employers ask for?
#
# From here on: the app's v2 dictionary (148 skills) on the clean text.

# %%
seek_ids = seek.assign(ad_id=seek.ad_id)
long_seek = extract(seek_ids, "description", "ad_id", patterns)
share = (100 * long_seek.groupby("skill").ad_id.nunique() / len(seek)).sort_values(ascending=False)
demand = share.rename("pct").to_frame().assign(category=lambda d: d.index.map(cat))
tech = demand[demand.category != "Professional"]
prof = demand[demand.category == "Professional"]
print("top professional skills:", prof.head(5).pct.round(1).to_dict())
print(f"technical skills in >=20% of ads: {(tech.pct >= 20).sum()}  |  in >=10%: {(tech.pct >= 10).sum()}  "
      f"|  in >=1%: {(tech.pct >= 1).sum()} of {len(seed)}")
tech.head(15).round(1)

# %% [markdown]
# The app's demand figures, `data/2_demand/skill_counts_v2.csv` (counted on the raw text in
# September), against Figure 3.1 (clean text): technical skills named in both.

# %%
v2 = pd.read_csv(paths.SKILL_COUNTS).set_index("skill").pct_ads
shared_v2 = [s for s in tech.index if v2.get(s, 0) > 0]
rho_v2 = np.corrcoef(v2[shared_v2].rank(), tech.pct[shared_v2].rank())[0, 1]
print(f"skill_counts_v2 vs Figure 3.1: rank correlation {rho_v2:.4f} over {len(shared_v2)} technical skills; "
      f"largest gap {(tech.pct[shared_v2] - v2[shared_v2]).abs().max():.1f} points")

# %%
top = tech.head(15).iloc[::-1]
fig, ax = plt.subplots(figsize=(7, 5))
ax.barh(top.index, top.pct, color=TEAL, height=0.68)
for y, v in enumerate(top.pct):
    ax.text(v + 1, y, f"{v:.0f}%", va="center", color=INK, fontsize=9)
ax.set_xlim(0, 100)
ax.set_xticks([])
ax.spines["bottom"].set_visible(False)
ax.tick_params(axis="y", length=0)
ax.set_title("Technical skills named in Australian Data Scientist ads", loc="left", color=INK, fontsize=12)
fig.subplots_adjust(bottom=0.06)
fig.text(0.01, 0.0, f"Seek Australia 2019-22, n = {len(seek):,} ads, clean text, {len(seed)}-skill dictionary",
         color=MUTED, fontsize=8)
fig.savefig(FIG / "fig1_top_skills.png")
plt.show()

# %%
uniq = seek_ids.drop_duplicates("description")
share_u = skill_shares(uniq)
r_u, n_u = spearman(share, share_u)
change = (share_u.reindex(share.index).fillna(0) - share).abs()
print(f"per listing (n = {len(seek):,}) vs per unique ad (n = {len(uniq):,}): rho {r_u:.4f} over {n_u} "
      f"technical skills, largest change {change.max():.1f} points")

# %% [markdown]
# How many skills does one ad ask for? This sets how many gaps a typical user sees.

# %%
tech_per_ad = long_seek[long_seek.category != "Professional"].groupby("ad_id").skill.nunique() \
    .reindex(seek.ad_id, fill_value=0)
print(f"technical skills per ad: median {tech_per_ad.median():.0f}, "
      f"interquartile {tech_per_ad.quantile(.25):.0f}-{tech_per_ad.quantile(.75):.0f}, "
      f"ads naming none: {(tech_per_ad == 0).sum()}")
ids = lambda s: set(long_seek[long_seek.skill == s].ad_id)
core = ids("Python") & ids("SQL") & ids("Statistics")
print(f"ads asking for Python AND SQL AND statistics: {100 * len(core) / len(seek):.1f}%")

# %% [markdown]
# ## 4. Can we trust the extractor?
#
# The Kaggle dataset ships the author's own flags for 25 tools on the same ads, so
# we can compare two independent extractors on all 3,204 ads (`validate_against_authorflags.py`).
# The author's flags are not ground truth, so this reports agreement (Cohen's kappa),
# not accuracy.

# %%
agree = pd.read_csv(paths.EXTRACTOR_AGREEMENT)
print(f"median kappa {agree.kappa.median():.3f} over {len(agree)} tools; "
      f"{(agree.kappa >= 0.6).sum()} at 0.60 or above (substantial)")
agree[["skill", "ours_pct", "theirs_pct", "agreement_pct", "kappa", "ours_only", "theirs_only"]]

# %% [markdown]
# Where the two disagree, which side is wrong? `glued_our_miss` = the term is in the
# ad but welded to the next word (our miss, on the raw text); `absent_their_fp` = the
# term is not in the ad at all (their flag cannot be right).

# %%
parts = pd.read_csv(paths.EXTRACTOR_AGREEMENT_DECOMPOSED)
print(f"their extra positives with the term absent from the ad: "
      f"{parts.absent_their_fp.sum():,} of {parts.theirs_only.sum():,}")
parts

# %% [markdown]
# Known blind spots of a dictionary, by design: a bare "R" matches "R&D" and a bare
# "Go" is the verb, so both are only counted in explicit forms and are under-counted.

# %%
demand.loc[demand.index.isin(["R", "Go", "Artificial intelligence"]), ["pct"]].round(1).T

# %% [markdown]
# **Two people labelling the same ads.** The 20 `double_label = y` ads were labelled by
# Hoai Thuong and Van Thong independently (`data/4_evaluation/labels/ad_skills.csv`, #55 and #85). Cohen's
# kappa with the evaluation harness's own function, every (ad, skill) pair one item. The
# harness command `python -m skillabus.evaluate kappa data/4_evaluation/labels/ad_skills.csv
# data/4_evaluation/labels/ad_skills.csv --a-name hoaithuongnguyen-uts --b-name tompham9016 --dictionary
# data/1_knowledge/skills/skills_seed_v2.csv` gives the "all labels" row; the "dictionary skills" row
# keeps only labels that are dictionary skills, since free-text labels cannot match between
# two people's wording.

# %%
from skillabus import evaluate as ev  # noqa: E402
LAB = str(paths.AD_SKILLS)
ann_a, ann_b = ev.load_ad_skills(LAB, "hoaithuongnguyen-uts"), ev.load_ad_skills(LAB, "tompham9016")
both_ads = sorted(set(ann_a) & set(ann_b))
dict_set = set(ev.load_dictionary(str(SEED)))
rows = []
for name, a, b in [("dictionary skills", {k: v & dict_set for k, v in ann_a.items()},
                    {k: v & dict_set for k, v in ann_b.items()}),
                   ("all labels", ann_a, ann_b)]:
    r = ev.annotator_agreement(a, b, both_ads, sorted(dict_set))
    rows.append((name, r["n_ads"], r["n_items"], round(r["kappa"], 3), r["both_yes"], r["a_only"], r["b_only"]))
pd.DataFrame(rows, columns=["labels compared", "ads", "items", "kappa", "both", "Hoai Thuong only", "Van Thong only"])

# %% [markdown]
# ## 5. Does the ranking hold elsewhere?
#
# Same 133-skill dictionary throughout, so each comparison measures the market, not
# the method. Each comparison changes something different.

# %%
p133 = build_patterns(paths.SKILLS_SEED_V1)
li_us = pd.read_csv(paths.SKILL_COUNTS_LINKEDIN_US).set_index("skill").pct_ads
gd_au = pd.read_csv(paths.SKILL_COUNTS_GLASSDOOR_AU).set_index("skill").pct_ads
jan24 = recent[(recent.period == "2024-01") & recent.full_text]
li_au24 = skill_shares(jan24, pats=p133)
checks = []
for name, s, n, changes in [
    ("Glassdoor Australia, 2022", gd_au, int(pd.read_csv(paths.SKILL_COUNTS_GLASSDOOR_AU).total_ads_in_sample[0]),
     "platform only"),
    ("LinkedIn US, 2023-24 (Data Scientist)", li_us, int(pd.read_csv(paths.SKILL_COUNTS_LINKEDIN_US).total_ads_in_sample[0]),
     "country and year"),
    ("LinkedIn Australia, Jan 2024 (data roles)", li_au24, len(jan24), "year and role mix"),
]:
    r, k = spearman(poster, s)
    checks.append((name, n, changes, round(r, 3), k))
pd.DataFrame(checks, columns=["compared with Seek AU 2019-22", "ads", "what differs", "Spearman rho", "shared skills"])

# %% [markdown]
# ## 6. What changed after 2022?
#
# `data/2_demand/skill_counts_2026.csv` (`recount_recent.py`): every skill in three
# periods, same method. Adzuna rows are excluded because the API cuts their text at
# 500 characters. A 2026 job-board ad counts only if it is `in_sample` (posted within 60
# days of its snapshot, at most 3 per employer and role group; `build_recent_sample.py`).
# `pct_2026` is the data-scientist titles, like the Seek file; `pct_2026_all` adds the
# other data roles. Both samples are small, so intervals are wide.

# %%
c26 = pd.read_csv(paths.SKILL_COUNTS_2026)
LLM = ["Large language models", "Generative AI", "Prompt engineering", "RAG",
       "LangChain", "Vector databases", "Hugging Face", "Transformers"]
c26[c26.skill.isin(LLM)][["skill", "pct_2019_22", "pct_2024_01", "n_2026", "pct_2026",
                          "pct_2026_low", "pct_2026_high", "pct_2026_all"]].sort_values("n_2026", ascending=False)

# %% [markdown]
# Skills whose 2019-22 share lies outside the 95% interval of the 2026 data-scientist
# share (technical skills, at least 3 of the 2026 ads, or a 2019-22 share above 20%):

# %%
tech26 = c26[c26.category != "Professional"].copy()
moved = tech26[((tech26.pct_2019_22 < tech26.pct_2026_low) & (tech26.n_2026 >= 3))
               | ((tech26.pct_2019_22 > tech26.pct_2026_high) & (tech26.pct_2019_22 > 20))]
moved = moved.assign(direction=np.where(moved.pct_2026 > moved.pct_2019_22, "up", "down"))
moved[["skill", "direction", "pct_2019_22", "pct_2024_01", "n_2026", "pct_2026", "pct_2026_low",
       "pct_2026_high", "pct_2026_all"]].sort_values(["direction", "pct_2026"], ascending=[False, False])

# %%
full = recent[recent.full_text]
y26 = full[full.period.astype(str).str.startswith("2026") & full.in_sample]
long_recent = extract(full, "description", "ad_id", patterns)
llm_ids = set(long_recent[long_recent.skill.isin(LLM)].ad_id) | set(long_seek[long_seek.skill.isin(LLM)].ad_id)
periods = [("2019-22\nSeek", seek_ids), ("Jan 2024\nLinkedIn", full[full.period == "2024-01"]),
           ("2026 job boards\ndata scientists", y26[y26.role_group == "data scientist"]),
           ("2026 job boards\nall data roles", y26)]
rows = []
for label, d in periods:
    k = d.ad_id.isin(llm_ids).sum()
    lo, hi = wilson(k, len(d))
    rows.append((label.replace("\n", " "), len(d), k, 100 * k / len(d), lo, hi))
trend = pd.DataFrame(rows, columns=["period", "ads", "with LLM-era skill", "pct", "low", "high"])
trend.round(1)

# %%
fig, ax = plt.subplots(figsize=(7.6, 3.8))
x = np.arange(len(trend))
ax.errorbar(x, trend.pct, yerr=[trend.pct - trend.low, trend.high - trend.pct], fmt="none",
            ecolor=MUTED, elinewidth=1.5, capsize=4)
ax.plot(x, trend.pct, "o", color=TEAL, markersize=9)
for i, r in trend.iterrows():
    ax.text(i + 0.08, r.pct, f"{r.pct:.0f}%  ({r['with LLM-era skill']} of {r.ads:,})", va="center",
            color=INK, fontsize=9)
ax.set_xticks(x, ["2019-22\nSeek", "Jan 2024\nLinkedIn", "2026\ndata scientists", "2026\nall data roles"])
ax.set_ylim(-3, 100)
ax.set_xlim(-0.4, 3.9)
ax.set_ylabel("ads naming an LLM-era skill (%)")
ax.yaxis.grid(True, color=GRID)
ax.set_axisbelow(True)
ax.set_title("LLM-era skills in Australian data ads", loc="left", color=INK, fontsize=12)
fig.text(0.01, -0.06, "LLMs, generative AI, prompt engineering, RAG, LangChain, vector databases, Hugging Face, "
         "transformers. Bars: 95% Wilson interval.", color=MUTED, fontsize=8)
fig.savefig(FIG / "fig2_llm_trend.png")
plt.show()

# %% [markdown]
# **Is that just the role mix?** The 2026 data roles include AI and ML engineers,
# whose ads mention LLMs by definition. Splitting the in-sample ads by title:

# %%
full = full[full.in_sample].assign(ai_title=full.title.str.contains(r"\bAI\b|machine learning|\bML\b|research scien",
                                                    case=False))
split = (full.assign(llm=full.ad_id.isin(llm_ids))
             .groupby(["period", "ai_title"]).llm.agg(ads="size", with_llm="sum"))
split["pct"] = (100 * split.with_llm / split.ads).round(1)
split

# %% [markdown]
# New tools that are not in our dictionary at all, by period. These are the
# "emerging" skills the app has to tag rather than look up:

# %%
NEW_TOOLS = ["LangGraph", "LangSmith", "LlamaIndex", "GraphRAG", "DeepSpeed", "vLLM", "Ollama",
             "OpenAI", "Anthropic", "Claude", "Gemini", "Bedrock", "ChatGPT", "Copilot"]
def mentions(d, term):
    return int(d.description.str.contains(rf"(?<![A-Za-z]){re.escape(term)}(?![A-Za-z])", regex=True).sum())
new = pd.DataFrame({label.replace("\n", " "): [mentions(d, t) for t in NEW_TOOLS] for label, d in periods},
                   index=NEW_TOOLS)
in_dict = set(seed.canonical.str.lower())
new[new.sum(axis=1) > 0].assign(in_dictionary=lambda d: [t.lower() in in_dict for t in d.index])

# %% [markdown]
# ## 7. What does the UTS curriculum cover?
#
# `data/1_knowledge/uts/subject_profiles.csv` (`build_subject_profiles.py`): one row per
# learning objective, assessment task, weekly topic or description sentence.

# %%
profiles["mdsi"] = profiles.course.fillna("").str.contains("C04372")
N_SUB = profiles.subject_code.nunique()
layer_table = profiles.pivot_table(index="mdsi", columns="layer", values="text", aggfunc="size", fill_value=0)
layer_table.index = layer_table.index.map({True: "MDSI (19 subjects)", False: "other courses"})
display(layer_table)
mdsi = profiles[profiles.mdsi]
per_subject = mdsi.pivot_table(index=["subject_code", "subject_name"], columns="layer", values="text",
                               aggfunc="size", fill_value=0)
print("MDSI subjects missing a layer:")
per_subject[(per_subject == 0).any(axis=1)]

# %% [markdown]
# Coverage of market demand: for each of the 25 most-demanded technical skills, how
# many subjects name it, and is one of them in MDSI?

# %%
prof_ids = profiles.reset_index().rename(columns={"index": "ad_id"})
long_prof = extract(prof_ids, "text", "ad_id", patterns).merge(
    prof_ids[["ad_id", "subject_code", "mdsi"]], on="ad_id")
top25 = tech.head(25).copy()
top25["subjects"] = [long_prof[long_prof.skill == s].subject_code.nunique() for s in top25.index]
top25["mdsi_subjects"] = [long_prof[(long_prof.skill == s) & long_prof.mdsi].subject_code.nunique()
                          for s in top25.index]
print(f"taught by at least one of the {N_SUB} subjects: {(top25.subjects > 0).sum()} of 25  |  "
      f"by an MDSI subject: {(top25.mdsi_subjects > 0).sum()} of 25")
print(f"not taught anywhere in the {N_SUB}:", list(top25[top25.subjects == 0].index))
top25.round(1)

# %% [markdown]
# Every dictionary skill, not only the top 25: which ones no subject names at all? These are
# the gaps the second tier (`external_courses.csv`) has to fill. Same extractor as above.

# %%
named = set(long_prof.skill)
unnamed = seed[~seed.canonical.isin(named)]
unnamed_tech = unnamed[unnamed.category != "Professional"]
print(f"dictionary skills named by no subject: {len(unnamed)} of {len(seed)} "
      f"({len(unnamed_tech)} of {(seed.category != 'Professional').sum()} technical)")
print("most demanded of them:", list(tech[tech.index.isin(unnamed_tech.canonical)].head(10).index))
# clean() writes every spelling of the tool as SPARKPlus, so this finds them all and never Apache Spark.
sparkplus = profiles[profiles.text.str.contains(r"(?i)sparkplus")]
print(f"subjects naming the SPARKPlus peer-review tool: {sparkplus.subject_code.nunique()}; "
      f"subjects the extractor reads as Apache Spark: {sorted(long_prof[long_prof.skill == 'Spark'].subject_code.unique())}")

# %% [markdown]
# The Handbook is not the whole curriculum. Students report what their subjects actually
# taught (plan D10, `taught_skills_student_reported.csv`, skill names only, from Canvas). How
# many of the skills the Handbook never names do those reports cover? So far two students have
# reported on nine MDSI subjects, so this is a lower bound on what UTS teaches.

# %%
taught = pd.read_csv(paths.UTS / "taught_skills_student_reported.csv", dtype=str, keep_default_na=False)
print(f"student-reported rows: {len(taught)} for {taught.subject_code.nunique()} subjects "
      f"from {taught.collected_by.nunique()} student(s)")
reported = set(taught.skill)
filled = unnamed_tech[unnamed_tech.canonical.isin(reported)]
print(f"technical skills the Handbook never names but a student reports as taught: "
      f"{len(filled)} of {len(unnamed_tech)}")
print("most demanded of them:", list(tech[tech.index.isin(filled.canonical)].head(10).index))
print("still unreported:", list(tech[tech.index.isin(unnamed_tech.canonical) & ~tech.index.isin(reported)].head(8).index))

# %%
d = top25.iloc[::-1]
fig, ax = plt.subplots(figsize=(7.2, 7))
colors = [TEAL if s > 0 else COPPER for s in d.subjects]
ax.barh(d.index, d.pct, color=colors, height=0.68)
for y, (v, m, s) in enumerate(zip(d.pct, d.mdsi_subjects, d.subjects)):
    note = "named by no UTS subject" if s == 0 else (f"{s} subject{'s' if s > 1 else ''}" + (" incl. MDSI" if m else ""))
    ax.text(v + 1, y, f"{v:.0f}%  ·  {note}", va="center", color=INK, fontsize=8)
ax.set_xlim(0, 120)
ax.set_xticks([])
ax.spines["bottom"].set_visible(False)
ax.tick_params(axis="y", length=0)
ax.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=TEAL), plt.Rectangle((0, 0), 1, 1, color=COPPER)],
          labels=["named in a UTS subject's text", f"named in none of the {N_SUB} subjects"], frameon=False,
          loc="lower right", fontsize=8)
ax.set_title("Market demand against the UTS curriculum", loc="left", color=INK, fontsize=12)
fig.subplots_adjust(bottom=0.05)
fig.text(0.01, 0.0, f"Bar = share of 3,204 Seek ads 2019-22. Subjects: {N_SUB} UTS Handbook 2026 subjects, "
         "learning objectives, assessments, topics and descriptions.", color=MUTED, fontsize=8)
fig.savefig(FIG / "fig3_subject_coverage.png")
plt.show()

# %% [markdown]
# The marker's example: does 36118 teach LLMs, and does any subject teach the LLM
# toolchain?

# %%
for term, pat in {"large language models": r"large language model|\bLLMs?\b",
                  "generative AI": r"generative a\.?i\b",
                  "prompt engineering": r"prompt engineering",
                  "RAG": r"retrieval[- ]augmented|\bRAG\b",
                  "transformers / BERT / GPT": r"\btransformers?\b|\bBERT\b|\bGPT\b"}.items():
    hit = profiles[profiles.text.str.contains(pat, case=False, regex=True)]
    where = ", ".join(f"{r.subject_code} ({r.layer})" for r in hit.itertuples()) or f"none of the {N_SUB} subjects"
    print(f"{term:26s} {where}")

# %% [markdown]
# ## 8. Are the resumes usable?
#
# `resumes_us_2021_clean.csv` (`clean_resumes.py`): emails, phones, URLs and names
# masked. There is no data-science category, so `n_data_skills` counts how many of
# six core data skills each resume names.

# %%
print(f"resumes: {len(resumes):,} in {resumes.category.nunique()} categories")
masks = {m: int(resumes.resume_text.str.count(re.escape(m)).sum()) for m in ["[NAME]", "[EMAIL]", "[PHONE]", "[URL]"]}
print("masked tokens:", masks)
print(f"length: median {int(resumes.resume_text.str.len().median()):,} chars")
display(resumes.n_data_skills.value_counts().sort_index().rename("resumes").to_frame().T)
print("categories of resumes with 2+ data skills:")
resumes[resumes.n_data_skills >= 2].category.value_counts().head(8).to_frame().T

# %% [markdown]
# ## 9. How far does ESCO reach?

# %%
mapping = pd.read_csv(paths.SKILL_TO_ESCO_V1)
mapped = (mapping.esco_uri.fillna("") != "").sum()
amb = lookup[lookup.ambiguous]
print(f"ESCO: {len(esco):,} concepts, {lookup.label.nunique():,} distinct labels")
print(f"our dictionary mapped by exact label: {mapped} of {len(mapping)} ({mapped / len(mapping):.0%})")
print(f"labels pointing at more than one concept: {amb.label.nunique():,} "
      f"({100 * amb.label.nunique() / lookup.label.nunique():.1f}%)")
probe = ["sql", "python (computer programming)", "machine learning", "deep learning", "tableau",
         "data visualisation", "large language models", "power bi"]
lookup[lookup.label.isin(probe)][["label", "preferred_label", "label_type", "ambiguous"]]

# %% [markdown]
# ## 10. Where does each of the 11 IT roles get its demand from, and what changed?
#
# From 15 Oct the app covers 11 IT roles in five families (plan D4-D6), not only Data
# Scientist. Every role's demand is in one table, `role_skill_demand.csv` (role x skill x source
# x period, all skills on the new vocabulary). Its sources differ in kind (full ad text, tool
# lists, occupation taxonomies), so a share is only read next to its source, period, n and text
# type.

# %%
from skillabus.match import DEMAND_PRIORITY  # noqa: E402  (the app's order of sources for a role's demand)

demand = pd.read_csv(paths.ROLE_SKILL_DEMAND)
role_occ = pd.read_csv(paths.ROLE_OCCUPATIONS)
family = role_occ.drop_duplicates("role").set_index("role").role_family
ad_rows = demand[demand.role.isin(family.index) & (demand.text_type != "taxonomy")]
ads_per_source = ad_rows.groupby(["role", "source"]).total_ads.first().unstack()
main_source = ads_per_source.apply(lambda r: next((s for s in DEMAND_PRIORITY if pd.notna(r.get(s))), None), axis=1)
role_table = pd.DataFrame({"family": family, "main source": main_source}).join(
    ads_per_source[[c for c in ["jobspipe_2026", "adzuna_2026", "ats_2026", "seek_2020_21", "data_jobs_2023", "seek_2019_22"]
                    if c in ads_per_source]].astype("Int64"))
jp = role_table.jobspipe_2026
print(f"{len(role_table)} roles; main source (the app's DEMAND_PRIORITY): {main_source.value_counts().to_dict()}")
print(f"JobsPipe 2026: {int(jp.sum())} ads, {int(jp.min())}-{int(jp.max())} per role; "
      f"Seek 2020-21 IT ads: {int(role_table.seek_2020_21.sum())} for {role_table.seek_2020_21.notna().sum()} roles")
print("occupation links (exact / close / broad):",
      {s: role_occ[role_occ.source == s].match.value_counts().to_dict() for s in ("esco", "onet", "asc")})
role_table.sort_values("family")

# %%
# The top skills of each role in its main source (JobsPipe 2026 for all 11 today).
for role, r in role_table.sort_values("family").iterrows():
    top = ad_rows[(ad_rows.role == role) & (ad_rows.source == r["main source"])].nlargest(5, "pct")
    print(f"{role:30} {r['main source']} (n = {int(top.total_ads.iloc[0])}): "
          + ", ".join(f"{s} {p:.0f}%" for s, p in zip(top.skill, top.pct)))

# %% [markdown]
# **What changed for Data Scientist.** The same role, the same matcher and vocabulary, two
# periods: the 3,204 Seek ads of 2019-22 and the JobsPipe ads of 2026 (n in the legend). The seven technical
# skills that rose most, the five that fell most, and the four that lead both periods.

# %%
ds = demand[(demand.role == "Data Scientist") & demand.source.isin(["seek_2019_22", "jobspipe_2026"])]
shift = ds.pivot_table(index="skill", columns="source", values="pct").fillna(0.0)
shift["change"] = shift.jobspipe_2026 - shift.seek_2019_22
cats = pd.read_csv(paths.SKILLS_VOCABULARY, dtype=str, keep_default_na=False).set_index("label").category
technical = shift[~shift.index.map(cats).isin(["Professional", "ESCO core skill", "Certification"])]
core = ["Python", "SQL", "Machine learning", "Statistics"]
picked = set(technical.nlargest(7, "change").index) | set(technical.nsmallest(5, "change").index) | set(core)
show = shift.loc[sorted(picked, key=lambda k: shift.change[k])]
n_old = int(ds[ds.source == "seek_2019_22"].total_ads.iloc[0]); n_new = int(ds[ds.source == "jobspipe_2026"].total_ads.iloc[0])
print(show.round(1).to_string())

fig, ax = plt.subplots(figsize=(7.2, 0.34 * len(show) + 1.1))
y = np.arange(len(show))
ax.hlines(y, show.seek_2019_22, show.jobspipe_2026, color=GRID, lw=2, zorder=1)
ax.scatter(show.seek_2019_22, y, s=46, color=MUTED, zorder=2, label=f"2019-22 Seek (n = {n_old:,})")
ax.scatter(show.jobspipe_2026, y, s=46, color=TEAL, zorder=3, label=f"2026 JobsPipe (n = {n_new})")
for yi, (old, new) in enumerate(zip(show.seek_2019_22, show.jobspipe_2026)):
    ax.text(max(old, new) + 1.5, yi, f"{new:.0f}%", va="center", fontsize=8, color=INK)
ax.set_yticks(y, show.index)
ax.set_xlim(0, 100)
ax.set_xlabel("share of Data Scientist ads naming the skill (%)")
ax.grid(axis="x", color=GRID, lw=0.6)
ax.legend(loc="lower right", frameon=False, fontsize=8)
fig.savefig(FIG / "fig4_ds_2019_vs_2026.png")
plt.show()

# %% [markdown]
# **The vocabulary (D5).** ESCO is the base; the team adds the skills ESCO lacks or names only
# as a wider concept. The report's headline count is the vocabulary builder's own: detection
# skills whose ESCO link is "broad" or "none" and that at least 3 Australian ads from at least 2
# employers name (`vocabulary_ad_counts.csv`).

# %%
import build_vocabulary  # noqa: E402  (data-eda/src)

vocab = pd.read_csv(paths.SKILLS_VOCABULARY, dtype=str, keep_default_na=False)
head = build_vocabulary.headline(vocab, build_vocabulary.load_counts(build_vocabulary.COUNTS))
kinds = vocab.category.map(lambda c: c if c in ("ESCO core skill", "Certification") else "skill or tool")
print(f"vocabulary: {len(vocab)} rows {kinds.value_counts().to_dict()}; "
      f"in the old dictionary: {vocab.label.isin(seed.canonical).sum()}")
print("ESCO link:", vocab.esco_match.value_counts().to_dict())
print(f"skills the Australian ads ask for that ESCO lacks: {head['n']} "
      f"({head['dictionary']} from the dictionary, {head['added']} added for IT)")
certs, store = pd.read_csv(paths.CERTIFICATIONS), pd.read_csv(paths.RESOURCES)
print(f"certifications: {len(certs)} from {certs.vendor.nunique()} vendors; Adzuna counts filled: "
      f"{certs.au_ads_count.notna().sum()}")
print(f"self-study resources: {len(store)} from {store.provider.nunique()} providers; cost {store.cost.value_counts().to_dict()}")

# %% [markdown]
# ## 11. What this means for the app
#
# | # | Finding | Evidence | For the app |
# |---|---|---|---|
# | 1 | A small core, then a long tail | Python, ML, SQL, statistics lead; few other skills pass 30% | gap charts are dominated by 3-4 skills; rank the tail by demand, not alphabetically |
# | 1b | 697 listings are re-listings | 2,507 unique texts; per-listing and per-ad rankings agree (section 3) | keep n = 3,204 listings, and say so |
# | 2 | The extractor agrees with an independent one | median kappa 0.637 over 14 tools on all 3,204 ads | dictionary tier is a defensible baseline |
# | 3 | The ranking is not a Seek artefact | rank correlation 0.75 with Glassdoor Australia (same years), 0.82 with LinkedIn US; 0.61 with LinkedIn Australia 2024, an engineer-heavy mix | demand_pct can stand for "the Data Scientist market" |
# | 4 | The LLM era arrived after 2022 | Data Scientist: large language models 0% (Seek 2019-22) -> 36% of 89 JobsPipe ads (2026), generative AI 26%, AI agents 22%; Spark, Hadoop, Scala fall (section 10); 61% of ML Engineer ads name LLMs | show the 2019-22 share as the trend; flag LLM skills as emerging |
# | 5 | 2026 demand is large enough per role | JobsPipe: 1,932 ads, 89-216 per role (section 10); the 22-ad job-board sample of section 6 is kept for its trend only | weigh gaps by JobsPipe 2026 (match.DEMAND_PRIORITY); show n with every share (about +/-10 points) |
# | 6 | Every role now has full-text ads | JobsPipe 2026 for all 11 roles, Seek 2020-21 for 10, 2023 tool lists for 7 (section 10) | role demand from role_skill_demand.csv; tool lists only as a cross-check |
# | 7 | The curriculum names most demand | 24 of the top 25 technical skills named by at least one of 360 subjects, 15 in MDSI; Scala in none; Spark, Hadoop only in 94693; two students' reports cover 28 of the 61 technical skills the Handbook never names (section 7) | named is not taught in depth; external courses cover the 62 skills no subject names; add students' reports as a second source of what is taught |
# | 8 | Subject text is uneven | assessment layer for 326 of 360 subjects; 9 MDSI subjects have no topic list, 3 have description only | thin subjects rank low for lack of text, not content |
# | 9 | Few resumes look like data profiles | 125 of 2,481 with 2+ data skills; none in a data category | draw CV-JD pairs from those 125 only |
# | 10 | ESCO reaches little of the modern stack | 36% of our dictionary maps; 716 ambiguous labels incl. "sql"; 145 skills Australian ads ask for are missing from ESCO or only broad there (section 10) | normalise() needs the emerging tag and a tie-break for ambiguous labels; the vocabulary keeps ESCO as the base and adds the rest with a reason |
# | 11 | Eleven roles, four kinds of evidence | full text (JobsPipe 2026, Seek), search counts (Adzuna), tool lists (data_jobs 2023), taxonomies (ESCO, O*NET); rankings agree across them at rho 0.40-0.97 (section 10) | show source, period, n and text type with every share; never compare shares across kinds |
#
# **Limitations to state in the report:** the main corpus is 2019-22 (Feb 2019 to
# Jan 2022), Data Scientist titles only, and 22% re-listings; 2026 demand rests on 89-216 JobsPipe ads per role
# (about +/-10 points), and the 2019-22 trend exists for Data Scientist only;
# resumes are US 2021 and de-identified rather than anonymous; subject profiles come
# from the public handbook and are uneven; matching is by keyword; ESCO coverage of the modern
# stack is low.
