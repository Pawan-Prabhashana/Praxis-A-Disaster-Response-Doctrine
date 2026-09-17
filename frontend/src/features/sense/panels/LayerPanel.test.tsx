import "@/lib/i18n";

import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { DEFAULT_VISIBILITY } from "@/features/sense/layers";
import { LayerPanel } from "@/features/sense/panels/LayerPanel";
import type { SourceInfo } from "@/lib/api";

const SOURCES: SourceInfo[] = [
  { key: "hdx-cod-ab-lka", name: "COD-AB admin boundaries", license: "CC BY", is_synthetic: false },
  { key: "synthetic-landslide", name: "Synthetic landslide", license: null, is_synthetic: true },
];

function renderPanel(overrides: Partial<Parameters<typeof LayerPanel>[0]> = {}) {
  const onToggle = vi.fn();
  const onAdminLevel = vi.fn();
  render(
    <LayerPanel
      visibility={{ ...DEFAULT_VISIBILITY }}
      counts={{ roads: 5398, incidents: 3341, landslide: 3 }}
      onToggle={onToggle}
      adminLevel={2}
      onAdminLevel={onAdminLevel}
      sources={SOURCES}
      {...overrides}
    />,
  );
  return { onToggle, onAdminLevel };
}

describe("LayerPanel", () => {
  it("marks the synthetic landslide layer with a 'sample' tag and roads as partial sample", () => {
    renderPanel();
    const landslide = screen.getByRole("switch", { name: /landslide susceptibility/i });
    expect(within(landslide).getByText(/^sample$/i)).toBeInTheDocument();

    const roads = screen.getByRole("switch", { name: /road network/i });
    expect(within(roads).getByText(/partial sample/i)).toBeInTheDocument();
  });

  it("does not tag a real layer as sample", () => {
    renderPanel();
    const incidents = screen.getByRole("switch", { name: /historical incidents/i });
    expect(within(incidents).queryByText(/sample/i)).not.toBeInTheDocument();
  });

  it("calls onToggle with the layer key when a layer is clicked", async () => {
    const user = userEvent.setup();
    const { onToggle } = renderPanel();
    await user.click(screen.getByRole("switch", { name: /road network/i }));
    expect(onToggle).toHaveBeenCalledWith("roads");
  });

  it("shows live feature counts", () => {
    renderPanel();
    expect(screen.getByText("5,398")).toBeInTheDocument();
    expect(screen.getByText("3,341")).toBeInTheDocument();
  });
});
