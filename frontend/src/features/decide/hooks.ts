/**
 * TanStack Query hooks + a debounce helper for Playbook Studio.
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import type {
  LeverSet,
  PlaybookCreate,
  PlaybookUpdate,
  ScoreResult,
  StressTestRequest,
} from "@/lib/api";

const STALE = 5 * 60_000;

export function useDebouncedValue<T>(value: T, delayMs: number): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setDebounced(value), delayMs);
    return () => clearTimeout(t);
  }, [value, delayMs]);
  return debounced;
}

export function usePlaybookDefaults(slug: string | null) {
  return useQuery({
    queryKey: ["playbook-defaults", slug],
    queryFn: () => api.playbookDefaults(slug as string),
    enabled: !!slug,
    staleTime: STALE,
  });
}

export function usePlaybookContext(slug: string | null) {
  return useQuery({
    queryKey: ["playbook-context", slug],
    queryFn: () => api.playbookContext(slug as string),
    enabled: !!slug,
    staleTime: STALE,
  });
}

export function usePlaybooks(slug: string | null) {
  return useQuery({
    queryKey: ["playbooks", slug],
    queryFn: () => api.listPlaybooks(slug as string),
    enabled: !!slug,
  });
}

/** Live, debounced scorecard preview for the current draft levers. */
export function usePreviewScore(slug: string | null, levers: LeverSet) {
  const debounced = useDebouncedValue(levers, 300);
  return useQuery<ScoreResult>({
    queryKey: ["preview-score", slug, debounced],
    queryFn: () => api.previewScore(slug as string, debounced),
    enabled: !!slug,
    staleTime: STALE,
    placeholderData: (prev) => prev, // keep last scorecard visible while recomputing
  });
}

export function useSheltersInRegions(slug: string | null, pcodes: string[]) {
  return useQuery({
    queryKey: ["shelters-in-regions", slug, [...pcodes].sort()],
    queryFn: () => api.sheltersInRegions(slug as string, pcodes),
    enabled: !!slug && pcodes.length > 0,
    staleTime: STALE,
  });
}

export function useCreatePlaybook(slug: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: PlaybookCreate) => api.createPlaybook(slug, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["playbooks", slug] }),
  });
}

export function useUpdatePlaybook(slug: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }: { id: number; body: PlaybookUpdate }) =>
      api.updatePlaybook(slug, id, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["playbooks", slug] }),
  });
}

export function useDeletePlaybook(slug: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api.deletePlaybook(slug, id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["playbooks", slug] }),
  });
}

// --- Stress test ---
export function useUncertaintyDefaults(slug: string | null) {
  return useQuery({
    queryKey: ["uncertainty-defaults", slug],
    queryFn: () => api.uncertaintyDefaults(slug as string),
    enabled: !!slug,
    staleTime: STALE,
  });
}

export function useStressRuns(slug: string | null, playbookId: number | null) {
  return useQuery({
    queryKey: ["stress-runs", slug, playbookId],
    queryFn: () => api.listStressRuns(slug as string, playbookId as number),
    enabled: !!slug && playbookId != null,
    staleTime: STALE,
  });
}

export function useStressTest(slug: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }: { id: number; body: StressTestRequest }) =>
      api.stressTest(slug, id, body),
    onSuccess: (_data, vars) => qc.invalidateQueries({ queryKey: ["stress-runs", slug, vars.id] }),
  });
}
