import "@/lib/i18n";

import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { AFTER_ACTION } from "@/features/learn/fixtures";

// The map (MapLibre) and the scatter (Recharts) don't render in jsdom — stub them.
vi.mock("@/features/learn/LearnMap", () => ({ LearnMap: () => <div data-testid="learn-map" /> }));
vi.mock("@/features/learn/RankScatter", () => ({
  RankScatter: () => <div data-testid="rank-scatter" />,
}));

import { AfterActionView } from "@/features/learn/AfterActionView";

describe("AfterActionView", () => {
  it("shows the mandatory predicted-vs-recorded framing", () => {
    render(<AfterActionView aa={AFTER_ACTION} bbox={null} />);
    expect(screen.getByText(/predicted vs\. recorded/i)).toBeInTheDocument();
    expect(screen.getAllByText(/not the outcome of executing the plan/i).length).toBeGreaterThan(0);
  });

  it("surfaces the inverted alignment with its label", () => {
    render(<AfterActionView aa={AFTER_ACTION} bbox={null} />);
    expect(screen.getByText("Prediction alignment")).toBeInTheDocument();
    expect(screen.getAllByText(/inverted/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/-0\.5/).length).toBeGreaterThan(0);
  });

  it("renders recorded impact with real numbers and honesty flags", () => {
    render(<AfterActionView aa={AFTER_ACTION} bbox={null} />);
    // The recorded table is labelled as the real historical baseline.
    expect(screen.getByText(/historical response baseline/i)).toBeInTheDocument();
    expect(screen.getByText("real data")).toBeInTheDocument();
    // Ratnapura's real deaths appear.
    expect(screen.getByText("84")).toBeInTheDocument();
    // The no-data district is stated, never a fabricated value.
    expect(screen.getByText(/no recorded data/i)).toBeInTheDocument();
    // Provenance footer distinguishes real recorded vs synthetic predicted inputs.
    expect(screen.getByText(/Recorded impact is real DesInventar data/i)).toBeInTheDocument();
  });

  it("renders the structured lessons with severities", () => {
    render(<AfterActionView aa={AFTER_ACTION} bbox={null} />);
    expect(screen.getByText("Ratnapura was under-prioritised")).toBeInTheDocument();
    expect(screen.getByText("For next time")).toBeInTheDocument();
    expect(screen.getAllByText("crit").length).toBeGreaterThan(0);
  });
});
