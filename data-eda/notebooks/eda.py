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
# # MDSI Skills Map — exploratory data analysis
#
# 36118 Applied NLP, AT2. Role B (data and EDA).
#
# This notebook answers five questions and produces the two figures used on the
# poster. Every number traces to a file in `data/raw/` — see `DATASETS.md` for
# provenance and `HOW_TO_USE_DATA.txt` for what each file is for.
#
# 1. What is in the corpus?
# 2. What skills does the Australian market ask for?
# 3. Does that ranking hold in another market?
# 4. Which skills are missing because of *when* we sampled?
# 5. Where are the gaps between the market and the UTS curriculum?

# %%
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
RAW = ROOT / "data" / "raw"
sys.path.insert(0, str(ROOT / "src"))

pd.set_option("display.max_colwidth", 90)
print("data folder:", RAW)

# %% [markdown]
# ## 1. The corpus
#
# The primary corpus is Seek Australia ads whose title contains "Data Scientist".
# It comes from a published Kaggle dataset — we did not scrape Seek, which their
# terms forbid.

# %%
ads = pd.read_csv(RAW / "jobs_au_seek_datascientist_2019-2022.csv", low_memory=False)
ads["listingDate"] = pd.to_datetime(ads["listingDate"], errors="coerce")

print(f"ads:            {len(ads):,}")
print(f"unique employers: {ads['company'].nunique():,}")
print(f"date range:     {ads.listingDate.min():%Y-%m} to {ads.listingDate.max():%Y-%m}")
print(f"description:    median {int(ads.description.str.len().median()):,} chars, "
      f"min {ads.description.str.len().min():,}, max {ads.description.str.len().max():,}")

# %% [markdown]
# Two checks that this is real data rather than a generated dataset: the state
# distribution should look like the Australian labour market, and description
# lengths should vary the way human-written ads do.

# %%
display(ads.state.value_counts().head(6).rename("ads").to_frame())
display(ads.listingDate.dt.year.value_counts().sort_index().rename("ads").to_frame())

# %% [markdown]
# NSW and Victoria dominate, which matches where Australian data roles actually
# sit. Length varies from a few hundred to 17k characters — synthetic corpora are
# far more uniform than this.

# %% [markdown]
# ## 2. What the market asks for
#
# Extraction is dictionary-based: `config/skills_seed.csv` holds 133 skills with
# aliases, tuned to how ads actually write. This is the *traditional* arm of the
# traditional-vs-neural comparison; every match traces back to a literal string,
# so it is fully inspectable.

# %%
from extract_skills import build_patterns, extract, summarise  # noqa: E402

patterns = build_patterns(ROOT / "config" / "skills_seed.csv")
long = extract(ads.assign(_id=ads.ad_id), "description", "_id", patterns)
counts = summarise(long, n_ads=len(ads))

counts.head(15)[["skill", "category", "n_ads", "pct_ads"]]

# %% [markdown]
# Python is in 83% of ads, SQL 57%, statistics 56% — then a long tail where no
# single tool passes 26%. That shape matters for the product: beyond three
# near-universal skills, demand fragments, which is exactly why a student cannot
# eyeball what to learn next.

# %%
tech = counts[counts.category != "Professional"]
prof = counts[counts.category == "Professional"]

print("Top technical skills")
print(tech.head(10)[["skill", "pct_ads"]].to_string(index=False))
print("\nTop professional skills")
print(prof.head(5)[["skill", "pct_ads"]].to_string(index=False))

# %% [markdown]
# **Communication appears in 28% of ads — more often than Tableau, AWS or Hadoop.**
# Professional skills are excluded from the poster chart because they do not map
# to subjects, which is what the product does. That is an editorial choice, so we
# state it in the caption rather than hide it.

# %% [markdown]
# ### Sanity checks
#
# Dumb string matching fails in predictable ways. These are the checks worth
# running before any number goes on a poster.

# %%
print("Skills above 85% (suspect over-matching):")
print(counts[counts.pct_ads > 85][["skill", "pct_ads"]].to_string(index=False) or "  none")

print("\nKnown under-counts by design:")
print(counts[counts.skill.isin(["R", "Go"])][["skill", "pct_ads"]].to_string(index=False))
print("  A bare 'R' matches 'R&D' and a bare 'Go' matches the verb, so the seed")
print("  dictionary only catches explicit forms. True share is higher than shown.")

