"""Rank subjects for the missing skills and build the learning path. Owner: Phuong Nhi."""


def recommend(gaps: list[dict], profiles_csv: str = "data/processed/subject_profiles.csv") -> dict:
    """Return `recommendations` and `learning_path` (data contract section 2)."""
    raise NotImplementedError