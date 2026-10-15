"""data/1_knowledge/learning_resources/certifications.csv (plan D11) and its two counting scripts.

Run: pytest tests/test_certifications.py. No network: the Adzuna counter runs on a fake HTTP session.
"""
import re
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "data-eda" / "src"))

import count_cert_adzuna as adz  # noqa: E402
import count_cert_mentions as cm  # noqa: E402
from skillabus import paths  # noqa: E402

REQUIRED = ["cert", "vendor", "exam_code", "level", "roles", "skills", "aliases_ads", "cost_aud", "cost_usd",
            "official_url", "date_checked", "adzuna_query", "au_ads_count", "count_date", "local_ads_mentions",
            "report_signal", "hot"]
ROLES = set(adz.ROLES)
LEVELS = {"foundational", "associate", "professional", "expert"}


@pytest.fixture(scope="module")
def certs():
    return pd.read_csv(paths.CERTIFICATIONS, dtype=str, keep_default_na=False)


def split(s):
    return [x.strip() for x in s.split(";") if x.strip()]


# ------------------------------------------------------------------ the file
def test_columns_in_order(certs):
    assert list(certs.columns[: len(REQUIRED)]) == REQUIRED


def test_one_row_per_cert_and_query(certs):
    assert not certs["cert"].duplicated().any()
    assert not certs["adzuna_query"].str.lower().duplicated().any()
    assert (certs["adzuna_query"].str.strip() != "").all()
    assert 30 <= len(certs) <= 60


def test_every_role_has_at_least_two_certs_and_no_unknown_role(certs):
    per_role = certs["roles"].map(split).explode().value_counts()
    assert set(per_role.index) <= ROLES, set(per_role.index) - ROLES
    short = {r: int(per_role.get(r, 0)) for r in ROLES if per_role.get(r, 0) < 2}
    assert not short, short


def test_levels_dates_and_urls(certs):
    assert set(certs["level"]) <= LEVELS
    assert certs["date_checked"].str.fullmatch(r"\d{4}-\d{2}-\d{2}").all()
    assert certs["official_url"].str.startswith("https://").all()


def test_costs_are_numbers_or_varies(certs):
    for col in ("cost_aud", "cost_usd"):
        bad = [v for v in certs[col] if v != "varies" and not re.fullmatch(r"\d+(\.\d{1,2})?", v)]
        assert not bad, (col, bad)
    assert (certs["cost_basis"].str.strip() != "").all()


def test_skills_use_the_dictionary_spelling(certs):
    seed = pd.read_csv(paths.SKILLS_SEED, skiprows=1)
    canon = {c.lower(): c for c in seed["canonical"]}
    wrong = {s for row in certs["skills"] for s in split(row) if s.lower() in canon and s != canon[s.lower()]}
    assert not wrong, wrong


def test_each_cert_is_found_by_its_own_aliases(certs):
    patterns = cm.compile_aliases(certs)
    for row in certs.itertuples():
        first = split(row.aliases_ads)[0]
        assert row.cert in cm.find_mentions(f"Must hold {first}.", patterns), row.cert


def test_counts_blank_or_whole_numbers(certs):
    for col in ("au_ads_count", "local_ads_mentions", "au_ads_count_prev"):
        assert certs[col].str.fullmatch(r"\d*").all(), col
    assert set(certs["hot"]) <= {"", "yes", "no"}


# ------------------------------------------------------------------ local mention counter
CERTS = pd.DataFrame({
    "cert": ["CCNA", "CCNA Cybersecurity", "CKA", "CKAD", "CTFL", "CTAL-TAE", "CISA", "Network+"],
    "aliases_ads": ["CCNA", "CCNA Cybersecurity; CyberOps Associate", "CKA; Certified Kubernetes Administrator",
                    "CKAD", "ISTQB; ISTQB Foundation", "ISTQB Advanced", "CISA", "CompTIA Network+; Network+"],
})


@pytest.mark.parametrize("text, expected", [
    ("CCNA required", {"CCNA"}),
    ("CCNA Cybersecurity or CyberOps-Associate", {"CCNA Cybersecurity"}),       # longest match wins
    ("CCNA and CCNA Cybersecurity", {"CCNA", "CCNA Cybersecurity"}),
    ("CKAD preferred", {"CKAD"}),                                               # CKA is not inside CKAD
    ("certified kubernetes administrator", {"CKA"}),                            # long names ignore case
    ("cka", set()),                                                             # acronyms do not
    ("ISTQB Advanced level", {"CTAL-TAE"}),
    ("ISTQB Foundation, ideally ISTQB Advanced", {"CTFL", "CTAL-TAE"}),
    ("Cisa, Ciscos", set()),
    ("CompTIA Network+ or Security+", {"Network+"}),
    ("network engineer", set()),
])
def test_find_mentions(text, expected):
    assert cm.find_mentions(text, cm.compile_aliases(CERTS)) == expected


def test_load_ads_drops_the_same_job_board_ad_seen_twice(tmp_path):
    seek = tmp_path / "seek.csv"
    pd.DataFrame({"ad_id": ["s1"], "title": ["Data Scientist"], "description": ["CISA a plus"]}).to_csv(seek, index=False)
    recent = tmp_path / "recent.csv"
    pd.DataFrame({"ad_id": ["ats-gh-1"], "title": ["Network Engineer"], "description": ["CCNA required"]}).to_csv(
        recent, index=False)
    ats = tmp_path / "ats.csv"
    pd.DataFrame({"ad_id": ["gh-1", "gh-2"], "title": ["Network Engineer", "SRE"],
                  "description": ["CCNA required", "CKA, CCNA"]}).to_csv(ats, index=False)
    ads = cm.load_ads(seek, recent, [ats, tmp_path / "missing.csv"])
    assert len(ads) == 3
    table = cm.count_mentions(ads, CERTS)
    assert table.loc["CCNA", "total"] == 2 and table.loc["CKA", "total"] == 1 and table.loc["CISA", "total"] == 1
    assert table.loc["CCNA", "recent_2024_26"] == 1 and table.loc["CCNA", "ats_2026"] == 1


