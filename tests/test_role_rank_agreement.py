"""role_rank_agreement.py (plan D7): the committed file is what the script computes from the demand table."""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "data-eda" / "src"))

from role_rank_agreement import OUT, agreement  # noqa: E402
from skillabus import paths  # noqa: E402

TABLE = pd.read_csv(paths.ROLE_SKILL_DEMAND)
COMMITTED = pd.read_csv(OUT)


def test_committed_file_is_current():
    # also the columns and their order: agreement() builds its frame with role_rank_agreement.COLUMNS
    pd.testing.assert_frame_equal(COMMITTED, agreement(TABLE).astype(COMMITTED.dtypes.to_dict()), check_exact=False,
                                  atol=1e-9)


def test_one_row_per_role_and_compared_source():
    data_jobs_roles = set(TABLE[TABLE.source == "data_jobs_2023"].role)
    assert set(COMMITTED[COMMITTED.compared_with == "data_jobs_2023"].role) == data_jobs_roles
    assert set(COMMITTED[COMMITTED.compared_with == "seek_2019_22"].role) == {"Data Scientist"}
    assert COMMITTED.spearman.between(-1, 1).all() and (COMMITTED.n_shared_skills >= 3).all()
