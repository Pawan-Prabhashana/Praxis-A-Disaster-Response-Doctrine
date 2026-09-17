/**
 * Free CARTO vector basemap styles (no API token). dark-matter for the default
 * dark "operational calm" theme; positron for light. Switched with the app theme.
 */

import type { Theme } from "@/store/ui";

export const BASEMAP_STYLES: Record<Theme, string> = {
  dark: "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
  light: "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
};

export function basemapStyle(theme: Theme): string {
  return BASEMAP_STYLES[theme];
}
