"""Scores for the four stages: extraction P/R/F1, matching P@5 + MRR, subject P@3, chat 1-5. Owner: Hoai Thuong.

Standard library only, so it runs on a fresh clone. Input shapes follow docs/data_contract.md and the
label templates in data/labels/. Every function takes plain dicts and lists; nothing here calls the
pipeline or an API, so the harness can be tested before the pipeline exists.

Also here: Cohen's kappa between two annotators (task "label 20 ads like Akash").

Command line (numbers for the report; the report names this file as the script):
    python -m skillabus.evaluate kappa  A.csv B.csv --a-name "Hoai Thuong" --b-name Akash \
        --dictionary data/processed/skills_seed_v2.csv
    python -m skillabus.evaluate extraction gold.csv pred.json [--method dictionary]
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from typing import Callable, Iterable, Mapping, Sequence

# --------------------------------------------------------------------------- helpers


def norm(label: str) -> str:
    """Case-fold, trim and collapse spaces, so 'Machine  Learning ' equals 'machine learning'."""
    return re.sub(r"\s+", " ", str(label).strip().casefold())


def mean(values: Iterable[float]) -> float:
    values = list(values)
    return sum(values) / len(values) if values else 0.0


def prf(tp: int, fp: int, fn: int) -> dict:
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f = 2 * p * r / (p + r) if p + r else 0.0
    return {"precision": p, "recall": r, "f1": f, "tp": tp, "fp": fp, "fn": fn}


def _rows(path: str) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(line for line in f if not line.lstrip().startswith("#")))


# --------------------------------------------------------------------------- loaders


def load_dictionary(path: str) -> list[str]:
    """Canonical skill names (normalised) from data/processed/skills_seed_v2.csv."""
    return sorted({norm(r["canonical"]) for r in _rows(path) if r.get("canonical")})


def load_ad_skills(path: str, annotator: str | None = None) -> dict[str, set[str]]:
    """ad_skills.csv -> {ad_id: {skill, ...}}. Pass `annotator` when two people share one file."""
    out: dict[str, set[str]] = defaultdict(set)
    for r in _rows(path):
        if annotator and r.get("annotator", "").strip().casefold() != annotator.strip().casefold():
            continue
        label = norm(r.get("skill_label", ""))
        if label and r.get("ad_id", "").strip():
            out[r["ad_id"].strip()].add(label)
    return dict(out)


def load_cv_jd_pairs(path: str) -> list[dict]:
    """cv_jd_pairs.csv rows with skill_label and evidence normalised; a leading '?' (unsure) is dropped."""
    rows = []
    for r in _rows(path):
        r = dict(r)
        r["skill_label"] = norm(r.get("skill_label", ""))
        r["gold_status"] = r.get("gold_status", "").strip().lower()
        r["resume_evidence_text"] = norm(r.get("resume_evidence_text", "").lstrip(" ?"))
        rows.append(r)
    return rows


def load_skill_subject_pairs(path: str) -> dict[tuple[str, str], str]:
    """skill_subject_pairs.csv -> {(skill, subject_code): 'y' | 'partly' | 'n'}."""
    return {
        (norm(r["skill_label"]), r["subject_code"].strip()): r["teaches"].strip().lower()
        for r in _rows(path)
        if r.get("skill_label") and r.get("subject_code") and r.get("teaches")
    }


# --------------------------------------------------------------------------- stage 1: extraction


def mentions_to_sets(
    mentions_by_ad: Mapping[str, Sequence[dict]],
    method: str | None = None,
    label_map: Mapping[str, str] | None = None,
) -> dict[str, set[str]]:
    """Skill mentions (data contract section 1) -> {ad_id: {skill}}.

    The label of a mention is its `canonical` (what extract() returns: the dictionary name, or None for a
    candidate outside the dictionary), else `skill_label` (after normalise()), else the raw `text`.
    method: keep only mentions with this `method` ('dictionary', 'ner', 'llm'), to compare the tiers.
    label_map: rename predicted labels into the gold vocabulary. normalise() returns ESCO labels
    ('Python (computer programming)') while the gold set uses dictionary names ('python'); map one
    to the other here, or the score measures spelling and not extraction.
    """
    label_map = {norm(k): norm(v) for k, v in (label_map or {}).items()}
    out: dict[str, set[str]] = {}
    for ad_id, mentions in mentions_by_ad.items():
        labels = set()
        for m in mentions:
            if method and m.get("method") != method:
                continue
            label = norm(m.get("canonical") or m.get("skill_label") or m.get("text", ""))
            labels.add(label_map.get(label, label))
        out[ad_id] = labels
    return out


def extraction_scores(gold: Mapping[str, set[str]], pred: Mapping[str, set[str]]) -> dict:
    """Micro-averaged precision / recall / F1 over the ads in `gold`. Ads missing from `pred` count as empty."""
    tp = fp = fn = 0
    for ad_id, g in gold.items():
        p = pred.get(ad_id, set())
        tp += len(g & p)
        fp += len(p - g)
        fn += len(g - p)
    return {**prf(tp, fp, fn), "n_ads": len(gold)}


def extraction_errors(gold: Mapping[str, set[str]], pred: Mapping[str, set[str]]) -> list[dict]:
    """Every false positive and false negative, for the error analysis in the report."""
    errors = []
    for ad_id, g in gold.items():
        p = pred.get(ad_id, set())
        errors += [{"ad_id": ad_id, "skill": s, "error": "false_negative"} for s in sorted(g - p)]
        errors += [{"ad_id": ad_id, "skill": s, "error": "false_positive"} for s in sorted(p - g)]
    return errors


# --------------------------------------------------------------------------- stage 2: matching


def is_relevant(item: str, relevant: set) -> bool:
    """True when `item` (a ranked resume sentence) is a gold evidence item.

    Annotators copy a short phrase from the resume, while the ranker returns whole sentences, so a gold
    phrase counts when it sits inside the sentence (after the same case / whitespace normalisation).
    """
    text = norm(item) if isinstance(item, str) else item
    return text in relevant or any(isinstance(g, str) and g and g in text for g in relevant)


def precision_at_k(ranked: Sequence, relevant: set, k: int = 5) -> float:
    """Standard P@k: relevant items in the top k, divided by k.

    With one gold sentence per skill this cannot exceed 1/k (0.2 at k=5). Report hit_at_k next to it.
    """
    return sum(1 for x in list(ranked)[:k] if is_relevant(x, relevant)) / k


def hit_at_k(ranked: Sequence, relevant: set, k: int = 5) -> float:
    return float(any(is_relevant(x, relevant) for x in list(ranked)[:k]))


def reciprocal_rank(ranked: Sequence, relevant: set) -> float:
    for i, x in enumerate(ranked, start=1):
        if is_relevant(x, relevant):
            return 1.0 / i
    return 0.0


def ranking_scores(cases: Sequence[tuple[Sequence, set]], k: int = 5) -> dict:
    """cases = [(ranked resume sentences, gold relevant sentences), ...], one per ad skill.

    Skills whose gold set is empty (status 'missing') cannot be ranked and are skipped; the count is returned.
    """
    scored = [(r, rel) for r, rel in cases if rel]
    return {
        "k": k,
        "p_at_k": mean(precision_at_k(r, rel, k) for r, rel in scored),
        "hit_at_k": mean(hit_at_k(r, rel, k) for r, rel in scored),
        "mrr": mean(reciprocal_rank(r, rel) for r, rel in scored),
        "n": len(scored),
        "n_skipped": len(cases) - len(scored),
    }


def matching_gold(rows: Sequence[dict], include_partial: bool = True) -> dict[tuple[str, str], dict]:
    """cv_jd_pairs rows -> {(pair_id, skill): {'status': ..., 'relevant': {gold evidence sentences}}}."""
    gold: dict[tuple[str, str], dict] = {}
    for r in rows:
        counts = r["gold_status"] == "have" or (include_partial and r["gold_status"] == "partial")
        evidence = r["resume_evidence_text"]
        gold[(r["pair_id"], r["skill_label"])] = {
            "status": r["gold_status"],
            "relevant": {evidence} if counts and evidence else set(),
        }
    return gold


def status_scores(
    gold: Mapping[tuple, str], pred: Mapping[tuple, str], labels: Sequence[str] = ("have", "partial", "missing")
) -> dict:
    """Three-state accuracy, per-class precision/recall/F1, macro F1 and a confusion table {(gold, pred): n}."""
    keys = [k for k in gold if k in pred]
    confusion = Counter((gold[k], pred[k]) for k in keys)
    per_class = {}
    for c in labels:
        tp = confusion[(c, c)]
        fp = sum(confusion[(g, c)] for g in labels if g != c)
        fn = sum(confusion[(c, p)] for p in labels if p != c)
        per_class[c] = prf(tp, fp, fn)
    return {
        "accuracy": mean(gold[k] == pred[k] for k in keys),
        "macro_f1": mean(v["f1"] for v in per_class.values()),
        "per_class": per_class,
        "confusion": dict(confusion),
        "n": len(keys),
        "n_not_predicted": len(gold) - len(keys),
    }


# --------------------------------------------------------------------------- stage 3: subject recommendation


def subject_precision_at_k(
    recs_by_skill: Mapping[str, Sequence[str]],
    gold: Mapping[tuple[str, str], str],
    k: int = 3,
    include_partly: bool = True,
) -> dict:
    """P@k over the labelled skill-subject pairs only.

    recs_by_skill: {skill: [subject_code, ...]} best first. gold: from load_skill_subject_pairs().
    The test set is small (30 pairs), so a recommended subject with no label is not counted either way;
    `coverage` says how much of the top-k was actually labelled. Report both.
    """
    good = {"y", "partly"} if include_partly else {"y"}
    relevant = labelled = total = 0
    for skill, subjects in recs_by_skill.items():
        for code in list(subjects)[:k]:
            total += 1
            verdict = gold.get((norm(skill), str(code)))
            if verdict is None:
                continue
            labelled += 1
            relevant += verdict in good
    return {
        "k": k,
        "p_at_k": relevant / labelled if labelled else 0.0,
        "relevant": relevant,
        "labelled": labelled,
        "total_recommended": total,
        "coverage": labelled / total if total else 0.0,
    }


# --------------------------------------------------------------------------- stage 4: chat (LLM as judge)

JUDGE_TEMPLATE = """You are grading an answer from a study-planning assistant.

