"""build_recent_sample.py: the 2026 sample must not depend on the order rows arrive in."""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "data-eda" / "src"))

from build_recent_sample import mark_sample  # noqa: E402


def _ads():
    # Quantium on 14 Oct: two ads on 18 Sep, two tied on 27 Aug for the third slot.
    rows = [("gh-4005587201", "2026-09-18"), ("gh-4005586201", "2026-09-18"),
            ("gh-4005992201", "2026-08-27"), ("gh-4005506201", "2026-08-27"),
            ("gh-4005991201", "2026-08-26")]
    return pd.DataFrame({
        "ad_id": [f"ats-{i}" for i, _ in rows], "posted": [p for _, p in rows],
        "company": "Quantium", "title": "Data Scientist", "period": "2026-10",
        "full_text": True, "snapshot": "2026-10-14", "age_days": 40.0,
    })


def test_cap_keeps_the_same_ads_whatever_the_row_order():
    picks = set()
    for seed in range(20):
        df = _ads().sample(frac=1, random_state=seed).reset_index(drop=True)
        out = mark_sample(df, max_age=60, cap=3)
        picks.add(frozenset(out.loc[out.in_sample, "ad_id"]))
    assert picks == {frozenset({"ats-gh-4005587201", "ats-gh-4005586201", "ats-gh-4005992201"})}


def test_old_ads_and_the_cap_still_apply():
    df = _ads()
    df.loc[0, "age_days"] = 61.0
    out = mark_sample(df, max_age=60, cap=3)
    assert not out.loc[0, "in_sample"]
    assert out.in_sample.sum() == 3
