"""Tests for src/skillabus/evaluate.py. Every expected value is worked out by hand in the comment beside it.

Run from the repo root:  python -m pytest tests/test_evaluate.py   (or: python tests/test_evaluate.py)
The evaluate.py tests need only the standard library. EvalRunTables imports skillabus.eval_run, which loads the
pipeline and its packages (requirements.txt); its last test runs the dictionary tier on the committed labels.
"""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from skillabus import evaluate as ev  # noqa: E402


def _write(path, text):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


class PhraseEvidenceTests(unittest.TestCase):
    def test_gold_phrase_inside_ranked_sentence_counts(self):
        ranked = ["Built XGBoost models for churn.", "Led a team of four."]
        gold = {"xgboost models"}
        self.assertEqual(ev.hit_at_k(ranked, gold, 5), 1.0)
        self.assertEqual(ev.reciprocal_rank(ranked, gold), 1.0)
        self.assertAlmostEqual(ev.precision_at_k(ranked, gold, 5), 0.2)

    def test_phrase_not_in_any_sentence_scores_zero(self):
        self.assertEqual(ev.hit_at_k(["Led a team of four."], {"xgboost"}, 5), 0.0)


class Dictionary(unittest.TestCase):
    # the unsure mark '?' on ad labels: Files.test_unsure_mark_is_dropped_from_ad_skill_labels
    def test_restrict_to_dictionary(self):
        got = ev.restrict_to({"1": {"sql", "telecommunications"}}, ["SQL", "Python"])
        self.assertEqual(got, {"1": {"sql"}})


class Extraction(unittest.TestCase):
    def test_prf_hand_example(self):
        gold = {"ad1": {"python", "sql", "tableau"}}
        pred = {"ad1": {"sql", "tableau", "spark"}}
        s = ev.extraction_scores(gold, pred)
        # tp = {sql, tableau} = 2, fp = {spark} = 1, fn = {python} = 1 -> P = R = 2/3, F1 = 2/3
        self.assertEqual((s["tp"], s["fp"], s["fn"]), (2, 1, 1))
        self.assertAlmostEqual(s["precision"], 2 / 3)
        self.assertAlmostEqual(s["f1"], 2 / 3)

    def test_micro_average_pools_across_ads(self):
        gold = {"a": {"x", "y"}, "b": {"z"}}
        pred = {"a": {"x"}, "b": {"z", "w"}}
        s = ev.extraction_scores(gold, pred)
        # a: tp1 fn1 ; b: tp1 fp1 -> tp 2, fp 1, fn 1 pooled
        self.assertEqual((s["tp"], s["fp"], s["fn"]), (2, 1, 1))

    def test_missing_ad_counts_as_empty_prediction(self):
        s = ev.extraction_scores({"a": {"x", "y"}}, {})
        self.assertEqual((s["tp"], s["fp"], s["fn"]), (0, 0, 2))
        self.assertEqual(s["f1"], 0.0)

    def test_labels_are_normalised(self):
        self.assertEqual(ev.norm("  Machine   Learning "), "machine learning")

    def test_mentions_filter_by_method_and_map_labels(self):
        mentions = {
            "ad1": [
                {"skill_label": "Python (computer programming)", "method": "dictionary"},
                {"skill_label": "deep learning", "method": "llm"},
            ]
        }
        got = ev.mentions_to_sets(mentions, "dictionary", {"Python (computer programming)": "python"})
        self.assertEqual(got, {"ad1": {"python"}})
        self.assertEqual(ev.mentions_to_sets(mentions)["ad1"], {"python (computer programming)", "deep learning"})

    def test_mentions_use_canonical_then_text(self):
        # extract() output (tiers 1-2): `canonical` is the dictionary name, or None for an off-dictionary candidate
        mentions = {
            "ad1": [
                {"text": "Python3", "canonical": "Python", "method": "ner"},
                {"text": "Prompt Engineering", "canonical": None, "method": "ner"},
            ]
        }
        self.assertEqual(ev.mentions_to_sets(mentions), {"ad1": {"python", "prompt engineering"}})

    def test_errors_list_both_kinds(self):
        errs = ev.extraction_errors({"a": {"x"}}, {"a": {"y"}})
        self.assertEqual({(e["skill"], e["error"]) for e in errs}, {("x", "false_negative"), ("y", "false_positive")})


