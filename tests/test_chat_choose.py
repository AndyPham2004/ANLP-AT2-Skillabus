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
    assert not chat.named_in("Should I take 36121 or 36123 in Autumn?", passages)      # to compare, not taken
    assert not chat.named_in("Should I take Deep Learning next semester?", passages)


def test_abbreviations_are_spelled_out_for_retrieval():
    assert chat.spell_out("Which subject teaches ML or NLP?") == \
        "Which subject teaches machine learning or natural language processing?"
    assert chat.spell_out("Is AIR travel fine?") == "Is AIR travel fine?"                  # whole words only


def test_one_source_per_subject_name_and_closed_subjects_dropped():
    p = {"text": "x", "source": "s", "layer": "description"}
    passages = [{**p, "subject_code": "42028", "subject_name": "Deep Learning and Convolutional Neural Network"},
                {**p, "subject_code": "421028", "subject_name": "Deep Learning and Convolutional Neural Network"},
                {**p, "subject_code": "31250", "subject_name": "Introduction to Data Analytics"}]   # Bachelor-only
    sources = chat.by_subject(passages, set(), "C04372")
    assert [s["subject_code"] for s in sources] == ["42028"]
    assert chat.source_name(sources[0]) == "42028 Deep Learning and Convolutional Neural Network"


def test_sources_keep_what_the_answer_cites_or_names():
    s = [{"subject_code": c, "subject_name": n} for c, n in (("31005", "ML"), ("36118", "NLP"), ("43023", "AI"))]
    reply, kept = chat.cited_only("Take 43023 AI [1] or 36118 NLP [3].", s)          # marks numbered wrongly
    assert [k["subject_code"] for k in kept] == ["43023", "36118"] and reply == "Take 43023 AI or 36118 NLP."
    reply, kept = chat.cited_only("The Handbook covers it [3].", s)                     # no code: marks renumbered
    assert [k["subject_code"] for k in kept] == ["43023"] and reply == "The Handbook covers it [1]."


def test_a_choice_leaves_out_taken_and_named_subjects(stub):
    stub.replies = ["Consider 36121 Artificial Intelligence Principles and Applications."]
    reply, sources = chat.answer(TAKEN_TEXT, None, ["36103"], "C04372")
    context = stub.calls[0][-1]["content"]
    assert "36103 Statistical Thinking" in context.split("Subjects:")[0]           # told what was ticked
    listed = context.split("Subjects:")[1]
    assert "36121" in listed and not any(c in listed for c in ("36100 ", "36106 ", "36103 ", "94691 "))
    assert [s["subject_code"] for s in sources] == ["36121"]


def test_subjects_named_in_the_answer_link_to_the_handbook():
    url = "https://coursehandbook.uts.edu.au/subject/2026/"
    s = [{"subject_code": "36103", "subject_name": "Statistical Thinking for Data Science", "url": url + "36103"},
         {"subject_code": "36100", "subject_name": "Data Science for Innovation", "url": url + "36100"},
         {"subject_code": "94699", "subject_name": "Innovation Lab: Internship Project", "url": url + "94699"}]
    reply, rest = chat.link_subjects("Take 36103 Statistical Thinking for Data Science, then 36100. 36103 again.", s)
    assert reply == (f"Take [36103 Statistical Thinking for Data Science]({url}36103), then [36100]({url}36100). "
                     "36103 again.")                                                   # first mention only
    assert [r["subject_code"] for r in rest] == ["94699"]


def test_the_handbook_links_to_the_students_course_page():
    reply = chat.link_handbook("Please refer to the UTS Handbook and your coordinator.", "C04372")
    assert reply == ("Please refer to [Master of Data Science and Innovation (C04372) in the UTS Handbook]"
                     "(https://coursehandbook.uts.edu.au/course/2026/C04372) and your coordinator.")
    assert chat.link_handbook("See the UTS Handbook.", None) == \
        "See [the UTS Handbook](https://coursehandbook.uts.edu.au)."                      # not enrolled yet
    linked = "[MDSI](https://coursehandbook.uts.edu.au/course/2026/C04372) and the UTS Handbook"
    assert chat.link_handbook(linked, "C04372") == linked                                    # linked once only


def test_every_course_mentioned_links_to_its_handbook_page():
    url = "https://coursehandbook.uts.edu.au/course/2026/"
    reply = chat.link_courses("Compare the Master of Artificial Intelligence with C04372 and the Master of "
                              "Artificial Intelligence again.")
    assert reply == (f"Compare the [Master of Artificial Intelligence]({url}C04443) with [C04372]({url}C04372) and "
                     "the Master of Artificial Intelligence again.")                     # first mention only
    linked = f"[Master of Data Science and Innovation]({url}C04372), the Master of Data Science and Innovation"
    assert chat.link_courses(linked) == linked                                          # already linked: left alone
    assert len(chat.backend.courses()) == 44 and all(c.startswith("C") for c, _ in chat.backend.courses())


def test_a_subject_asked_about_stays_even_when_taken(stub):
    # 17 Oct: "36106 or 36120 for deep learning?" with both ticked as taken answered "couldn't find anything".
    stub.replies = ["36120 Advanced Machine Learning Application goes further than 36106; you have taken both."]
    reply, sources = chat.answer("36106 or 36120 for deep learning?", None, ["36106", "36120", "36100"], "C04372")
    context = stub.calls[0][-1]["content"]
    assert "asks about subjects they have already taken" in context and "36106" in context.split("Subjects:")[1]
    assert [s["subject_code"] for s in sources] == ["36120", "36106"]


def test_a_repeated_question_shows_its_sources_once(stub):
    # 17 Oct: the history carried the source list the app adds; the model copied it and the app added its own.
    stub.replies = ["Take 36118 Applied Natural Language Processing [1].\n\n[1] 36118 Applied Natural Language Processing"]
    history = [{"role": "user", "content": "Which subject teaches LLMs?"},
               {"role": "assistant", "content": "Take 36118 [1].\n\n[1] 36118 Applied Natural Language Processing",
                "answer": "Take 36118 [1]."}]
    reply, sources = chat.answer("Which subject teaches LLMs?", None, [], "C04372", history)
    assert stub.calls[0][2]["content"] == "Take 36118 [1]."                # the answer only, not the list
    assert reply == "Take 36118 Applied Natural Language Processing." and [s["subject_code"] for s in sources] == ["36118"]


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
