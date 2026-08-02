import { test, expect } from "@playwright/test";

const SHOTS = "../docs/screenshots";

test("Docs: create project → sprint → document, edit, live preview", async ({ page }) => {
  // DocsView uses window.prompt for project/sprint names.
  const answers = ["Mobile App Revamp", "Sprint 1 — Discovery"];
  let i = 0;
  page.on("dialog", (d) => d.accept(answers[i++] ?? "x"));

  await page.goto("/");
  await expect(page.getByRole("button", { name: "Docs" })).toBeVisible();

  await page.getByRole("button", { name: "+ Project" }).click();
  await expect(page.getByText("Mobile App Revamp")).toBeVisible();

  await page.getByRole("button", { name: "+ Sprint" }).click();
  await page.getByRole("button", { name: "Sprint 1 — Discovery" }).click();

  // Add a PRD from the library.
  await page.locator(".add-doc select").selectOption("prd");
  await page.getByRole("button", { name: "Add" }).click();

  // Editor opens with the starter; add content, blur to auto-save.
  const editor = page.locator(".src");
  await expect(editor).toBeVisible();
  await editor.fill(
    "# Mobile App Revamp — PRD\n\n## Goal\nShip a faster onboarding.\n\n## Requirements\n1. Sub-2s cold start\n2. Passkey login\n",
  );
  await page.locator(".title-input").click(); // blur the editor → save

  // Live preview renders the markdown.
  await expect(page.locator(".preview .md h1")).toContainText("Mobile App Revamp");
  await expect(page.locator(".save-state")).toHaveText("saved");

  await page.screenshot({ path: `${SHOTS}/docs.png` });
});
