import "@/lib/i18n";

import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { StressResult, UncertaintyConfig } from "@/lib/api";

const CONFIG: UncertaintyConfig = {
  version: 1,
  target_score: 60,
  params: [
    {
      key: "displacement_rate",
      label: "Displacement rate",
      param_class: "assumption",
      distribution: { kind: "triangular", low: 0.08, high: 0.3, mode: 0.15 },
      basis: "Planning assumption.",
      enabled: true,
    },
    {
      key: "closure_realization",
      label: "Road-closure severity",
      param_class: "synthetic_derived",
      distribution: { kind: "triangular", low: 0.5, high: 1.5, mode: 1.0 },
      basis: "Synthetic sample data.",
      enabled: true,
    },
  ],
};

const h = vi.hoisted(() => ({
  mutate: vi.fn(),
  state: {
    data: undefined as { result: StressResult } | undefined,
    isPending: false,
    isError: false,
  },
}));

vi.mock("@/features/decide/hooks", () => ({
  useUncertaintyDefaults: () => ({ data: CONFIG }),
  useStressRuns: () => ({ data: [] }),
  useStressTest: () => ({ mutate: h.mutate, ...h.state }),
}));

vi.mock("@/features/decide/stress/StressHistogram", () => ({
  StressHistogram: () => <div data-testid="histogram" />,
}));

import { StressPanel } from "@/features/decide/stress/StressPanel";

afterEach(() => {
  h.mutate.mockReset();
  h.state.data = undefined;
});

describe("StressPanel", () => {
  it("renders each parameter with its honesty class badge", () => {
    render(<StressPanel slug="s" playbookId={7} />);
    const closure = screen.getByRole("checkbox", { name: "Road-closure severity" }).closest("li");
    expect(closure).not.toBeNull();
    expect(within(closure as HTMLElement).getByText("sample-derived")).toBeInTheDocument();
    const disp = screen.getByRole("checkbox", { name: "Displacement rate" }).closest("li");
    expect(within(disp as HTMLElement).getByText("assumption")).toBeInTheDocument();
  });

  it("shapes the stress request with toggled params and iteration count", async () => {
    const user = userEvent.setup();
    render(<StressPanel slug="s" playbookId={7} />);
    await user.click(screen.getByRole("checkbox", { name: "Road-closure severity" }));
    await user.click(screen.getByRole("button", { name: /run stress test/i }));

    expect(h.mutate).toHaveBeenCalledTimes(1);
    const arg = h.mutate.mock.calls[0]?.[0] as
      | { id: number; body: { n_iterations: number; config: UncertaintyConfig } }
      | undefined;
    expect(arg?.id).toBe(7);
    expect(arg?.body.n_iterations).toBe(500);
    const closure = arg?.body.config.params.find((p) => p.key === "closure_realization");
    expect(closure?.enabled).toBe(false);
  });

  it("prompts to save when the playbook is unsaved", () => {
    render(<StressPanel slug="s" playbookId={null} />);
    expect(screen.getByText(/save this playbook first/i)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /run stress test/i })).not.toBeInTheDocument();
  });

  it("renders the robustness band and worst-plausible when a result exists", () => {
    h.state.data = {
      result: {
        version: 1,
        seed: 1,
        n_iterations: 500,
        point_overall: 70,
        overall: {
          mean: 65,
          median: 66,
          std: 6,
          p05: 55,
          p25: 61,
          p75: 71,
          p95: 74,
          min: 48,
          max: 80,
          histogram: [],
        },
        metrics: {},
        robustness: {
          worst_plausible: 55,
          probability_meets_target: 0.8,
          target_score: 60,
          median: 66,
        },
        config: CONFIG,
        uses_synthetic_data: true,
        epistemic_note: "epistemic",
      },
    };
    render(<StressPanel slug="s" playbookId={7} />);
    expect(screen.getByText(/55.*74/)).toBeInTheDocument(); // 90% band statement
    expect(screen.getAllByText(/worst-plausible/i).length).toBeGreaterThan(0);
    expect(screen.getByTestId("histogram")).toBeInTheDocument();
    // point (70) is 4 pts above median (66) → optimistic reversal note
    expect(screen.getByText(/optimistic/i)).toBeInTheDocument();
  });
});
