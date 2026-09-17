/**
 * Playbook Studio UI state: which mode (builder/compare), the working draft the
 * builder edits, and which playbooks are selected for comparison. Ephemeral;
 * server truth lives in TanStack Query.
 */

import { create } from "zustand";

import type { LeverSet, Playbook } from "@/lib/api";

export type StudioMode = "builder" | "compare";

export const EMPTY_LEVERS: LeverSet = {
  version: 1,
  priority_region_pcodes: [],
  activated_shelter_ids: [],
  evacuation: { at_risk_threshold: 0 },
  resources: { response_teams: 0, boats: 0, allocation: "proportional_to_need" },
  access: { avoid_closed_roads: true },
};

export interface Draft {
  name: string;
  description: string;
  levers: LeverSet;
}

interface DecideState {
  mode: StudioMode;
  editingId: number | null;
  draft: Draft;
  compareIds: number[];
  setMode: (mode: StudioMode) => void;
  startNew: (levers: LeverSet) => void;
  editPlaybook: (pb: Playbook) => void;
  setDraftName: (name: string) => void;
  setDraftDescription: (description: string) => void;
  setLevers: (levers: LeverSet) => void;
  patchLevers: (patch: Partial<LeverSet>) => void;
  toggleCompare: (id: number) => void;
  clearCompare: () => void;
}

const NEW_DRAFT = (levers: LeverSet): Draft => ({ name: "", description: "", levers });

export const useDecideStore = create<DecideState>((set) => ({
  mode: "builder",
  editingId: null,
  draft: NEW_DRAFT(EMPTY_LEVERS),
  compareIds: [],
  setMode: (mode) => set({ mode }),
  startNew: (levers) => set({ editingId: null, draft: NEW_DRAFT(levers), mode: "builder" }),
  editPlaybook: (pb) =>
    set({
      editingId: pb.id,
      draft: { name: pb.name, description: pb.description ?? "", levers: pb.levers },
      mode: "builder",
    }),
  setDraftName: (name) => set((s) => ({ draft: { ...s.draft, name } })),
  setDraftDescription: (description) => set((s) => ({ draft: { ...s.draft, description } })),
  setLevers: (levers) => set((s) => ({ draft: { ...s.draft, levers } })),
  patchLevers: (patch) =>
    set((s) => ({ draft: { ...s.draft, levers: { ...s.draft.levers, ...patch } } })),
  toggleCompare: (id) =>
    set((s) => {
      if (s.compareIds.includes(id)) {
        return { compareIds: s.compareIds.filter((x) => x !== id) };
      }
      if (s.compareIds.length >= 3) return s; // compare at most 3
      return { compareIds: [...s.compareIds, id] };
    }),
  clearCompare: () => set({ compareIds: [] }),
}));