class Matching(unittest.TestCase):
    def test_rank_metrics(self):
        ranked = ["s1", "s2", "s3"]
        self.assertAlmostEqual(ev.reciprocal_rank(ranked, {"s3"}), 1 / 3)  # first hit at rank 3
        self.assertEqual(ev.reciprocal_rank(ranked, {"zzz"}), 0.0)
        self.assertAlmostEqual(ev.precision_at_k(ranked, {"s3"}, k=5), 0.2)  # 1 hit / k=5
        self.assertAlmostEqual(ev.precision_at_k(ranked, {"s1", "s3"}, k=2), 0.5)  # 1 hit in top 2
        self.assertEqual(ev.hit_at_k(ranked, {"s3"}, k=2), 0.0)
        self.assertEqual(ev.hit_at_k(ranked, {"s3"}, k=3), 1.0)

    def test_ranking_scores_skip_missing_skills(self):
        cases = [(["a", "b"], {"a"}), (["a", "b"], {"b"}), (["a", "b"], set())]  # RR 1, 1/2, skipped
        s = ev.ranking_scores(cases, k=5)
        self.assertEqual((s["n"], s["n_skipped"]), (2, 1))
        self.assertAlmostEqual(s["mrr"], 0.75)
        self.assertEqual(s["hit_at_k"], 1.0)

    def test_status_scores(self):
        gold = {1: "have", 2: "have", 3: "missing", 4: "partial"}
        pred = {1: "have", 2: "missing", 3: "missing", 4: "partial"}
        s = ev.status_scores(gold, pred)
        self.assertAlmostEqual(s["accuracy"], 0.75)  # 3 of 4
        self.assertEqual(s["confusion"][("have", "missing")], 1)
        # have: tp1 fp0 fn1 -> P1 R.5 F1 2/3 ; missing: tp1 fp1 fn0 -> P.5 R1 F1 2/3 ; partial: F1 1
        self.assertAlmostEqual(s["macro_f1"], (2 / 3 + 2 / 3 + 1) / 3)

    def test_matching_gold_from_rows(self):
        rows = [
            {"pair_id": "P1", "skill_label": "sql", "gold_status": "have", "resume_evidence_text": "wrote sql queries"},
            {"pair_id": "P1", "skill_label": "spark", "gold_status": "partial", "resume_evidence_text": "used hadoop"},
            {"pair_id": "P1", "skill_label": "go", "gold_status": "missing", "resume_evidence_text": ""},
        ]
        g = ev.matching_gold(rows)
        self.assertEqual(g[("P1", "sql")]["relevant"], {"wrote sql queries"})
        self.assertEqual(g[("P1", "spark")]["relevant"], {"used hadoop"})
        self.assertEqual(g[("P1", "go")]["relevant"], set())
        self.assertEqual(ev.matching_gold(rows, include_partial=False)[("P1", "spark")]["relevant"], set())


class Subjects(unittest.TestCase):
    def test_p_at_k_counts_only_labelled_pairs(self):
        gold = {("machine learning", "36106"): "y", ("machine learning", "36104"): "n", ("sql", "36100"): "partly"}
        recs = {"machine learning": ["36106", "36104", "99999"], "sql": ["36100"]}
        s = ev.subject_precision_at_k(recs, gold, k=3)
        # labelled: 36106 y, 36104 n, 36100 partly = 3 ; relevant (y + partly) = 2 ; 99999 unlabelled
        self.assertAlmostEqual(s["p_at_k"], 2 / 3)
        self.assertEqual((s["labelled"], s["total_recommended"]), (3, 4))
        self.assertAlmostEqual(s["coverage"], 0.75)
        self.assertAlmostEqual(ev.subject_precision_at_k(recs, gold, k=3, include_partly=False)["p_at_k"], 1 / 3)

    def test_k_limits_the_list(self):
        gold = {("sql", "A"): "n", ("sql", "B"): "y"}
        self.assertEqual(ev.subject_precision_at_k({"sql": ["A", "B"]}, gold, k=1)["p_at_k"], 0.0)