Question: {question}
Reference answer: {reference}
Retrieved passages:
{passages}
Assistant answer: {answer}

Score two things from 1 (worst) to 5 (best):
- relevance: does the answer address the question, compared with the reference answer?
- faithfulness: is every claim supported by the retrieved passages (5 = fully supported, 1 = invented)?
Reply with JSON only: {{"relevance": <1-5>, "faithfulness": <1-5>, "reason": "<one sentence>"}}"""


def judge_prompt(question: str, reference: str, answer: str, passages: Sequence[str]) -> str:
    return JUDGE_TEMPLATE.format(
        question=question,
        reference=reference,
        answer=answer,
        passages="\n".join(f"- {p}" for p in passages) or "(none)",
    )


def parse_judge(text: str) -> dict:
    """Pull the JSON scores out of a judge reply; raises ValueError if a score is missing or not 1-5."""
    match = re.search(r"\{.*\}", text, flags=re.S)
    if not match:
        raise ValueError(f"no JSON in judge reply: {text[:80]!r}")
    data = json.loads(match.group(0))
    out = {"reason": str(data.get("reason", ""))}
    for key in ("relevance", "faithfulness"):
        value = int(data[key])
        if not 1 <= value <= 5:
            raise ValueError(f"{key} must be 1-5, got {value}")
        out[key] = value
    return out


def judge_answers(items: Sequence[dict], call_llm: Callable[[str], str]) -> list[dict]:
    """items: {'question', 'reference', 'answer', 'passages'}. call_llm(prompt) -> reply text (inject the API call).

    A reply that cannot be parsed is kept with an 'error' field instead of being dropped, so failures stay visible.
    """
    results = []
    for item in items:
        reply = call_llm(judge_prompt(item["question"], item["reference"], item["answer"], item.get("passages", [])))
        try:
            results.append({**item, **parse_judge(reply)})
        except (ValueError, KeyError, json.JSONDecodeError) as exc:
            results.append({**item, "error": str(exc)})
    return results


def chat_summary(judged: Sequence[dict]) -> dict:
    ok = [j for j in judged if "error" not in j]
    return {
        "relevance_mean": mean(j["relevance"] for j in ok),
        "faithfulness_mean": mean(j["faithfulness"] for j in ok),
        "share_faithfulness_4plus": mean(j["faithfulness"] >= 4 for j in ok),
        "n": len(ok),
        "n_unparsed": len(judged) - len(ok),
    }


# --------------------------------------------------------------------------- inter-annotator agreement


def cohens_kappa(a: Sequence, b: Sequence) -> float:
    """Cohen's kappa for two equal-length label lists (any hashable labels)."""
    if len(a) != len(b) or not a:
        raise ValueError("need two non-empty label lists of equal length")
    n = len(a)
    observed = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    expected = sum(ca[c] / n * cb[c] / n for c in set(ca) | set(cb))
    if expected == 1.0:  # both annotators used one identical label throughout
        return 1.0
    return (observed - expected) / (1 - expected)


