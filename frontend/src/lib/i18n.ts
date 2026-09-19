/**
 * i18next initialisation.
 *
 * Three of Sri Lanka's official languages are wired: English (default), Sinhala,
 * and Tamil. `si`/`ta` translate the full operational surface and every honesty
 * label; anything omitted falls back to English per-key (`fallbackLng`), so the
 * UI never shows an empty or garbled string. The active language is driven by
 * the Zustand UI store (persisted); see `store/ui.ts`.
 */

import i18n from "i18next";
import { initReactI18next } from "react-i18next";

import en from "@/config/locales/en";
import si from "@/config/locales/si";
import ta from "@/config/locales/ta";

export const SUPPORTED_LANGUAGES = ["en", "si", "ta"] as const;
export type SupportedLanguage = (typeof SUPPORTED_LANGUAGES)[number];

export function isSupportedLanguage(value: string): value is SupportedLanguage {
  return (SUPPORTED_LANGUAGES as readonly string[]).includes(value);
}

void i18n.use(initReactI18next).init({
  resources: {
    en: { translation: en },
    si: { translation: si },
    ta: { translation: ta },
  },
  lng: "en",
  fallbackLng: "en",
  supportedLngs: SUPPORTED_LANGUAGES,
  interpolation: { escapeValue: false }, // React already escapes.
  returnNull: false,
});

export default i18n;
