"""build_role_skill_demand.py (plan D6): the one demand table, and its agreement with the files it supersedes."""

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "data-eda" / "src"))

import build_role_profiles as brp  # noqa: E402
from build_role_skill_demand import (  # noqa: E402
    ATS_PERIOD, COLUMNS, COUNTED, EXTRA_TOKEN_MAP, IT_MIXED_FAMILY, IT_MIXED_ROLE, JOBSPIPE_PERIOD, MIN_ROLE_ADS,
    MIXED_FAMILY, MIXED_ROLE, SEEK_2020_21_PERIOD, SOURCES, TEXT_TYPE, adzuna_rows, ats_rows, committed_inputs,
    data_jobs_rows, jobspipe_rows, load_data_jobs, recent_rows, seek_2020_21_rows, seek_rows, taxonomy_rows, to_frame,
    to_label, tool_lookup,
)
from build_vocabulary import read_table, read_table_text, to_csv_text  # noqa: E402
from recount_recent import wilson  # noqa: E402
from skillabus import paths  # noqa: E402

TABLE = pd.read_csv(paths.ROLE_SKILL_DEMAND)
TABLE["importance"] = TABLE.importance.fillna("")
INPUTS = committed_inputs()
VOCAB, FAMILIES = INPUTS["vocab"], INPUTS["families"]
SEED = read_table(paths.SKILLS_SEED)
COUNTS = TABLE[TABLE.source.isin(COUNTED)]
TAXONOMY = TABLE[~TABLE.source.isin(COUNTED)]
LOOKUP = tool_lookup(VOCAB, set(SEED.canonical))
EPS = 0.1 + 1e-9

# The app's tier-1 matcher (extract.py) tries the longest alias at each place in a sentence, so a longer
# alias of another dictionary skill hides the shorter one. Van Thong's extract_skills.py, which made
# skill_counts_v2.csv and skill_counts_2026.csv, matches each skill on its own and counts both. These
# skills can therefore sit below those files on the same text; nothing else may.
LONGEST_ALIAS = {
    "SQL": "'SQL Server' counts as SQL Server only",
    "Cloud platforms": "'Google Cloud' counts as Google Cloud only",
    "Azure": "'Azure ML', 'Azure Machine Learning' count as Azure ML only",
    "Machine learning": "'Azure Machine Learning' counts as Azure ML only",
    "Artificial intelligence": "'Generative AI', 'Responsible AI', 'Vertex AI' count as those skills only",
}


def shares(source: str, period: str, role: str) -> pd.Series:
    block = COUNTS[(COUNTS.source == source) & (COUNTS.period == period) & (COUNTS.role == role)]
    return block.set_index("skill").pct


# ---------------------------------------------------------------- shape
def test_columns_and_allowed_values():
    assert list(TABLE.columns) == COLUMNS
    assert set(TABLE.source) == set(SOURCES)
    assert (TABLE.text_type == TABLE.source.map(TEXT_TYPE)).all()
    assert (COUNTS.importance == "").all()
    assert set(TABLE.importance[TABLE.source == "esco_occupation"]) == {"essential", "optional"}
    assert set(TABLE.importance[TABLE.source == "onet"]) == {"in_demand"}
    assert set(TABLE.role) <= set(FAMILIES) | {MIXED_ROLE, IT_MIXED_ROLE}
    assert (TABLE.role_family == TABLE.role.map({**FAMILIES, MIXED_ROLE: MIXED_FAMILY, IT_MIXED_ROLE: IT_MIXED_FAMILY})).all()
    assert set(TABLE.period[TABLE.source == "ats_2026"]) == {ATS_PERIOD}
    assert set(TABLE.period[TABLE.source == "jobspipe_2026"]) == {JOBSPIPE_PERIOD}
    assert set(TABLE.period[TABLE.source == "seek_2020_21"]) == {SEEK_2020_21_PERIOD}
    assert not TABLE.duplicated(["role", "skill_id", "source", "period"]).any()
    assert set(TABLE.period[TABLE.source == "recent_2024_26"]) == {"2024-01", "2026"}


def test_every_skill_is_a_vocabulary_skill():
    label_of = dict(zip(VOCAB.skill_id, VOCAB.label))
    assert TABLE.skill_id.isin(label_of).all()
    assert (TABLE.skill == TABLE.skill_id.map(label_of)).all()


