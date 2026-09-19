import { describe, expect, it, vi } from "vitest";

// The virtual module is provided by vite-plugin-pwa; stub it so the test never
// depends on a real service-worker build.
vi.mock("virtual:pwa-register", () => ({ registerSW: () => () => {} }));

import { registerServiceWorker } from "@/lib/pwa";

describe("registerServiceWorker", () => {
  it("does not throw where service workers are unsupported (jsdom)", () => {
    // jsdom's navigator has no `serviceWorker`, so registration is skipped.
    expect(() => registerServiceWorker()).not.toThrow();
  });
});