# ------------------------------------------------------------------ Adzuna counter, mocked HTTP
class FakeResponse:
    def __init__(self, status, payload):
        self.status_code, self._payload, self.text = status, payload, str(payload)

    def json(self):
        return self._payload


class FakeSession:
    """Adzuna stand-in: count = 1000 with no query, else the number given for the phrase."""

    def __init__(self, counts, status=200, total=1000):
        self.counts, self.status, self.total, self.calls = counts, status, total, []

    def get(self, url, params=None, timeout=None, verify=True):
        self.calls.append((url, dict(params)))
        if self.status != 200:
            return FakeResponse(self.status, {})
        q = params.get("what_phrase") or params.get("what")
        n = self.total if not q else self.counts.get(q, 0)
        return FakeResponse(200, {"count": n, "results": [{"id": "1"}] if n else []})


def small_certs():
    return pd.DataFrame({
        "cert": ["A", "B", "C", "D"],
        "roles": ["Cloud Engineer", "Cloud Engineer", "Cloud Engineer; DevOps/SRE", "Business Analyst"],
        "adzuna_query": ["AZ-104", "CKA", "Terraform Associate", "CBAP"],
        "au_ads_count": ["", "", "40", ""], "count_date": ["", "", "2026-10-01", ""],
        "au_ads_count_prev": ["", "", "", ""], "count_date_prev": ["", "", "", ""],
        "report_signal": ["", "", "", "Some Report 2026: listed"], "hot": ["", "", "", ""],
    })


def test_count_all_sends_one_phrase_call_per_row_and_keeps_the_previous_count():
    session = FakeSession({"AZ-104": 120, "CKA": 30, "Terraform Associate": 55, "CBAP": 3})
    out, everything = adz.count_all(small_certs(), session, delay=0, today="2026-10-16", app_id="id",
                                    app_key="key", retry_wait=0)
    assert everything == 1000
    assert len(session.calls) == 5                                   # the denominator + one per row
    url, params = session.calls[1]
    assert url.endswith("/jobs/au/search/1")
    assert params["results_per_page"] == 1 and params["what_phrase"] == "AZ-104" and "what" not in params
    assert params["app_id"] == "id" and params["app_key"] == "key"
    assert out["au_ads_count"].tolist() == ["120", "30", "55", "3"]
    assert set(out["count_date"]) == {"2026-10-16"}
    assert out.loc[2, "au_ads_count_prev"] == "40" and out.loc[2, "count_date_prev"] == "2026-10-01"


def test_count_all_stops_when_adzuna_ignores_the_phrase():
    session = FakeSession({"AZ-104": 1000})
    with pytest.raises(adz.PhraseIgnored):
        adz.count_all(small_certs(), session, delay=0, today="2026-10-16", app_id="i", app_key="k", retry_wait=0)


def test_words_mode_and_category_filter():
    session = FakeSession({"AZ-104": 7})
    adz.count_ads(session, "AZ-104", match="words", category="it-jobs", app_id="i", app_key="k", retry_wait=0)
    params = session.calls[0][1]
    assert params["what"] == "AZ-104" and "what_phrase" not in params and params["category"] == "it-jobs"


def test_bad_key_stops_the_run():
    with pytest.raises(SystemExit):
        adz.count_ads(FakeSession({}, status=401), "CKA", app_id="i", app_key="bad", retry_wait=0)


def test_rate_limited_call_is_retried_once_then_left_blank():
    session = FakeSession({}, status=429)
    assert adz.count_ads(session, "CKA", app_id="i", app_key="k", retry_wait=0) is None
    assert len(session.calls) == 2


def test_hot_rule():
    certs = small_certs()
    certs["au_ads_count"] = ["120", "30", "55", "3"]
    certs["count_date"] = "2026-10-16"
    certs.loc[2, ["au_ads_count_prev", "count_date_prev"]] = ["40", "2026-10-01"]
    out = adz.apply_hot_rule(certs).set_index("cert")
    assert out.loc["A", "hot"] == "yes" and "Cloud Engineer" in out.loc["A", "hot_reason"]   # top third of 3
    assert out.loc["B", "hot"] == "no"
    assert out.loc["C", "hot"] == "yes" and "DevOps/SRE" in out.loc["C", "hot_reason"]       # only DevOps cert
    assert "rising +38%" in out.loc["C", "hot_reason"]
    assert out.loc["D", "hot"] == "yes" and "Some Report 2026" in out.loc["D", "hot_reason"]
    certs["au_ads_count"] = ""
    assert set(adz.apply_hot_rule(certs)["hot"]) == {""}                                    # no counts, no flag


def test_main_end_to_end_on_a_copy(tmp_path, monkeypatch):
    src = tmp_path / "certs.csv"
    pd.read_csv(paths.CERTIFICATIONS, dtype=str, keep_default_na=False).head(3).to_csv(src, index=False)
    fake = FakeSession({})
    monkeypatch.setattr(adz.requests, "Session", lambda: fake)
    monkeypatch.setattr(adz.time, "sleep", lambda s: None)
    adz.main(["--certs", str(src), "--app-id", "i", "--app-key", "k", "--date", "2026-10-16"])
    out = pd.read_csv(src, dtype=str, keep_default_na=False)
    assert out["au_ads_count"].tolist() == ["0", "0", "0"] and set(out["count_date"]) == {"2026-10-16"}
    assert len(fake.calls) == 4
