/**
 * Typed, validated access to build-time environment configuration.
 *
 * Vite only exposes variables prefixed with `VITE_`. We read them once here so
 * the rest of the app depends on a small, well-typed surface rather than
 * scattering `import.meta.env` reads throughout the codebase.
 */

function readApiBaseUrl(): string {
  const raw = import.meta.env.VITE_API_BASE_URL;
  // When the variable is UNSET, fall back to the conventional local API origin
  // so a fresh clone runs. When it is set — even to "" — honour it: an empty
  // value means "same origin" (relative /api paths), which is how the production
  // nginx image serves the app and proxies the API.
  if (raw === undefined) return "http://localhost:8000";
  return raw.trim().replace(/\/$/, "");
}

export const env = {
  apiBaseUrl: readApiBaseUrl(),
} as const;

export type Env = typeof env;
