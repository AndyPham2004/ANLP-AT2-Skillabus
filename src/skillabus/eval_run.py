"""Run the whole evaluation and write the tables of report section 6. Owner: Hoai Thuong.

    python -m skillabus.evaluate --all [--methods dictionary,ner,llm] [--out data/processed]

For each extraction tier that can run here it writes <out>/eval_results.json (dictionary) or
<out>/eval_results_<tier>.json, and one <out>/eval_tables.md with the tables of section 6. A tier that
cannot run (no spaCy, no API key and no cached LLM answers) is listed as "not run" with the reason.
Stages whose labelled file does not exist yet (skill-subject pairs, chat questions) and kappa without a
second annotator are listed the same way, so the output always says what is missing.

evaluate.py stays standard-library only; this module imports the pipeline and is loaded only by --all.
"""
from __future__ import annotations

import csv
import json
import os
import re
from pathlib import Path

from . import evaluate as ev
from .extract import extract
from .match import match, rank_evidence

ROOT = Path(__file__).resolve().parents[2]
ADS = ROOT / "data-eda/data/clean/jobs_au_seek_datascientist_2019-2022_clean.csv"
RES = ROOT / "data-eda/data/clean/resumes_us_2021_clean.csv"
DICT = ROOT / "data/processed/skills_seed_v2.csv"
LAB = ROOT / "data/labels"
TIERS = ("dictionary", "ner", "llm")
GOLD_ANNOTATOR = "hoaithuongnguyen-uts"   # whose ad_skills.csv rows are the extraction gold; the other annotator is for kappa only


def _table(path: Path, key: str, field: str) -> dict:
    csv.field_size_limit(10**9)
    with open(path, newline="", encoding="utf-8") as f:
        return {r[key]: r[field] for r in csv.DictReader(f)}


def run_tier(method: str, gold_annotator: str | None = GOLD_ANNOTATOR) -> dict:
    """Extraction scores, matching (end to end and matching only) and evidence ranking for one tier."""
    ads, res = _table(ADS, "ad_id", "description"), _table(RES, "resume_id", "resume_text")
    dic = ev.load_dictionary(str(DICT))
    out: dict = {"method": method}

    gold = ev.load_ad_skills(str(LAB / "ad_skills.csv"), gold_annotator)   # one annotator: a second one's rows must not enlarge the gold set
    pred = {ad: {ev.norm(m.get("canonical") or m.get("skill_label") or m["text"]) for m in extract(ads[ad], method)}
            for ad in gold}
    out["extraction_all"] = ev.extraction_scores(gold, pred)
    out["extraction_dictionary_skills"] = ev.extraction_scores(ev.restrict_to(gold, dic), ev.restrict_to(pred, dic))
    out["extraction_errors"] = ev.extraction_errors(ev.restrict_to(gold, dic), ev.restrict_to(pred, dic))

    rows = ev.load_cv_jd_pairs(str(LAB / "cv_jd_pairs.csv"))
    canon = {ev.norm(r["canonical"]): r["canonical"] for r in ev._rows(str(DICT)) if r.get("canonical")}
    by_pair: dict[str, list[dict]] = {}
    for r in rows:
        by_pair.setdefault(r["pair_id"], []).append(r)
    res_cache: dict = {}
    out["n_pairs"] = len(by_pair)
    for setting in ("end_to_end", "matching_only"):
        g_status, p_status, cases, detail = {}, {}, [], []
        for pid, rs in by_pair.items():
            ad_id, rid = rs[0]["ad_id"], rs[0]["resume_id"]
            res_sk = res_cache.setdefault(rid, extract(res[rid], method))
            if setting == "end_to_end":
                ad_sk = extract(ads[ad_id], method)
            else:
                ad_sk = [{"text": canon[r["skill_label"]], "canonical": canon[r["skill_label"]], "method": "gold",
                          "sentence": canon[r["skill_label"]]} for r in rs]
            got = {ev.norm(x["skill_label"]): x["status"] for x in match(ad_sk, res_sk)}
            for r in rs:
                k = (pid, r["skill_label"])
                g_status[k] = r["gold_status"]
                p_status[k] = got.get(r["skill_label"], "not_extracted")
                if setting == "end_to_end" and r["gold_status"] in ("have", "partial") and r["resume_evidence_text"]:
                    cases.append((rank_evidence(canon[r["skill_label"]], res[rid]), {r["resume_evidence_text"]}))
                if g_status[k] != p_status[k]:
                    detail.append({"pair": pid, "skill": r["skill_label"], "gold": g_status[k], "pred": p_status[k]})
        st = ev.status_scores(g_status, {k: ("missing" if v == "not_extracted" else v) for k, v in p_status.items()})
        st["confusion"] = {f"{g}->{p}": n for (g, p), n in st["confusion"].items()}
        out[f"matching_{setting}"] = st
        out[f"matching_{setting}_errors"] = detail
        if setting == "end_to_end":
            out["ad_skill_not_extracted"] = sum(v == "not_extracted" for v in p_status.values())
            out["ranking"] = ev.ranking_scores(cases, k=5)
    return out


