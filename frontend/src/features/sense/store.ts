/**
 * Ephemeral UI state for the Sense dashboard: layer visibility, admin choropleth
 * level, and the currently selected feature. Not persisted — it resets per
 * session and is scoped to this dashboard.
 */

import { create } from "zustand";

import { DEFAULT_VISIBILITY, type LayerKey } from "@/features/sense/layers";
import type { AdminProps, IncidentProps, RiverProps, ShelterProps } from "@/lib/api";

export type AdminLevel = 2 | 3 | 4;

export type SelectedFeature =
  | { kind: "incident"; props: IncidentProps }
  | { kind: "shelter"; props: ShelterProps }
  | { kind: "river"; props: RiverProps }
  | { kind: "admin"; props: AdminProps };

interface SenseState {
  visibility: Record<LayerKey, boolean>;
  adminLevel: AdminLevel;
  selected: SelectedFeature | null;
  toggleLayer: (key: LayerKey) => void;
  setLayer: (key: LayerKey, visible: boolean) => void;
  setAdminLevel: (level: AdminLevel) => void;
  select: (feature: SelectedFeature) => void;
  clearSelection: () => void;
}

export const useSenseStore = create<SenseState>((set) => ({
  visibility: { ...DEFAULT_VISIBILITY },
  // Level 2 (districts) by default: population — the choropleth variable — is
  // published by COD-PS only down to district level.
  adminLevel: 2,
  selected: null,
  toggleLayer: (key) =>
    set((s) => ({ visibility: { ...s.visibility, [key]: !s.visibility[key] } })),
  setLayer: (key, visible) => set((s) => ({ visibility: { ...s.visibility, [key]: visible } })),
  setAdminLevel: (level) => set({ adminLevel: level }),
  select: (feature) => set({ selected: feature }),
  clearSelection: () => set({ selected: null }),
}));
