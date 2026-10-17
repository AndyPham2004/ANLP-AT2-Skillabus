"""clean_resumes.py: the contact and name patterns added for #53."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "data-eda" / "src"))

from clean_resumes import CREDENTIAL_NAME, PHONE, TITLED_NAME  # noqa: E402


def test_phone_numbers_with_spaced_separators_are_found():
    for number in ["(281) 491 - 3225", "(281) - 777 - 6237", "(678)-898- 2283", "281-491-3225", "+1 832 498 5155"]:
        assert PHONE.search(number), number


def test_dates_and_ids_are_not_phone_numbers():
    for text in ["2012 - 2014", "Jan 2012 - 12 2014", "Certification# X0209353-2609"]:
        assert not PHONE.search(text), text


def test_titled_names_are_masked_but_not_software():
    out = TITLED_NAME.sub(r"\1[NAME]", "Dr. Suleman Lalani , MD; Mr. Hale; Ms Office; Ms Visual Basic")
    assert out == "Dr. [NAME] , MD; Mr. [NAME]; Ms Office; Ms Visual Basic"


def test_names_before_a_credential_are_masked_but_not_places():
    # Two words, like a name: only leaving MD (Maryland) out of the credentials keeps it.
    out = CREDENTIAL_NAME.sub("[NAME]", "Edna Takahashi, RN ICU; Microsoft Office, PhD; Silver Spring, MD")
    assert out == "[NAME], RN ICU; Microsoft Office, PhD; Silver Spring, MD"
