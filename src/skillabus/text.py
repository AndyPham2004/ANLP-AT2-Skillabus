"""Small text helpers shared by the pipeline stages."""

from __future__ import annotations

import io
import re
from pathlib import Path

EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE = re.compile(r"(?<![\w(])(?:\+?\(?\d[\d\s().-]{7,}\d)(?!\w)")
# "2019-2022" and "120000-140000" match PHONE's shape: two digit runs joined by a dash are a range.
RANGE = re.compile(r"\d+\s*[-\u2013]\s*\d+")
URL = re.compile(r"\b(?:https?://|www\.)\S+|\blinkedin\.com/\S+", re.I)


def mask_pii(text: str) -> str:
    """Replace emails, phone numbers and URLs before any text leaves the machine."""
    text = EMAIL.sub("[EMAIL]", text or "")
    text = URL.sub("[URL]", text)
    return PHONE.sub(_phone, text)


def _phone(m: re.Match) -> str:
    """A phone number has 8+ digits and is not a plain range ("2019-2022", "120000-140000")."""
    span = m.group()
    if sum(c.isdigit() for c in span) < 8 or RANGE.fullmatch(span.strip()):
        return span
    return "[PHONE]"


def read_csv_skipping_notes(path, **kwargs):
    """pandas.read_csv without the leading "# ..." note lines.

    read_csv(comment="#") also cuts every value at "#", so the C# row became "C".
    """
    import pandas as pd
    lines = Path(path).read_text(encoding="utf-8").splitlines(keepends=True)
    return pd.read_csv(io.StringIO("".join(l for l in lines if not l.startswith("#"))), **kwargs)


def split_sentences(s: str) -> list[str]:
    s = re.sub(r"\s+", " ", s or "").strip()
    return [p.strip() for p in re.split(r"(?<=[.!?])\s+", s) if len(p.strip()) > 3]


def text_units(text: str) -> list[str]:
    """Bullets and sentences of an ad or resume, with hard line wraps joined back up."""
    units = []
    for block in re.split(r"\n\s*[-•*▪●]\s+|\n\s*\n", text or ""):
        units.extend(split_sentences(block.replace("\n", " ")))
    return units


def sentence_with(span: str, units: list[str]) -> str | None:
    """The first sentence containing span as a whole word (case-insensitive), or None if it is not in the text.

    Whole-word matters for short skills: "R" must not match the r in "your".
    """
    rx = re.compile(rf"(?<![\w+#]){re.escape(span.strip())}(?![\w+#])", re.I)
    return next((u for u in units if rx.search(u)), None)


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
