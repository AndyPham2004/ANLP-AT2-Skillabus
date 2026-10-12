"""Run the evaluation on the labelled test sets (task #24). Owner: Hoai Thuong.

    python notebooks/ht_run_evaluation.py [--method dictionary|ner|llm] [--out FILE]

Extraction: dictionary tier on the 20 overlap ads vs data/labels/ad_skills.csv.
Matching:  match() on the CV-JD pairs vs data/labels/cv_jd_pairs.csv (3-state) and
           rank_evidence() for P@5 / Hit@5 / MRR on the have/partial rows.
--method picks the extraction tier used for both the extraction scores and the end-to-end matching run.
"ner" needs spaCy and en_core_web_sm; "llm" needs the OpenAI key (or the cached responses in data/cache/llm_extract).
Without --out, dictionary writes data/processed/eval_results.json and the other tiers eval_results_<method>.json.
"""
import argparse, csv, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
csv.field_size_limit(10**9)
from skillabus import evaluate as ev
from skillabus.extract import extract
from skillabus.match import match, rank_evidence

ADS = ROOT / "data-eda/data/clean/jobs_au_seek_datascientist_2019-2022_clean.csv"
RES = ROOT / "data-eda/data/clean/resumes_us_2021_clean.csv"
DICT = ROOT / "data/processed/skills_seed_v2.csv"
LAB = ROOT / "data/labels"


def table(path, key, field):
    with open(path, newline="", encoding="utf-8") as f:
        return {r[key]: r[field] for r in csv.DictReader(f)}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out"); ap.add_argument("--method", default="dictionary", choices=["dictionary", "ner", "llm"]); a = ap.parse_args()
    method = a.method
    out_path = a.out or str(ROOT / "data/processed" / ("eval_results.json" if method == "dictionary" else f"eval_results_{method}.json"))
    ads, res = table(ADS, "ad_id", "description"), table(RES, "resume_id", "resume_text")
    dic = ev.load_dictionary(str(DICT))
    out = {"method": method}

    # ---- extraction
    gold = ev.load_ad_skills(str(LAB / "ad_skills.csv"))
    pred = {ad: {ev.norm(m.get("canonical") or m.get("skill_label") or m["text"]) for m in extract(ads[ad], method)} for ad in gold}
    out["extraction_all"] = ev.extraction_scores(gold, pred)
    out["extraction_dictionary_skills"] = ev.extraction_scores(ev.restrict_to(gold, dic), ev.restrict_to(pred, dic))
    out["extraction_errors"] = ev.extraction_errors(ev.restrict_to(gold, dic), ev.restrict_to(pred, dic))

    # ---- matching, two settings: end to end (ad skills from extract()) and matching only (ad skills = the gold labels)
    rows = ev.load_cv_jd_pairs(str(LAB / "cv_jd_pairs.csv"))
    canon = {ev.norm(r["canonical"]): r["canonical"] for r in ev._rows(str(DICT)) if r.get("canonical")}
    by_pair = {}
    for r in rows:
        by_pair.setdefault(r["pair_id"], []).append(r)
    res_cache = {}
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
                k = (pid, r["skill_label"]); g_status[k] = r["gold_status"]
                p_status[k] = got.get(r["skill_label"], "not_extracted")
                if setting == "end_to_end" and r["gold_status"] in ("have", "partial") and r["resume_evidence_text"]:
                    cases.append((rank_evidence(r["skill_label"], res[rid]), {r["resume_evidence_text"]}))
                if g_status[k] != p_status[k]:
                    detail.append({"pair": pid, "skill": r["skill_label"], "gold": g_status[k], "pred": p_status[k]})
        st = ev.status_scores(g_status, {k: ("missing" if v == "not_extracted" else v) for k, v in p_status.items()})
        st["confusion"] = {f"{g}->{p}": n for (g, p), n in st["confusion"].items()}
        out[f"matching_{setting}"] = st
        out[f"matching_{setting}_errors"] = detail
        if setting == "end_to_end":
            out["ad_skill_not_extracted"] = sum(v == "not_extracted" for v in p_status.values())
            out["ranking"] = ev.ranking_scores(cases, k=5)
    es, ms, mo, rk = out["extraction_all"], out["matching_end_to_end"], out["matching_matching_only"], out["ranking"]
    print(f"method={method}  extraction P={es['precision']:.3f} R={es['recall']:.3f} F1={es['f1']:.3f}")
    print(f"matching accuracy end-to-end={ms['accuracy']:.3f} (macro F1 {ms['macro_f1']:.3f}), matching-only={mo['accuracy']:.3f} (macro F1 {mo['macro_f1']:.3f})")
    print(f"ranking P@5={rk['p_at_k']:.3f} Hit@5={rk['hit_at_k']:.3f} MRR={rk['mrr']:.3f} (n={rk['n']})")
    Path(out_path).write_text(json.dumps(out, indent=1, default=str), encoding="utf-8")
    print("wrote", out_path)

main()
