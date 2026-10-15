"""Skill extraction, three tiers: dictionary -> spaCy NER (owner: Phuong Nhi) -> GPT-4o-mini (owner: Quan).

Every tier returns the same list of skill mentions (docs/data_contract.md, section 1,
before normalisation):

    {"text": "Python", "canonical": "Python", "method": "dictionary",
     "sentence": "Strong programming experience with Python and SQL."}

`text`      the words as they appear in the ad or resume
`canonical` the skill name in data/1_knowledge/skills/skills_seed_v2.csv, or None when the
            mention is not in the dictionary (tier 2 candidates, emerging skills)
`method`    which tier found it: dictionary, ner, llm
`sentence`  the full sentence, kept as the evidence the app shows

Tier 1, dictionary: exact alias lookup. Fast, transparent, the baseline.
Tier 2, ner: tier 1 plus what spaCy adds: part-of-speech filtering of ambiguous
aliases ("excel in a team" is a verb, not the spreadsheet), plural forms
("REST APIs", "stakeholders"), and candidate skills outside the dictionary found
through dependency cues ("experience with X") and PRODUCT entities.
"""

from __future__ import annotations

import csv
import re
from functools import lru_cache

from . import paths

SEED_CSV = paths.SKILLS_SEED
METHODS = ("dictionary", "ner", "llm")
SPACY_MODEL = "en_core_web_sm"


# --------------------------------------------------------------------------- sentences

_BULLET = re.compile(r"^\s*(?:[-*•·▪‣◦–—]|\d{1,2}[.)])\s+")
_DANGLING = re.compile(
    r"(?:,|\b(?:and|or|of|the|a|an|in|with|to|for|on|at|by|from|as|using|including))$", re.I
)
_SENT_END = re.compile(r"(?<=[.!?])\s+(?=[\"'(\[]?[A-Z0-9])")
_ABBREVIATIONS = ("e.g.", "i.e.", "etc.", "incl.", "vs.", "approx.", "inc.", "ltd.", "pty.")
_URL_OR_EMAIL = re.compile(r"https?://\S+|www\.\S+|\S+@\S+")


def split_sentences(text: str) -> list[str]:
    """Split an ad or resume into evidence sentences.

    Ads and resumes are mostly bullet lists, where a statistical sentence splitter does
    badly, so this is rule based: each bullet or line is its own unit, hard-wrapped
    lines are joined back, and prose is split after . ! ?
    Both tiers use this function, so the same mention carries the same sentence
    whichever tier found it.
    """
    blocks: list[str] = []
    current, current_indent = "", 0

    for raw in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = raw.strip()
        if not line:
            if current:
                blocks.append(current)
            current = ""
            continue
        indent = len(raw) - len(raw.lstrip())
        wrapped = (
            current
            and not _BULLET.match(raw)
            and current[-1] not in ".!?:"
            and (line[0].islower() or indent > current_indent or _DANGLING.search(current))
        )
        if wrapped:
            current += " " + line
        else:
            if current:
                blocks.append(current)
            current, current_indent = line, indent
    if current:
        blocks.append(current)

    sentences: list[str] = []
    for block in blocks:
        block = re.sub(r"\s+", " ", _BULLET.sub("", block)).strip()
        pieces: list[str] = []
        for piece in _SENT_END.split(block):
            if pieces and pieces[-1].lower().endswith(_ABBREVIATIONS):
                pieces[-1] += " " + piece
            else:
                pieces.append(piece)
        sentences.extend(p for p in pieces if re.search(r"[A-Za-z]", p))
    return sentences


# -------------------------------------------------------------------------- dictionary

@lru_cache(maxsize=None)
def load_dictionary(path: str | None = None) -> tuple[dict, ...]:
    """Read skills_seed_v2.csv: one dict per skill with canonical, category, strict, aliases."""
    with open(path or SEED_CSV, encoding="utf-8", newline="") as f:
        rows = csv.DictReader(line for line in f if not line.startswith("#"))
        return tuple(
            {
                "canonical": row["canonical"].strip(),
                "category": row["category"].strip(),
                "strict": row["strict"].strip() == "1",
                "aliases": tuple(a.strip() for a in row["aliases"].split("|") if a.strip()),
            }
            for row in rows
        )


