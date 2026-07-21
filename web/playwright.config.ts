import { existsSync } from "node:fs";
import { defineConfig, devices } from "@playwright/test";

// Use the environment's pre-installed Chromium when present (this sandbox);
// otherwise fall back to Playwright's managed browser (CI runs
// `playwright install`). Override with PW_CHROMIUM.
const candidate =
  process.env.PW_CHROMIUM ?? "/opt/pw-browsers/chromium-1194/chrome-linux/chrome";
const executablePath = existsSync(candidate) ? candidate : undefined;

export default defineConfig({
  testDir: "./e2e",
  timeout: 30_000,
  expect: { timeout: 7_000 },
  fullyParallel: true,
  reporter: [["list"]],
  use: {
    baseURL: "http://localhost:5173",
    trace: "on-first-retry",
  },
  projects: [
    {
      name: "chromium",
      use: {
        ...devices["Desktop Chrome"],
        launchOptions: {
          ...(executablePath ? { executablePath } : {}),
          args: ["--no-sandbox"], // container runs as root
        },
      },
    },
  ],
  webServer: {
    command: "npm run dev -- --port 5173 --strictPort",
    url: "http://localhost:5173",
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
});