def kappa_result() -> dict | str:
    """Kappa between two annotators in data/labels/ad_skills.csv, or the reason it cannot be computed.

    "dictionary" restricts both sides to dictionary skills (every unlabelled dictionary skill counts as an agreed
    absence); "all" also counts free-text labels, which only one annotator may have written, so it is lower.
    """
    path = LAB / "ad_skills.csv"
    names = sorted({r.get("annotator", "").strip() for r in ev._rows(str(path)) if r.get("annotator", "").strip()})
    if len(names) < 2:
        return f"not run: ad_skills.csv has labels from {len(names)} annotator ({', '.join(names) or 'none'}); a second annotator's rows are needed (#63)"
    a, b = ev.load_ad_skills(str(path), names[0]), ev.load_ad_skills(str(path), names[1])
    shared = sorted(set(a) & set(b))
    if not shared:
        return f"not run: {names[0]} and {names[1]} share no ads"
    universe = ev.load_dictionary(str(DICT))
    res = ev.annotator_agreement(ev.restrict_to(a, universe), ev.restrict_to(b, universe), shared, universe)
    res["all_labels"] = ev.annotator_agreement(a, b, shared, universe)
    res["annotators"] = names[:2]
    return res


SUBJECT_METHODS = ("keyword", "tfidf", "embed")
CODE = re.compile(r"(?<!\d)(\d{5})(?!\d)")


def subject_result(methods=SUBJECT_METHODS) -> dict:
    """Subject P@3 for each retrieval method on data/labels/skill_subject_pairs.csv.

    Each labelled skill is looked up with recommend.subject_evidence(); the subjects are taken best first, one per code.
    A method that cannot run here (no sentence-transformers) is listed under "skipped" with the reason.
    """
    from .recommend import subject_evidence
    gold = ev.load_skill_subject_pairs(str(LAB / "skill_subject_pairs.csv"))
    canon = {ev.norm(r["canonical"]): r["canonical"] for r in ev._rows(str(DICT)) if r.get("canonical")}
    skills = sorted({skill for skill, _ in gold})
    out: dict = {"n_pairs": len(gold), "n_skills": len(skills), "methods": {}, "skipped": {}}
    for m in methods:
        try:
            found = subject_evidence([canon.get(s, s) for s in skills], method=m)
        except (RuntimeError, ImportError, OSError, ValueError) as error:
            out["skipped"][m] = f"{type(error).__name__}: {str(error).splitlines()[0][:120]}"
            continue
        recs = {s: list(dict.fromkeys(e["subject_code"] for e in found.get(canon.get(s, s), []))) for s in skills}
        out["methods"][m] = {"with_partly": ev.subject_precision_at_k(recs, gold, 3, True),
                             "y_only": ev.subject_precision_at_k(recs, gold, 3, False)}
    return out


