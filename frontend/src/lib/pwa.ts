/**
 * Service-worker registration for offline support.
 *
 * `virtual:pwa-register` is provided by vite-plugin-pwa. In development and in
 * the jsdom test runner the plugin ships a no-op, and we additionally guard on
 * `serviceWorker` support, so this never throws where a worker cannot run.
 */

import { registerSW } from "virtual:pwa-register";

export function registerServiceWorker(): void {
  if (typeof navigator === "undefined" || !("serviceWorker" in navigator)) return;
  try {
    // autoUpdate: the new worker takes over on the next navigation.
    registerSW({ immediate: true });
  } catch {
    // A failed registration must never break the app.
  }
}
