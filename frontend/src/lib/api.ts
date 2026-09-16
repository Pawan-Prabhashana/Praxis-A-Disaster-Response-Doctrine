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

export const api = {
  health: (): Promise<HealthResponse> => request<HealthResponse>("/health"),
  meta: (): Promise<MetaResponse> => request<MetaResponse>("/api/v1/meta"),
} as const;
