import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

/**
 * Dev proxy so the console can call the platform with same-origin URLs.
 * `/api` + `/health` + `/metrics` are exactly the three surfaces the UI uses;
 * the API never needs CORS, and the browser never sees an API key.
 */
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: "127.0.0.1",
    proxy: {
      "/api": "http://127.0.0.1:8000",
      "/health": "http://127.0.0.1:8000",
      "/metrics": "http://127.0.0.1:8000",
    },
  },
});
