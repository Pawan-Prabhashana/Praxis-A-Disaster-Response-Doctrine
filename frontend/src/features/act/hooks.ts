/**
 * TanStack Query hooks for the Act brief workspace.
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import type { BriefRequest } from "@/lib/api";
import { api } from "@/lib/api";

const STALE = 5 * 60_000;

export function useBriefs(slug: string | null, playbookId: number | null) {
  return useQuery({
    queryKey: ["briefs", slug, playbookId],
    queryFn: () => api.listBriefs(slug as string, playbookId as number),
    enabled: !!slug && playbookId != null,
    staleTime: STALE,
  });
}

export function useCreateBrief(slug: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }: { id: number; body: BriefRequest }) =>
      api.createBrief(slug, id, body),
    onSuccess: (_data, vars) => qc.invalidateQueries({ queryKey: ["briefs", slug, vars.id] }),
  });
}
