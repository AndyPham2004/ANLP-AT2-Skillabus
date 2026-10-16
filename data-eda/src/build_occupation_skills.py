"""The skills each IT role's occupation requires, from ESCO, O*NET and the Australian Skills Classification (plan D4).

A role here is one of the 11 the app offers (plan 4.1). No taxonomy has "the role"; each has
occupations. ROLE_OCCUPATIONS below says which occupation of each source stands for each role,
how close it is, and why. It was chosen by searching the source files and O*NET OnLine's
alternate titles (15 Oct 2026), not by guessing:

  match = exact   the occupation's own title names the role
          close   the role's title is one of the occupation's alternate titles (ESCO altLabel,
                  O*NET alternate title), or the same job under another name
          broad   the source has no occupation for the role; this is the nearest wider one

Sources (all in data/raw/, not in git):
  ESCO v1.2.1    occupations_en.csv, occupationSkillRelations_en.csv (essential / optional),
                 skills_en.csv (skill type), digitalSkillsCollection_en.csv
  O*NET 31.0     occupation_data.csv, software_skills.csv. Only rows with In Demand = Y: that
                 flag is per occupation. "Hot Technology" is market-wide (it marks Microsoft Excel
                 for 859 of 923 occupations), so it is kept as onet_hot and never used.
  ASC v1.0       Australian Skills Classification, National Skills Commission (March 2021,
                 ANZSCO 2013 codes), CC BY 4.0: Occupation_Descriptions.csv, Core_competencies.csv
                 (10 per occupation, level 1-10), Technology_tools.csv (tool categories).
                 Left out: Specialist_tasks.csv (work activities such as "Monitor the security
                 of digital information", not skill names); Tech_tools_example_tools.csv (example
                 products per category for the whole market, not per occupation: the same
                 problem as O*NET's Hot flag); Common_tech_tools.csv (office tools ASC says
                 every occupation uses).

Outputs (data/1_knowledge/taxonomies/):
  role_occupations.csv   role, role_family, source, occupation_code, occupation_title, match, why
  occupation_skills.csv  role, source, occupation_code, occupation_title, skill, skill_ref,
                         skill_type, importance, esco_digital, onet_hot
    one row per role x source x skill. When a role has two occupations in one source
    (Network/Systems Administrator in ASC), a skill both list is one row: the codes and titles
    are joined with "|" and the stronger importance is kept.
    importance: ESCO essential / optional; O*NET in_demand; ASC core competency = the level the
    occupation needs, "1"-"10" (1-3 basic, 4-7 intermediate, 8-10 high); ASC tool = listed.

Usage (from the repo root):
    python data-eda/src/build_occupation_skills.py
    python data-eda/src/build_occupation_skills.py --raw "C:/path/to/another/checkout/data/raw"
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))  # repo src/, for skillabus.paths
from skillabus import paths  # noqa: E402

log = logging.getLogger("build_occupation_skills")

# The 11 roles in plan order (docs/notes/data_it_scope_2026-10-14.md, 4.1). Names match
# data/2_demand/role_profiles.csv, so the two files join on `role`.
ROLES = {
    "Data Scientist": "Data & AI",
    "Data Analyst": "Data & AI",
    "Data Engineer": "Data & AI",
    "Machine Learning Engineer": "Data & AI",
    "Software Engineer": "Software",
    "QA/Test Engineer": "Software",
    "Cloud Engineer": "Cloud & infrastructure",
    "DevOps/SRE": "Cloud & infrastructure",
    "Network/Systems Administrator": "Cloud & infrastructure",
    "Cybersecurity Analyst": "Security",
    "Business Analyst": "Business analysis",
}
SOURCES = ("esco", "onet", "asc")
MATCHES = ("exact", "close", "broad")

# (role, source, code, match, why). The code is the ESCO occupation code (ISCO-based, e.g. 2511.4;
# the builder writes its concept URI), the O*NET-SOC code or the ANZSCO code. Titles are read
# from the source files, so a typo stops the build instead of reaching the CSV.
ROLE_OCCUPATIONS = [
    ("Data Scientist", "esco", "2511.4", "exact",
     "ESCO occupation 'data scientist'"),
    ("Data Scientist", "onet", "15-2051.00", "exact", "O*NET 'Data Scientists'"),
    ("Data Scientist", "asc", "224113", "broad",
     "ANZSCO 2013 has no data scientist; ANZSCO 2022 put 224115 Data Scientist in this unit group (2241)"),

    ("Data Analyst", "esco", "2511.3", "exact",
     "ESCO occupation 'data analyst'"),
    ("Data Analyst", "onet", "15-2051.01", "close",
     "O*NET alternate title 'Data Analyst'; O*NET search ranks Data Scientists first, which would copy that role"),
    ("Data Analyst", "asc", "224113", "broad",
     "ANZSCO 2013 has no data analyst; ANZSCO 2022 put 224114 Data Analyst in this unit group (2241)"),

    ("Data Engineer", "esco", "2511.20", "exact",
     "ESCO occupation 'data engineer'"),
    ("Data Engineer", "onet", "15-1243.00", "close",
     "O*NET alternate titles 'Data Engineer', 'Big Data Engineer'"),
    ("Data Engineer", "asc", "262111", "broad",
     "ANZSCO 2013 has no data engineer; the database administrator builds and runs the data stores"),

    ("Machine Learning Engineer", "esco", "2511.11", "close",
     "'machine learning engineer' is an alt label of ESCO 'artificial intelligence engineer'"),
    ("Machine Learning Engineer", "onet", "15-1221.00", "close",
     "O*NET alternate title 'Machine Learning Engineer' (also under Data Scientists; this keeps the two roles apart)"),
    ("Machine Learning Engineer", "asc", "261313", "broad",
     "ANZSCO 2013 has no ML engineer; the job is software engineering of ML systems"),

    ("Software Engineer", "esco", "2512.4", "close",
     "'software engineer' is an alt label of ESCO 'software developer'"),
    ("Software Engineer", "onet", "15-1252.00", "close", "O*NET alternate title 'Software Engineer'"),
    ("Software Engineer", "asc", "261313", "exact", "ANZSCO 'Software Engineer'"),

    ("QA/Test Engineer", "esco", "2519.7", "close",
     "ESCO 'software tester' (alt label 'software testing specialist'); ICT test analyst and ICT system tester are narrower"),
    ("QA/Test Engineer", "onet", "15-1253.00", "exact", "O*NET 'Software Quality Assurance Analysts and Testers'"),
    ("QA/Test Engineer", "asc", "261314", "close",
     "ANZSCO 'Software Tester'; 263211 ICT Quality Assurance Engineer covers QA process, not testing"),

    ("Cloud Engineer", "esco", "2512.1", "exact",
     "ESCO occupation 'cloud engineer'"),
    ("Cloud Engineer", "onet", "15-1299.08", "close", "O*NET alternate title 'Cloud Engineer'"),
    ("Cloud Engineer", "asc", "263111", "broad",
     "ANZSCO 2013 has no cloud engineer; nearest is the engineer who deploys network and system services"),

    ("DevOps/SRE", "esco", "2512.7", "close",
     "ESCO 'cloud DevOps engineer', alt labels 'devops engineer', 'site reliability devops engineer'"),
    ("DevOps/SRE", "onet", "15-1252.00", "close",
     "O*NET alternate titles 'DevOps Engineer', 'Site Reliability Engineer' (same occupation as Software Engineer)"),
    ("DevOps/SRE", "asc", "261313", "broad",
     "ANZSCO 2013 has no DevOps; the later code 261316 DevOps Engineer sits in the same unit group 2613"),

    ("Network/Systems Administrator", "esco", "2522.1", "exact",
     "ESCO 'ICT system administrator', alt labels 'network administrator', 'system and network administrator'"),
    ("Network/Systems Administrator", "onet", "15-1244.00", "exact", "O*NET 'Network and Computer Systems Administrators'"),
    ("Network/Systems Administrator", "asc", "262113", "exact",
     "ANZSCO 'Systems Administrator'; ASC splits the role, see 263112"),
    ("Network/Systems Administrator", "asc", "263112", "exact",
     "ANZSCO 'Network Administrator'; ASC splits the role, see 262113"),

    ("Cybersecurity Analyst", "esco", "2529.7", "close",
     "ESCO 'cyber incident responder', alt label 'SOC Analyst'; ESCO files 'cybersecurity analyst' under digital forensics expert, too narrow"),
    ("Cybersecurity Analyst", "onet", "15-1212.00", "close", "O*NET alternate title 'Cybersecurity Analyst'"),
    ("Cybersecurity Analyst", "asc", "262112", "close",
     "ANZSCO 'ICT Security Specialist'; ASC v1.0 predates the later code 262116 Cyber Security Analyst"),

    ("Business Analyst", "esco", "2511.9", "close",
     "ESCO 'ICT business analyst' (alt 'IT business analyst'); ESCO 'business analyst' (2421.1) is strategy consulting"),
    ("Business Analyst", "onet", "15-1211.00", "close",
     "O*NET alternate titles 'Business Analyst', 'IT Business Analyst'"),
    ("Business Analyst", "asc", "2611", "close",
     "ASC has only the unit group 'ICT Business and Systems Analysts' (holds 261111 ICT Business Analyst)"),
]

IMPORTANCE = ("essential", "optional", "in_demand", "listed") + tuple(str(i) for i in range(1, 11))

COLUMNS_OCC = ["role", "role_family", "source", "occupation_code", "occupation_title", "match", "why"]
COLUMNS_SKILLS = ["role", "source", "occupation_code", "occupation_title", "skill", "skill_ref",
                  "skill_type", "importance", "esco_digital", "onet_hot"]

# Raw files, as paths.py names them under data/raw/; --raw moves the root.
RAW_FILES = {
    "esco_occupations": paths.ESCO_OCCUPATIONS_RAW,
    "esco_relations": paths.ESCO_OCCUPATION_SKILLS_RAW,
    "esco_skills": paths.ESCO_RAW,
    "esco_digital": paths.ESCO_DIGITAL_RAW,
    "onet_occupations": paths.ONET_OCCUPATIONS_RAW,
    "onet_tools": paths.ONET_TOOLS_RAW,
    "asc_occupations": paths.ASC_OCCUPATIONS_RAW,
    "asc_core": paths.ASC_CORE_COMPETENCIES_RAW,
    "asc_tools": paths.ASC_TECH_TOOLS_RAW,
}


def raw_files(raw: Path) -> dict[str, Path]:
    """The raw inputs under `raw` instead of paths.RAW; stops with the list of missing files."""
    files = {k: raw / p.relative_to(paths.RAW) for k, p in RAW_FILES.items()}
    missing = [str(p) for p in files.values() if not p.exists()]
    if missing:
        raise SystemExit("Raw files not found (data/README.md says where each comes from):\n  " + "\n  ".join(missing))
    return files


def read(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8")


def occupation_table(mapping: list[tuple], lookup: dict[str, dict[str, list[tuple[str, str]]]]) -> pd.DataFrame:
    """role_occupations.csv. lookup[source][code] = [(code written to the CSV, title)]; a code that
    is missing, or (ESCO) shared by two concepts, stops the build."""
    rows, unknown = [], []
    for role, source, code, match, why in mapping:
        if role not in ROLES or source not in SOURCES or match not in MATCHES or not why:
            unknown.append(f"{role}: {source} {code} (role, source, match or why not allowed)")
            continue
        found = lookup[source].get(code, [])
        if len(found) != 1:
            unknown.append(f"{role}: {source} {code} ({len(found)} matches)")
            continue
        written, title = found[0]
        rows.append({"role": role, "role_family": ROLES[role], "source": source, "occupation_code": written,
                     "occupation_title": title, "match": match, "why": why})
    if unknown:
        raise SystemExit("Occupation rows that do not check out:\n  " + "\n  ".join(unknown))
    return pd.DataFrame(rows, columns=COLUMNS_OCC)


def esco_skills(occ: pd.DataFrame, rel: pd.DataFrame, skills: pd.DataFrame, digital: set[str]) -> pd.DataFrame:
    """Essential and optional skills of each role's ESCO occupation."""
    skill_type = dict(zip(skills.conceptUri, skills.skillType))
    m = occ[occ.source == "esco"].merge(rel, left_on="occupation_code", right_on="occupationUri")
    return pd.DataFrame({
        "role": m.role, "source": "esco", "occupation_code": m.occupation_code,
        "occupation_title": m.occupation_title, "skill": m.skillLabel, "skill_ref": m.skillUri,
        # 59 relation rows in the whole file have no skillType; skills_en.csv has it
        "skill_type": [t or skill_type.get(u, "") for t, u in zip(m.skillType, m.skillUri)],
        "importance": m.relationType,
        "esco_digital": ["y" if u in digital else "n" for u in m.skillUri], "onet_hot": "",
    })


