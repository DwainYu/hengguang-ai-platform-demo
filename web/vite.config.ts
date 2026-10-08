import react from "@vitejs/plugin-react";
import { defineConfig, loadEnv } from "vite";

/**
 * Dev proxy so the console can call the platform with same-origin URLs.
 * `/api` + `/health` + `/metrics` are exactly the three surfaces the UI uses,
 * so the API never needs CORS and the browser never sees an API key.
 *
 * The proxy target is configurable so the same console can be pointed at a local
 * API instance (Local Real Embedding mode) without touching source or config files:
 * `VITE_API_PROXY_TARGET=http://127.0.0.1:8001 npm run dev` (or `npm run dev:local`).
 * The default keeps the Docker/main behaviour: the API published on port 8000.
 */
const DEFAULT_API_TARGET = "http://127.0.0.1:8000";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "VITE_");
  const target = env.VITE_API_PROXY_TARGET || DEFAULT_API_TARGET;
  return {
    plugins: [react()],
    server: {
      port: 5173,
      host: "127.0.0.1",
      proxy: {
        "/api": target,
        "/health": target,
        "/metrics": target,
      },
    },
  };
});