# %% [markdown]
# ## 3. Does the ranking hold in another market?
#
# LinkedIn's US ads carry full text, so the *same* extractor runs on them. That is
# what makes this comparison legitimate — a corpus of pre-extracted skills would
# only tell us how two extractors differ.

# %%
us = pd.read_csv(RAW / "jobs_us_linkedin_2023-2024.csv", low_memory=False,
                 usecols=["job_id", "title", "description"])
us_ds = us[us.title.str.contains(r"data scientist", case=False, na=False)]
print(f"US Data Scientist ads: {len(us_ds):,}")

us_long = extract(us_ds, "description", "job_id", patterns)
us_counts = summarise(us_long, n_ads=len(us_ds))

cmp = (counts[["skill", "category", "pct_ads"]].rename(columns={"pct_ads": "AU_2019_22"})
       .merge(us_counts[["skill", "pct_ads"]].rename(columns={"pct_ads": "US_2023_24"}),
              on="skill", how="outer").fillna(0))
cmp["diff"] = (cmp.US_2023_24 - cmp.AU_2019_22).round(1)

both = cmp[(cmp.category != "Professional") & (cmp.AU_2019_22 > 0) & (cmp.US_2023_24 > 0)]
rho = np.corrcoef(both.AU_2019_22.rank(), both.US_2023_24.rank())[0, 1]
print(f"shared technical skills: {len(both)}")
print(f"Spearman rank correlation: {rho:.3f}")

cmp[cmp.category != "Professional"].nlargest(8, "AU_2019_22")[
    ["skill", "AU_2019_22", "US_2023_24", "diff"]]

# %% [markdown]
# Rank correlation of 0.82 across 100 shared skills, with the top five within
# about three points of each other. Two continents, two job boards, two time
# windows — and the core ranking holds. That validates building the product on
# the larger Australian corpus.

# %% [markdown]
# ## 4. The recency gap, measured
#
# The Australian ads are 2019–2022, which predates the LLM tooling wave. Rather
# than concede that as a limitation, we can measure it.

# %%
llm = ["Large language models", "Prompt engineering", "RAG", "LangChain",
       "Hugging Face", "Vector databases", "Transformers", "PyTorch", "Docker"]
gap = cmp[cmp.skill.isin(llm)].sort_values("diff", ascending=False)
gap[["skill", "AU_2019_22", "US_2023_24", "diff"]]

# %% [markdown]
# Every LLM-era skill sits at **exactly 0.0%** in the 2019–22 Australian ads and
# appears in the 2023–24 US ads — large language models at 15.8%. Hadoop moves the
# other way, 17.4% to 10.5%.
#
# So the absence is a property of the sampling window, not of the Australian
# market, and we can now show that rather than assert it.
#
# **Caveat.** Geography and time change together between these two corpora, so no
# single difference can be attributed to one alone. The LLM result survives it
# because those tools did not exist commercially before 2022.

# %% [markdown]
# ## 5. The curriculum side
#
# 70 UTS subjects across six postgraduate courses, scraped from the handbook with
# learning outcomes intact.

# %%
subj = pd.read_csv(RAW / "uts_subjects_2026.csv")
subj = subj.drop_duplicates(subset="subject_code")          # 10 sit in two courses
usable = subj[subj.n_outcomes > 0]                          # 3 are 2cp placeholders

print(f"subjects: {len(subj)}  |  usable: {len(usable)}  |  faculties: {subj.faculty.nunique()}")
print(f"MDSI: {subj.courses.str.contains('C04372').sum()}   "
      f"non-MDSI (the recommendation pool): {(~subj.courses.str.contains('C04372')).sum()}")
display(subj.curriculum_group.value_counts().rename("subjects").to_frame())

# %% [markdown]
# ### Which in-demand skills does the curriculum cover?
#
# Keyword search over subject name, learning outcomes, topics and description.
# Crude, but enough to find the obvious holes — and the obvious hole is real.

# %%
text = (subj.subject_name.fillna("") + " " + subj.learning_outcomes.fillna("") + " "
        + subj.topics.fillna("") + " " + subj.description.fillna("")).str.lower()

probe = {"Python": r"python", "SQL": r"\bsql\b", "AWS / cloud": r"aws|amazon web|cloud",
         "Machine learning": r"machine learning", "Visualisation": r"visualis|visualiz",
         "Statistics": r"statistic", "Ethics / governance": r"ethic|governance"}

