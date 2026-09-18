"""Deterministic brief template.

Renders a complete, professional brief from ``BriefFacts`` alone — no LLM. This
is BOTH the no-key fallback path and the per-section source the numeric guard
uses to repair any LLM section that fails validation. Every number here comes
straight from the facts, so it is correct by construction.
"""

from __future__ import annotations

from app.services.brief.content import (
    SECTION_ORDER,
    SECTION_TITLES,
    BriefContent,
    BriefSection,
    SectionKey,
)
from app.services.brief.facts import BriefFacts


def _n(value: float | int) -> str:
    """Format an integer-valued number with thousands separators."""
    return f"{round(value):,}"


def _score(value: float) -> str:
    """A score formatted to one decimal (matches how facts store scores)."""
    return f"{value:.1f}"


def _join_regions(facts: BriefFacts) -> str:
    names = [r.name for r in facts.strategy.priority_regions]
    if not names:
        return "no districts"
    return ", ".join(names)


def _situation(facts: BriefFacts) -> list[str]:
    s = facts.scenario
    when = f" ({s.event_date.isoformat()})" if s.event_date else ""
    paras = [
        f"{s.name}{when} is a {s.hazard_type} event. Within the observed flood extent, "
        f"an estimated {_n(facts.scorecard.total_at_risk)} people across the affected "
        f"districts are at risk."
    ]
    if s.description:
        paras.append(s.description)
    return paras


def _strategy(facts: BriefFacts) -> list[str]:
    st = facts.strategy
    sc = facts.scorecard
    paras = [
        f"This brief recommends the “{st.name}” strategy. It prioritises "
        f"{st.priority_region_count} district(s) — {_join_regions(facts)} — covering "
        f"{_n(sc.covered_at_risk)} of the {_n(sc.total_at_risk)} at-risk population.",
        f"It activates {_n(st.activated_shelter_count)} shelter(s) providing an estimated "
        f"{_n(st.activated_capacity)} spaces, supported by {_n(st.response_teams)} response "
        f"team(s) and {_n(st.boats)} boat(s) under a "
        f"{st.allocation.replace('_', ' ')} allocation.",
    ]
    if st.description:
        paras.append(st.description)
    return paras


def _performance(facts: BriefFacts) -> list[str]:
    sc = facts.scorecard
    metric_bits = ", ".join(
        f"{m.label} {_score(m.score)}/100 (weight {m.weight_pct}%)" for m in sc.metrics
    )
    paras = [
        f"On the deterministic scorecard the strategy scores {_score(sc.overall)}/100: "
        f"{metric_bits}."
    ]
    r = facts.robustness
    if r is not None:
        paras.append(
            f"Under modeled uncertainty ({_n(r.n_iterations)} Monte Carlo iterations, "
            f"seed {r.seed}) the overall score spans {_score(r.p05)}-{_score(r.p95)} "
            f"(90% band) around a median of {_score(r.median)}. The worst-plausible outcome "
            f"(5th percentile) is {_score(r.worst_plausible)}, and the strategy meets the "
            f"target of {r.target_score} in {r.probability_meets_target_pct}% of modeled "
            f"conditions."
        )
        note = (
            "This is modeled (epistemic) uncertainty from documented parameter distributions, "
            "not measured forecast spread."
        )
        if r.point_is_optimistic:
            note += (
                f" Note the deterministic point score ({_score(r.point_overall)}) sits above "
                f"the median under uncertainty — treat the point score as optimistic."
            )
        paras.append(note)
    return paras


def _tasking(facts: BriefFacts) -> list[str]:
    st = facts.strategy
    paras: list[str] = []
    if st.priority_regions:
        lines = [
            f"{r.name}: {_n(r.at_risk_population)} at risk"
            + (" — access impaired by closures" if r.is_access_impaired else "")
            for r in st.priority_regions
        ]
        paras.append("Priority districts for tasking: " + "; ".join(lines) + ".")
    paras.append(
        f"Stand up {_n(st.activated_shelter_count)} shelter(s) (~{_n(st.activated_capacity)} "
        f"spaces) and deploy {_n(st.response_teams)} team(s) and {_n(st.boats)} boat(s), "
        f"allocated {st.allocation.replace('_', ' ')}."
    )
    evac = (
        f"Evacuate districts whose at-risk population is at least "
        f"{_n(st.evacuation_threshold)}."
        if st.evacuation_threshold > 0
        else "Evacuation is advised across all prioritised districts."
    )
    access = (
        " Route around closed roads where flagged."
        if st.avoid_closed_roads
        else " Road closures are not being routed around in this plan."
    )
    paras.append(evac + access)
    return paras


def _risks(facts: BriefFacts) -> list[str]:
    paras: list[str] = []
    gaps = facts.coverage_gaps
    if gaps:
        top = gaps[:5]
        bits = ", ".join(f"{g.name} ({_n(g.at_risk_population)})" for g in top)
        paras.append(
            f"{facts.scorecard.coverage_gap_count} at-risk district(s) fall outside the priority "
            f"set, leaving {_n(facts.scorecard.uncovered_at_risk)} people uncovered. "
            f"Largest gaps: {bits}."
        )
    else:
        paras.append("No at-risk districts are left outside the priority set.")
    if facts.synthetic_influences:
        paras.append("Data caution: " + " ".join(facts.synthetic_influences))
    return paras


def _provenance(facts: BriefFacts) -> list[str]:
    paras = ["Assumptions: " + " ".join(facts.assumptions)]
    if facts.synthetic_influences:
        paras.append("Synthetic influences: " + " ".join(facts.synthetic_influences))
    if facts.robustness is not None:
        paras.append(
            f"Robustness figures are reproducible from seed {facts.robustness.seed} over "
            f"{_n(facts.robustness.n_iterations)} iterations. {facts.robustness.epistemic_note}"
        )
    paras.append(
        "All figures in this brief are computed by Praxis from real ingested data and "
        "validated against source; narrative structure only is AI-assisted."
    )
    return paras


_BUILDERS = {
    SectionKey.SITUATION: _situation,
    SectionKey.STRATEGY: _strategy,
    SectionKey.PERFORMANCE: _performance,
    SectionKey.TASKING: _tasking,
    SectionKey.RISKS: _risks,
    SectionKey.PROVENANCE: _provenance,
}


def template_headline(facts: BriefFacts) -> str:
    return f"Operational brief — {facts.strategy.name}"


def render_section(key: SectionKey, facts: BriefFacts) -> BriefSection:
    """Render one section from facts alone (used for fallback and guard repair)."""
    return BriefSection(
        key=key,
        title=SECTION_TITLES[key],
        paragraphs=_BUILDERS[key](facts),
        from_template=True,
    )


def render_template_brief(facts: BriefFacts) -> BriefContent:
    """Render the complete brief deterministically from facts (no LLM)."""
    return BriefContent(
        headline=template_headline(facts),
        sections=[render_section(key, facts) for key in SECTION_ORDER],
        generator="template",
    )
