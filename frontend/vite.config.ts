import path from "node:path";
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [
    react(),
    // Installable, offline-capable app shell. The service worker is built only
    // for production (devOptions.enabled = false), so the dev server and the
    // jsdom test runner never register it.
    VitePWA({
      registerType: "autoUpdate",
      includeAssets: ["favicon.svg"],
      manifest: {
        name: "Praxis — Disaster Response Command",
        short_name: "Praxis",
        description:
          "A disaster response doctrine and command platform for Sri Lanka: Sense, Decide, Act, Learn.",
        theme_color: "#0f1620",
        background_color: "#0f1620",
        display: "standalone",
        start_url: "/",
        icons: [
          { src: "favicon.svg", sizes: "any", type: "image/svg+xml", purpose: "any maskable" },
        ],
      },
      workbox: {
        // Precache the app shell, code, styles, and self-hosted fonts (incl. the
        // Sinhala/Tamil Noto woff2) so the whole UI loads with no network.
        globPatterns: ["**/*.{js,css,html,svg,woff,woff2,ico}"],
        maximumFileSizeToCacheInBytes: 4 * 1024 * 1024, // allow the map-vendor chunk
        navigateFallback: "index.html",
        runtimeCaching: [
          {
            // API GETs: serve fresh when online, fall back to cache when offline.
            // Never silently stale — the UI shows an offline/stale indicator.
            urlPattern: ({ url }) => url.pathname.startsWith("/api/"),
            handler: "NetworkFirst",
            options: {
              cacheName: "praxis-api",
              networkTimeoutSeconds: 5,
              expiration: { maxEntries: 80, maxAgeSeconds: 60 * 60 * 24 },
              cacheableResponse: { statuses: [0, 200] },
            },
          },
          {
            // CARTO basemap tiles/styles — best-effort only. Third-party tiles
            // are not guaranteed cacheable offline (documented limitation).
            urlPattern: ({ url }) => url.hostname.endsWith("basemaps.cartocdn.com"),
            handler: "CacheFirst",
            options: {
              cacheName: "praxis-basemap",
              expiration: { maxEntries: 300, maxAgeSeconds: 60 * 60 * 24 * 7 },
              cacheableResponse: { statuses: [0, 200] },
            },
          },
        ],
      },
    }),
  ],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 5173,
    strictPort: true,
  },
  build: {
    rollupOptions: {
      output: {
        // Split large, stable vendor libraries into their own chunks for
        // better browser caching and to keep the app chunk lean.
        manualChunks: {
          "react-vendor": ["react", "react-dom", "react-router-dom"],
          "data-vendor": ["@tanstack/react-query", "zustand", "i18next", "react-i18next"],
          "motion-vendor": ["framer-motion"],
          "map-vendor": ["maplibre-gl"],
          "chart-vendor": ["recharts"],
        },
      },
    },
  },
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
    css: true,
  },
});
