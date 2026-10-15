"""Can the student enrol in a subject, and when? Owner: Phuong Nhi.

    load_rules()                         ->  Rules from prerequisites.csv and offerings.csv (data contract section 3)
    enrolment(code, done, rules)         ->  {"status": "open" | "needs" | "closed", "needs": [...], "reason": ...}
    schedule(path, rules, start)         ->  the path laid out over sessions, prerequisites first

The access-conditions rule of a subject is a boolean expression over numbered items, for example
"((1 OR 1a) AND 2)". An item is satisfied when:
    academic, with a subject code   the student has taken that subject
    corequisite                     the student has taken it, or takes it in the same session
    admission                       its text names the student's course (C04372 for MDSI)
    academic, no code               (credit points) its text names the student's course
Anything else (admission into another course, an item the scrape did not capture) is not
satisfied, so we never recommend a subject the student may be refused. Antirequisites are read
item by item, not as a rule: the subject closes when the student has taken ANY subject on its
antirequisite list, or when it is on the antirequisite list of a subject they have taken (the
site often lists a pair on one side only). The rule string is ignored for antirequisites: the
site prints the list as "(1 AND 2 AND 3)", and some rules name items it does not list. A rule left empty because the access-conditions site has no
record of the subject (`evop_found` = n) is treated as open but flagged `unverified`.

A subject that is not open may still be reachable: if its rule is met by taking at most
MAX_NEEDS more subjects that are open now, recommend() adds them to the path before it.
Without the two files every subject is open and has no sessions, so the pipeline still runs
on the old profiles.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass, field
from datetime import date
from functools import lru_cache
from pathlib import Path

from . import paths

ROOT = paths.ROOT
PREREQUISITES_CSV = paths.PREREQUISITES
OFFERINGS_CSV = paths.OFFERINGS
HOME_COURSE = "C04372"
MAX_NEEDS = 2              # at most this many prerequisites are added for one subject
SESSIONS = ("Autumn", "Spring")
MAX_REASON = 160           # characters of the "why not" text the app shows


@dataclass(frozen=True)
class Item:
    type: str              # academic, admission, corequisite, other, or "" when the scrape left it blank
    code: str              # the subject it names, or ""
    text: str


@dataclass(frozen=True)
class Rule:
    expr: str                          # "((1 OR 1a) AND 2)"; "" = no condition
    items: dict[str, Item]


@dataclass
class Rules:
    requisite: dict[str, Rule] = field(default_factory=dict)
    antirequisite: dict[str, Rule] = field(default_factory=dict)
    unverified: set[str] = field(default_factory=set)       # no record on the access-conditions site
    offered: dict[str, tuple[str, ...]] = field(default_factory=dict)   # code -> teaching periods
    has_offerings: bool = False

    @property
    def loaded(self) -> bool:
        return bool(self.requisite or self.antirequisite or self.offered)


# ---------------------------------------------------------------------------- loading

def _read(path: Path) -> list[dict]:
    with open(path, encoding="utf-8-sig", newline="") as f:
        return [{k: (v or "").strip() for k, v in row.items()} for row in csv.DictReader(f)]


@lru_cache(maxsize=4)
def _load(prereq: str, prereq_mtime: float, offer: str, offer_mtime: float) -> Rules:
    rules = Rules()
    if prereq:
        parts: dict[tuple[str, str], tuple[str, dict]] = {}
        for row in _read(Path(prereq)):
            code, kind = row["subject_code"], row["kind"]
            expr, items = parts.setdefault((code, kind), (row.get("rule", ""), {}))
            if row.get("item"):
                items[row["item"]] = Item(row.get("type", ""), row.get("requisite_code", ""), row.get("requisite_text", ""))
            if row.get("evop_found") == "n":
                rules.unverified.add(code)
        for (code, kind), (expr, items) in parts.items():
            target = rules.requisite if kind == "requisite" else rules.antirequisite
            target[code] = Rule(expr, items)
    if offer:
        periods: dict[str, list[str]] = {}
        for row in _read(Path(offer)):
            periods.setdefault(row["subject_code"], []).append(row["teaching_period"])
        rules.offered = {code: tuple(dict.fromkeys(p)) for code, p in periods.items()}
        rules.has_offerings = True
    return rules


def load_rules(prerequisites_csv: str | Path | None = None, offerings_csv: str | Path | None = None) -> Rules:
    """The rules from the two files; a file that does not exist is skipped (everything open)."""
    paths = []
    for given, default in ((prerequisites_csv, PREREQUISITES_CSV), (offerings_csv, OFFERINGS_CSV)):
        path = Path(given) if given else default
        path = path if path.is_absolute() else ROOT / path
        paths += [str(path), path.stat().st_mtime] if path.exists() else ["", 0.0]
    return _load(*paths)


# ------------------------------------------------------------------- the rule expression

_TOKEN = re.compile(r"\(|\)|AND|OR|[0-9]+[a-z]*")


def _parse(expr: str):
    """"((1 OR 1a) AND 2)" -> ("AND", [("OR", ["1", "1a"]), "2"]). AND binds tighter than OR."""
    tokens = _TOKEN.findall(expr)
    pos = 0

    def take(expected=None):
        nonlocal pos
        token = tokens[pos] if pos < len(tokens) else None
        if expected and token != expected:
            raise ValueError(f"bad rule {expr!r}: expected {expected} at token {pos}")
        pos += 1
        return token

    def disjunction():
        parts = [conjunction()]
        while pos < len(tokens) and tokens[pos] == "OR":
            take("OR")
            parts.append(conjunction())
        return parts[0] if len(parts) == 1 else ("OR", parts)

    def conjunction():
        parts = [atom()]
        while pos < len(tokens) and tokens[pos] == "AND":
            take("AND")
            parts.append(atom())
        return parts[0] if len(parts) == 1 else ("AND", parts)

    def atom():
        if pos < len(tokens) and tokens[pos] == "(":
            take("(")
            node = disjunction()
            take(")")
            return node
        return take()

    tree = disjunction()
    if pos != len(tokens):
        raise ValueError(f"bad rule {expr!r}: trailing tokens")
    return tree


@lru_cache(maxsize=4096)
def _tree(expr: str):
    return _parse(expr)


def _satisfied(item: Item | None, done: set[str], home_course: str | None, same_session: set[str]) -> bool:
    if item is None:
        return False                                   # the scrape did not capture this item
    if item.code:
        return item.code in done or (item.type == "corequisite" and item.code in same_session)
    if home_course and home_course in item.text:      # admission into, or credit points in, the student's course
        return True
    return False


def _cost(node, rule: Rule, done, home_course, addable):
    """The fewest extra subjects that make `node` true: a frozenset, or None when impossible."""
    if isinstance(node, str):
        item = rule.items.get(node)
        if _satisfied(item, done, home_course, set()):
            return frozenset()
        if item is not None and item.code and item.type in ("academic", "corequisite") and addable(item.code):
            return frozenset({item.code})
        return None
    op, children = node
    costs = [_cost(child, rule, done, home_course, addable) for child in children]
    if op == "AND":
        if any(c is None for c in costs):
            return None
        return frozenset().union(*costs)
    options = [c for c in costs if c is not None]
    return min(options, key=lambda c: (len(c), sorted(c)), default=None)


def _true(node, rule: Rule, done, home_course) -> bool:
    if isinstance(node, str):
        return _satisfied(rule.items.get(node), done, home_course, set())
    op, children = node
    results = (_true(child, rule, done, home_course) for child in children)
    return all(results) if op == "AND" else any(results)


# -------------------------------------------------------------------------- enrolment

def _period(name: str) -> str | None:
    return next((s for s in SESSIONS if s in name), None)


def sessions_offered(code: str, rules: Rules) -> list[str]:
    """Autumn and/or Spring when the subject runs in them, else the periods it does run in."""
    periods = rules.offered.get(code, ())
    main = [s for s in SESSIONS if any(_period(p) == s for p in periods)]
    return main or list(periods)


def _describe(rule: Rule, done: set[str], home_course: str | None) -> str:
    """The part of a rule the student does not meet, in words: "needs 42172 ... or 41040 ..."."""
    def label(key: str) -> str:
        item = rule.items.get(key)
        if item is None:
            return f"item {key} (not in the Handbook data)"
        if item.code:
            return item.text or item.code
        if item.type == "admission":
            return "admission into another course"
        if "credit points" in item.text:
            return "credit points in another course"
        return item.text or "a condition the Handbook does not list"

    def render(node, top=False):
        if isinstance(node, str):
            return None if _satisfied(rule.items.get(node), done, home_course, set()) else label(node)
        op, children = node
        if op == "OR" and any(_true(c, rule, done, home_course) for c in children):
            return None
        parts = [p for p in (render(c) for c in children) if p]
        parts = list(dict.fromkeys(parts))
        if op == "OR" and len(parts) > 3:
            more = len(parts) - 3
            parts = parts[:3] + [f"{more} other option{'s' if more > 1 else ''}"]
        text = (" and " if op == "AND" else " or ").join(parts)
        return text if top or len(parts) == 1 else f"({text})"

    missing = render(_tree(rule.expr), top=True)
    if not missing:
        return ""
    text = "needs " + missing
    return text if len(text) <= MAX_REASON else text[: MAX_REASON - 1].rsplit(" ", 1)[0] + " …"


def antirequisite_clash(code: str, done: set[str], rules: Rules) -> list[str]:
    """Subjects in `done` that rule `code` out, in either direction."""
    anti = rules.antirequisite.get(code)
    mine = {it.code for it in anti.items.values() if it.code} if anti else set()
    theirs = {other for other in done
              if other in rules.antirequisite
              and code in {it.code for it in rules.antirequisite[other].items.values()}}
    return sorted((mine & done) | theirs)


def enrolment(code: str, done: set[str], rules: Rules, home_course: str | None = HOME_COURSE,
              _depth: int = 0) -> dict:
    """Whether the student can take `code` next, given the subjects in `done`.

    status  "open"    can enrol now
            "needs"   can enrol after the subjects in `needs` (each open now)
            "closed"  cannot: not taught this year, an antirequisite, or a condition we cannot meet
    """
    out = {"status": "open", "needs": [], "reason": "", "unverified": code in rules.unverified}
    if rules.has_offerings and code not in rules.offered and code in rules.requisite:   # scraped, no 2026 period
        return {**out, "status": "closed", "reason": "not taught in 2026 (Handbook)"}
    clash = antirequisite_clash(code, done, rules)
    if clash:
        return {**out, "status": "closed", "reason": f"antirequisite: already took {', '.join(clash)}"}
    rule = rules.requisite.get(code)
    if not rule or not rule.expr:
        return out

    def addable(other: str) -> bool:
        return (_depth == 0 and other != code and other not in done
                and other in rules.requisite              # a subject outside the scrape cannot be planned
                and enrolment(other, done, rules, home_course, _depth + 1)["status"] == "open")

    needs = _cost(_tree(rule.expr), rule, done, home_course, addable)
    if needs is None or len(needs) > MAX_NEEDS:
        return {**out, "status": "closed", "reason": _describe(rule, done, home_course)}
    if needs:
        return {**out, "status": "needs", "needs": sorted(needs), "reason": "take " + ", ".join(sorted(needs)) + " first"}
    return out


# --------------------------------------------------------------------------- sessions

def next_session(today: date | None = None) -> tuple[str, int]:
    """The next Autumn (Feb-Jun) or Spring (Jul-Nov) session a student can still plan for."""
    today = today or date.today()
    if today.month <= 2:
        return "Autumn", today.year
    if today.month <= 7:
        return "Spring", today.year
    return "Autumn", today.year + 1


def _session_names(start: tuple[str, int]):
    period, year = start
    i = SESSIONS.index(period)
    while True:
        yield f"{SESSIONS[i]} {year}"
        i += 1
        if i == len(SESSIONS):
            i, year = 0, year + 1


def schedule(path: list[str], rules: Rules, start: tuple[str, int] | None = None, done: set[str] | None = None,
             home_course: str | None = HOME_COURSE) -> list[dict]:
    """Lay the path over sessions: a subject goes in the first session after its prerequisites
    in the path that teaches it (a corequisite may share the session).

    Each item: subject_code, session ("Autumn 2027"), offered (["Autumn", "Spring"]), after
    (prerequisites taken earlier in the path), unverified.
    """
    names = list(zip(range(len(path) * 2 + 2), _session_names(start or next_session())))
    placed: dict[str, int] = {}
    plan = []
    for code in path:
        rule = rules.requisite.get(code)
        after, earliest = [], 0
        for it in (rule.items.values() if rule else ()):
            if it.code in placed:
                after.append(it.code)
                earliest = max(earliest, placed[it.code] + (0 if it.type == "corequisite" else 1))
        offered = sessions_offered(code, rules)
        main = [s for s in offered if s in SESSIONS]
        slot = next((i for i, name in names[earliest:] if not main or name.split()[0] in main), earliest)
        placed[code] = slot
        session = names[slot][1]
        if offered and not main:                         # Summer, Session 3, ...: no Autumn/Spring slot
            session = f"{' or '.join(offered[:2])}, {session.split()[1]}"
        plan.append({"subject_code": code, "session": session, "offered": offered,
                     "after": sorted(set(after)), "unverified": code in rules.unverified, "_slot": slot})
    plan.sort(key=lambda step: step["_slot"])            # stable: path order within a session
    for step in plan:
        del step["_slot"]
    return plan
