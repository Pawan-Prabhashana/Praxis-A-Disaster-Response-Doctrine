"""Unit tests for the numeric-consistency guard (anti-hallucination)."""

from __future__ import annotations

from app.services.brief.content import BriefSection, SectionKey
from app.services.brief.guard import build_number_pool, check_section, verify_brief
from tests.brief_fixtures import make_facts


def _section(text: str) -> BriefSection:
    return BriefSection(key=SectionKey.SITUATION, title="Situation overview", paragraphs=[text])


def test_guard_passes_numbers_present_in_facts() -> None:
    facts = make_facts()
    pool = build_number_pool(facts)
    # 549,007 covered + 260 teams are real facts; formatting/commas are tolerated.
    section = _section("The strategy covers 549,007 people with 260 teams.")
    report = check_section(section, pool)
    assert report.ok
    assert report.numbers_checked == 2


def test_guard_rejects_a_fabricated_number() -> None:
    facts = make_facts()
    pool = build_number_pool(facts)
    section = _section("An estimated 999,999 people are at risk.")
    report = check_section(section, pool)
    assert not report.ok
    assert "999,999" in report.offending


def test_guard_tolerates_integer_rounding_of_a_score() -> None:
    facts = make_facts()
    pool = build_number_pool(facts)
    overall = facts.scorecard.overall  # e.g. 41.2
    rounded = str(round(overall))  # the model may round to an integer
    section = _section(f"The strategy scores {rounded} out of 100.")
    assert check_section(section, pool).ok


def test_verify_brief_flags_the_offending_section_only() -> None:
    facts = make_facts()
    good = BriefSection(key=SectionKey.STRATEGY, title="s", paragraphs=["Prioritises 2 districts."])
    bad = BriefSection(
        key=SectionKey.SITUATION, title="s", paragraphs=["12,345,678 people at risk."]
    )
    report = verify_brief(facts, [good, bad])
    assert not report.ok
    assert report.failed_keys == {"situation"}
