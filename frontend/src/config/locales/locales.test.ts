import { describe, expect, it } from "vitest";

import en from "@/config/locales/en";
import si from "@/config/locales/si";
import ta from "@/config/locales/ta";

// biome-ignore lint/suspicious/noExplicitAny: generic deep lookup over locale objects
function get(obj: any, path: string): unknown {
  return path.split(".").reduce((acc, key) => acc?.[key], obj);
}

// The integrity of the product: these honesty / provenance / epistemic labels
// MUST be present and non-empty in every language.
const CRITICAL_KEYS = [
  "sense.provenance.real",
  "sense.provenance.sample",
  "sense.layers.landslideNote",
  "sense.layers.sheltersNote",
  "decide.provenance.real",
  "decide.provenance.synthetic",
  "decide.provenance.assumption",
  "decide.paramClass.synthetic_derived",
  "decide.syntheticBanner",
  "decide.closuresNote",
  "decide.planningNote",
  "decide.stress.epistemic",
  "act.validatedNote",
  "act.templateNote",
  "act.syntheticWarn",
  "learn.framing",
  "learn.realBadge",
  "learn.provenanceFooter",
  "learn.noData",
  "offline.banner",
];

describe("locales", () => {
  it("has every critical honesty label in all three languages", () => {
    for (const key of CRITICAL_KEYS) {
      for (const [name, bundle] of [
        ["en", en],
        ["si", si],
        ["ta", ta],
      ] as const) {
        const value = get(bundle, key);
        expect(typeof value, `${name}:${key}`).toBe("string");
        expect((value as string).trim().length, `${name}:${key}`).toBeGreaterThan(0);
      }
    }
  });

  it("actually translates the core surface (si/ta differ from English)", () => {
    // A representative sample that must not be left in English.
    for (const key of ["nav.sense", "decide.provenance.real", "learn.alignmentTitle"]) {
      expect(get(si, key), `si:${key}`).not.toBe(get(en, key));
      expect(get(ta, key), `ta:${key}`).not.toBe(get(en, key));
    }
  });

  it("preserves interpolation placeholders across languages", () => {
    // The stress statement uses {{low}}/{{high}}/{{median}}/{{worst}}.
    for (const bundle of [en, si, ta]) {
      const stmt = get(bundle, "decide.stress.statement") as string;
      for (const ph of ["{{low}}", "{{high}}", "{{median}}", "{{worst}}"]) {
        expect(stmt).toContain(ph);
      }
    }
  });
});
