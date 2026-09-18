"""Prompt construction for the brief narrator.

The model receives the facts payload and is instructed to STRUCTURE and NARRATE
it — never to introduce a number or place not present in the facts. Output is
strict JSON keyed by the fixed section ids so parsing/rendering is deterministic.
The numeric guard is the enforcement; this prompt is the first line of defence.
"""

from __future__ import annotations

import json

from app.services.brief.content import SECTION_TITLES, SectionKey
from app.services.brief.facts import BriefFacts

SYSTEM_PROMPT = (
    "You are an operations officer drafting a disaster-response operational brief "
    "for a government command centre. You write in clear, calm, command-oriented "
    "English for field commanders. You are given a JSON payload of FACTS already "
    "computed by the Praxis platform. You must obey these rules without exception:\n"
    "1. Every quantity, place name, score, population, capacity, seed, and date you "
    "write MUST come from the FACTS payload. Never invent, estimate, round beyond the "
    "given precision, or infer any number or place not present in FACTS.\n"
    "2. Preserve honesty flags: where a metric's provenance is 'synthetic' or "
    "'assumption', say so; keep the modeled (epistemic) framing for uncertainty and "
    "never present it as measured forecast spread.\n"
    "3. Do not give investment, legal, or medical advice; do not add recommendations "
    "unsupported by FACTS.\n"
    "4. Output STRICT JSON only, no markdown, no commentary."
)


def _section_list() -> str:
    return "\n".join(f'  - "{key.value}": {title}' for key, title in SECTION_TITLES.items())


def build_user_prompt(facts: BriefFacts) -> str:
    """The user message: instructions, the required shape, and the FACTS."""
    keys = ", ".join(f'"{k.value}"' for k in SectionKey)
    facts_json = json.dumps(facts.model_dump(mode="json"), indent=2)
    return (
        "Write the operational brief as STRICT JSON. The top-level object must have "
        f"exactly these keys: {keys}. Each value is an array of 1-3 prose paragraphs "
        "(plain strings, no markdown). Sections and their intent:\n"
        f"{_section_list()}\n\n"
        "Guidance per section:\n"
        "  - situation: the event and the scale of who is at risk (from FACTS).\n"
        "  - strategy: the recommended strategy and why, in plain terms.\n"
        "  - performance: the deterministic score AND, if present, the stress-test "
        "robustness (band, worst-plausible, probability of meeting target) with the "
        "epistemic-uncertainty framing.\n"
        "  - tasking: concrete priority actions — which districts, shelters, resource "
        "allocation, evacuation policy.\n"
        "  - risks: coverage gaps and anything resting on synthetic/assumption data.\n"
        "  - provenance: assumptions, synthetic influences, seed/reproducibility.\n\n"
        "Every number and place must be traceable to FACTS. Output JSON only.\n\n"
        f"FACTS:\n{facts_json}"
    )