def _alias_pattern(aliases, flags) -> re.Pattern | None:
    """One regex for many aliases. Longest alias first, so 'sql server' wins over 'sql'.

    The lookarounds stand in for \\b, which fails on aliases such as c++, c#, .net.
    """
    if not aliases:
        return None
    body = "|".join(re.escape(a) for a in sorted(aliases, key=len, reverse=True))
    return re.compile(rf"(?<![A-Za-z0-9])(?:{body})(?![A-Za-z0-9])", flags)


@lru_cache(maxsize=None)
def _matchers(path: str | None = None):
    """Alias lookups and regexes. Only aliases are matched; `canonical` is a display name
    (the dictionary leaves out bare 'R', 'Go', 'Oracle', 'RAG' on purpose).
    strict = 1 means case-sensitive (R, SAS)."""
    loose: dict[str, list[str]] = {}
    strict: dict[str, list[str]] = {}
    for skill in load_dictionary(path):
        for alias in skill["aliases"]:
            if skill["strict"]:
                strict.setdefault(alias, []).append(skill["canonical"])
            else:
                loose.setdefault(alias.lower(), []).append(skill["canonical"])
    return loose, strict, _alias_pattern(loose, re.IGNORECASE), _alias_pattern(strict, 0)


def _dictionary_hits(sentence: str, path: str | None = None) -> list[tuple[int, int, str]]:
    """(start, end, canonical) for every alias found in one sentence, in reading order.

    An alias shared by two skills ('pl/sql' is SQL and Oracle) gives one hit per skill.
    Strict aliases are context patterns ('Python and R'), so they never hide other hits.
    """
    loose, strict, loose_re, strict_re = _matchers(path)
    # Blank out URLs and e-mails (same length, so offsets still fit the sentence).
    searchable = _URL_OR_EMAIL.sub(lambda m: " " * len(m.group()), sentence)
    hits = []
    if loose_re:
        for m in loose_re.finditer(searchable):
            hits += [(m.start(), m.end(), c) for c in loose[m.group().lower()]]
    if strict_re:
        for m in strict_re.finditer(searchable):
            hits += [(m.start(), m.end(), c) for c in strict[m.group()]]
    return sorted(hits)


def _mention(text: str, canonical: str | None, method: str, sentence: str) -> dict:
    return {"text": text, "canonical": canonical, "method": method, "sentence": sentence}


def _extract_dictionary(text: str) -> list[dict]:
    mentions = []
    for sentence in split_sentences(text):
        seen = set()
        for start, end, canonical in _dictionary_hits(sentence):
            if canonical not in seen:  # one mention per skill per sentence
                seen.add(canonical)
                mentions.append(_mention(sentence[start:end], canonical, "dictionary", sentence))
    return mentions


# ------------------------------------------------------------------------------- spaCy

# Words that introduce a skill: "experience with X", "knowledge of X", "proficient in X".
_CUES = {
    "experience", "experienced", "knowledge", "proficiency", "proficient", "expertise",
    "understanding", "familiarity", "familiar", "skill", "skilled", "background", "exposure",
    "competency", "competence", "fluency", "fluent", "command", "certification", "training",
}
_USE_VERBS = {"use", "utilise", "utilize", "leverage"}       # "using X", "leverage X"
_LIST_PREPS = {"including", "like"}                          # "tools including X"
_PATH_DEPS = {"pobj", "prep", "pcomp", "dobj", "conj", "appos"}
_NON_SKILL_PREPS = {"at", "from", "for", "within", "by", "over", "during", "since", "than"}