def test_counted_rows_have_shares_and_wilson_bounds():
    assert (COUNTS.n_ads >= 1).all() and (COUNTS.n_ads <= COUNTS.total_ads).all()
    assert ((COUNTS.pct - (100 * COUNTS.n_ads / COUNTS.total_ads).round(1)).abs() <= 0.05 + 1e-9).all()
    assert ((COUNTS.pct_low <= COUNTS.pct) & (COUNTS.pct <= COUNTS.pct_high)).all()
    assert ((COUNTS.pct_low >= 0) & (COUNTS.pct_high <= 100)).all()
    for r in COUNTS.drop_duplicates(["n_ads", "total_ads"]).itertuples():
        assert (r.pct_low, r.pct_high) == wilson(int(r.n_ads), int(r.total_ads)), r


def test_taxonomy_rows_have_no_counts():
    assert TAXONOMY[["n_ads", "total_ads", "pct", "pct_low", "pct_high"]].isna().all().all()
    assert set(TAXONOMY.text_type) == {"taxonomy"}


def test_one_denominator_per_block_and_the_known_totals():
    assert (COUNTS.groupby(["role", "source", "period"]).total_ads.nunique() == 1).all()
    seek = COUNTS[COUNTS.source == "seek_2019_22"]
    assert set(seek.role) == {"Data Scientist"} and set(seek.total_ads) == {len(INPUTS["seek"])} == {3204}
    dj = COUNTS[COUNTS.source == "data_jobs_2023"].groupby("role").total_ads.first()
    old = pd.read_csv(paths.ROLE_PROFILES).groupby("role").total_ads.first()
    assert dj.to_dict() == old.to_dict()                       # Data Engineer 4,438 ... ML Engineer 263
    c26 = pd.read_csv(paths.SKILL_COUNTS_2026).iloc[0]
    recent = COUNTS[COUNTS.source == "recent_2024_26"].groupby(["period", "role"]).total_ads.first()
    assert recent.to_dict() == {("2024-01", MIXED_ROLE): c26.total_2024_01, ("2026", MIXED_ROLE): c26.total_2026_all}
    adz = COUNTS[COUNTS.source == "adzuna_2026"].groupby("role").total_ads.first()
    live = INPUTS["adzuna"].groupby("role").role_total.first().astype(int)
    assert adz.to_dict() == live.to_dict() and set(adz.index) == set(FAMILIES)   # every one of the 11 roles


def test_every_role_has_taxonomy_rows_and_every_essential_skill():
    for role in FAMILIES:
        rows = TAXONOMY[TAXONOMY.role == role]
        assert {"esco_occupation", "onet"} <= set(rows.source), role
    occ = INPUTS["occupation_skills"]
    essential = occ[(occ.source == "esco") & (occ.importance == "essential")]
    have = set(zip(TAXONOMY.role, TAXONOMY.skill_id))
    assert all((r.role, f"esco:{r.skill_ref}") in have for r in essential.itertuples())


# ---------------------------------------------------------------- the rules of each source
def test_recent_blocks_follow_the_30_ad_rule():
    own = COUNTS[(COUNTS.source == "recent_2024_26") & (COUNTS.role != MIXED_ROLE)]
    assert (own.total_ads >= MIN_ROLE_ADS).all()
    n = MIN_ROLE_ADS
    recent = pd.DataFrame({
        "period": ["2026-10"] * n + ["2026-09"] * 2 + ["2024-01"] * 5,
        "role_group": ["data scientist"] * n + ["data role"] * 2 + ["data scientist"] * 5,
        "full_text": ["True"] * (n + 7), "in_sample": ["True"] * (n + 7),
        "description": ["Python and SQL."] * n + ["Tableau."] * 2 + ["Python."] * 5})
    recent.loc[n + 6, "in_sample"] = "False"                 # out of the sample: not counted
    rows, _ = recent_rows(VOCAB, recent, FAMILIES)
    blocks = pd.DataFrame(rows).groupby(["period", "role"]).total_ads.first().to_dict()
    assert blocks == {("2026", "Data Scientist"): n, ("2026", MIXED_ROLE): 2, ("2024-01", MIXED_ROLE): 4}


