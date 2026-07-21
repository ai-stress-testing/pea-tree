import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

// The Ollama default origin. Proxied in dev so the browser isn't blocked by
// CORS; overridable at runtime via the Settings panel (see src/lib/settings.ts).
const OLLAMA = process.env.OLLAMA_ORIGIN ?? "http://localhost:11434";

export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      "/ollama": {
        target: OLLAMA,
        changeOrigin: true,
        rewrite: (p) => p.replace(/^\/ollama/, ""),
      },
    },
  },
  test: {
    globals: true,
    environment: "node",
  },
});
