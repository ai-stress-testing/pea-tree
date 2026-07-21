import { test, expect } from "@playwright/test";

test.beforeEach(async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Mermaid" }).click();
});

test("renders the seeded diagram", async ({ page }) => {
  await expect(page.getByTestId("mermaid-canvas").locator("svg")).toBeVisible();
});

test("creates a diagram, edits its source, and persists across reload", async ({ page }) => {
  await page.getByTestId("new-diagram").click();
  await page.getByTestId("diagram-name").fill("Flow A");

  const src = page.getByTestId("diagram-source");
  await src.fill("flowchart LR\n  Start --> Finish");
  // Renders the edited source.
  await expect(page.getByTestId("mermaid-canvas").locator("svg")).toBeVisible();

  await page.waitForTimeout(400); // let the debounced save flush
  await page.reload();
  await page.getByRole("button", { name: "Mermaid" }).click();
  await expect(page.getByTestId("diagram-source")).toHaveValue(/Start --> Finish/);
});

test("shows a visible error state for invalid source, never a blank pane", async ({ page }) => {
  await page.getByTestId("new-diagram").click();
  await page.getByTestId("diagram-source").fill("flowchart LR\n  A --> ");
  await expect(page.getByTestId("mermaid-error")).toBeVisible();
});
