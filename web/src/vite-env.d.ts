/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Optional API origin override (default: same origin, proxied by Vite / nginx). */
  readonly VITE_API_BASE?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
