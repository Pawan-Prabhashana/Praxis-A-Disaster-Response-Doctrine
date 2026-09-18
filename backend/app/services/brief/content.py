"""Structured brief content — the section skeleton shared by every generator.

Both the LLM generator and the deterministic template emit exactly this shape,
so rendering (frontend, HTML, PDF) never needs to know which produced it. The
section set is FIXED and ordered; only the prose differs.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

BRIEF_CONTENT_VERSION = 1


class SectionKey(StrEnum):
    SITUATION = "situation"
    STRATEGY = "strategy"
    PERFORMANCE = "performance"
    TASKING = "tasking"
    RISKS = "risks"
    PROVENANCE = "provenance"


# Ordered sections with their canonical titles. The generator fills the body.
SECTION_TITLES: dict[SectionKey, str] = {
    SectionKey.SITUATION: "Situation overview",
    SectionKey.STRATEGY: "Recommended strategy & rationale",
    SectionKey.PERFORMANCE: "Expected performance",
    SectionKey.TASKING: "Priority actions & tasking",
    SectionKey.RISKS: "Coverage gaps & risks",
    SectionKey.PROVENANCE: "Assumptions & data provenance",
}

SECTION_ORDER: tuple[SectionKey, ...] = tuple(SECTION_TITLES.keys())


class BriefSection(BaseModel):
    """One rendered section: a title and one or more prose paragraphs."""

    key: SectionKey
    title: str
    # Paragraphs of plain prose. A list keeps rendering deterministic (no
    # markdown parsing needed) while allowing multi-paragraph sections.
    paragraphs: list[str] = Field(default_factory=list)
    # True when this section's prose came from the template (originally, or after
    # the numeric guard rejected the LLM version).
    from_template: bool = False


class BriefContent(BaseModel):
    """The full ordered brief body, plus how it was produced."""

    version: int = BRIEF_CONTENT_VERSION
    headline: str
    sections: list[BriefSection]
    # "llm" when narration passed the guard for at least one section, else
    # "template". Individual sections carry their own ``from_template`` flag.
    generator: str = "template"