def chat_result(call_llm=None, methods=("tfidf", "embed"), k: int = 5) -> dict:
    """Chat questions: did retrieval bring back the subjects the reference answer cites (no API needed),
    and, when call_llm is given, the LLM judge's relevance and faithfulness for the answers built from those passages.

    call_llm(prompt) -> reply text. Used for both the answer and the judge, so a cached or fake client works.
    """
    from .rag import retrieve
    questions = ev._rows(str(LAB / "chat_questions.csv"))
    out: dict = {"n_questions": len(questions), "retrieval": {}, "skipped": {}}
    for m in methods:
        try:
            hits, recalls, per_q = [], [], []
            for q in questions:
                want = set(CODE.findall(q["source"]))
                got = [p["subject_code"] for p in retrieve(q["question"], k=k, method=m) if p.get("subject_code")]
                hit = bool(want & set(got))
                recall = len(want & set(got)) / len(want) if want else 0.0
                hits.append(hit)
                recalls.append(recall)
                per_q.append({"question_id": q["question_id"], "hit": hit, "recall": recall, "missing": sorted(want - set(got))})
            out["retrieval"][m] = {"hit_at_k": ev.mean(hits), "subject_recall_at_k": ev.mean(recalls), "k": k, "per_question": per_q}
        except (RuntimeError, ImportError, OSError, ValueError) as error:
            out["skipped"][m] = f"{type(error).__name__}: {str(error).splitlines()[0][:120]}"
    if call_llm is not None:
        method = next(iter(out["retrieval"]), None)
        items = []
        for q in questions:
            passages = retrieve(q["question"], k=k, method=method)
            context = "\n".join(f"[{i + 1}] {p['source']}: {p['text']}" for i, p in enumerate(passages))
            answer = call_llm("You help UTS data science students choose subjects. Answer only from the numbered Handbook "
                              "passages. Cite them like [1]. Two to four sentences.\n\nPassages:\n"
                              f"{context}\n\nQuestion: {q['question']}")
            items.append({"question_id": q["question_id"], "question": q["question"], "reference": q["reference_answer"],
                          "answer": answer, "passages": [p["text"] for p in passages]})
        judged = ev.judge_answers(items, call_llm)
        out["judge"] = {"method": method, **ev.chat_summary(judged), "rows": judged}
    return out


def openai_caller():
    """call_llm backed by GPT-4o-mini when OPENAI_API_KEY is set, else None."""
    if not os.getenv("OPENAI_API_KEY"):
        return None
    from openai import OpenAI
    client = OpenAI()

    def call(prompt: str) -> str:
        resp = client.chat.completions.create(model="gpt-4o-mini", temperature=0, messages=[{"role": "user", "content": prompt}])
        return resp.choices[0].message.content
    return call


def _f(x) -> str:
    return f"{x:.3f}"


def tables_md(results: dict, skipped: dict, kappa, other: dict) -> str:
    L = ["# Evaluation tables", "", "Generated by `python -m skillabus.evaluate --all`. Do not edit by hand.", ""]
    L += ["## Extraction (20 labelled ads)", "", "| Tier | Scored on | P | R | F1 | TP / FP / FN |", "|---|---|---|---|---|---|"]
    for m in TIERS:
        if m in results:
            for label, key in (("all skills", "extraction_all"), ("dictionary skills only", "extraction_dictionary_skills")):
                e = results[m][key]
                L.append(f"| {m} | {label} | {_f(e['precision'])} | {_f(e['recall'])} | {_f(e['f1'])} | {e['tp']} / {e['fp']} / {e['fn']} |")
        else:
            L.append(f"| {m} | not run | | | | {skipped.get(m, '')} |")
    L += ["", "## Matching (45 CV-JD pairs)", "", "| Tier | Ad skills from | Accuracy | Macro F1 | have P / R | partial P / R | missing P / R |", "|---|---|---|---|---|---|---|"]
    for m in TIERS:
        if m in results:
            for label, key in (("extract()", "matching_end_to_end"), ("gold labels", "matching_matching_only")):
                s = results[m][key]; pc = s["per_class"]
                cell = lambda c: f"{pc[c]['precision']:.2f} / {pc[c]['recall']:.2f}"
                L.append(f"| {m} | {label} | {_f(s['accuracy'])} | {_f(s['macro_f1'])} | {cell('have')} | {cell('partial')} | {cell('missing')} |")
    first = next((results[m] for m in TIERS if m in results), None)
    if first:
        rk = first["ranking"]
        L += ["", "## Evidence ranking (have and partial rows)", "", "| Metric | Value |", "|---|---|",
              f"| P@5 | {_f(rk['p_at_k'])} |", f"| Hit@5 | {_f(rk['hit_at_k'])} |", f"| MRR | {_f(rk['mrr'])} |", f"| n | {rk['n']} |"]
    L += ["", "## Annotator agreement", ""]
    if isinstance(kappa, dict):
        k2 = kappa["all_labels"]
        L += [f"Cohen's kappa between {' and '.join(kappa['annotators'])} on {kappa['n_ads']} ads:", "",
              "| Items | kappa | Interpretation | Observed agreement |", "|---|---|---|---|",
              f"| Dictionary skills only | {_f(kappa['kappa'])} | {kappa['interpretation']} | {_f(kappa['observed_agreement'])} |",
              f"| All labels incl. free text | {_f(k2['kappa'])} | {k2['interpretation']} | {_f(k2['observed_agreement'])} |"]
    else:
        L += [kappa]
    if isinstance(other.get("subject"), dict):
        sj = other["subject"]
        L += ["", f"## Subject recommendation, P@3 ({sj['n_pairs']} labelled skill-subject pairs, {sj['n_skills']} skills)", "",
              "| Method | P@3 (y or partly) | P@3 (y only) | Labelled / recommended | Coverage |", "|---|---|---|---|---|"]
        for m, r in sj["methods"].items():
            a, b = r["with_partly"], r["y_only"]
            L.append(f"| {m} | {_f(a['p_at_k'])} | {_f(b['p_at_k'])} | {a['labelled']} / {a['total_recommended']} | {_f(a['coverage'])} |")
        L += [f"| {m} | not run | | | {why} |" for m, why in sj["skipped"].items()]
    if isinstance(other.get("chat"), dict):
        ch = other["chat"]
        L += ["", f"## Chat retrieval ({ch['n_questions']} questions)", "", "| Method | Hit@k | Subject recall@k |", "|---|---|---|"]
        for m, r in ch["retrieval"].items():
            L.append(f"| {m} | {_f(r['hit_at_k'])} | {_f(r['subject_recall_at_k'])} |")
        L += [f"| {m} | not run | {why} |" for m, why in ch["skipped"].items()]
        if "judge" in ch:
            j = ch["judge"]
            L += ["", f"LLM judge (retrieval: {j['method']}, n={j['n']}, unparsed={j['n_unparsed']}): relevance {j['relevance_mean']:.2f}/5, "
                      f"faithfulness {j['faithfulness_mean']:.2f}/5, share of answers with faithfulness 4+: {j['share_faithfulness_4plus']:.2f}"]
    L += ["", "## Not run", ""] + [f"- {k}: {v}" for k, v in other.items() if isinstance(v, str)]
    return "\n".join(L) + "\n"


