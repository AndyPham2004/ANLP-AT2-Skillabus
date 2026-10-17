"""Tests for the Handbook chat's subject choice (app/chat.py, 17 Oct): codes and names, one source per subject,
subjects taken or named left out, and one follow-up question for a vague request. The model is a stub, so no key
is needed and the run is the same on every machine."""
import sys
import types
from pathlib import Path

import pytest

pytestmark = pytest.mark.usefixtures("tfidf_only")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

import chat  # noqa: E402

TAKEN_TEXT = ("I already took Data Science for Innovation, Machine Learning and Algorightms, Data Visualization and "
              "Python Programming. I'm planning Deep Learning. Which one more should I pick?")


class StubOpenAI:
    """Answers in turn from `replies` and records the messages it was sent."""
    replies: list[str] = []
    calls: list[list[dict]] = []

    def __init__(self):
        self.chat = types.SimpleNamespace(completions=types.SimpleNamespace(create=self._create))

    def _create(self, model, temperature, messages):
        StubOpenAI.calls.append(messages)
        text = StubOpenAI.replies.pop(0)
        return types.SimpleNamespace(choices=[types.SimpleNamespace(message=types.SimpleNamespace(content=text))])


@pytest.fixture
def stub(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test")
    monkeypatch.setitem(sys.modules, "openai", types.SimpleNamespace(OpenAI=StubOpenAI))
    StubOpenAI.replies, StubOpenAI.calls = [], []
    return StubOpenAI


def test_subjects_the_question_names_are_found_with_typos():
    passages = chat.subject_passages(chat.backend.course_subjects("C04372"), set())
    assert {"36100", "36106", "36104", "36122", "94691"} <= chat.named_in(TAKEN_TEXT, passages)
    assert not chat.named_in("Which subject teaches large language models?", passages)


def test_one_source_per_subject_name_and_closed_subjects_dropped():
    p = {"text": "x", "source": "s", "layer": "description"}
    passages = [{**p, "subject_code": "42028", "subject_name": "Deep Learning and Convolutional Neural Network"},
                {**p, "subject_code": "421028", "subject_name": "Deep Learning and Convolutional Neural Network"},
                {**p, "subject_code": "31250", "subject_name": "Introduction to Data Analytics"}]   # Bachelor-only
    sources = chat.by_subject(passages, set(), "C04372")
    assert [s["subject_code"] for s in sources] == ["42028"]
    assert chat.source_name(sources[0]) == "42028 Deep Learning and Convolutional Neural Network"


def test_sources_keep_what_the_answer_cites_or_names():
    s = [{"subject_code": c, "subject_name": n} for c, n in (("1", "A"), ("36118", "NLP"), ("43023", "AI"))]
    reply, kept = chat.cited_only("Take 36118 NLP [2] or 43023 AI.", s)
    assert [k["subject_code"] for k in kept] == ["36118", "43023"] and "[1]" in reply and "[2]" not in reply


def test_a_choice_leaves_out_taken_and_named_subjects(stub):
    stub.replies = ["Consider 36121 Artificial Intelligence Principles and Applications."]
    reply, sources = chat.answer(TAKEN_TEXT, None, ["36103"], "C04372")
    context = stub.calls[0][-1]["content"]
    assert "36103 Statistical Thinking" in context.split("Subjects:")[0]           # told what was ticked
    listed = context.split("Subjects:")[1]
    assert "36121" in listed and not any(c in listed for c in ("36100 ", "36106 ", "36103 ", "94691 "))
    assert [s["subject_code"] for s in sources] == ["36121"]


def test_a_vague_request_gets_one_follow_up_then_an_answer(stub):
    stub.replies = ["FOLLOW-UP: What is your goal?", "Take 94693 Big Data Engineering [1]."]
    reply, sources = chat.answer("Which subject should I take?", None, [], "C04372")
    assert sources is None and reply == "What is your goal?"
    history = [{"role": "user", "content": "Which subject should I take?"},
               {"role": "assistant", "content": reply, "followup": True}]
    reply, sources = chat.answer("Data engineering", None, [], "C04372", history)
    sent = stub.calls[1]
    assert "do not ask another" in sent[0]["content"]
    assert [m["content"] for m in sent[1:3]] == ["Which subject should I take?", "What is your goal?"]
    assert sources and sources[0]["subject_code"] == "94693"
