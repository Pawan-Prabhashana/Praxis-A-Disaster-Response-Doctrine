/**
 * Registry of the Sense dashboard's map layers.
 *
 * Static display metadata only (labels, ordering, default visibility, whether a
 * layer is synthetic by nature). Live counts and per-feature provenance come
 * from the loaded data at runtime.
 */

export type LayerKey =
  | "admin"
  | "flood"
  | "landslide"
  | "roads"
  | "shelters"
  | "incidents"
  | "rivers";

export interface LayerDef {
  key: LayerKey;
  /** i18n key for the visible label. */
  labelKey: string;
  /** i18n key for a short descriptor / provenance note. */
  noteKey: string;
  defaultVisible: boolean;
  /** True when the entire layer is synthetic sample data. */
  synthetic: boolean;
  /** True when only some features are synthetic (provenance is per-feature). */
  partialSynthetic: boolean;
}

/** Draw/legend order (top of legend → drawn last/on top handled in map). */
export const LAYER_DEFS: readonly LayerDef[] = [
  {
    key: "admin",
    labelKey: "sense.layers.admin",
    noteKey: "sense.layers.adminNote",
    defaultVisible: true,
    synthetic: false,
    partialSynthetic: false,
  },
  {
    key: "flood",
    labelKey: "sense.layers.flood",
    noteKey: "sense.layers.floodNote",
    defaultVisible: true,
    synthetic: false,
    partialSynthetic: false,
  },
  {
    key: "landslide",
    labelKey: "sense.layers.landslide",
    noteKey: "sense.layers.landslideNote",
    defaultVisible: false,
    synthetic: true,
    partialSynthetic: false,
  },
  {
    key: "roads",
    labelKey: "sense.layers.roads",
    noteKey: "sense.layers.roadsNote",
    defaultVisible: true,
    synthetic: false,
    partialSynthetic: true,
  },
  {
    key: "shelters",
    labelKey: "sense.layers.shelters",
    noteKey: "sense.layers.sheltersNote",
    defaultVisible: true,
    synthetic: false,
    partialSynthetic: false,
  },
  {
    key: "incidents",
    labelKey: "sense.layers.incidents",
    noteKey: "sense.layers.incidentsNote",
    defaultVisible: true,
    synthetic: false,
    partialSynthetic: false,
  },
  {
    key: "rivers",
    labelKey: "sense.layers.rivers",
    noteKey: "sense.layers.riversNote",
    defaultVisible: true,
    synthetic: false,
    partialSynthetic: false,
  },
] as const;

export const DEFAULT_VISIBILITY: Record<LayerKey, boolean> = Object.fromEntries(
  LAYER_DEFS.map((l) => [l.key, l.defaultVisible]),
) as Record<LayerKey, boolean>;
