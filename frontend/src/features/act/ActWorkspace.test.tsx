import "@/lib/i18n";

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { TEMPLATE_BRIEF } from "@/features/act/fixtures";
import { useUiStore } from "@/store/ui";

const h = vi.hoisted(() => ({
  mutate: vi.fn(),
  playbook: {
    id: 2,
    name: "Wide coverage",
    score_result: { overall: 63.5 },
  },
  run: { id: 5, seed: 2024, n_iterations: 500, created_at: "2026-09-18T09:00:00Z" },
}));

vi.mock("@/features/decide/hooks", () => ({
  usePlaybooks: () => ({ data: [h.playbook], isLoading: false }),
  useStressRuns: () => ({ data: [h.run] }),
}));

vi.mock("@/features/act/hooks", () => ({
  useBriefs: () => ({ data: [{ id: 1 }] }),
  useCreateBrief: () => ({ mutate: h.mutate, isPending: false, isError: false, data: undefined }),
}));

vi.mock("@tanstack/react-query", () => ({
  useQuery: () => ({ data: TEMPLATE_BRIEF, isLoading: false }),
}));

vi.mock("@/lib/api", () => ({
  api: {
    briefExportUrl: (slug: string, id: number, briefId: number, fmt: string) =>
      `http://api.test/scenarios/${slug}/playbooks/${id}/briefs/${briefId}/export.${fmt}`,
    getBrief: vi.fn(),
  },
}));

import { ActWorkspace } from "@/features/act/ActWorkspace";

beforeEach(() => {
  useUiStore.setState({ selectedScenarioSlug: "2017-sw-monsoon-kalu-ganga" });
});

afterEach(() => {
  h.mutate.mockReset();
});

describe("ActWorkspace", () => {
  it("wires export buttons to the server-rendered HTML and PDF endpoints", () => {
    render(<ActWorkspace />);
    const html = screen.getByRole("link", { name: /HTML/i });
    const pdf = screen.getByRole("link", { name: /Download PDF/i });
    expect(html).toHaveAttribute("href", expect.stringContaining("/export.html"));
    expect(pdf).toHaveAttribute("href", expect.stringContaining("/export.pdf"));
  });

  it("generates a brief for the selected playbook with the attached stress run", async () => {
    const user = userEvent.setup();
    render(<ActWorkspace />);
    await user.click(screen.getByRole("button", { name: /regenerate|generate brief/i }));
    expect(h.mutate).toHaveBeenCalledTimes(1);
    const arg = h.mutate.mock.calls[0]?.[0] as
      | { id: number; body: { stress_run_id: number | null } }
      | undefined;
    expect(arg?.id).toBe(2);
    expect(arg?.body.stress_run_id).toBe(5);
  });
});
