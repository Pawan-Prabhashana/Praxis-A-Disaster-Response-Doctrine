import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { AppProviders } from "@/app/providers";
import { AppShell } from "@/components/shell/AppShell";

// Keep the shell test deterministic and offline: stub the API client so the
// system-status indicator does not perform real network requests.
vi.mock("@/lib/api", () => ({
  api: {
    health: vi.fn().mockResolvedValue({
      status: "ok",
      db: "ok",
      version: "0.1.0",
      environment: "test",
    }),
    meta: vi.fn(),
  },
  ApiError: class ApiError extends Error {},
}));

function renderShell() {
  return render(
    <AppProviders>
      <MemoryRouter initialEntries={["/"]}>
        <Routes>
          <Route path="/" element={<AppShell />}>
            <Route index element={<div data-testid="workspace" />} />
          </Route>
        </Routes>
      </MemoryRouter>
    </AppProviders>,
  );
}

describe("AppShell", () => {
  it("renders navigation links for all four response-loop stages", () => {
    renderShell();

    for (const stage of ["Sense", "Decide", "Act", "Learn"]) {
      expect(screen.getByRole("link", { name: new RegExp(stage, "i") })).toBeInTheDocument();
    }
  });

  it("renders the product wordmark and the routed workspace", () => {
    renderShell();

    expect(screen.getByText("Praxis")).toBeInTheDocument();
    expect(screen.getByTestId("workspace")).toBeInTheDocument();
  });
});
