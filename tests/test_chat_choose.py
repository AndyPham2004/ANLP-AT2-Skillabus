"""Tests for the Handbook chat's subject choice (app/chat.py, 17 Oct): codes and names, one source per subject,
subjects taken or named left out, and one follow-up question for a vague request. The model is a stub, so no key
is needed and the run is the same on every machine."""
import re
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


def test_a_plan_without_a_course_asks_which_course_then_links_it(stub):
    # 17 Oct: not enrolled, "give me a study plan" pointed to the Handbook's front page; the course page is the help
    reply, sources = chat.answer("Give me a full 2-year study plan", None, [], None)
    assert sources is None and "Which UTS course" in reply and not stub.calls             # asked without the model
    history = [{"role": "user", "content": "Give me a full 2-year study plan"},
               {"role": "assistant", "content": reply, "followup": True}]
    reply, sources = chat.answer("Master of Data Science and Innovation", None, [], None, history)
    assert "(https://coursehandbook.uts.edu.au/course/2026/C04372)" in reply and sources == [] and not stub.calls
    # enrolled: the link only, no subjects "for your goal" when none was given (17 Oct test, Master of Cybersecurity)
    reply, sources = chat.answer("Give me a 2-year study plan", None, [], "C04430")
    assert "(https://coursehandbook.uts.edu.au/course/2026/C04430)" in reply and sources == [] and not stub.calls
    assert not re.search(r"\b\d{5,6}\b", reply)                                       # no subject codes
    assert chat.course_named("I'm in MDSI") == "C04372" and chat.course_named("the Master of Cybersecurity") == "C04430"


def test_fixes_from_the_17_oct_test_run(stub):
    # an invented code loses it; a real code gets its own name back
    assert chat.fix_codes('The subject is "36119 Machine Learning."') == 'The subject is "Machine Learning."'
    assert chat.fix_codes("1. 36106 Data Analytics for Business (runs in Spring)") == \
        "1. 36106 Machine Learning Algorithms and Applications (runs in Spring)"
    ok = "Take 36118 Applied Natural Language Processing in Autumn 2027."
    assert chat.fix_codes(ok) == ok
    assert chat.fix_codes("I have nothing on 99999.", "What does 99999 teach?") == "I have nothing on 99999."
    assert chat.fix_codes("See the Master of Business Analytics (C04444) page.") == "See the Master of Business Analytics page."
    assert chat.fix_codes("See C04372.") == "See C04372."
    # the model's own link to the Handbook front page is pointed at the course; no link inside a link
    reply = chat.link_handbook("See [the UTS Handbook](https://coursehandbook.uts.edu.au).", "C04379")
    assert reply == "See [the UTS Handbook](https://coursehandbook.uts.edu.au/course/2026/C04379)."
    bad = "See [MBA (C04444) in the UTS Handbook](https://coursehandbook.uts.edu.au/course/2026/C04444)."
    assert chat.link_handbook(chat.fix_codes(bad), "C04379") == \
        "See [MBA in the UTS Handbook](https://coursehandbook.uts.edu.au/course/2026/C04379)."
    # "Master of AI" is the Master of Artificial Intelligence; a subject named like the question comes first
    assert chat.course_named("Give me a study plan, Master of AI") == "C04443"
    assert "36122" in [p["subject_code"] for p in chat.name_matches("Which subject teaches Python?")]
    assert not chat.name_matches("I want to be a data scientist, give me a full 2-year study plan for my degree")
    # an answer that names no subject lists none
    assert chat.cited_only("I'm unable to answer that question.", [{"subject_code": "26899"}]) == \
        ("I'm unable to answer that question.", [])
    # a short question of its own is not read with the one before
    stub.replies = ["36106 Machine Learning Algorithms and Applications teaches it."]
    history = [{"role": "user", "content": "Give me a list of subjects that teach Python."},
               {"role": "assistant", "content": "36122 Python Programming", "answer": "36122 Python Programming"}]
    chat.answer("Which subject teaches ML?", None, [], "C04372", history)
    assert "Python Programming:" not in stub.calls[0][-1]["content"].split("Question:")[0].split("Subjects:")[1][:80]


def test_a_student_starting_a_course_gets_first_session_subjects(stub):
    # 17 Oct: "will be enrolling in the Master of Cybersecurity" got the Industry and Research Projects, "considering
    # the subjects you have already taken" (none ticked), and no link to the course
    stub.replies = ["For Autumn 2027 consider 42000 Cryptography."]
    reply, sources = chat.answer("What should I take this Autumn 2027 given I will be enrolling to master of "
                                 "cybersecurity?", None, [], None)
    sent = stub.calls[0][-1]["content"]
    listed = sent.split("Subjects:")[1]
    assert not re.search(r"\b(Project|Capstone|Internship|Research)\b", listed)
    assert "No subjects are marked as taken" in sent and "starting the course" in sent
    assert "(https://coursehandbook.uts.edu.au/course/2026/C04430)" in reply


def test_review_194_questions_are_answered_not_canned(stub):
    # Quan's review: PLAN caught "electives", "plan to", "core subjects", "credit points" and gave the fixed text
    for q in ("Which electives should I take for data engineering?",
              "I plan to take Deep Learning next semester, which one more should I pick?",
              "Which core subjects teach machine learning?", "How many credit points is 36118?"):
        stub.replies, stub.calls[:] = ["See 36106 Machine Learning Algorithms and Applications."], []
        reply, sources = chat.answer(q, None, [], "C04372")
        assert stub.calls and "I can't lay out a full study plan" not in reply, q
    for q in ("Give me a 2-year study plan", "Can you give me a full plan?", "What is the course structure?"):
        assert chat.PLAN.search(q), q


def test_review_194_fix_codes_keeps_a_second_subject():
    assert chat.fix_codes("Take 36118 Data Analytics and 36120 Advanced Machine Learning Application.") == \
        "Take 36118 Applied Natural Language Processing and 36120 Advanced Machine Learning Application."


def test_review_194_follow_on_needs_a_real_pointer():
    assert not chat.FOLLOW_ON.search("Which subject teaches more statistics?")
    assert not chat.FOLLOW_ON.search("Which subject teaches IT security?")
    assert not chat.FOLLOW_ON.search("What should I take this Autumn?")
    for q in ("Does it run in Spring?", "Give me two more", "How about the Master of Business Analytics?"):
        assert chat.FOLLOW_ON.search(q), q


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
