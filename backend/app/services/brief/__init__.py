"""Operational-brief generation (Phase 6 — Act).

The brief NARRATES real computed facts; it never invents them. The trust
boundary is ``facts.BriefFacts`` — the only thing the generator may state as
fact — and ``guard.verify_brief`` enforces that every number in the generated
prose traces back to those facts. See docs/BRIEF.md.
"""
