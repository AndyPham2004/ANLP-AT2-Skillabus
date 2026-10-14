"""Tests for data-eda/src/build_subject_profiles.py cleaning rules. Run: pytest tests/test_build_subject_profiles.py"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "data-eda" / "src"))

from build_subject_profiles import clean, drop_ai_policy, split_outcomes, split_topics  # noqa: E402


def test_zero_width_space_and_hyphen_mojibake_are_repaired():
    assert clean("cyberâ\u0080\u0090attack") == "cyber-attack"
    assert clean("Communication â\u0080\u008b") == "Communication"


def test_placeholder_outcomes_are_dropped():
    assert split_outcomes("SLO1: TBC (B.1) SLO2: Build a model (C.1)") == ["Build a model (C.1)"]


def test_numbered_topics_without_delimiters_are_split():
    text = "(1) Cloud computing fundamentals (2) Cloud architecture model (3) Cloud application workflow development"
    assert split_topics(text) == (["Cloud computing fundamentals", "Cloud architecture model",
                                   "Cloud application workflow development"], True)


def test_ai_policy_sentences_leave_the_assessment_text():
    text = ("Build a classifier on the given data. Students are permitted to use generative AI tools and all use "
            "must be acknowledged. Report the accuracy.")
    assert drop_ai_policy(text) == "Build a classifier on the given data. Report the accuracy."


def test_ai_as_content_is_kept():
    text = "Design a generative AI pipeline for a business briefing. Evaluate the outputs."
    assert drop_ai_policy(text) == text
