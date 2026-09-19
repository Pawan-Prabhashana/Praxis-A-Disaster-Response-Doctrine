import "@fontsource-variable/inter";
import "@fontsource-variable/jetbrains-mono";
// Self-hosted Sinhala + Tamil glyphs (Inter lacks them) — bundled for offline use.
import "@fontsource/noto-sans-sinhala/400.css";
import "@fontsource/noto-sans-sinhala/500.css";
import "@fontsource/noto-sans-sinhala/600.css";
import "@fontsource/noto-sans-sinhala/700.css";
import "@fontsource/noto-sans-tamil/400.css";
import "@fontsource/noto-sans-tamil/500.css";
import "@fontsource/noto-sans-tamil/600.css";
import "@fontsource/noto-sans-tamil/700.css";
import "@/styles/globals.css";

import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { App } from "@/app/App";
import { registerServiceWorker } from "@/lib/pwa";
import { applyLanguage, applyTheme, useUiStore } from "@/store/ui";

// Apply the persisted theme + language before first paint to avoid a flash.
applyTheme(useUiStore.getState().theme);
applyLanguage(useUiStore.getState().language);

// Register the offline service worker (no-op in dev / unsupported browsers).
registerServiceWorker();

const container = document.getElementById("root");
if (!container) {
  throw new Error("Root element #root not found");
}

createRoot(container).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
