import "@/lib/i18n";

import { act, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { OfflineBanner } from "@/components/shell/OfflineBanner";

function setOnline(value: boolean) {
  vi.spyOn(navigator, "onLine", "get").mockReturnValue(value);
  act(() => {
    window.dispatchEvent(new Event(value ? "online" : "offline"));
  });
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe("OfflineBanner", () => {
  it("is hidden while online", () => {
    setOnline(true);
    const { container } = render(<OfflineBanner />);
    expect(container).toBeEmptyDOMElement();
  });

  it("appears with an honest stale-data warning when offline", () => {
    setOnline(false);
    render(<OfflineBanner />);
    expect(screen.getByText(/showing saved data — it may not be live/i)).toBeInTheDocument();
    expect(screen.getByText(/map tiles may not load/i)).toBeInTheDocument();
  });
});