class Chat(unittest.TestCase):
    def test_parse_judge_handles_wrapped_json(self):
        reply = 'Sure!\n```json\n{"relevance": 4, "faithfulness": 5, "reason": "ok"}\n```'
        self.assertEqual(ev.parse_judge(reply)["faithfulness"], 5)

    def test_parse_judge_rejects_bad_scores(self):
        with self.assertRaises(ValueError):
            ev.parse_judge('{"relevance": 9, "faithfulness": 3}')
        with self.assertRaises(ValueError):
            ev.parse_judge("no json here")

    def test_judge_answers_keeps_unparsed_replies(self):
        replies = iter(['{"relevance": 5, "faithfulness": 3, "reason": "x"}', "garbage"])
        items = [{"question": "q", "reference": "r", "answer": "a", "passages": ["p"]}] * 2
        judged = ev.judge_answers(items, lambda prompt: next(replies))
        s = ev.chat_summary(judged)
        self.assertEqual((s["n"], s["n_unparsed"]), (1, 1))
        self.assertEqual(s["relevance_mean"], 5.0)

    def test_prompt_contains_all_parts(self):
        p = ev.judge_prompt("Which subject teaches NLP?", "36118", "36118 does", ["36118 covers LLMs"])
        for part in ("Which subject teaches NLP?", "36118 covers LLMs", "Reply with JSON only"):
            self.assertIn(part, p)


class Agreement(unittest.TestCase):
    def test_kappa_textbook_example(self):
        # 50 items: both yes 20, A yes/B no 5, A no/B yes 10, both no 15.
        # observed = 35/50 = .7 ; expected = (25/50)(30/50) + (25/50)(20/50) = .3 + .2 = .5 ; kappa = .2/.5 = .4
        a = [1] * 20 + [1] * 5 + [0] * 10 + [0] * 15
        b = [1] * 20 + [0] * 5 + [1] * 10 + [0] * 15
        self.assertAlmostEqual(ev.cohens_kappa(a, b), 0.4)

    def test_perfect_and_chance(self):
        self.assertEqual(ev.cohens_kappa([1, 0, 1, 0], [1, 0, 1, 0]), 1.0)
        self.assertAlmostEqual(ev.cohens_kappa([1, 1, 0, 0], [1, 0, 1, 0]), 0.0)  # 50% observed = 50% expected
        self.assertEqual(ev.cohens_kappa([1, 1, 1], [1, 1, 1]), 1.0)  # both constant, identical

    def test_bands(self):
        self.assertEqual(ev.interpret_kappa(0.4), "fair")
        self.assertEqual(ev.interpret_kappa(0.41), "moderate")
        self.assertEqual(ev.interpret_kappa(0.9), "almost perfect")
        self.assertEqual(ev.interpret_kappa(-0.1), "poor")

    def test_annotator_agreement_uses_dictionary_for_negatives(self):
        a = {"ad1": {"python", "sql"}, "ad2": {"spark"}}
        b = {"ad1": {"python"}, "ad2": {"spark", "tableau"}}
        universe = ["python", "sql", "spark", "tableau", "go", "r"]  # 6 skills x 2 ads = 12 items
        r = ev.annotator_agreement(a, b, universe=universe)
        # both yes: python@ad1, spark@ad2 = 2 ; A only: sql@ad1 = 1 ; B only: tableau@ad2 = 1 ; both no: 8
        self.assertEqual((r["both_yes"], r["a_only"], r["b_only"], r["both_no"]), (2, 1, 1, 8))
        self.assertAlmostEqual(r["observed_agreement"], 10 / 12)
        # expected = (3/12)(3/12) + (9/12)(9/12) = 90/144 ; kappa = (120/144 - 90/144) / (54/144) = 30/54
        self.assertAlmostEqual(r["kappa"], 30 / 54)

    def test_disagreements(self):
        d = ev.disagreements({"ad1": {"a", "b"}}, {"ad1": {"b", "c"}})
        self.assertEqual({(x["skill"], x["only"]) for x in d}, {("a", "a"), ("c", "b")})