# Noun-phrase heads and modifiers that are never a skill on their own.
_GENERIC_HEADS = {
    "experience", "year", "month", "skill", "knowledge", "ability", "understanding", "team",
    "role", "environment", "tool", "technology", "technique", "method", "methodology",
    "solution", "problem", "degree", "field", "area", "range", "variety", "level", "work",
    "project", "business", "company", "organisation", "organization", "client", "customer",
    "stakeholder", "opportunity", "requirement", "responsibility", "record", "trend",
    "practice", "principle", "concept", "system", "process", "outcome", "insight", "model",
    "platform", "framework", "language", "package", "library", "product", "service", "data",
    "dataset", "industry", "sector", "domain", "discipline", "equivalent", "capability",
    "way", "thing", "lot", "number", "type", "kind", "combination", "mix", "focus", "use",
}
_GENERIC_MODIFIERS = {
    "strong", "excellent", "good", "great", "solid", "sound", "advanced", "deep", "proven",
    "other", "various", "relevant", "extensive", "demonstrated", "latest", "new", "modern",
    "similar", "related", "practical", "prior", "previous", "significant", "broad", "basic",
    "working", "commercial", "professional", "hands", "in", "depth", "-", "such", "several",
    "multiple", "least", "more", "minimum", "complex", "large", "big", "high",
}
# en_core_web_sm was trained on news text and labels Python as GPE, Scala and Keras as
# PERSON, Tableau as GPE. So its PERSON / GPE / ORG labels are not used to accept or
# reject anything; only its number and date labels are, plus a short list of places.
_NOT_SKILL_ENTITIES = {"DATE", "TIME", "MONEY", "PERCENT", "CARDINAL", "ORDINAL", "QUANTITY"}
_PLACES = {
    "australia", "sydney", "melbourne", "brisbane", "perth", "adelaide", "canberra", "hobart",
    "darwin", "nsw", "victoria", "queensland", "tasmania", "apac", "anz", "cbd",
}


@lru_cache(maxsize=1)
def _nlp():
    try:
        import spacy
        return spacy.load(SPACY_MODEL)
    except (ImportError, OSError) as error:
        raise RuntimeError(
            f'extract(method="ner") needs spaCy and {SPACY_MODEL}: pip install -r requirements.txt'
        ) from error


def _fold_plurals(doc) -> None:
    """Set each token's NORM to lower case, with plural nouns folded to the singular.

    Only plurals the tagger marks NNS / NNPS are folded. Full lemmatisation would turn
    the alias 'clustering' into 'cluster' and tag every 'Kubernetes cluster' as the
    Clustering skill. Irregular plurals keep their form ('data' must not become 'datum').
    """
    for token in doc:
        plural = token.tag_ in ("NNS", "NNPS") and token.lower_.endswith("s")
        token.norm_ = token.lemma_.lower() if plural else token.lower_


@lru_cache(maxsize=1)
def _plural_matcher():
    """PhraseMatcher over the non-strict aliases, compared with the plural-folded text."""
    nlp = _nlp()  # first, so a missing spaCy raises the RuntimeError with the install hint
    from spacy.matcher import PhraseMatcher

    loose, _, _, _ = _matchers()
    matcher = PhraseMatcher(nlp.vocab, attr="NORM")
    for alias in loose:
        pattern = nlp.make_doc(alias)
        for token in pattern:
            token.norm_ = token.lower_
        matcher.add(alias, [pattern])
    return matcher


def _is_verb(span) -> bool:
    """A one-word alias used as a finite verb is not a skill: 'excel in', 'spark new ideas'.

    -ing forms are kept, because 'coaching juniors' and 'forecasting demand' are skills.
    """
    return len(span) == 1 and span[0].pos_ in ("VERB", "AUX") and span[0].tag_ != "VBG"


def _in_skill_context(token, max_hops: int = 5) -> bool:
    """Walk up the dependency tree: is this noun the object of a cue such as
    'experience with', 'knowledge of', 'using', 'such as'?"""
    for _ in range(max_hops):
        if token.dep_ not in _PATH_DEPS:
            return False
        if token.dep_ == "prep" and token.lower_ in _NON_SKILL_PREPS:
            return False
        head = token.head
        if head.lemma_.lower() in _CUES:
            return True
        if token.dep_ == "dobj" and head.lemma_.lower() in _USE_VERBS:
            return True
        if token.dep_ == "pobj" and (
            head.lower_ in _LIST_PREPS
            or (head.lower_ == "as" and any(child.lower_ == "such" for child in head.children))
        ):
            return True
        token = head
    return False


def _clean_candidate(chunk):
    """Trim a noun chunk to its skill-like core; None when nothing useful is left."""
    start, end = chunk.start, chunk.end
    doc = chunk.doc
    while start < end and (
        doc[start].pos_ in ("DET", "PRON", "PUNCT", "NUM", "CCONJ", "ADP", "SYM")
        or doc[start].lemma_.lower() in _GENERIC_MODIFIERS
    ):
        start += 1
    while end > start and doc[end - 1].pos_ == "PUNCT":
        end -= 1
    span = doc[start:end]
    if not 1 <= len(span) <= 4:
        return None
    root = span.root.lemma_.lower()
    if root in _GENERIC_HEADS or root in _CUES or span.root.pos_ not in ("NOUN", "PROPN"):
        return None
    if any(t.like_num or t.ent_type_ in _NOT_SKILL_ENTITIES or t.lower_ in _PLACES for t in span):
        return None
    if len(span.text) < 2 or all(t.is_stop for t in span):
        return None
    # One lower-case common noun ("clusters", "analysis") is too vague; one-word
    # candidates must look like a name ("KNIME", "Alteryx", "VLOOKUP").
    if len(span) == 1 and span[0].pos_ != "PROPN" and span.text.islower():
        return None
    return span