def interpret_kappa(kappa: float) -> str:
    """Landis & Koch (1977) bands, the usual wording in reports."""
    for upper, word in ((0.0, "poor"), (0.20, "slight"), (0.40, "fair"), (0.60, "moderate"), (0.80, "substantial")):
        if kappa < upper or (upper > 0 and kappa <= upper):
            return word
    return "almost perfect"


def annotator_agreement(
    a: Mapping[str, set[str]],
    b: Mapping[str, set[str]],
    ads: Sequence[str] | None = None,
    universe: Iterable[str] | None = None,
) -> dict:
    """Kappa between two annotators of ad_skills.csv.

    Each (ad, skill) is one item, labelled present or absent by each person. Pass the dictionary as
    `universe` so that skills nobody labelled count as agreed absences; without it the kappa is computed
    on the labelled skills only and is too pessimistic. Skills outside the dictionary are always added.
    """
    ads = sorted(ads if ads is not None else set(a) & set(b))
    skills = set(universe or ()) | {s for ad in ads for s in a.get(ad, set()) | b.get(ad, set())}
    items = [(ad, s) for ad in ads for s in sorted(skills)]
    ya = [s in a.get(ad, set()) for ad, s in items]
    yb = [s in b.get(ad, set()) for ad, s in items]
    both_yes = sum(x and y for x, y in zip(ya, yb))
    a_only = sum(x and not y for x, y in zip(ya, yb))
    b_only = sum(y and not x for x, y in zip(ya, yb))
    kappa = cohens_kappa(ya, yb)
    return {
        "kappa": kappa,
        "interpretation": interpret_kappa(kappa),
        "observed_agreement": mean(x == y for x, y in zip(ya, yb)),
        "n_ads": len(ads),
        "n_items": len(items),
        "both_yes": both_yes,
        "a_only": a_only,
        "b_only": b_only,
        "both_no": len(items) - both_yes - a_only - b_only,
    }


