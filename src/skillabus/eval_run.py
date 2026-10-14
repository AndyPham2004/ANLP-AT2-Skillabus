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
    L += ["", "## Not run", ""] + [f"- {k}: {v}" for k, v in other.items()]
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
    other = {}
    for name, fname in (("Subject P@3", "skill_subject_pairs.csv"), ("Chat judge", "chat_questions.csv")):
        other[name] = "labelled file present but this stage is not wired into --all yet" if (LAB / fname).exists() else f"not run: data/labels/{fname} does not exist yet"
    (out / "eval_tables.md").write_text(tables_md(results, skipped, kappa, other), encoding="utf-8")
    print("wrote", out / "eval_tables.md")
    return 0
