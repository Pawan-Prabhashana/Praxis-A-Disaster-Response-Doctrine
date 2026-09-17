import "@/lib/i18n";

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Scorecard } from "@/features/decide/scorecard/Scorecard";
import type { ScoreResult } from "@/lib/api";

const RESULT: ScoreResult = {
  version: 1,
  overall: 63.5,
  metrics: [
    {
      key: "population_coverage",
      score: 0.7,
      weight: 0.35,
      provenance: "real",
      raw: { covered_at_risk: 700000, total_at_risk: 1000000 },
      notes: [],
    },
    {
      key: "accessibility",
      score: 0.25,
      weight: 0.15,
      provenance: "synthetic",
      raw: { reachable_activated: 10, activated_shelters: 40 },
      notes: ["Uses synthetic road-closure data; treat as indicative only."],
    },
    {
      key: "resource_adequacy",
      score: 0.5,
      weight: 0.2,
      provenance: "assumption",
      raw: { response_capacity: 50000 },
      notes: [],
    },
  ],
  coverage_gaps: [{ pcode: "LK31", name: "Galle", at_risk_population: 108294 }],
  totals: { total_at_risk: 1000000, covered_at_risk: 700000 },
  uses_synthetic_data: true,
  assumptions_used: ["Displacement rate: 15% of at-risk population needs shelter."],
};

describe("Scorecard", () => {
  it("renders the overall score and each metric with its provenance flag", () => {
    render(<Scorecard result={RESULT} />);

    expect(screen.getByText("63.5")).toBeInTheDocument();
    // provenance badges: real / sample (synthetic) / assumption
    expect(screen.getByText("real")).toBeInTheDocument();
    expect(screen.getByText("sample")).toBeInTheDocument();
    expect(screen.getByText("assumption")).toBeInTheDocument();
  });

  it("surfaces raw numbers and coverage gaps for transparency", () => {
    render(<Scorecard result={RESULT} />);
    // a raw input value is shown (transparency)
    expect(screen.getByText("700,000")).toBeInTheDocument();
    // coverage gap region surfaced
    expect(screen.getByText("Galle")).toBeInTheDocument();
  });

  it("warns when the scorecard relies on synthetic data", () => {
    render(<Scorecard result={RESULT} />);
    expect(screen.getByText(/synthetic or assumed inputs/i)).toBeInTheDocument();
  });
});
