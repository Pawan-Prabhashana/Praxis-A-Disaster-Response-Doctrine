/**
 * TanStack Query hooks for the Learn (after-action) workspace.
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import type { AfterActionRequest } from "@/lib/api";
import { api } from "@/lib/api";

const STALE = 5 * 60_000;

export function useRecordedOutcomes(slug: string | null) {
  return useQuery({
    queryKey: ["recorded-outcomes", slug],
    queryFn: () => api.recordedOutcomes(slug as string),
    enabled: !!slug,
    staleTime: STALE,
  });
}

export function useAfterActions(slug: string | null, playbookId: number | null) {
  return useQuery({
    queryKey: ["after-actions", slug, playbookId],
    queryFn: () => api.listAfterActions(slug as string, playbookId as number),
    enabled: !!slug && playbookId != null,
    staleTime: STALE,
  });
}

export function useCreateAfterAction(slug: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }: { id: number; body: AfterActionRequest }) =>
      api.createAfterAction(slug, id, body),
    onSuccess: (_data, vars) =>
      qc.invalidateQueries({ queryKey: ["after-actions", slug, vars.id] }),
  });
}