def test_tool_names_map_as_role_profiles_did_plus_the_vocabulary():
    old_lookup, _ = brp.load_dictionary()
    for name in old_lookup:
        assert to_label(name, LOOKUP) == brp.to_skill(name, old_lookup), name
    assert to_label("word", LOOKUP) == "Microsoft Office"         # Van Thong's TOKEN_MAP
    assert to_label("splunk", LOOKUP) == "Splunk"                 # a vocabulary row the dictionary lacked
    assert to_label("confluence", LOOKUP) == "Confluence"
    assert to_label("spring", LOOKUP) == "Spring"                 # by label: in a tool list it is the framework
    assert to_label("centos", LOOKUP) == "Linux" and to_label("no-sql", LOOKUP) == "NoSQL"   # EXTRA_TOKEN_MAP
    assert to_label("go", LOOKUP) is None and to_label("c", LOOKUP) is None                  # unreliable
    assert to_label("atlassian", LOOKUP) is None                  # no vocabulary row: reported as unmapped


def test_data_jobs_rows_count_ads_naming_a_tool():
    df = pd.DataFrame({
        "job_country": ["Australia"] * 4, "job_title_short": ["Cloud Engineer"] * 3 + ["Data Analyst"],
        "job_title": ["CE1", "CE2", "CE1", "DA"], "company_name": ["A", "B", "A", "C"],
        "job_location": ["Sydney"] * 4,
        "job_skills": ["['python', 'splunk', 'c']", "['centos', 'linux', 'vmware']", "['python', 'splunk', 'c']", ""]})
    rows, unmapped, totals = data_jobs_rows(VOCAB, df, FAMILIES, set(SEED.canonical))
    out = pd.DataFrame(rows).set_index("skill")
    assert totals == {"Cloud Engineer": 2, "Data Analyst": 0}  # a repeat dropped; an empty list is no ad
    assert out.loc["Linux", "n_ads"] == 1 and out.loc["Splunk", "pct"] == 50.0
    assert unmapped == {"vmware": 1} and "C" not in out.index


def test_taxonomy_rows_map_onet_tools_to_one_label():
    rows, left_out = taxonomy_rows(VOCAB, INPUTS["occupation_skills"], INPUTS["onet_map"], FAMILIES)
    onet = pd.DataFrame(rows).query("source == 'onet'")
    assert not onet.duplicated(["role", "skill"]).any()
    assert "Microsoft Office" in set(onet.skill[onet.role == "Business Analyst"])   # Office, Outlook, PowerPoint
    assert left_out["onet"] == {"eMASS (dropped in onet_tool_map.csv)": 1}
    assert set(left_out["esco_occupation"]) == {"optional skill not in the vocabulary"}


# ---------------------------------------------------------------- agreement with the superseded files
def test_data_jobs_shares_agree_with_role_profiles():
    """Same rows, title map and denominators; a share moves only where EXTRA_TOKEN_MAP adds a spelling."""
    rp = pd.read_csv(paths.ROLE_PROFILES)
    dj = COUNTS[COUNTS.source == "data_jobs_2023"].set_index(["role", "skill"])
    moved = []
    for r in rp.itertuples():
        new = dj.loc[(r.role, r.skill)]
        if new.n_ads != r.n_ads:
            assert r.skill in EXTRA_TOKEN_MAP.values() and new.n_ads > r.n_ads, (r.role, r.skill)
            moved.append((r.role, r.skill))
        else:
            assert new.pct == r.pct_ads and (new.pct_low, new.pct_high) == (r.pct_low, r.pct_high)
    assert len(moved) <= 6                                      # Linux (distributions) and NoSQL ("no-sql")


def classify(new: float, old: float, clean: float, skill: str) -> str:
    """Why a share differs from the September file: the rule of the next two tests."""
    if abs(new - old) <= EPS:
        return "same"
    if abs(new - clean) <= EPS and new > old:
        return "clean text"       # skill_counts_v2.csv was counted on the raw text with welded words
    if skill in LONGEST_ALIAS and new < clean:
        return "longest alias"
    return "unexplained"


ALIASES_MOVED = {"Data security", "Artificial intelligence"}


