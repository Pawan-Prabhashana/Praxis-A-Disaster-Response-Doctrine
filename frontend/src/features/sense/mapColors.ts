/**
 * Resolve the design-system CSS custom properties into concrete color strings
 * for MapLibre paint (which cannot read CSS variables). Re-read on theme change
 * so the map recolors with the rest of the UI.
 */

const TOKENS = [
  "background",
  "foreground",
  "surface",
  "surface-raised",
  "border",
  "muted-foreground",
  "primary",
  "signal-ok",
  "signal-ok-foreground",
  "signal-warn",
  "signal-crit",
  "signal-info",
] as const;

export type MapColorToken = (typeof TOKENS)[number];

export type MapColors = Record<MapColorToken, string>;

/** Read the current resolved token values as `hsl(...)` strings. */
export function readMapColors(): MapColors {
  const styles = getComputedStyle(document.documentElement);
  const out = {} as MapColors;
  for (const token of TOKENS) {
    const triplet = styles.getPropertyValue(`--${token}`).trim();
    // Fallback keeps the map usable even if a token is momentarily unresolved.
    out[token] = triplet ? `hsl(${triplet})` : "#888888";
  }
  return out;
}

/** An `hsl(... / alpha)` string for a token at a given opacity. */
export function withAlpha(colors: MapColors, token: MapColorToken, alpha: number): string {
  const value = colors[token];
  // value is `hsl(H S% L%)`; inject the alpha channel.
  return value.replace(/^hsl\((.+)\)$/, (_, inner) => `hsl(${inner} / ${alpha})`);
}