def onet_tools(occ: pd.DataFrame, tools: pd.DataFrame) -> pd.DataFrame:
    """In-demand tools of each role's O*NET occupation; the Hot flag is carried, not used."""
    demand = tools[tools["In Demand"] == "Y"]
    m = occ[occ.source == "onet"].merge(demand, left_on="occupation_code", right_on="O*NET-SOC Code")
    return pd.DataFrame({
        "role": m.role, "source": "onet", "occupation_code": m.occupation_code,
        "occupation_title": m.occupation_title, "skill": m["Workplace Example"],
        "skill_ref": "onet:" + m["Element ID"] + ":" + m["Workplace Example"],
        "skill_type": m["Element Name"], "importance": "in_demand", "esco_digital": "",
        "onet_hot": m["Hot Technology"],
    })


def asc_skills(occ: pd.DataFrame, core: pd.DataFrame, tools: pd.DataFrame) -> pd.DataFrame:
    """Core competencies (with the level the occupation needs) and technology tools of each ASC occupation."""
    a = occ[occ.source == "asc"]
    c = a.merge(core, left_on="occupation_code", right_on="ANZSCO_Code")
    t = a.merge(tools, left_on="occupation_code", right_on="ANZSCO_Code")
    frames = [
        pd.DataFrame({"role": c.role, "occupation_code": c.occupation_code, "occupation_title": c.occupation_title,
                      "skill": c.Core_Competencies, "skill_ref": "asc:core_competency:" + c.Core_Competencies,
                      "skill_type": "core competency", "importance": c.Score.str.strip()}),
        pd.DataFrame({"role": t.role, "occupation_code": t.occupation_code, "occupation_title": t.occupation_title,
                      "skill": t.Technology_tool, "skill_ref": "asc:technology_tool:" + t.Technology_tool,
                      "skill_type": "technology tool", "importance": "listed"}),
    ]
    out = pd.concat(frames, ignore_index=True)
    out.insert(1, "source", "asc")
    out["esco_digital"], out["onet_hot"] = "", ""
    return out


