"""Brief generation orchestration: template, or LLM narration under the guard.

Flow (always safe):
  1. No LLM ready (disabled / no key) -> deterministic template. Done.
  2. LLM ready -> one bounded call; parse JSON sections.
     - parse failure -> full template fallback.
  3. Numeric guard validates each generated section against the facts.
     - any failing or missing section is REPAIRED from the template.
  4. The brief ships only guard-clean prose; provenance records what happened.
"""

from __future__ import annotations

import json
import re
from collections.abc import Awaitable, Callable

from pydantic import BaseModel

from app.core.config import Settings
from app.core.logging import get_logger
from app.services.brief.content import (
    SECTION_ORDER,
    SECTION_TITLES,
    BriefContent,
    BriefSection,
    SectionKey,
)
from app.services.brief.facts import BriefFacts
from app.services.brief.guard import GuardReport, verify_brief
from app.services.brief.llm import LlmClient, LlmError
from app.services.brief.prompt import SYSTEM_PROMPT, build_user_prompt
from app.services.brief.template import render_section, render_template_brief, template_headline

log = get_logger("praxis.brief.generator")

# An async completion function: (system, user) -> raw text. Injectable for tests.
CompleteFn = Callable[[str, str], Awaitable[str]]

_FENCE_RE = re.compile(r"^\s*```(?:json)?\s*|\s*```\s*$", re.IGNORECASE)


class GeneratedBrief(BaseModel):
    """The generated brief plus how it was produced (for persistence/audit)."""

    content: BriefContent
    guard: GuardReport
    generator: str  # "llm" | "template"
    model: str | None = None


def _template_result(facts: BriefFacts, *, model: str | None = None) -> GeneratedBrief:
    content = render_template_brief(facts)
    # A template brief is trivially guard-clean (numbers come from facts).
    guard = verify_brief(facts, content.sections)
    return GeneratedBrief(content=content, guard=guard, generator="template", model=model)


def _parse_sections(raw: str) -> dict[str, list[str]] | None:
    """Parse the model's JSON into {section_key: [paragraphs]} or None."""
    cleaned = _FENCE_RE.sub("", raw.strip())
    try:
        data = json.loads(cleaned)
    except (json.JSONDecodeError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    out: dict[str, list[str]] = {}
    for key, value in data.items():
        if isinstance(value, str):
            paras = [value]
        elif isinstance(value, list):
            paras = [str(p).strip() for p in value if str(p).strip()]
        else:
            continue
        if paras:
            out[str(key)] = paras
    return out


async def generate_brief(
    facts: BriefFacts,
    settings: Settings,
    *,
    complete: CompleteFn | None = None,
) -> GeneratedBrief:
    """Produce a brief: template when no LLM, else guarded LLM narration."""
    call = complete
    if call is None:
        if not settings.llm_ready:
            log.info("brief.generated", generator="template", reason="llm_disabled")
            return _template_result(facts)
        try:
            client = LlmClient(settings)
        except LlmError as exc:
            log.warning("brief.llm_unavailable", error=str(exc))
            return _template_result(facts)
        call = client.complete

    # One bounded LLM call; any failure falls back to the template.
    try:
        raw = await call(SYSTEM_PROMPT, build_user_prompt(facts))
    except LlmError as exc:
        log.warning("brief.llm_failed_fallback_template", error=str(exc))
        return _template_result(facts, model=settings.llm_model)

    parsed = _parse_sections(raw)
    if parsed is None:
        log.warning("brief.llm_unparsable_fallback_template")
        return _template_result(facts, model=settings.llm_model)

    # Build candidate LLM sections (missing ones will be templated below).
    llm_sections: list[BriefSection] = []
    for key in SECTION_ORDER:
        paragraphs = parsed.get(key.value)
        if paragraphs:
            llm_sections.append(
                BriefSection(key=key, title=SECTION_TITLES[key], paragraphs=paragraphs)
            )

    guard = verify_brief(facts, llm_sections)
    failed = guard.failed_keys  # set[str]
    by_key: dict[SectionKey, BriefSection] = {s.key: s for s in llm_sections}

    sections: list[BriefSection] = []
    repaired: list[str] = []
    llm_kept = 0
    for key in SECTION_ORDER:
        candidate = by_key.get(key)
        if candidate is not None and key.value not in failed:
            sections.append(candidate)
            llm_kept += 1
        else:
            sections.append(render_section(key, facts))
            repaired.append(key.value)

    guard.repaired_sections = repaired
    generator = "llm" if llm_kept > 0 else "template"
    log.info(
        "brief.generated",
        generator=generator,
        llm_sections=llm_kept,
        repaired=len(repaired),
        repaired_keys=repaired,
    )
    content = BriefContent(
        headline=template_headline(facts),
        sections=sections,
        generator=generator,
    )
    return GeneratedBrief(
        content=content, guard=guard, generator=generator, model=settings.llm_model
    )
