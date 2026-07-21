import { test, expect } from "@playwright/test";

// Each test gets a fresh browser context (isolated localStorage), so the
// seeded default board is the starting point every time.
test.beforeEach(async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Kanban" }).click();
  await expect(page.getByTestId("board")).toBeVisible();
});

test("seeds the default board with four ruled columns", async ({ page }) => {
  for (const id of ["col-backlog", "col-doing", "col-review", "col-done"]) {
    await expect(page.getByTestId(`column-${id}`)).toBeVisible();
  }
  await expect(page.getByTestId("count-col-doing")).toHaveText("1/3");
});

test("adds a card and persists it across a reload", async ({ page }) => {
  await page.getByTestId("add-title-col-backlog").fill("Wire Postgres repository");
  await page.getByTestId("add-ref-col-backlog").fill("#42");
  await page.getByTestId("add-col-backlog").click();

  const backlog = page.getByTestId("column-col-backlog");
  await expect(backlog.getByText("Wire Postgres repository")).toBeVisible();
  await expect(backlog.getByText("#42")).toBeVisible();

  // Reload: state comes back from localStorage via the repository.
  await page.reload();
  await page.getByRole("button", { name: "Kanban" }).click();
  await expect(
    page.getByTestId("column-col-backlog").getByText("Wire Postgres repository"),
  ).toBeVisible();
});

test("moves a card across columns with the nav buttons and updates counts", async ({ page }) => {
  // The seed card in In Progress.
  const doing = page.getByTestId("column-col-doing");
  const card = doing.locator('[data-testid^="card-"]').first();
  const testId = await card.getAttribute("data-testid");
  const cardId = testId!.replace("card-", "");

  await page.getByTestId(`right-${cardId}`).click(); // In Progress -> Review
  await expect(page.getByTestId("count-col-doing")).toHaveText("0/3");
  await expect(
    page.getByTestId("column-col-review").getByTestId(`card-${cardId}`),
  ).toBeVisible();
});

test("surfaces a WIP-limit breach without blocking the move", async ({ page }) => {
  // In Progress limit is 3, already has 1 seed card. Add 3 more => 4/3.
  for (let i = 0; i < 3; i++) {
    await page.getByTestId("add-title-col-doing").fill(`wip card ${i}`);
    await page.getByTestId("add-col-doing").click();
  }
  const count = page.getByTestId("count-col-doing");
  await expect(count).toHaveText("4/3");
  // The over-limit count is flagged (danger color class).
  await expect(count).toHaveClass(/over/);
});
