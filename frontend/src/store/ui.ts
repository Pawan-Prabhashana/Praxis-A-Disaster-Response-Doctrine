/**
 * Global UI state (client-only): theme and sidebar collapse.
 *
 * Server/remote state lives in TanStack Query; this Zustand store holds
 * ephemeral interface state and persists the user's theme + layout choices to
 * localStorage so they survive reloads.
 */

import { create } from "zustand";
import { persist } from "zustand/middleware";

export type Theme = "dark" | "light";

interface UiState {
  theme: Theme;
  sidebarCollapsed: boolean;
  /** Slug of the active scenario (null until one is selected/loaded). */
  selectedScenarioSlug: string | null;
  toggleTheme: () => void;
  setTheme: (theme: Theme) => void;
  toggleSidebar: () => void;
  setSelectedScenario: (slug: string | null) => void;
}

export const useUiStore = create<UiState>()(
  persist(
    (set) => ({
      theme: "dark",
      sidebarCollapsed: false,
      selectedScenarioSlug: null,
      toggleTheme: () => set((s) => ({ theme: s.theme === "dark" ? "light" : "dark" })),
      setTheme: (theme) => set({ theme }),
      toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
      setSelectedScenario: (slug) => set({ selectedScenarioSlug: slug }),
    }),
    {
      name: "praxis-ui",
      partialize: (state) => ({
        theme: state.theme,
        sidebarCollapsed: state.sidebarCollapsed,
        selectedScenarioSlug: state.selectedScenarioSlug,
      }),
    },
  ),
);

/**
 * Apply the current theme to the document root. Called from a React effect so
 * the DOM stays in sync with the store (and initial paint respects the
 * persisted choice).
 */
export function applyTheme(theme: Theme): void {
  const root = document.documentElement;
  root.setAttribute("data-theme", theme);
}
