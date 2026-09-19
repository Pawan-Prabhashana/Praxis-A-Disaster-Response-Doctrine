/**
 * Global UI state (client-only): theme, language, and sidebar collapse.
 *
 * Server/remote state lives in TanStack Query; this Zustand store holds
 * ephemeral interface state and persists the user's theme + language + layout
 * choices to localStorage so they survive reloads.
 */

import { create } from "zustand";
import { persist } from "zustand/middleware";

import i18n, { type SupportedLanguage, isSupportedLanguage } from "@/lib/i18n";

export type Theme = "dark" | "light";

interface UiState {
  theme: Theme;
  language: SupportedLanguage;
  sidebarCollapsed: boolean;
  /** Slug of the active scenario (null until one is selected/loaded). */
  selectedScenarioSlug: string | null;
  toggleTheme: () => void;
  setTheme: (theme: Theme) => void;
  setLanguage: (language: SupportedLanguage) => void;
  toggleSidebar: () => void;
  setSelectedScenario: (slug: string | null) => void;
}

export const useUiStore = create<UiState>()(
  persist(
    (set) => ({
      theme: "dark",
      language: "en",
      sidebarCollapsed: false,
      selectedScenarioSlug: null,
      toggleTheme: () => set((s) => ({ theme: s.theme === "dark" ? "light" : "dark" })),
      setTheme: (theme) => set({ theme }),
      setLanguage: (language) => {
        applyLanguage(language);
        set({ language });
      },
      toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
      setSelectedScenario: (slug) => set({ selectedScenarioSlug: slug }),
    }),
    {
      name: "praxis-ui",
      partialize: (state) => ({
        theme: state.theme,
        language: state.language,
        sidebarCollapsed: state.sidebarCollapsed,
        selectedScenarioSlug: state.selectedScenarioSlug,
      }),
      // Re-apply the persisted language to i18next + <html> once rehydrated.
      onRehydrateStorage: () => (state) => {
        if (state) applyLanguage(state.language);
      },
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

/** Sync i18next and the document `lang` attribute to the chosen language. */
export function applyLanguage(language: string): void {
  const lang = isSupportedLanguage(language) ? language : "en";
  void i18n.changeLanguage(lang);
  document.documentElement.setAttribute("lang", lang);
}
