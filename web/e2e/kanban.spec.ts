import { test, expect } from "@playwright/test";

const SHOTS = "../docs/screenshots";

test("Kanban: quick-add an issue and move it down the pipeline", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Kanban" }).click();

  const cols = page.locator(".col");
  await expect(cols).toHaveCount(5); // Zettlebucket → In Review → Drafting → Approved → Implemented

  // Quick intake lives in the first (Zettlebucket) column.
  await page.locator(".intake input").fill("Passkey login flow");
  await page.locator(".intake").getByRole("button", { name: "Add" }).click();
  await expect(cols.nth(0).locator(".card")).toHaveCount(1);

  // Move it right into "In Review".
  await cols.nth(0).locator(".card").first().locator(".card-nav button").last().click();
  await expect(cols.nth(0).locator(".card")).toHaveCount(0);
  await expect(cols.nth(1).locator(".card")).toHaveCount(1);

  // A couple more for a fuller board shot.
  for (const t of ["Cold-start profiling", "Remove legacy SDK"]) {
    await page.locator(".intake input").fill(t);
    await page.locator(".intake").getByRole("button", { name: "Add" }).click();
  }
  await page.screenshot({ path: `${SHOTS}/kanban.png` });
});
