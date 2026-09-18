"""Unit tests for server-side brief rendering (HTML + PDF)."""

from __future__ import annotations

from app.services.brief.render import render_html, render_pdf
from app.services.brief.template import render_template_brief
from tests.brief_fixtures import make_facts


def test_html_render_includes_key_facts_and_banner() -> None:
    facts = make_facts()
    content = render_template_brief(facts)
    html = render_html(facts, content, {})
    assert "<html" in html.lower()
    assert facts.strategy.name in html
    # Honesty banner and provenance survive into the document.
    assert "validated against source" in html
    assert "Sample data" in html  # synthetic accessibility badge label


def test_pdf_render_produces_a_real_pdf() -> None:
    facts = make_facts()
    content = render_template_brief(facts)
    pdf = render_pdf(facts, content, {})
    assert pdf[:5] == b"%PDF-"
    assert len(pdf) > 1000