def _is_abbreviation_of(span, taken) -> bool:
    """'retrieval-augmented generation (RAG)': the bracket repeats the skill before it."""
    doc = span.doc
    return (
        span.start >= 2
        and doc[span.start - 1].text == "("
        and any(start <= span.start - 2 < end for start, end in taken)
    )


def _overlaps(span, taken) -> bool:
    return any(span.start < end and start < span.end for start, end in taken)


def _extract_ner(text: str) -> list[dict]:
    nlp = _nlp()  # first, so a missing spaCy raises the RuntimeError with the install hint
    from spacy.util import filter_spans

    sentences = split_sentences(text)
    mentions = []

    for sentence, doc in zip(sentences, nlp.pipe(sentences)):
        found = []       # (first token index, text, canonical)
        taken = []       # token ranges already used by a dictionary skill
        rejected = []    # token ranges the part-of-speech filter threw out

        # 1. Tier 1 hits, unless spaCy says the word is a verb here.
        for start, end, canonical in _dictionary_hits(sentence):
            span = doc.char_span(start, end, alignment_mode="expand")
            if span is None:
                continue
            if _is_verb(span):
                rejected.append((span.start, span.end))
                continue
            found.append((span.start, sentence[start:end], canonical))
            taken.append((span.start, span.end))

        # 2. Plural or singular forms the exact lookup missed: "REST APIs", "stakeholders".
        _fold_plurals(doc)
        loose = _matchers()[0]
        extra = [span for span in _plural_matcher()(doc, as_spans=True)
                 if not _overlaps(span, taken) and not _is_verb(span)]
        for span in filter_spans(extra):
            for canonical in loose[span.label_]:
                found.append((span.start, span.text, canonical))
            taken.append((span.start, span.end))

        # 3. Candidates outside the dictionary: noun chunks governed by a skill cue,
        #    and anything the pretrained NER labels PRODUCT. normalise() decides later
        #    whether each one is an ESCO, Lightcast or emerging skill.
        blocked = taken + rejected
        candidates = [_clean_candidate(chunk) for chunk in doc.noun_chunks
                      if _in_skill_context(chunk.root)]
        candidates += [_clean_candidate(ent) for ent in doc.ents if ent.label_ == "PRODUCT"]
        candidates = [span for span in candidates if span is not None
                      and not _overlaps(span, blocked) and not _is_abbreviation_of(span, taken)]
        for span in filter_spans(candidates):
            found.append((span.start, span.text, None))

        seen = set()
        for _, surface, canonical in sorted(found, key=lambda item: item[0]):
            key = canonical or surface.lower()
            if key not in seen:
                seen.add(key)
                mentions.append(_mention(surface, canonical, "ner", sentence))
    return mentions


# ------------------------------------------------------------------------------ public

def extract(text: str, method: str = "dictionary") -> list[dict]:
    """Return skill mentions (data contract section 1, before normalisation).

    method = "dictionary"  tier 1, exact alias lookup in skills_seed_v2.csv
    method = "ner"         tier 2, tier 1 + spaCy (POS filter, plurals, new candidates)
    method = "llm"         tier 3, GPT-4o-mini (Quan)
    """
    if method not in METHODS:
        raise ValueError(f"method must be one of {METHODS}, got {method!r}")
    if not text or not text.strip():
        return []
    if method == "dictionary":
        return _extract_dictionary(text)
    if method == "ner":
        return _extract_ner(text)
    try:  # tier 3 lives in llm_extract.py (Quan)
        from .llm_extract import extract_llm
    except ImportError as error:
        raise NotImplementedError("Tier 3 (GPT-4o-mini) is in llm_extract.py, not on this branch yet.") from error
    return extract_llm(text)
