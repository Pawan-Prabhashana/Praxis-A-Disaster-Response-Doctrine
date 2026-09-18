"""Lessons + optional narrated assessment for an after-action review.

The structured **lessons** are deterministic (every number traces to the
analysis by construction). The short narrative **assessment** may optionally be
LLM-narrated, reusing the Phase-6 trust pipeline EXACTLY: real facts in, a
numeric-consistency guard on the output, deterministic template fallback, and it
works with no key (LLM injected/mocked in tests).
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from pydantic import BaseModel

from app.core.config import Settings
from app.core.logging import get_logger
from app.services.after_action.models import (
    AfterActionResult,
    DistrictComparison,
    Lesson,
    LessonSeverity,
)
from app.services.brief.guard import offending_numbers, pool_from_payload
from app.services.brief.llm import LlmClient, LlmError

log = get_logger("praxis.after_action.lessons")

CompleteFn = Callable[[str, str], Awaitable[str]]

SYSTEM_PROMPT = (
    "You are a disaster-response analyst writing the assessment line of an "
    "after-action review for a government command centre. You are given JSON FACTS "
    "already computed by Praxis. Rules, without exception:\n"
    "1. This is a PREDICTED-vs-RECORDED review. The recorded side is the ACTUAL "
    "historical event impact (DesInventar), NOT the outcome of executing any plan. "
    "Never imply the plan was executed or that these are its measured results.\n"
    "2. Every number you write MUST come from FACTS — never invent or alter one.\n"
    "3. Write 2-4 calm, plain-English sentences. No markdown, no lists."
)


def _n(value: int) -> str:
    return f"{value:,}"


def template_assessment(result: AfterActionResult) -> str:
    """Deterministic assessment paragraph (the fallback + guard baseline)."""
    a = result.alignment
    year = result.event_year
    when = f" {year}" if year else ""
    lead = (
        f"This is a predicted-vs-recorded review: Praxis's at-risk ranking for "
        f'"{result.playbook_name}" compared against the actual recorded{when} impact '
        f"(DesInventar historical baseline) — not the outcome of executing the plan. "
        f"The predicted and recorded rankings align {a.label} (Spearman {a.spearman}); "
        f"{a.top_k_overlap} of the top {a.top_k} hardest-hit districts were in the "
        f"strategy's predicted top {a.top_k}."
    )
    worst = result.worst_under_prioritised
    if worst is not None:
        lead += (
            f" Most notably, {worst.name} recorded {_n(worst.deaths)} deaths yet ranked "
            f"#{worst.predicted_rank} of {a.n_districts} in predicted at-risk — a signal to "
            f"weight recorded-impact history, not flood exposure alone."
        )
    return lead


def _ordinal_gap(result: AfterActionResult) -> DistrictComparison | None:
    """The most over-prioritised district (highest predicted, lower recorded)."""
    candidates = [d for d in result.districts if d.has_data and d.rank_delta <= -2]
    return min(candidates, key=lambda d: (d.rank_delta, -d.predicted_rank), default=None)


def build_template_lessons(result: AfterActionResult) -> list[Lesson]:
    """Structured, numbers-traceable lessons (deterministic)."""
    a = result.alignment
    lessons: list[Lesson] = []

    align_sev = {
        "inverted": LessonSeverity.CRIT,
        "weak": LessonSeverity.WARN,
        "moderate": LessonSeverity.INFO,
        "strong": LessonSeverity.INFO,
    }[a.label]
    lessons.append(
        Lesson(
            key="alignment",
            severity=align_sev,
            title=f"Prediction alignment: {a.label}",
            detail=(
                f"The strategy's at-risk ranking correlates {a.label} with recorded impact "
                f"(Spearman {a.spearman}); {a.top_k_overlap} of the top {a.top_k} hardest-hit "
                f"districts (of {a.n_with_data} with recorded data) were in its predicted "
                f"top {a.top_k}."
            ),
        )
    )

    worst = result.worst_under_prioritised
    if worst is not None:
        lessons.append(
            Lesson(
                key="under_prioritised",
                severity=LessonSeverity.CRIT,
                title=f"{worst.name} was under-prioritised",
                detail=(
                    f"{worst.name} recorded impact rank #{worst.impact_rank} "
                    f"({_n(worst.deaths)} deaths, {_n(worst.houses_destroyed)} houses destroyed, "
                    f"{_n(worst.affected)} affected) but ranked #{worst.predicted_rank} of "
                    f"{a.n_districts} in the strategy's predicted at-risk order."
                ),
            )
        )

    over = _ordinal_gap(result)
    if over is not None and (worst is None or over.pcode != worst.pcode):
        lessons.append(
            Lesson(
                key="over_prioritised",
                severity=LessonSeverity.WARN,
                title=f"{over.name} ranked highest at-risk but recorded lower impact",
                detail=(
                    f"{over.name} was predicted #{over.predicted_rank} at-risk but recorded "
                    f"{_n(over.deaths)} deaths (impact rank #{over.impact_rank}) — flood "
                    f"exposure did not track loss of life here."
                ),
            )
        )

    for spot in result.blind_spots[:2]:
        lessons.append(
            Lesson(
                key=f"blind_spot:{spot.pcode}",
                severity=LessonSeverity.CRIT,
                title=f"Blind spot: {spot.name} not prioritised",
                detail=(
                    f"{spot.name} recorded impact ({_n(spot.deaths)} deaths, "
                    f"{_n(spot.affected)} affected) but was outside the strategy's priority set."
                ),
            )
        )

    if worst is not None:
        focus = worst.name
    elif result.blind_spots:
        focus = result.blind_spots[0].name
    else:
        focus = None
    lessons.append(
        Lesson(
            key="loop_closure",
            severity=LessonSeverity.INFO,
            title="For next time",
            detail=(
                "Weight recorded-impact history — especially loss of life — alongside "
                "flood-inundation at-risk"
                + (f", so districts like {focus} are not under-weighted." if focus else ".")
            ),
        )
    )
    return lessons


class AssessmentGuard(BaseModel):
    ok: bool
    offending: list[str] = []
    from_template: bool = True


class LessonsContent(BaseModel):
    """Lessons plus the (optionally narrated) assessment and its guard outcome."""

    version: int = 1
    assessment: str
    lessons: list[Lesson]
    generator: str = "template"  # "llm" | "template"
    model: str | None = None
    guard: AssessmentGuard = AssessmentGuard(ok=True)


def _user_prompt(result: AfterActionResult) -> str:
    import json

    return (
        "Write the assessment paragraph (2-4 sentences) from these FACTS. Preserve "
        "the predicted-vs-recorded framing; use only numbers present in FACTS.\n\n"
        f"FACTS:\n{json.dumps(result.model_dump(mode='json'))}"
    )


async def generate_lessons(
    result: AfterActionResult,
    settings: Settings,
    *,
    complete: CompleteFn | None = None,
) -> LessonsContent:
    """Template lessons always; assessment via guarded LLM when available."""
    lessons = build_template_lessons(result)
    fallback = template_assessment(result)

    call = complete
    if call is None:
        if not settings.llm_ready:
            log.info("after_action.lessons", generator="template", reason="llm_disabled")
            return LessonsContent(assessment=fallback, lessons=lessons)
        try:
            call = LlmClient(settings).complete
        except LlmError as exc:
            log.warning("after_action.llm_unavailable", error=str(exc))
            return LessonsContent(assessment=fallback, lessons=lessons)

    try:
        raw = await call(SYSTEM_PROMPT, _user_prompt(result))
    except LlmError as exc:
        log.warning("after_action.llm_failed_fallback_template", error=str(exc))
        return LessonsContent(assessment=fallback, lessons=lessons, model=settings.llm_model)

    pool = pool_from_payload(result.model_dump(mode="json"))
    offending = offending_numbers(raw, pool)
    if offending:
        log.warning("after_action.assessment_guard_repaired", offending=offending)
        return LessonsContent(
            assessment=fallback,
            lessons=lessons,
            generator="template",
            model=settings.llm_model,
            guard=AssessmentGuard(ok=False, offending=offending, from_template=True),
        )

    log.info("after_action.lessons", generator="llm")
    return LessonsContent(
        assessment=raw.strip(),
        lessons=lessons,
        generator="llm",
        model=settings.llm_model,
        guard=AssessmentGuard(ok=True, from_template=False),
    )
