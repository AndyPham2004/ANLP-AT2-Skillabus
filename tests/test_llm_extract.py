"""Tier-3 extraction without calling OpenAI: a fake client returns canned JSON."""

import json
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from skillabus import llm_extract  # noqa: E402
from skillabus.text import mask_pii, sentence_with, text_units  # noqa: E402

AD = """Data Scientist - Python, SQL
Contact jane.doe@example.com or +61 412 345 678.

Key Requirements
- Strong programming experience with Python and SQL.
- In-depth knowledge of deep learning, Generative AI; LLM, GenAI etc.
- Strong analytical and problem-solving skills.
"""


class FakeClient:
    def __init__(self, skills):
        self.calls, self.sent = 0, []
        payload = json.dumps({"skills": skills})
        create = self._create(payload)
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=create))

    def _create(self, payload):
        def create(**kw):
            self.calls += 1
            self.sent.append(kw["messages"][-1]["content"])
            return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=payload))])
        return create


def test_keeps_only_skills_in_the_text_and_takes_the_sentence_from_the_text(tmp_path, monkeypatch):
    monkeypatch.setattr(llm_extract, "CACHE_DIR", tmp_path)
    client = FakeClient([
        {"text": "Python", "kind": "hard"},
        {"text": "LLM", "kind": "hard"},
        {"text": "problem-solving", "kind": "soft"},
        {"text": "Kubernetes", "kind": "hard"},   # not in the ad: must be dropped
        {"text": "python", "kind": "hard"},       # duplicate: must be dropped
    ])
    out = llm_extract.extract_llm(AD, client=client)
    assert [m["text"] for m in out] == ["Python", "LLM", "problem-solving"]
    assert all(m["method"] == "llm" for m in out)
    assert out[1]["sentence"].startswith("In-depth knowledge of deep learning")
    assert out[2]["kind"] == "soft"


def test_masks_personal_details_before_the_call(tmp_path, monkeypatch):
    monkeypatch.setattr(llm_extract, "CACHE_DIR", tmp_path)
    client = FakeClient([])
    llm_extract.extract_llm(AD, client=client)
    sent = client.sent[0]
    assert "jane.doe@example.com" not in sent and "412 345 678" not in sent
    assert "[EMAIL]" in sent and "[PHONE]" in sent


def test_second_run_uses_the_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(llm_extract, "CACHE_DIR", tmp_path)
    client = FakeClient([{"text": "SQL", "kind": "hard"}])
    first = llm_extract.extract_llm(AD, client=client)
    second = llm_extract.extract_llm(AD, client=client)
    assert first == second and client.calls == 1     # a cached text never reaches the key check in _call


def test_no_key_and_no_cache_raises_runtime_error(tmp_path, monkeypatch):
    monkeypatch.setattr(llm_extract, "CACHE_DIR", tmp_path)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    try:
        llm_extract.extract_llm(AD)
    except RuntimeError as error:
        assert "OPENAI_API_KEY" in str(error)
    else:
        raise AssertionError("expected RuntimeError")
    assert not list(tmp_path.iterdir())   # nothing cached


def test_reads_the_evaluation_cache_but_writes_only_the_runtime_cache(tmp_path, monkeypatch):
    runtime, evaluation = tmp_path / "runtime", tmp_path / "evaluation"
    monkeypatch.setattr(llm_extract, "CACHE_DIR", runtime)
    monkeypatch.setattr(llm_extract, "EVAL_CACHE_DIR", evaluation)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    name = llm_extract._cache_name(mask_pii(AD))
    evaluation.mkdir()
    (evaluation / name).write_text(json.dumps([{"text": "SQL", "kind": "hard"}]), encoding="utf-8")
    assert [m["text"] for m in llm_extract.extract_llm(AD)] == ["SQL"]   # no key needed: committed answer
    assert not runtime.exists()                                           # reading writes nothing
    client = FakeClient([{"text": "Python", "kind": "hard"}])
    assert [m["text"] for m in llm_extract.extract_llm(AD.replace("SQL", "Go"), client=client)] == ["Python"]
    assert sorted(p.parent.name for p in tmp_path.rglob("*.json")) == ["evaluation", "runtime"]


def replying(content):
    client = FakeClient([])
    client.chat.completions.create = lambda **kw: SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))])
    return client


def test_a_reply_that_is_not_json_returns_nothing_and_is_not_cached(tmp_path, monkeypatch):
    # 17 Oct: such a reply was cached as [], so that ad or resume never got GPT skills again.
    monkeypatch.setattr(llm_extract, "CACHE_DIR", tmp_path)
    for content in ("not json", "", None):
        assert llm_extract.extract_llm(AD, client=replying(content)) == []
        assert not list(tmp_path.iterdir()), content                 # nothing cached
    good = FakeClient([{"text": "SQL", "kind": "hard"}])
    assert [m["text"] for m in llm_extract.extract_llm(AD, client=good)] == ["SQL"]   # the next run asks again
    assert good.calls == 1


def test_a_reply_with_no_skills_is_cached(tmp_path, monkeypatch):
    # An answer that says "no skills" is an answer: the next run reads it instead of paying for it again.
    monkeypatch.setattr(llm_extract, "CACHE_DIR", tmp_path)
    assert llm_extract.extract_llm(AD, client=FakeClient([])) == []
    assert len(list(tmp_path.iterdir())) == 1


def test_whole_word_sentence_match():
    units = text_units("Your role is varied.\n- Experience with R and Python.")
    assert sentence_with("R", units) == "Experience with R and Python."
    assert sentence_with("Scala", units) is None


def test_mask_pii_leaves_skills_alone():
    assert mask_pii("Python, SQL, C++ and 3-5 years") == "Python, SQL, C++ and 3-5 years"


def test_mask_pii_keeps_ranges_and_short_numbers():
    text = "Seek ads 2019-2022, salary 120000-140000, 3-5 years, ref 2026/10"
    assert mask_pii(text) == text


def test_mask_pii_masks_australian_phone_formats():
    for phone in ("0412 345 678", "+61 2 9123 4567", "(02) 9123 4567", "0412-345-678"):
        assert mask_pii(f"Call {phone} today") == "Call [PHONE] today", phone
