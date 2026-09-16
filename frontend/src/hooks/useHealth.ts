/**
 * Polls the backend `/health` endpoint via TanStack Query so the system-status
 * indicator reflects live API + database reachability.
 */

import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type { HealthResponse } from "@/lib/api";

export const HEALTH_QUERY_KEY = ["health"] as const;

export function useHealth() {
  return useQuery<HealthResponse>({
    queryKey: HEALTH_QUERY_KEY,
    queryFn: api.health,
    refetchInterval: 15_000, // keep the status indicator current
    refetchOnWindowFocus: true,
    retry: 1,
    staleTime: 5_000,
  });
}
