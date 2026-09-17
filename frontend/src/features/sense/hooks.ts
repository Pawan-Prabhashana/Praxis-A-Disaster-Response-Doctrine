/**
 * TanStack Query hooks for the Sense dashboard. Each layer is a separate query
 * keyed by scenario slug so toggling visibility never refetches, and switching
 * scenarios swaps cleanly. GeoJSON is static per scenario → long staleTime.
 */

import { useQuery } from "@tanstack/react-query";

import type { AdminLevel } from "@/features/sense/store";
import { api } from "@/lib/api";

const LAYER_STALE = 5 * 60_000;

export function useScenarioDetail(slug: string | null) {
  return useQuery({
    queryKey: ["scenario-detail", slug],
    queryFn: () => api.scenarioDetail(slug as string),
    enabled: !!slug,
    staleTime: LAYER_STALE,
  });
}

export function useAdminRegions(slug: string | null, level: AdminLevel) {
  return useQuery({
    queryKey: ["admin-regions", slug, level],
    queryFn: () => api.adminRegions(slug as string, level),
    enabled: !!slug,
    staleTime: LAYER_STALE,
  });
}

export function useHazardLayers(slug: string | null) {
  return useQuery({
    queryKey: ["hazard-layers", slug],
    queryFn: () => api.hazardLayers(slug as string),
    enabled: !!slug,
    staleTime: LAYER_STALE,
  });
}

export function useShelters(slug: string | null) {
  return useQuery({
    queryKey: ["shelters", slug],
    queryFn: () => api.shelters(slug as string),
    enabled: !!slug,
    staleTime: LAYER_STALE,
  });
}

export function useIncidents(slug: string | null) {
  return useQuery({
    queryKey: ["incidents", slug],
    queryFn: () => api.incidents(slug as string),
    enabled: !!slug,
    staleTime: LAYER_STALE,
  });
}

export function useRoads(slug: string | null) {
  return useQuery({
    queryKey: ["roads", slug],
    queryFn: () => api.roads(slug as string),
    enabled: !!slug,
    staleTime: LAYER_STALE,
  });
}

export function useRivers(slug: string | null) {
  return useQuery({
    queryKey: ["rivers", slug],
    queryFn: () => api.rivers(slug as string),
    enabled: !!slug,
    staleTime: LAYER_STALE,
  });
}

export function useDischarge(slug: string | null, riverPointId: number | null) {
  return useQuery({
    queryKey: ["discharge", slug, riverPointId],
    queryFn: () => api.discharge(slug as string, riverPointId as number),
    enabled: !!slug && riverPointId != null,
    staleTime: LAYER_STALE,
  });
}