def disagreements(a: Mapping[str, set[str]], b: Mapping[str, set[str]], ads: Sequence[str] | None = None) -> list[dict]:
    """Skills only one annotator labelled. Review these together; they are also material for the error analysis."""
    out = []
    for ad in sorted(ads if ads is not None else set(a) & set(b)):
        out += [{"ad_id": ad, "skill": s, "only": "a"} for s in sorted(a.get(ad, set()) - b.get(ad, set()))]
        out += [{"ad_id": ad, "skill": s, "only": "b"} for s in sorted(b.get(ad, set()) - a.get(ad, set()))]
    return out


# --------------------------------------------------------------------------- command line


def _fmt(d: Mapping) -> str:
    return "\n".join(f"{k}: {round(v, 3) if isinstance(v, float) else v}" for k, v in d.items())


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m skillabus.evaluate")
    sub = parser.add_subparsers(dest="cmd", required=True)

    k = sub.add_parser("kappa", help="Cohen's kappa between two annotators")
    k.add_argument("file_a")
    k.add_argument("file_b")
    k.add_argument("--a-name", help="annotator column value to keep from file_a")
    k.add_argument("--b-name", help="annotator column value to keep from file_b")
    k.add_argument("--dictionary", help="skills_seed_v2.csv, so unlabelled skills count as agreed absences")
    k.add_argument("--ads", help="comma-separated ad_ids to compare (default: ads both labelled)")

    e = sub.add_parser("extraction", help="P/R/F1 of predicted mentions (JSON {ad_id: [mention, ...]}) vs a gold CSV")
    e.add_argument("gold_csv")
    e.add_argument("pred_json")
    e.add_argument("--method", choices=["dictionary", "ner", "llm"])
    e.add_argument("--label-map", help="JSON file {predicted label: gold label}")

    args = parser.parse_args(argv)
    if args.cmd == "kappa":
        a, b = load_ad_skills(args.file_a, args.a_name), load_ad_skills(args.file_b, args.b_name)
        ads = args.ads.split(",") if args.ads else None
        universe = load_dictionary(args.dictionary) if args.dictionary else None
        print(_fmt(annotator_agreement(a, b, ads, universe)))
        diff = disagreements(a, b, ads)
        print(f"\n{len(diff)} skills labelled by only one person:")
        for d in diff:
            print(f"  {d['ad_id']}\t{d['skill']}\tonly {d['only']}")
    else:
        with open(args.pred_json, encoding="utf-8") as f:
            mentions = json.load(f)
        label_map = json.load(open(args.label_map, encoding="utf-8")) if args.label_map else None
        pred = mentions_to_sets(mentions, args.method, label_map)
        print(_fmt(extraction_scores(load_ad_skills(args.gold_csv), pred)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
