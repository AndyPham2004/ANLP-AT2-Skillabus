"""Tests for data-eda/src/scrape_assessments.py row building. Run: pytest tests/test_scrape_assessments.py"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "data-eda" / "src"))

from scrape_assessments import rows_from_items, task_text  # noqa: E402

SUBJECT = {"subject_code": "36118", "subject_name": "Applied Natural Language Processing", "course": "C04372"}
ITEMS = [
    {"number": "3", "name": "Assessment 3: Critical Reflection", "assessment_type": "Reflection", "weight": "20",
     "individual": "Individual", "description": None},
    {"number": "2", "name": "Assessment 2: End-to-end NLP project", "assessment_type": "Report", "weight": "50",
     "individual": "Group, group and individually assessed", "description": None},
    {"number": "1", "name": "Assessment 1: Text Analysis", "assessment_type": "Report", "weight": "30",
     "individual": "Individual", "description": "<p>Extract  skills from job ads.</p>"},
]


def test_task_text_folds_type_weight_group_and_description():
    assert task_text(ITEMS[1]) == "Assessment 2: End-to-end NLP project (Report, 50%, Group, group and individually assessed)"
    assert task_text(ITEMS[2]) == "Assessment 1: Text Analysis (Report, 30%, Individual). Extract skills from job ads."


def test_rows_are_ordered_by_task_number_in_profile_shape():
    rows = rows_from_items(ITEMS, SUBJECT, "u")
    assert [r["text"].split(":")[0] for r in rows] == ["Assessment 1", "Assessment 2", "Assessment 3"]
    assert set(rows[0]) == {"subject_code", "subject_name", "course", "layer", "text", "source_url", "collected_by"}
    assert rows[0]["layer"] == "assessment" and rows[0]["course"] == "C04372"


def test_duplicate_items_across_offerings_collapse():
    assert len(rows_from_items(ITEMS + ITEMS, SUBJECT, "u")) == 3


def test_no_items_gives_no_rows():
    assert rows_from_items([], SUBJECT, "u") == [] and rows_from_items(None, SUBJECT, "u") == []
