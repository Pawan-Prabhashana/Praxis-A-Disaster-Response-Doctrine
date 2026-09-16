/**
 * Typed, validated access to build-time environment configuration.
 *
 * Vite only exposes variables prefixed with `VITE_`. We read them once here so
 * the rest of the app depends on a small, well-typed surface rather than
 * scattering `import.meta.env` reads throughout the codebase.
 */

function readApiBaseUrl(): string {
  const raw = import.meta.env.VITE_API_BASE_URL?.trim();
  // Fall back to the conventional local API origin so a fresh clone runs.
  return raw && raw.length > 0 ? raw.replace(/\/$/, "") : "http://localhost:8000";
}

export const env = {
  apiBaseUrl: readApiBaseUrl(),
} as const;

export type Env = typeof env;