def strength(importance: str) -> int:
    """Higher = stronger, to keep one row when two occupations of a role list the same skill."""
    if importance.isdigit():
        return int(importance)
    return {"essential": 2, "optional": 1}.get(importance, 0)


def merge_occupations(skills: pd.DataFrame, occ: pd.DataFrame) -> pd.DataFrame:
    """One row per role x source x skill_ref: codes and titles joined with '|', strongest importance."""
    order = {(r.role, r.source, r.occupation_code): i for i, r in enumerate(occ.itertuples())}
    skills = skills.assign(_o=[order[k] for k in zip(skills.role, skills.source, skills.occupation_code)])
    rows = []
    for _, g in skills.sort_values("_o", kind="stable").groupby(["role", "source", "skill_ref"], sort=False):
        first = g.iloc[0].to_dict()
        if len(g) > 1:
            first["occupation_code"] = "|".join(dict.fromkeys(g.occupation_code))
            first["occupation_title"] = "|".join(dict.fromkeys(g.occupation_title))
            first["importance"] = max(g.importance, key=strength)
        rows.append(first)
    return pd.DataFrame(rows)[COLUMNS_SKILLS]


def sort_skills(df: pd.DataFrame) -> pd.DataFrame:
    """Plan order of roles; esco, onet, asc; strongest first; then by label."""
    role_rank = {r: i for i, r in enumerate(ROLES)}
    src_rank = {s: i for i, s in enumerate(SOURCES)}
    key = pd.DataFrame({
        "r": df.role.map(role_rank), "s": df.source.map(src_rank),
        "t": (df.skill_type == "technology tool").astype(int),        # ASC: competencies before tools
        "i": -df.importance.map(strength), "k": df.skill.str.casefold(), "u": df.skill_ref,
    })
    idx = key.sort_values(list(key.columns), kind="stable").index
    return df.loc[idx].reset_index(drop=True)