rows = []
for label, pat in probe.items():
    hit = subj[text.str.contains(pat, regex=True, na=False)]
    demand = counts.loc[counts.skill.str.lower() == label.split(" /")[0].lower(), "pct_ads"]
    rows.append({
        "skill": label,
        "% of ads": float(demand.iloc[0]) if len(demand) else None,
        "subjects": len(hit),
        "in MDSI": hit.courses.str.contains("C04372").sum(),
    })
pd.DataFrame(rows)

# %% [markdown]
# ### The worked example
#
# **AWS appears in 22% of Australian Data Scientist ads. No MDSI subject mentions
# AWS or cloud at all.** Master of Artificial Intelligence has two — and both are
# open to an MDSI student through their 24 credit points of free electives.

# %%
cloud = subj[text.str.contains(r"aws|amazon web|cloud", regex=True, na=False)]
cloud[["subject_code", "subject_name", "faculty", "courses"]]

# %% [markdown]
# That is the product in one row: a market skill, a measured curriculum gap, and
# the specific subject code that fills it — in a faculty the student would never
# think to browse.
#
# (Keyword matching over subject text, so spot-check by hand before publishing.)

# %% [markdown]
# ## 6. How well does ESCO cover modern skills?
#
# ESCO supplies the shared vocabulary — the thing that lets a subject saying "text
# mining" and an ad saying "NLP" be recognised as the same skill. The question is
# how much of the modern toolchain it actually contains.

# %%
esco = pd.read_csv(RAW / "taxonomy_esco_v1.2.1" / "skills_en.csv", low_memory=False)
mapping = pd.read_csv(ROOT / "config" / "skill_to_esco.csv")
mapped = (mapping.esco_uri.fillna("") != "").sum()

print(f"ESCO concepts:        {len(esco):,}")
print(f"our dictionary:       {len(mapping)} skills")
print(f"mapped by exact label: {mapped} ({mapped / len(mapping):.0%})")
print("\nUnmapped, by category:")
print(mapping[mapping.esco_uri.fillna("") == ""].category.value_counts().to_string())

# %% [markdown]
# Only 36% maps by exact label, and 73 skills (55%) have no ESCO concept at all —
# Docker, Kubernetes, XGBoost, Snowflake, Tableau and the entire LLM stack.
#
# Two consequences:
#
# - **A finding for the poster.** The standard vocabulary students are measured
#   against has not caught up with the market they are entering. O\*NET fills part
#   of the hole with 8,753 tool names.
# - **A baseline for the evaluation.** 36% is the number a semantic matcher has to
#   beat. ESCO writes `use spreadsheets software` where an ad writes `Excel`;
#   exact matching cannot bridge that, embeddings should.

# %% [markdown]
# ## 7. Figures for the poster
#
# Both regenerate from the numbers computed above, at 300 dpi and sized for one A0
# column at 1:1.

# %%
from chart_top15 import plot as plot_top15  # noqa: E402

out = ROOT / "outputs"
out.mkdir(exist_ok=True)
counts.to_csv(out / "skill_counts_PRIMARY.csv", index=False)

plot_top15(tech.reset_index(drop=True), 15, "What Australian employers ask for",
           "Seek Australia · Data Scientist ads 2019-2022",
           out / "block5_top_skills.png")

# %%
# !python ../src/chart_sources.py

# %% [markdown]
# ## Findings
#
# | # | Finding | Evidence |
# |---|---|---|
# | 1 | Python 83%, SQL 57%, statistics 56%, then a fragmented tail | n = 3,204 Seek AU ads |
# | 2 | Communication beats Tableau, AWS and Hadoop | 28% vs 19%, 22%, 17% |
# | 3 | The ranking holds across markets | Spearman 0.819, 100 shared skills |
# | 4 | The LLM gap is temporal, not Australian | 0.0% in 2019-22, 15.8% in 2023-24 |
# | 5 | ESCO misses 55% of modern data skills | 73 of 133, incl. Docker, XGBoost |
# | 6 | AWS wanted by 22% of ads, absent from all of MDSI | 2 subjects exist, both outside MDSI |
#
# Findings 4, 5 and 6 are the ones worth poster space — each turns something that
# looks like a weakness into a measured result.