def test_seek_shares_agree_with_skill_counts_v2():
    """The 148 dictionary skills, Data Scientist, the 3,204 Seek ads.

    Rule: within 0.1 point of skill_counts_v2.csv; or, where not, the share equals skill_counts_2026.csv's
    pct_2019_22 (the same ads after cleaning, the same aliases, Van Thong's counter) within 0.1 and is higher
    than v2 (cleaning splits welded words, "TableauSuperior", so it can only add mentions); or the skill is
    one LONGEST_ALIAS hides and the share is below the clean-text count. The vocabulary did not change any
    dictionary alias (checked first), so no difference comes from aliases.
    """
    by_label = VOCAB.set_index("label")
    assert all(by_label.loc[s.canonical, "aliases_ads"] == s.aliases for s in SEED.itertuples())
    new = shares("seek_2019_22", "2019-22", "Data Scientist")
    v2 = pd.read_csv(paths.SKILL_COUNTS).set_index("skill").pct_ads
    clean = pd.read_csv(paths.SKILL_COUNTS_2026).set_index("skill").pct_2019_22
    assert set(v2.index) == set(SEED.canonical)
    why = {s: classify(new.get(s, 0.0), v2[s], clean[s], s) for s in SEED.canonical}
    # #120 (16 Oct): "cyber security" / "cybersecurity" moved from Data security to ESCO cyber security,
    # so Data security can only be lower than the counts made with the old aliases. 17 Oct: Artificial intelligence
    # no longer matches a bare "AI", only the phrases ads use for the skill, so it too can only be lower.
    for skill in ALIASES_MOVED:
        if why[skill] != "same" and new.get(skill, 0.0) < v2[skill]:
            why[skill] = "aliases moved"
    assert [s for s, w in why.items() if w == "unexplained"] == []
    assert sum(w in ("same", "aliases moved") for w in why.values()) >= 120


@pytest.mark.parametrize("period, column", [("2024-01", "pct_2024_01"), ("2026", "pct_2026_all")])
def test_recent_shares_agree_with_skill_counts_2026(period, column):
    """Same ads and aliases as skill_counts_2026.csv: within 0.1, or below it where a longer alias hides the skill."""
    new = shares("recent_2024_26", period, MIXED_ROLE)
    old = pd.read_csv(paths.SKILL_COUNTS_2026).set_index("skill")[column]
    off = {s: (new.get(s, 0.0), old[s]) for s in old.index if abs(new.get(s, 0.0) - old[s]) > EPS}
    assert all(s in LONGEST_ALIAS and n < o for s, (n, o) in off.items()), off


# ---------------------------------------------------------------- the committed file is current
def committed(source: str) -> pd.DataFrame:
    text = paths.ROLE_SKILL_DEMAND.read_text(encoding="utf-8")
    table = read_table_text(text)
    return table[table.source.isin([source] if isinstance(source, str) else source)].reset_index(drop=True)


def rebuilt(rows) -> pd.DataFrame:
    return read_table_text(to_csv_text(to_frame(rows)))


def test_ats_blocks_follow_the_30_ad_rule_and_skip_other():
    own = COUNTS[(COUNTS.source == "ats_2026") & ~COUNTS.role.isin([MIXED_ROLE, IT_MIXED_ROLE])]
    assert (own.total_ads >= MIN_ROLE_ADS).all()
    n = MIN_ROLE_ADS
    ats = pd.DataFrame({
        "role": ["Software Engineer"] * n + ["Data Scientist"] * 2 + ["Cybersecurity Analyst"] * 3 + ["other"] * 4,
        "description": ["Java and Python."] * n + ["Python."] * 2 + ["Splunk."] * 3 + ["Python sales."] * 4})
    rows, notes = ats_rows(VOCAB, ats, FAMILIES)
    blocks = pd.DataFrame(rows).groupby("role").total_ads.first().to_dict()
    assert blocks == {"Software Engineer": n, MIXED_ROLE: 2, IT_MIXED_ROLE: 3}      # "other" is not counted
    assert {r["period"] for r in rows} == {ATS_PERIOD} and {r["text_type"] for r in rows} == {"full_text"}
    with pytest.raises(ValueError):
        ats_rows(VOCAB, pd.DataFrame({"role": ["Astronaut"], "description": ["Python."]}), FAMILIES)


