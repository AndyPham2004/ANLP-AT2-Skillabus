"""Do live 2026 Adzuna counts rank a role's skills like the older sources? (plan D7, issue #115)

For every role with Adzuna rows and another counted source in role_skill_demand.csv (data_jobs 2023
tool lists for 7 roles, Seek 2019-22 full text for Data Scientist), the Spearman rank correlation of
the two sources' shares over the skills both name (n_ads >= 1 in each). Writes
data/5_crosscheck/role_rank_agreement.csv.

Read with care: Adzuna was searched only for each role's 15 priority skills, and for the 7 data_jobs
roles those 15 were picked from the same data_jobs shares, so the skills compared are the ones that
source ranks high. Rho says whether the order within that top group holds in 2026, over at most 15
skills; it is not a test over all skills.

Usage (from the repo root):
    python data-eda/src/role_rank_agreement.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from skillabus import paths  # noqa: E402

OUT = paths.ROLE_RANK_AGREEMENT
COMPARED = ("data_jobs_2023", "seek_2019_22")
COLUMNS = ["role", "source", "compared_with", "compared_period", "n_shared_skills", "spearman",
           "adzuna_ads", "compared_ads"]


def agreement(table: pd.DataFrame) -> pd.DataFrame:
    adz = table[table.source == "adzuna_2026"]
    rows = []
    for role, a in adz.groupby("role"):
        for other in COMPARED:
            b = table[(table.source == other) & (table.role == role)]
            if b.empty:
                continue
            both = a.set_index("skill").pct.rename("adzuna").to_frame().join(
                b.set_index("skill").pct.rename("other"), how="inner")
            rho = both.adzuna.rank().corr(both.other.rank()) if len(both) >= 3 else float("nan")
            rows.append({"role": role, "source": "adzuna_2026", "compared_with": other,
                         "compared_period": b.period.iloc[0], "n_shared_skills": len(both),
                         "spearman": round(rho, 3), "adzuna_ads": int(a.total_ads.iloc[0]),
                         "compared_ads": int(b.total_ads.iloc[0])})
    return pd.DataFrame(rows, columns=COLUMNS).sort_values(["compared_with", "role"]).reset_index(drop=True)


def main() -> None:
    out = agreement(pd.read_csv(paths.ROLE_SKILL_DEMAND))
    out.to_csv(OUT, index=False, lineterminator="\n")
    print(out.to_string(index=False))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
