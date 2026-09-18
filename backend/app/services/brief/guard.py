"""Numeric-consistency guard — the structural anti-hallucination boundary.

Rule enforced: **every number in the generated prose must trace back to a number
in ``BriefFacts``.** We build a pool of every numeric token that appears anywhere
in the facts payload (numeric fields and numbers embedded in strings such as
dates, notes, and assumptions — all themselves facts), then check each number in
each generated section against it. A section containing a number that is NOT in
the pool has failed and is repaired from the deterministic template. No
unverified figure is ever emitted. Guard outcomes are logged by the generator.
"""

from __future__ import annotations

import json
import re

from pydantic import BaseModel, Field

from app.services.brief.content import BriefSection
from app.services.brief.facts import BriefFacts

# Numbers like 1234, 1,234, 12.5, 60 — optionally with a trailing percent sign
# (which we drop; the numeric value is what matters).
_NUMBER_RE = re.compile(r"\d[\d,]*(?:\.\d+)?")

# Percentile / scale anchors used in standard phrasing ("90% band", "5th
# percentile", "/100"). Every domain figure (counts, scores, populations,
# target, seed) is validated against the facts pool proper, not these.
_SCALE_ANCHORS: frozenset[float] = frozenset({0.0, 5.0, 25.0, 50.0, 75.0, 90.0, 95.0, 100.0})


class SectionGuard(BaseModel):
    key: str
    ok: bool
    numbers_checked: int
    offending: list[str] = Field(default_factory=list)


class GuardReport(BaseModel):
    """The outcome of validating a generated brief against its facts."""

    ok: bool
    sections: list[SectionGuard] = Field(default_factory=list)
    repaired_sections: list[str] = Field(default_factory=list)

    @property
    def failed_keys(self) -> set[str]:
        return {s.key for s in self.sections if not s.ok}


def _to_float(token: str) -> float | None:
    try:
        return float(token.replace(",", ""))
    except ValueError:
        return None


def extract_numbers(text: str) -> list[float]:
    """All numeric values in a string (commas stripped, percent ignored)."""
    out: list[float] = []
    for match in _NUMBER_RE.findall(text):
        value = _to_float(match)
        if value is not None:
            out.append(value)
    return out


def build_number_pool(facts: BriefFacts) -> set[float]:
    """Every number that legitimately appears in the facts (the allow-set)."""
    payload = json.dumps(facts.model_dump(mode="json"))
    pool = set(extract_numbers(payload))
    return pool | set(_SCALE_ANCHORS)


def _matches(candidate: float, pool: set[float]) -> bool:
    """True when ``candidate`` equals a pool value within rounding tolerance.

    Tolerance is the larger of 0.5 (integer rounding of a one-decimal score) and
    1% of the value (formatting/rounding of large populations). A materially
    different number — a fabricated fact — falls outside this and is rejected.
    """
    return any(abs(candidate - allowed) <= max(0.5, abs(allowed) * 0.01) for allowed in pool)


def check_section(section: BriefSection, pool: set[float]) -> SectionGuard:
    """Validate every number in one generated section against the pool."""
    offending: list[str] = []
    checked = 0
    for paragraph in section.paragraphs:
        for match in _NUMBER_RE.findall(paragraph):
            value = _to_float(match)
            if value is None:
                continue
            checked += 1
            if not _matches(value, pool):
                offending.append(match)
    return SectionGuard(
        key=str(section.key),
        ok=not offending,
        numbers_checked=checked,
        offending=offending,
    )


def verify_brief(facts: BriefFacts, sections: list[BriefSection]) -> GuardReport:
    """Validate a set of generated sections; report per-section pass/fail."""
    pool = build_number_pool(facts)
    reports = [check_section(s, pool) for s in sections]
    return GuardReport(ok=all(r.ok for r in reports), sections=reports)
