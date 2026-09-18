import "@/lib/i18n";

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { AFTER_ACTION } from "@/features/learn/fixtures";
import { useUiStore } from "@/store/ui";

const h = vi.hoisted(() => ({
  mutate: vi.fn(),
  playbook: { id: 2, name: "Wide coverage", score_result: { overall: 82.6 } },
}));

vi.mock("@/features/decide/hooks", () => ({
  usePlaybooks: () => ({ data: [h.playbook], isLoading: false }),
}));
vi.mock("@/features/sense/hooks", () => ({
  useScenarioDetail: () => ({ data: { bbox: null } }),
}));
vi.mock("@/features/learn/hooks", () => ({
  useAfterActions: () => ({ data: [{ id: 1 }] }),
  useCreateAfterAction: () => ({
    mutate: h.mutate,
    isPending: false,
    isError: false,
    data: undefined,
  }),
}));
vi.mock("@tanstack/react-query", () => ({
  useQuery: () => ({ data: AFTER_ACTION, isLoading: false }),
}));
vi.mock("@/features/learn/AfterActionView", () => ({
  AfterActionView: ({ aa }: { aa: typeof AFTER_ACTION }) => (
    <div data-testid="aa-view">{aa.result.playbook_name}</div>
  ),
}));
vi.mock("@/lib/api", () => ({ api: { getAfterAction: vi.fn() } }));

import { LearnWorkspace } from "@/features/learn/LearnWorkspace";

beforeEach(() => {
  useUiStore.setState({ selectedScenarioSlug: "2017-sw-monsoon-kalu-ganga" });
});
afterEach(() => h.mutate.mockReset());

describe("LearnWorkspace", () => {
  it("renders the after-action for the selected playbook", () => {
    render(<LearnWorkspace />);
    expect(screen.getByTestId("aa-view")).toHaveTextContent("Wide coverage");
  });

  it("runs an after-action for the selected playbook", async () => {
    const user = userEvent.setup();
    render(<LearnWorkspace />);
    await user.click(screen.getByRole("button", { name: /after-action/i }));
    expect(h.mutate).toHaveBeenCalledTimes(1);
    const arg = h.mutate.mock.calls[0]?.[0] as { id: number; body: object } | undefined;
    expect(arg?.id).toBe(2);
  });
});
