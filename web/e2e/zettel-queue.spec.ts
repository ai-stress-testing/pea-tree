import { test, expect } from "@playwright/test";

const SHOTS = "../docs/screenshots";

test("Zettlebucket intake routes to the Agent-Queue for triage", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Zettlebucket" }).click();

  // Apply a template, then submit.
  await page.getByRole("button", { name: "Bug Report" }).click();
  await page.locator(".title").fill("Crash on rotate during upload");
  await page.screenshot({ path: `${SHOTS}/zettel.png` });

  await page.getByRole("button", { name: /Submit/ }).click();
  await expect(page.locator(".flash")).toContainText("routed to Agent-Queue");

  // The triage line item appears in the Agent-Queue.
  await page.getByRole("button", { name: "Agent-Queue" }).click();
  const rows = page.locator(".q-table tbody tr");
  await expect(rows.first()).toBeVisible();
  await expect(page.locator(".q-table")).toContainText("issue #");
  await expect(page.locator(".state.green").first()).toContainText("idle");

  // Pause / resume works (queue management).
  await page.locator(".controls").first().getByRole("button", { name: "Pause" }).click();
  await expect(page.locator(".state.paused").first()).toBeVisible();
  await page.screenshot({ path: `${SHOTS}/queue.png` });
});
