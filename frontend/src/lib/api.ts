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

const DEFAULT_TIMEOUT_MS = 20000;

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

// --- Playbooks (Phase 4) ----------------------------------------------------
export type Provenance = "real" | "synthetic" | "assumption";
export type AllocationStrategy = "proportional_to_need" | "even";

export interface EvacuationPolicy {
  at_risk_threshold: number;
}
export interface ResourcePosture {
  response_teams: number;
  boats: number;
  allocation: AllocationStrategy;
}
export interface AccessPolicy {
  avoid_closed_roads: boolean;
}
export interface LeverSet {
  version: number;
  priority_region_pcodes: string[];
  activated_shelter_ids: number[];
  evacuation: EvacuationPolicy;
  resources: ResourcePosture;
  access: AccessPolicy;
}

export interface SubMetric {
  key: string;
  score: number;
  weight: number;
  provenance: Provenance;
  raw: Record<string, number | string>;
  notes: string[];
}
export interface CoverageGap {
  pcode: string;
  name: string;
  at_risk_population: number;
}
export interface ScoreResult {
  version: number;
  overall: number;
  metrics: SubMetric[];
  coverage_gaps: CoverageGap[];
  totals: Record<string, number>;
  uses_synthetic_data: boolean;
  assumptions_used: string[];
}

export interface Playbook {
  id: number;
  scenario_slug: string;
  name: string;
  description: string | null;
  levers: LeverSet;
  score_result: ScoreResult | null;
  created_at: string;
  updated_at: string;
}
export interface PlaybookCreate {
  name: string;
  description?: string | null;
  levers: LeverSet;
}
export interface PlaybookUpdate {
  name?: string;
  description?: string | null;
  levers?: LeverSet;
}
export interface RegionContext {
  pcode: string;
  name: string;
  population: number;
  at_risk_population: number;
  is_access_impaired: boolean;
}
export interface SheltersInRegions {
  ids: number[];
  total: number;
}

// --- Stress test / uncertainty (Phase 5) ------------------------------------
export type ParamClass = "real_uncertainty" | "assumption" | "synthetic_derived";
export type DistKind = "triangular" | "uniform" | "constant";

export interface Distribution {
  kind: DistKind;
  low: number;
  high: number;
  mode: number;
}
export interface UncertaintyParam {
  key: string;
  label: string;
  param_class: ParamClass;
  distribution: Distribution;
  basis: string;
  enabled: boolean;
}
export interface UncertaintyConfig {
  version: number;
  target_score: number;
  params: UncertaintyParam[];
}
export interface HistogramBin {
  start: number;
  end: number;
  count: number;
}
export interface DistributionSummary {
  mean: number;
  median: number;
  std: number;
  p05: number;
  p25: number;
  p75: number;
  p95: number;
  min: number;
  max: number;
  histogram: HistogramBin[];
}
export interface Robustness {
  worst_plausible: number;
  probability_meets_target: number;
  target_score: number;
  median: number;
}
export interface StressResult {
  version: number;
  seed: number;
  n_iterations: number;
  point_overall: number;
  overall: DistributionSummary;
  metrics: Record<string, DistributionSummary>;
  robustness: Robustness;
  config: UncertaintyConfig;
  uses_synthetic_data: boolean;
  epistemic_note: string;
}
export interface StressRun {
  id: number;
  playbook_id: number;
  scenario_slug: string;
  n_iterations: number;
  seed: number;
  created_at: string;
  result: StressResult;
}
export interface StressTestRequest {
  config?: UncertaintyConfig;
  n_iterations: number;
  seed?: number | null;
}

function jsonInit(method: string, body: unknown): RequestInit {
  return {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  };
}

async function requestVoid(path: string, init?: RequestInit): Promise<void> {
  const response = await fetch(`${env.apiBaseUrl}${path}`, {
    ...init,
    headers: { Accept: "application/json", ...init?.headers },
  });
  if (!response.ok) throw new ApiError(`Request to ${path} failed`, response.status);
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

  // --- Playbooks ---
  playbookDefaults: (slug: string): Promise<LeverSet> =>
    request<LeverSet>(scenarioPath(slug, "/playbook-defaults")),
  playbookContext: (slug: string): Promise<RegionContext[]> =>
    request<RegionContext[]>(scenarioPath(slug, "/playbook-context")),
  sheltersInRegions: (slug: string, pcodes: string[], limit = 500): Promise<SheltersInRegions> =>
    request<SheltersInRegions>(
      scenarioPath(
        slug,
        `/shelters-in-regions?pcodes=${encodeURIComponent(pcodes.join(","))}&limit=${limit}`,
      ),
    ),
  previewScore: (slug: string, levers: LeverSet): Promise<ScoreResult> =>
    request<ScoreResult>(scenarioPath(slug, "/playbooks/preview-score"), jsonInit("POST", levers)),
  listPlaybooks: (slug: string): Promise<Playbook[]> =>
    request<Playbook[]>(scenarioPath(slug, "/playbooks")),
  getPlaybook: (slug: string, id: number): Promise<Playbook> =>
    request<Playbook>(scenarioPath(slug, `/playbooks/${id}`)),
  createPlaybook: (slug: string, body: PlaybookCreate): Promise<Playbook> =>
    request<Playbook>(scenarioPath(slug, "/playbooks"), jsonInit("POST", body)),
  updatePlaybook: (slug: string, id: number, body: PlaybookUpdate): Promise<Playbook> =>
    request<Playbook>(scenarioPath(slug, `/playbooks/${id}`), jsonInit("PUT", body)),
  deletePlaybook: (slug: string, id: number): Promise<void> =>
    requestVoid(scenarioPath(slug, `/playbooks/${id}`), { method: "DELETE" }),

  // --- Stress test ---
  uncertaintyDefaults: (slug: string): Promise<UncertaintyConfig> =>
    request<UncertaintyConfig>(scenarioPath(slug, "/uncertainty-defaults")),
  stressTest: (slug: string, id: number, body: StressTestRequest): Promise<StressRun> =>
    request<StressRun>(scenarioPath(slug, `/playbooks/${id}/stress-test`), jsonInit("POST", body)),
  listStressRuns: (slug: string, id: number): Promise<StressRun[]> =>
    request<StressRun[]>(scenarioPath(slug, `/playbooks/${id}/stress-runs`)),
} as const;
