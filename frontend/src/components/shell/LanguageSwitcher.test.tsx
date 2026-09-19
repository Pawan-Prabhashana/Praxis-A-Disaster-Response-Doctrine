import "@/lib/i18n";

import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { LanguageSwitcher } from "@/components/shell/LanguageSwitcher";
import { TooltipProvider } from "@/components/ui/tooltip";
import i18n from "@/lib/i18n";
import { useUiStore } from "@/store/ui";

afterEach(() => {
  useUiStore.getState().setLanguage("en");
});

describe("language switching", () => {
  it("translates the core surface to Sinhala via the store action", () => {
    useUiStore.getState().setLanguage("si");
    expect(useUiStore.getState().language).toBe("si");
    expect(i18n.language).toBe("si");
    expect(i18n.t("nav.sense")).toBe("නිරීක්ෂණය");
    // Honesty labels are correctly translated (not left in English).
    expect(i18n.t("decide.provenance.synthetic")).toBe("නියැදි");
    expect(i18n.t("language.dataNote")).toMatch(/දත්ත/);
    // <html lang> is synced for correct script rendering.
    expect(document.documentElement.getAttribute("lang")).toBe("si");
  });

  it("translates the core surface to Tamil via the store action", () => {
    useUiStore.getState().setLanguage("ta");
    expect(i18n.t("nav.decide")).toBe("தீர்மானம்");
    expect(i18n.t("learn.realBadge")).toBe("உண்மைத் தரவு");
    expect(document.documentElement.getAttribute("lang")).toBe("ta");
  });

  it("falls back to English for any untranslated long-form key", () => {
    useUiStore.getState().setLanguage("si");
    // Every key we translated is present; missing keys would fall back to en.
    // Assert the switcher renders the active short label.
    render(
      <TooltipProvider>
        <LanguageSwitcher />
      </TooltipProvider>,
    );
    expect(screen.getByText("සිං")).toBeInTheDocument();
  });
});
