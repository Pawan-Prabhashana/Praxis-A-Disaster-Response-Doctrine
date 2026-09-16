/**
 * i18next initialisation.
 *
 * The scaffolding for full localisation is in place, but only English is wired
 * up in this phase. Sinhala (`si`) and Tamil (`ta`) — Sri Lanka's other
 * official languages — are added in Phase 8; their resource bundles slot in
 * beside `en` below with no further wiring.
 */

import i18n from "i18next";
import { initReactI18next } from "react-i18next";

import en from "@/config/locales/en";

export const SUPPORTED_LANGUAGES = ["en"] as const;
export type SupportedLanguage = (typeof SUPPORTED_LANGUAGES)[number];

void i18n.use(initReactI18next).init({
  resources: { en: { translation: en } },
  lng: "en",
  fallbackLng: "en",
  supportedLngs: SUPPORTED_LANGUAGES,
  interpolation: { escapeValue: false }, // React already escapes.
  returnNull: false,
});

export default i18n;