def test_committed_ats_file_has_roles_and_masked_text():
    ats = INPUTS["ats"]
    assert list(ats.columns) == ["ad_id", "source", "company", "title", "role", "location", "posted", "snapshot", "description", "url"]
    assert set(ats.role) <= set(FAMILIES) | {"other"} and (ats.role != "other").sum() >= MIN_ROLE_ADS
    assert not ats.duplicated(["company", "title", "description"]).any() and not ats.duplicated("ad_id").any()
    assert not ats.description.str.contains(r"[\w.+-]+@[\w-]+\.[\w.-]+", regex=True).any()       # emails masked
    assert (ats.description.str.len() >= 200).all()
    age = (pd.to_datetime(ats.snapshot) - pd.to_datetime(ats.posted.replace("", pd.NA))).dt.days
    assert (age.dropna() <= 60).all() and not ats.duplicated(["company", "title"]).any()      # the 60-day rule


def test_jobspipe_blocks_cover_every_role_from_the_committed_skills_file():
    jp = INPUTS["jobspipe"]
    assert list(jp.columns) == ["ad_id", "role", "title", "company", "location", "date_posted", "employer_type", "seniority",
                                "providers", "url", "n_chars", "skills", "esco_tags"]
    assert set(jp.role) == set(FAMILIES) and (jp.role.value_counts() >= MIN_ROLE_ADS).all()   # every role its own block
    assert not jp.duplicated("ad_id").any() and not jp.duplicated(["company", "title"]).any()
    assert jp.url.str.startswith("http").all()                                                 # the link to the posting
    blocks = COUNTS[COUNTS.source == "jobspipe_2026"].groupby("role").total_ads.first().astype(int).to_dict()
    assert blocks == jp.role.value_counts().to_dict()
    small = pd.DataFrame({"role": ["Data Scientist"] * 2 + ["Cloud Engineer"] * 3, "skills": ["Python|SQL"] * 2 + ["AWS"] * 3})
    rows, _ = jobspipe_rows(VOCAB, small, FAMILIES)
    assert pd.DataFrame(rows).groupby("role").total_ads.first().to_dict() == {MIXED_ROLE: 2, IT_MIXED_ROLE: 3}
    with pytest.raises(ValueError):
        jobspipe_rows(VOCAB, pd.DataFrame({"role": ["Data Scientist"], "skills": ["Not a skill"]}), FAMILIES)


def test_seek_2020_21_blocks_come_from_the_committed_skills_file():
    s21 = INPUTS["seek_2020_21"]
    assert list(s21.columns) == ["ad_id", "role", "title", "company", "state", "post_date", "period_file", "url", "n_chars", "skills"]
    assert set(s21.role) <= set(FAMILIES) and not s21.duplicated("ad_id").any()
    own = COUNTS[(COUNTS.source == "seek_2020_21") & ~COUNTS.role.isin([MIXED_ROLE, IT_MIXED_ROLE])]
    assert (own.total_ads >= MIN_ROLE_ADS).all()
    blocks = own.groupby("role").total_ads.first().astype(int).to_dict()
    counts = s21.role.value_counts()
    assert blocks == {r: int(n) for r, n in counts.items() if n >= MIN_ROLE_ADS}


def test_committed_seek_recent_adzuna_and_taxonomy_rows_are_what_the_builder_writes():
    v, f = VOCAB, FAMILIES
    assert committed("seek_2019_22").equals(rebuilt(seek_rows(v, INPUTS["seek"], f["Data Scientist"])))
    assert committed("recent_2024_26").equals(rebuilt(recent_rows(v, INPUTS["recent"], f)[0]))
    tax, _ = taxonomy_rows(v, INPUTS["occupation_skills"], INPUTS["onet_map"], f)
    assert committed(["esco_occupation", "onet"]).equals(rebuilt(tax))
    assert committed("adzuna_2026").equals(rebuilt(adzuna_rows(v, INPUTS["adzuna"], f)))
    assert committed("ats_2026").equals(rebuilt(ats_rows(v, INPUTS["ats"], f)[0]))
    assert committed("jobspipe_2026").equals(rebuilt(jobspipe_rows(v, INPUTS["jobspipe"], f)[0]))
    assert committed("seek_2020_21").equals(rebuilt(seek_2020_21_rows(v, INPUTS["seek_2020_21"], f)[0]))


def test_committed_data_jobs_rows_are_what_the_builder_writes():
    try:
        postings = load_data_jobs(paths.RAW)
    except SystemExit:
        pytest.skip("the raw data_jobs file is not in data/raw/ (run the builder with --check instead)")
    rows, _, _ = data_jobs_rows(VOCAB, postings, FAMILIES, set(SEED.canonical))
    assert committed("data_jobs_2023").equals(rebuilt(rows))
