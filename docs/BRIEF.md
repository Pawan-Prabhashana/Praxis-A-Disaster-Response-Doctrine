# The operational brief — trust model & pipeline

Praxis turns a chosen playbook (and, optionally, its stress-test result) into a
structured, exportable **operational brief** a commander could hand to field
teams. The defining rule of this phase:

> **The LLM narrates and structures REAL computed data. It never invents,
> estimates, or alters any number, place, or fact.**

Every quantity in a brief — scores, bands, worst-plausible, populations, shelter
counts/capacity, priority regions, coverage gaps — comes from the Phase-4 scoring
result and the Phase-5 stress result. The model's job is prose, ordering, and
emphasis. This document is the judge-defense for *"how do you stop it
hallucinating?"*.

## The pipeline (facts → prompt → guard → render)

```
playbook + scenario + (optional) stress run
        │  gather_scoring_inputs()  ·  score()  ·  StressResult
        ▼
build_brief_facts(...)  ──►  BriefFacts     [the trust boundary]
        │                    the ONLY thing stated as fact
        ├─────────────────────────────► render_template_brief(facts)
        │                                deterministic prose (no LLM)
        ▼
prompt (facts + strict rules)  ──►  LLM (one bounded call)  ──►  JSON sections
        ▼
verify_brief(facts, sections)  ──►  GuardReport
        │  any section with a number NOT in the facts  → repaired from template
        ▼
BriefContent (guard-clean)  ──►  persist (brief table)  ──►  render HTML / PDF
```

Source: `backend/app/services/brief/` (`facts.py`, `prompt.py`, `llm.py`,
`guard.py`, `generator.py`, `template.py`, `render.py`).

## 1. The trust boundary — `BriefFacts`

`build_brief_facts(...)` assembles a typed object of **only real computed facts**:
scenario identity; the strategy's levers in plain terms (priority districts by
name + at-risk, activated shelters + assumed capacity, resource posture,
evacuation policy); the deterministic scorecard (per-metric score, weight,
**provenance class**, raw numbers); the stress summary (median, p05–p95 band,
worst-plausible, probability of meeting target, seed, iterations, epistemic
note); coverage gaps; and an explicit list of assumptions and synthetic
influences. Assembly is pure — no DB/HTTP/clock/randomness. **Nothing else may be
stated as fact.**

Honesty flags survive end to end: each metric keeps its `real` / `synthetic` /
`assumption` provenance, and the modeled-(epistemic)-uncertainty framing is
attached to every robustness figure. A brief built on a synthetic-influenced
metric (accessibility, from synthetic road closures) says so.

## 2. Section structure (fixed)

Both generators emit the same ordered sections, so rendering never depends on
which produced them:

1. **Situation overview** — the event and who is at risk.
2. **Recommended strategy & rationale** — the levers in plain terms.
3. **Expected performance** — the deterministic scorecard **and** the stress-test
   robustness in plain language, with the epistemic framing visible.
4. **Priority actions & tasking** — districts, shelters, resource allocation,
   evacuation policy.
5. **Coverage gaps & risks** — uncovered at-risk population; anything resting on
   sample/assumption data.
6. **Assumptions & data provenance** — assumptions, synthetic influences, seed /
   reproducibility.

## 3. The numeric-consistency guard (anti-hallucination)

After generation, `verify_brief` enforces the core invariant:

- Build a **number pool**: every numeric token that appears anywhere in the facts
  payload — numeric fields *and* numbers embedded in strings (dates, notes,
  assumptions), since those are themselves facts — plus a small set of
  percentile/scale anchors (`0, 5, 25, 50, 75, 90, 95, 100`) for standard phrasing
  ("90% band", "5th percentile", "/100").
- Extract every number from each generated section and check it against the pool,
  tolerant of formatting (commas, `%`) and rounding (the larger of ±0.5 and ±1%,
  so a one-decimal score written as an integer, or a population re-rounded, still
  matches — but a materially different, fabricated figure does not).
- Any section containing an unmatched number **fails** and is **replaced by its
  deterministic template version** (which is correct by construction). Clean
  sections keep their AI prose. Outcomes are logged (`brief.generated` with the
  repaired keys) and persisted in the brief's `guard` report.

Result: **no unverified figure is ever emitted.** If the model invents
"999,999 people at risk", that section silently falls back to the true template
text. Unit tests assert both directions (a correct number passes; a fabricated one
is caught) — see `tests/test_brief_guard.py` and `tests/test_brief_generator.py`.

## 4. The no-LLM fallback (always available)

The brief works with **no LLM and no key**. When `PRAXIS_LLM_ENABLED` is false or
no key is present, `generate_brief` returns `render_template_brief(facts)` — a
complete, professional brief built from facts alone. The same template is the
per-section repair source for the guard. The whole test suite runs, and every
endpoint works, with no key (tests inject a fake completion; a real API is never
called).

The UI shows a quiet indicator: *"generated without AI narration"* on the template
path, *"narrative is AI-structured; figures validated against source"* on the LLM
path, and a *"verified template"* badge on any individual section the guard
repaired.

## 5. LLM configuration (env; key never committed)

All via `PRAXIS_`-prefixed settings (see `.env.example`, placeholders only):

| Variable | Default | Meaning |
| -------- | ------- | ------- |
| `PRAXIS_LLM_ENABLED` | `false` | Master switch for narration. |
| `PRAXIS_LLM_API_KEY` | *(empty)* | Anthropic API key. No key ⇒ template path. |
| `PRAXIS_LLM_MODEL` | `claude-sonnet-5` | Model id. |
| `PRAXIS_LLM_BASE_URL` | `https://api.anthropic.com` | Messages API base (override for a gateway). |
| `PRAXIS_LLM_API_VERSION` | `2023-06-01` | `anthropic-version` header. |
| `PRAXIS_LLM_MAX_TOKENS` | `2000` | Generation cap. |
| `PRAXIS_LLM_TIMEOUT_S` | `30` | Per-call timeout. |

**Client choice.** A thin async **httpx** wrapper on the Anthropic Messages API
(`llm.py`) — no heavyweight SDK (httpx is already a core dependency), with
`PRAXIS_LLM_BASE_URL` giving provider flexibility. One bounded call per brief
(no agentic loop), wrapped in a **tenacity** retry with a timeout; any failure
falls back to the template. Nothing runs at import time, so the app and tests work
offline with no key.

## 6. Export (HTML + PDF)

`render.py` renders one Jinja2 template to **print-ready HTML** (screen +
`@media print`) and to **PDF** via **xhtml2pdf** — a pure-Python HTML→PDF engine
that needs no native libraries, so a real downloadable PDF works locally and in
CI with zero setup. The export is light-themed (a document to print) and carries
the honesty banner, the scorecard, the robustness summary, and a
provenance/generation footer. Endpoints:
`GET …/briefs/{id}/export.html` and `…/export.pdf`.

## 7. Persistence & auditability

Each brief persists (migration `0005`, `brief` table) a **snapshot of the facts**
it was built from, the generated content, the guard report, and generation
metadata (generator, model). Because the facts snapshot is stored, a brief stays
reproducible and auditable even if the underlying data later changes. Endpoints:
`POST …/playbooks/{id}/brief`, `GET …/briefs`, `GET …/briefs/{id}`.

## Scope

Phase 6 is the Act stage only. It does not build the Learn/after-action stage, and
it does not calibrate the narration against outcomes. The trust boundary (real
facts only) and the no-key fallback are the two guarantees that must never break.