def run_all(methods=TIERS, out_dir: str | Path | None = None, gold_annotator: str | None = GOLD_ANNOTATOR) -> int:
    out = Path(out_dir) if out_dir else ROOT / "data/processed"
    out.mkdir(parents=True, exist_ok=True)
    results, skipped = {}, {}
    for m in methods:
        try:
            results[m] = run_tier(m, gold_annotator)
        except (RuntimeError, ImportError, NotImplementedError, OSError) as error:
            skipped[m] = f"{type(error).__name__}: {str(error).splitlines()[0][:120]}"
            print(f"{m}: not run ({skipped[m]})")
            continue
        name = "eval_results.json" if m == "dictionary" else f"eval_results_{m}.json"
        (out / name).write_text(json.dumps(results[m], indent=1, default=str), encoding="utf-8")
        e = results[m]
        print(f"{m}: extraction F1 {e['extraction_all']['f1']:.3f}; matching accuracy {e['matching_end_to_end']['accuracy']:.3f}; Hit@5 {e['ranking']['hit_at_k']:.3f}")
    kappa = kappa_result()
    other: dict = {}
    for key, name, fname, fn in (("subject", "Subject P@3", "skill_subject_pairs.csv", subject_result),
                                 ("chat", "Chat retrieval and judge", "chat_questions.csv", lambda: chat_result(openai_caller()))):
        if not (LAB / fname).exists():
            other[name] = f"not run: data/labels/{fname} does not exist yet"
            continue
        try:
            other[key] = fn()
            (out / f"eval_{key}.json").write_text(json.dumps(other[key], indent=1, default=str), encoding="utf-8")
        except (RuntimeError, ImportError, OSError, ValueError) as error:
            other[name] = f"not run: {type(error).__name__}: {str(error).splitlines()[0][:120]}"
    if isinstance(other.get("chat"), dict) and "judge" not in other["chat"]:
        other["Chat LLM judge"] = "not run: set OPENAI_API_KEY (answers and judge use GPT-4o-mini)"
    (out / "eval_tables.md").write_text(tables_md(results, skipped, kappa, other), encoding="utf-8")
    print("wrote", out / "eval_tables.md")
    return 0
