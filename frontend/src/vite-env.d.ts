/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Base URL the browser client uses to reach the Praxis API. */
  readonly VITE_API_BASE_URL: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