def build(files: dict[str, Path]) -> tuple[pd.DataFrame, pd.DataFrame]:
    esco_occ = read(files["esco_occupations"])
    onet_occ = read(files["onet_occupations"])
    asc_occ = read(files["asc_occupations"])
    lookup: dict[str, dict[str, list[tuple[str, str]]]] = {s: {} for s in SOURCES}
    for code, uri, title in zip(esco_occ.code, esco_occ.conceptUri, esco_occ.preferredLabel):
        lookup["esco"].setdefault(code, []).append((uri, title))
    for code, title in zip(onet_occ["O*NET-SOC Code"], onet_occ.Title):
        lookup["onet"].setdefault(code, []).append((code, title))
    for code, title in zip(asc_occ.ANZSCO_Code.str.strip(), asc_occ.ANZSCO_Title.str.strip()):
        lookup["asc"].setdefault(code, []).append((code, title))
    occ = occupation_table(ROLE_OCCUPATIONS, lookup)

    rel = read(files["esco_relations"])
    esco_skill_table = read(files["esco_skills"])
    digital = set(read(files["esco_digital"]).conceptUri)
    core = read(files["asc_core"]).assign(ANZSCO_Code=lambda d: d.ANZSCO_Code.str.strip())
    asc_tools = read(files["asc_tools"]).assign(ANZSCO_Code=lambda d: d.ANZSCO_Code.str.strip(),
                                                 Technology_tool=lambda d: d.Technology_tool.str.strip())
    skills = pd.concat([
        esco_skills(occ, rel, esco_skill_table, digital),
        onet_tools(occ, read(files["onet_tools"])),
        asc_skills(occ, core, asc_tools),
    ], ignore_index=True)
    skills = sort_skills(merge_occupations(skills, occ))
    odd = set(skills.importance) - set(IMPORTANCE)
    if odd:
        raise SystemExit(f"Importance values the README does not define: {sorted(odd)}")
    return occ, skills


