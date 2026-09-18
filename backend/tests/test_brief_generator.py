"""Unit tests for brief generation: template fallback + guarded LLM narration.

No test calls a real LLM. The no-key path must yield a complete, valid brief;
the LLM path is exercised with an injected fake completion.
"""

from __future__ import annotations

import json

from app.core.config import Settings
from app.services.brief.content import SECTION_ORDER
from app.services.brief.generator import generate_brief
from tests.brief_fixtures import make_facts


def _all_sections_present(content) -> bool:
    return [s.key.value for s in content.sections] == [k.value for k in SECTION_ORDER]


async def test_no_key_uses_template_and_is_complete() -> None:
    facts = make_facts()
    result = await generate_brief(facts, Settings(llm_enabled=False, llm_api_key=None))
    assert result.generator == "template"
    assert result.guard.ok
    assert _all_sections_present(result.content)
    assert all(s.from_template for s in result.content.sections)


async def test_enabled_but_no_key_falls_back_to_template() -> None:
    # llm_enabled True but no key -> not llm_ready -> template, no network.
    facts = make_facts()
    result = await generate_brief(facts, Settings(llm_enabled=True, llm_api_key=None))
    assert result.generator == "template"


async def test_llm_hallucinated_number_is_repaired_from_template() -> None:
    facts = make_facts()

    async def fake_complete(system: str, user: str) -> str:
        sections = {k.value: ["Prose without any figures."] for k in SECTION_ORDER}
        sections["situation"] = ["An impossible 987,654 people are affected."]
        return json.dumps(sections)

    settings = Settings(llm_enabled=True, llm_api_key="test-key")
    result = await generate_brief(facts, settings, complete=fake_complete)

    assert result.generator == "llm"  # at least one clean section survived
    assert "situation" in result.guard.repaired_sections
    situation = next(s for s in result.content.sections if s.key.value == "situation")
    assert situation.from_template  # the fabricated section was replaced
    strategy = next(s for s in result.content.sections if s.key.value == "strategy")
    assert not strategy.from_template  # a clean section is kept as LLM prose


async def test_unparsable_llm_output_falls_back_to_template() -> None:
    facts = make_facts()

    async def broken_complete(system: str, user: str) -> str:
        return "not json at all"

    settings = Settings(llm_enabled=True, llm_api_key="test-key")
    result = await generate_brief(facts, settings, complete=broken_complete)
    assert result.generator == "template"
    assert _all_sections_present(result.content)