class Files(unittest.TestCase):
    def test_unsure_mark_is_dropped_from_ad_skill_labels(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "ad_skills.csv")
            _write(path, "ad_id,skill_label,in_dictionary,evidence_text,annotator\n"
                         "ad1,?Telecommunications,n,?telco experience,Akash\nad1, ? SQL,y,sql,Akash\n")
            self.assertEqual(ev.load_ad_skills(path), {"ad1": {"telecommunications", "sql"}})

    def test_loaders_and_cli_kappa(self):
        with tempfile.TemporaryDirectory() as tmp:
            header = "ad_id,skill_label,in_dictionary,evidence_text,annotator\n"
            both = header + "ad1,Python,y,knows python,Hoai Thuong\nad1,SQL,y,sql,Akash\nad1,Python,y,python,Akash\n"
            path = os.path.join(tmp, "ad_skills.csv")
            _write(path, both)
            self.assertEqual(ev.load_ad_skills(path, "akash"), {"ad1": {"sql", "python"}})
            self.assertEqual(ev.load_ad_skills(path, "Hoai Thuong"), {"ad1": {"python"}})
            seed = os.path.join(tmp, "seed.csv")
            _write(seed, "# comment line\ncanonical,category,strict,aliases\nPython,P,0,python\nSQL,P,0,sql\nGo,P,0,golang\n")
            self.assertEqual(ev.load_dictionary(seed), ["go", "python", "sql"])
            self.assertEqual(ev.main(["kappa", path, path, "--a-name", "Hoai Thuong", "--b-name", "Akash", "--dictionary", seed]), 0)


class EvalRunTables(unittest.TestCase):
    """--all must say what it could not run instead of failing or leaving a table out silently."""

    def test_skipped_tier_and_missing_files_are_listed(self):
        from skillabus.eval_run import tables_md
        text = tables_md({}, {"ner": "RuntimeError: needs spaCy"}, "not run: one annotator", {"Chat judge": "not run: file missing"})
        self.assertIn("| ner | not run |", text)
        self.assertIn("RuntimeError: needs spaCy", text)
        self.assertIn("not run: one annotator", text)
        self.assertIn("- Chat judge: not run: file missing", text)

    def test_subject_and_chat_tables(self):
        from skillabus.eval_run import tables_md
        pk = {"k": 3, "p_at_k": 0.5, "relevant": 1, "labelled": 2, "total_recommended": 4, "coverage": 0.5}
        subject = {"n_pairs": 2, "n_skills": 1, "methods": {"tfidf": {"with_partly": pk, "y_only": pk}}, "skipped": {"embed": "ImportError: no model"}}
        chat = {"n_questions": 1, "retrieval": {"tfidf": {"hit_at_k": 1.0, "subject_recall_at_k": 0.5}}, "skipped": {}}
        text = tables_md({}, {}, "k", {"subject": subject, "chat": chat, "Chat LLM judge": "not run: no key"})
        self.assertIn("| tfidf | 0.500 | 0.500 | 2 / 4 | 0.500 |", text)
        self.assertIn("| embed | not run |", text)
        self.assertIn("| tfidf | 1.000 | 0.500 |", text)
        self.assertIn("- Chat LLM judge: not run: no key", text)

    def test_run_all_dictionary_tier_writes_the_tables(self):
        """Smoke test on the committed labels: the dictionary tier must run and reach the tables.

        run_all returns 0 and writes the table headings even when a tier fails (it lists the tier as "not run"),
        so only the tier's own row shows that it ran.
        """
        import tempfile
        from pathlib import Path
        from skillabus import paths
        from skillabus.eval_run import run_all
        if not (paths.AD_SKILLS.exists() and paths.CV_JD_PAIRS.exists() and paths.SEEK_ADS.exists() and paths.RESUMES.exists()):
            self.skipTest("labelled sets or their inputs are not in this checkout")
        with tempfile.TemporaryDirectory() as tmp:
            run_all(("dictionary",), tmp)
            text = (Path(tmp) / "eval_tables.md").read_text(encoding="utf-8")
            self.assertIn("| dictionary | all skills |", text)
            self.assertNotIn("| dictionary | not run |", text)


if __name__ == "__main__":
    unittest.main()
