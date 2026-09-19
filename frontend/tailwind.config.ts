import type { Config } from "tailwindcss";
import animate from "tailwindcss-animate";

/**
 * Praxis design system — Tailwind bridge.
 *
 * Colors are declared as HSL channel triplets in `src/styles/globals.css`
 * (e.g. `--background: 210 24% 7%`) and consumed here via `hsl(var(--token))`.
 * This keeps ONE source of truth for tokens and lets the same class names
 * resolve to the dark (default) or light palette without touching markup.
 */
const config: Config = {
  darkMode: ["class", '[data-theme="dark"]'],
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: { "2xl": "1440px" },
    },
    extend: {
      colors: {
        background: "hsl(var(--background) / <alpha-value>)",
        foreground: "hsl(var(--foreground) / <alpha-value>)",
        surface: {
          DEFAULT: "hsl(var(--surface) / <alpha-value>)",
          raised: "hsl(var(--surface-raised) / <alpha-value>)",
          foreground: "hsl(var(--surface-foreground) / <alpha-value>)",
        },
        card: {
          DEFAULT: "hsl(var(--card) / <alpha-value>)",
          foreground: "hsl(var(--card-foreground) / <alpha-value>)",
        },
        popover: {
          DEFAULT: "hsl(var(--popover) / <alpha-value>)",
          foreground: "hsl(var(--popover-foreground) / <alpha-value>)",
        },
        primary: {
          DEFAULT: "hsl(var(--primary) / <alpha-value>)",
          foreground: "hsl(var(--primary-foreground) / <alpha-value>)",
        },
        muted: {
          DEFAULT: "hsl(var(--muted) / <alpha-value>)",
          foreground: "hsl(var(--muted-foreground) / <alpha-value>)",
        },
        accent: {
          DEFAULT: "hsl(var(--accent) / <alpha-value>)",
          foreground: "hsl(var(--accent-foreground) / <alpha-value>)",
        },
        border: "hsl(var(--border) / <alpha-value>)",
        input: "hsl(var(--input) / <alpha-value>)",
        ring: "hsl(var(--ring) / <alpha-value>)",
        // Operational status signals — distinct from the amber brand accent.
        signal: {
          ok: "hsl(var(--signal-ok) / <alpha-value>)",
          "ok-foreground": "hsl(var(--signal-ok-foreground) / <alpha-value>)",
          warn: "hsl(var(--signal-warn) / <alpha-value>)",
          "warn-foreground": "hsl(var(--signal-warn-foreground) / <alpha-value>)",
          crit: "hsl(var(--signal-crit) / <alpha-value>)",
          "crit-foreground": "hsl(var(--signal-crit-foreground) / <alpha-value>)",
          info: "hsl(var(--signal-info) / <alpha-value>)",
          "info-foreground": "hsl(var(--signal-info-foreground) / <alpha-value>)",
        },
      },
      fontFamily: {
        // Inter for Latin; self-hosted Noto Sans Sinhala/Tamil provide the
        // glyphs Inter lacks so si/ta render cleanly (see main.tsx imports).
        sans: [
          "Inter Variable",
          "Inter",
          "Noto Sans Sinhala",
          "Noto Sans Tamil",
          "system-ui",
          "sans-serif",
        ],
        mono: ["JetBrains Mono Variable", "JetBrains Mono", "ui-monospace", "monospace"],
      },
      fontSize: {
        // A compact, dense type scale suited to an operations console.
        "2xs": ["0.6875rem", { lineHeight: "1rem", letterSpacing: "0.02em" }],
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      boxShadow: {
        // Elevation scale — layered, low-glare for dark surfaces.
        e1: "0 1px 2px 0 hsl(0 0% 0% / 0.25)",
        e2: "0 2px 8px -2px hsl(0 0% 0% / 0.35)",
        e3: "0 8px 24px -6px hsl(0 0% 0% / 0.45)",
        glow: "0 0 0 1px hsl(var(--primary) / 0.35), 0 0 20px -4px hsl(var(--primary) / 0.45)",
      },
      keyframes: {
        "fade-in": {
          from: { opacity: "0", transform: "translateY(4px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        "pulse-signal": {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.35" },
        },
      },
      animation: {
        "fade-in": "fade-in 0.4s cubic-bezier(0.22, 1, 0.36, 1)",
        "pulse-signal": "pulse-signal 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
      },
    },
  },
  plugins: [animate],
};

export default config;
