/**
 * Fetches the list of scenarios from the backend for the scenario selector.
 */

import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type { Scenario } from "@/lib/api";

export const SCENARIOS_QUERY_KEY = ["scenarios"] as const;

export function useScenarios() {
  return useQuery<Scenario[]>({
    queryKey: SCENARIOS_QUERY_KEY,
    queryFn: api.scenarios,
    staleTime: 60_000,
  });
}
