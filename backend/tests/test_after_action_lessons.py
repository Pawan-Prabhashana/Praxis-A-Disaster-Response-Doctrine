"""Unit tests for after-action lessons + guarded assessment (keyless)."""

from __future__ import annotations

from app.core.config import Settings
from app.services.after_action.analysis import build_after_action
from app.services.after_action.lessons import build_template_lessons, generate_lessons
from app.services.brief.guard import offending_numbers, pool_from_payload
from tests.after_action_fixtures import OUTCOMES, PREDICTIONS


def _result():
    return build_after_action("s", "Wide coverage", 2017, PREDICTIONS, OUTCOMES)


def test_template_lessons_are_traceable_and_flag_the_inversion() -> None:
    r = _result()
    lessons = build_template_lessons(r)
    keys = {le.key for le in lessons}
    assert "alignment" in keys
    assert "under_prioritised" in keys
    assert "loop_closure" in keys
    # Every number in every lesson traces to the analysis (guard-clean).
    pool = pool_from_payload(r.model_dump(mode="json"))
    for le in lessons:
        assert offending_numbers(le.detail, pool) == []


async def test_no_key_assessment_is_template_and_guard_clean() -> None:
    r = _result()
    content = await generate_lessons(r, Settings(llm_enabled=False, llm_api_key=None))
    assert content.generator == "template"
    assert content.guard.ok
    pool = pool_from_payload(r.model_dump(mode="json"))
    assert offending_numbers(content.assessment, pool) == []


async def test_clean_llm_assessment_is_kept() -> None:
    r = _result()

    async def good(system: str, user: str) -> str:
        return "Predicted-vs-recorded: rankings align inverted (Spearman -0.5)."

    content = await generate_lessons(r, Settings(llm_enabled=True, llm_api_key="k"), complete=good)
    assert content.generator == "llm"
    assert content.guard.ok


async def test_hallucinated_assessment_falls_back_to_template() -> None:
    r = _result()

    async def bad(system: str, user: str) -> str:
        return "An impossible 987654 people died in Ratnapura."

    content = await generate_lessons(r, Settings(llm_enabled=True, llm_api_key="k"), complete=bad)
    assert content.generator == "template"
    assert content.guard.ok is False
    assert "987654" in content.guard.offending
