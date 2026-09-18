"""Server-side rendering of a brief to print-ready HTML and to PDF.

One Jinja2 template drives both: the browser download (screen + ``@media
print``) and the PDF (via xhtml2pdf, a pure-Python HTML->PDF engine needing no
native libraries). The export is intentionally light-themed — a document meant
to be printed and handed to field teams — and carries an honesty banner, the
scorecard, the robustness summary, and a provenance/generation footer.
"""

from __future__ import annotations

import io
from datetime import UTC, datetime
from typing import Any

from jinja2 import Environment, select_autoescape
from xhtml2pdf import pisa

from app.services.brief.content import BriefContent
from app.services.brief.facts import BriefFacts

_PROVENANCE_LABEL = {"real": "Real data", "synthetic": "Sample data", "assumption": "Assumption"}
_PROVENANCE_COLOR = {"real": "#1a7f5a", "synthetic": "#b45309", "assumption": "#1d4ed8"}

_env = Environment(autoescape=select_autoescape(["html", "xml"]))
_env.filters["comma"] = lambda v: f"{round(float(v)):,}"
_env.filters["score"] = lambda v: f"{float(v):.1f}"

_TEMPLATE = _env.from_string(
    """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<title>{{ content.headline }}</title>
<style>
  @page { size: A4; margin: 1.6cm; }
  body { font-family: Helvetica, Arial, sans-serif; color: #1a2027; font-size: 11pt;
         line-height: 1.5; background: #ffffff; }
  h1 { font-size: 19pt; margin: 0 0 2px; color: #0f172a; }
  h2 { font-size: 13pt; margin: 18px 0 6px; color: #0f172a;
       border-bottom: 1px solid #d5dbe2; padding-bottom: 3px; }
  .meta { color: #5b6570; font-size: 9pt; margin-bottom: 12px; }
  .banner { background: #eef4ff; border: 1px solid #c7d9ff; color: #24406e;
            padding: 8px 10px; font-size: 9pt; margin-bottom: 14px; }
  p { margin: 0 0 8px; }
  table { width: 100%; border-collapse: collapse; margin: 6px 0 4px; }
  th, td { text-align: left; padding: 5px 7px; font-size: 10pt;
           border-bottom: 1px solid #e3e8ee; }
  th { color: #5b6570; font-weight: bold; }
  .num { text-align: right; }
  .tag { font-size: 8pt; font-weight: bold; padding: 1px 6px; color: #ffffff; }
  .fromtpl { color: #8a939c; font-size: 8pt; }
  .foot { margin-top: 18px; border-top: 1px solid #d5dbe2; padding-top: 8px;
          color: #5b6570; font-size: 8.5pt; }
  .kv { margin: 2px 0; }
</style>
</head>
<body>
  <h1>{{ content.headline }}</h1>
  <div class="meta">
    {{ facts.scenario.name }} &middot; {{ facts.scenario.hazard_type }}
    {% if facts.scenario.event_date %}&middot; {{ facts.scenario.event_date }}{% endif %}
    &middot; Prepared {{ generated_at }}
  </div>

  <div class="banner">
    Figures are computed by Praxis from real ingested data and validated against source;
    narrative structure is {{ narrative_note }}.
    {% if facts.uses_synthetic_data %}This brief includes metrics influenced by synthetic
    sample data (flagged below).{% endif %}
  </div>

  {% for section in content.sections %}
  <h2>{{ section.title }}{% if section.from_template and generator == "llm" %}
    <span class="fromtpl">(verified template)</span>{% endif %}</h2>
    {% for para in section.paragraphs %}<p>{{ para }}</p>{% endfor %}

    {% if section.key == "performance" %}
    <table>
      <tr><th>Metric</th><th class="num">Score</th><th class="num">Weight</th><th>Basis</th></tr>
      {% for m in facts.scorecard.metrics %}
      <tr>
        <td>{{ m.label }}</td>
        <td class="num">{{ m.score | score }}</td>
        <td class="num">{{ m.weight_pct }}%</td>
        <td><span class="tag" style="background: {{ prov_color[m.provenance] }};">
          {{ prov_label[m.provenance] }}</span></td>
      </tr>
      {% endfor %}
      <tr><td><strong>Overall</strong></td>
          <td class="num"><strong>{{ facts.scorecard.overall | score }}</strong></td>
          <td class="num"></td><td></td></tr>
    </table>
    {% if facts.robustness %}
    <div class="kv"><strong>Under modeled uncertainty</strong>
      ({{ facts.robustness.n_iterations | comma }} iterations, seed {{ facts.robustness.seed }}):
      median {{ facts.robustness.median | score }}, 90% band
      {{ facts.robustness.p05 | score }}&ndash;{{ facts.robustness.p95 | score }},
      worst-plausible {{ facts.robustness.worst_plausible | score }},
      meets target {{ facts.robustness.target_score }} in
      {{ facts.robustness.probability_meets_target_pct }}% of conditions.</div>
    {% endif %}
    {% endif %}
  {% endfor %}

  <div class="foot">
    <div class="kv">Provenance: {{ facts.assumptions | join(" ") }}</div>
    {% if facts.synthetic_influences %}
    <div class="kv">Synthetic influences: {{ facts.synthetic_influences | join(" ") }}</div>
    {% endif %}
    <div class="kv">Generated {{ generated_at }}
      {%- if model %} &middot; model {{ model }}{% endif %}
      &middot; narrative: {{ generator }}
      {%- if guard_repaired %} &middot; {{ guard_repaired }} section(s) verified from template
      {%- endif %}.</div>
  </div>
</body>
</html>"""
)


def _context(facts: BriefFacts, content: BriefContent, meta: dict[str, Any]) -> dict[str, Any]:
    return {
        "facts": facts,
        "content": content,
        "generated_at": meta.get("generated_at")
        or datetime.now(tz=UTC).strftime("%Y-%m-%d %H:%M UTC"),
        "generator": content.generator,
        "narrative_note": (
            "AI-assisted" if content.generator == "llm" else "generated without AI narration"
        ),
        "model": meta.get("model"),
        "guard_repaired": meta.get("guard_repaired", 0),
        "prov_label": _PROVENANCE_LABEL,
        "prov_color": _PROVENANCE_COLOR,
    }


def render_html(facts: BriefFacts, content: BriefContent, meta: dict[str, Any]) -> str:
    """Render the brief to a standalone, print-ready HTML document."""
    return _TEMPLATE.render(**_context(facts, content, meta))


def render_pdf(facts: BriefFacts, content: BriefContent, meta: dict[str, Any]) -> bytes:
    """Render the brief to PDF bytes (via xhtml2pdf; no native deps)."""
    html = render_html(facts, content, meta)
    buffer = io.BytesIO()
    result = pisa.CreatePDF(src=html, dest=buffer, encoding="utf-8")
    if result.err:
        raise RuntimeError("PDF rendering failed")
    return buffer.getvalue()