def summary(occ: pd.DataFrame, skills: pd.DataFrame) -> None:
    counts = skills.assign(col=skills.source + ":" + skills.importance.where(
        ~skills.importance.str.isdigit(), "core")).pivot_table(
        index="role", columns="col", values="skill", aggfunc="size", fill_value=0)
    counts = counts.reindex(index=list(ROLES), fill_value=0)
    cols = [c for c in ["esco:essential", "esco:optional", "onet:in_demand", "asc:core", "asc:listed"] if c in counts]
    log.info("Rows per role and source (asc:core = 10 core competencies, asc:listed = technology tools):")
    log.info(counts[cols].to_string())
    matches = occ.groupby("source").match.value_counts().unstack(fill_value=0)
    log.info("Matches per source:\n%s", matches.to_string())
    onet = skills[skills.source == "onet"]
    per_tool = onet.groupby("skill").role.nunique()
    log.info("O*NET in-demand tools: %d distinct; %d named for 3 or more roles: %s", len(per_tool),
             (per_tool >= 3).sum(), ", ".join(f"{t} {n}" for t, n in per_tool[per_tool >= 3].sort_values(
                 ascending=False, kind="stable").items()))
    log.info("Of the O*NET rows, %d are also flagged Hot (kept for information, not used)", (onet.onet_hot == "Y").sum())
    ess = skills[(skills.source == "esco") & (skills.importance == "essential")]
    log.info("ESCO essential skills: %d rows, %d distinct over the 11 roles; %d of them in the digital collection",
             len(ess), ess.skill_ref.nunique(), ess[ess.esco_digital == "y"].skill_ref.nunique())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--raw", type=Path, default=paths.RAW, help="the data/raw/ folder (default: this checkout's)")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    occ, skills = build(raw_files(args.raw))
    paths.TAXONOMIES.mkdir(parents=True, exist_ok=True)
    occ.to_csv(paths.ROLE_OCCUPATIONS, index=False, encoding="utf-8", lineterminator="\n")
    skills.to_csv(paths.OCCUPATION_SKILLS, index=False, encoding="utf-8", lineterminator="\n")
    log.info("Wrote %s: %d rows; %s: %d rows", paths.ROLE_OCCUPATIONS.name, len(occ),
             paths.OCCUPATION_SKILLS.name, len(skills))
    summary(occ, skills)


if __name__ == "__main__":
    main()
