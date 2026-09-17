/**
 * Typed API client for the Praxis backend.
 *
 * A thin wrapper over `fetch` that centralises the base URL, JSON handling,
 * timeouts, and error shaping. Response types mirror the backend Pydantic
 * schemas so the two stay in lock-step.
 */

import { env } from "@/config/env";

export type ComponentStatus = "ok" | "error";

export interface HealthResponse {
  status: ComponentStatus;
  db: ComponentStatus;
  version: string;
  environment: string;
}

export interface ScenarioSummary {
  id: string;
  name: string;
}

export interface MetaResponse {
  app_name: string;
  version: string;
  environment: string;
  scenarios: ScenarioSummary[];
}

export type HazardType = "flood" | "landslide" | "cyclone" | "multi";
export type ScenarioStatus = "historical" | "simulated" | "live";

/** A scenario as returned by GET /api/v1/scenarios. */
export interface Scenario {
  id: number;
  slug: string;
  name: string;
  hazard_type: HazardType;
  status: ScenarioStatus;
  event_date: string | null;
}

export interface SourceInfo {
  key: string;
  name: string;
  license: string | null;
  is_synthetic: boolean;
}

export interface ScenarioBBox {
  min_lon: number;
  min_lat: number;
  max_lon: number;
  max_lat: number;
}

export interface ScenarioDetail extends Scenario {
  description: string | null;
  bbox: ScenarioBBox | null;
  center: { lon: number; lat: number } | null;
  layers: Record<string, number>;
  sources: SourceInfo[];
}

// --- GeoJSON (light typings; geometry passed through to MapLibre as-is) ------
export interface GeoGeometry {
  type: string;
  coordinates: unknown;
}

export interface GeoFeature<P> {
  type: "Feature";
  geometry: GeoGeometry;
  properties: P;
}

export interface GeoFeatureCollection<P> {
  type: "FeatureCollection";
  features: GeoFeature<P>[];
}

export interface AdminProps {
  id: number;
  pcode: string;
  level: number;
  name_en: string;
  name_si: string | null;
  name_ta: string | null;
  population: number | null;
  source: string;
  is_synthetic: boolean;
}

export interface HazardProps {
  id: number;
  layer_type: string;
  name: string;
  severity_class: number | null;
  severity_label: string | null;
  is_synthetic: boolean;
  source: string;
}

export interface ShelterProps {
  id: number;
  name: string;
  kind: string;
  capacity: number | null;
  is_synthetic: boolean;
  source: string;
  note: string;
}

export interface IncidentProps {
  id: number;
  type: string;
  severity: string | null;
  occurred_at: string | null;
  description: string | null;
  is_synthetic: boolean;
  source: string;
}

export interface RoadProps {
  id: number;
  name: string | null;
  road_class: string | null;
  closed: boolean;
  closure_reason: string | null;
  closure_is_synthetic: boolean | null;
  source: string;
}

export interface RiverProps {
  id: number;
  key: string;
  name: string;
  river_name: string | null;
  source: string;
}

// --- River discharge (GloFAS ensemble) --------------------------------------
export interface DischargeDay {
  valid_date: string;
  mean: number | null;
  median: number | null;
  p25: number | null;
  p75: number | null;
  min: number | null;
  max: number | null;
}

export interface RiverPointDischarge {
  river_point_id: number;
  key: string;
  name: string;
  river_name: string | null;
  lon: number;
  lat: number;
  source: string;
  is_synthetic: boolean;
  series: DischargeDay[];
}

export interface DischargeResponse {
  scenario_slug: string;
  points: RiverPointDischarge[];
}

/** Error raised for non-2xx responses or transport/timeout failures. */
export class ApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

const DEFAULT_TIMEOUT_MS = 8000;

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), DEFAULT_TIMEOUT_MS);

  try {
    const response = await fetch(`${env.apiBaseUrl}${path}`, {
      ...init,
      signal: controller.signal,
      headers: { Accept: "application/json", ...init?.headers },
    });

    if (!response.ok) {
      throw new ApiError(`Request to ${path} failed`, response.status);
    }

    return (await response.json()) as T;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    const message = error instanceof Error ? error.message : "Network request failed";
    // status 0 == the request never reached the server (offline/timeout).
    throw new ApiError(message, 0);
  } finally {
    clearTimeout(timeout);
  }
}

function scenarioPath(slug: string, suffix = ""): string {
  return `/api/v1/scenarios/${encodeURIComponent(slug)}${suffix}`;
}

export const api = {
  health: (): Promise<HealthResponse> => request<HealthResponse>("/health"),
  meta: (): Promise<MetaResponse> => request<MetaResponse>("/api/v1/meta"),
  scenarios: (): Promise<Scenario[]> => request<Scenario[]>("/api/v1/scenarios"),
  scenarioDetail: (slug: string): Promise<ScenarioDetail> =>
    request<ScenarioDetail>(scenarioPath(slug)),
  adminRegions: (slug: string, level: number): Promise<GeoFeatureCollection<AdminProps>> =>
    request<GeoFeatureCollection<AdminProps>>(scenarioPath(slug, `/admin-regions?level=${level}`)),
  hazardLayers: (slug: string, type?: string): Promise<GeoFeatureCollection<HazardProps>> =>
    request<GeoFeatureCollection<HazardProps>>(
      scenarioPath(slug, `/hazard-layers${type ? `?type=${encodeURIComponent(type)}` : ""}`),
    ),
  shelters: (slug: string): Promise<GeoFeatureCollection<ShelterProps>> =>
    request<GeoFeatureCollection<ShelterProps>>(scenarioPath(slug, "/shelters")),
  incidents: (slug: string): Promise<GeoFeatureCollection<IncidentProps>> =>
    request<GeoFeatureCollection<IncidentProps>>(scenarioPath(slug, "/incidents")),
  roads: (slug: string): Promise<GeoFeatureCollection<RoadProps>> =>
    request<GeoFeatureCollection<RoadProps>>(scenarioPath(slug, "/roads")),
  rivers: (slug: string): Promise<GeoFeatureCollection<RiverProps>> =>
    request<GeoFeatureCollection<RiverProps>>(scenarioPath(slug, "/rivers")),
  discharge: (slug: string, riverPointId?: number): Promise<DischargeResponse> =>
    request<DischargeResponse>(
      scenarioPath(slug, `/discharge${riverPointId ? `?river_point_id=${riverPointId}` : ""}`),
    ),
} as const;
