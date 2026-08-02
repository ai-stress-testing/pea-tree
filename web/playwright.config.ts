import { existsSync } from "node:fs";
import { defineConfig, devices } from "@playwright/test";

// Pre-installed Chromium in this environment; fall back to Playwright's managed
// browser (CI) if absent.
const candidate =
  process.env.PW_CHROMIUM ?? "/opt/pw-browsers/chromium-1194/chrome-linux/chrome";
const executablePath = existsSync(candidate) ? candidate : undefined;

// Shared SQLite backend => tests must run serially.
export default defineConfig({
  testDir: "./e2e",
  timeout: 30_000,
  expect: { timeout: 7_000 },
  fullyParallel: false,
  workers: 1,
  reporter: [["list"]],
  use: {
    baseURL: "http://localhost:5173",
    viewport: { width: 1320, height: 860 },
    trace: "on-first-retry",
    launchOptions: {
      ...(executablePath ? { executablePath } : {}),
      args: ["--no-sandbox"],
    },
  },
  webServer: [
    {
      // FastAPI backend on a fresh temp DB (agents self-seed on startup).
      command:
        'bash -lc "cd ../backend && rm -rf /tmp/takt-e2e && mkdir -p /tmp/takt-e2e && TAKT_DATA_DIR=/tmp/takt-e2e .venv/bin/uvicorn app.main:app --port 8000"',
      url: "http://localhost:8000/api/health",
      reuseExistingServer: !process.env.CI,
      timeout: 60_000,
    },
    {
      command: "npm run dev",
      url: "http://localhost:5173",
      reuseExistingServer: !process.env.CI,
      timeout: 60_000,
    },
  ],
});
