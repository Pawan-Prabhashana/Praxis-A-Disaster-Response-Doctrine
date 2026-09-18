import "@/lib/i18n";

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { BriefDocument } from "@/features/act/BriefDocument";
import { TEMPLATE_BRIEF } from "@/features/act/fixtures";
import type { Brief } from "@/lib/api";

describe("BriefDocument", () => {
  it("renders the headline, sections, and the deterministic scorecard", () => {
    render(<BriefDocument brief={TEMPLATE_BRIEF} />);
    expect(screen.getByText("Operational brief — Wide coverage")).toBeInTheDocument();
    expect(screen.getByText("Situation overview")).toBeInTheDocument();
    expect(screen.getByText("Expected performance")).toBeInTheDocument();
    // Overall score from the scorecard table.
    expect(screen.getByText("63.5")).toBeInTheDocument();
  });

  it("preserves honesty flags: synthetic warning and provenance badges", () => {
    render(<BriefDocument brief={TEMPLATE_BRIEF} />);
    // Synthetic influence -> warning banner.
    expect(screen.getByText(/synthetic sample data/i)).toBeInTheDocument();
    // The synthetic metric carries a "sample" provenance badge.
    expect(screen.getByText("sample")).toBeInTheDocument();
    expect(screen.getByText("real")).toBeInTheDocument();
  });

  it("shows the no-AI indicator for a template-generated brief", () => {
    render(<BriefDocument brief={TEMPLATE_BRIEF} />);
    expect(screen.getByText(/without AI narration/i)).toBeInTheDocument();
    // No "verified template" badges when the whole brief is template-generated.
    expect(screen.queryByText(/verified template/i)).not.toBeInTheDocument();
  });

  it("renders robustness with the epistemic framing when a stress run is attached", () => {
    render(<BriefDocument brief={TEMPLATE_BRIEF} />);
    expect(screen.getByText(/Robustness under modeled uncertainty/i)).toBeInTheDocument();
    expect(screen.getByText(/worst-plausible 48\.0/i)).toBeInTheDocument();
    expect(screen.getByText(/Modeled \(epistemic\) uncertainty/i)).toBeInTheDocument();
  });

  it("flags AI-narrated sections that were repaired from the template", () => {
    const llmBrief: Brief = {
      ...TEMPLATE_BRIEF,
      generator: "llm",
      content: {
        ...TEMPLATE_BRIEF.content,
        generator: "llm",
        // Only the performance section was repaired from the template.
        sections: TEMPLATE_BRIEF.content.sections.map((s) => ({
          ...s,
          from_template: s.key === "performance",
        })),
      },
      guard: { ok: false, sections: [], repaired_sections: ["performance"] },
    };
    render(<BriefDocument brief={llmBrief} />);
    expect(screen.getByText(/narrative is AI-structured/i)).toBeInTheDocument();
    // Exactly the repaired (from_template) section is badged.
    expect(screen.getAllByText(/verified template/i)).toHaveLength(1);
  });
});
