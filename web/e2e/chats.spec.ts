import { test, expect } from "@playwright/test";

const SHOTS = "../docs/screenshots";

test("Chats: enter a team breakout room and post a message", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Chats" }).click();

  // Rooms are teams; open the security room.
  await page.locator(".room", { hasText: "security" }).click();
  await expect(page.locator(".room-head")).toContainText("security");

  const input = page.locator(".composer input");
  await input.fill("Should passkey enrollment be mandatory for admin accounts?");
  await page.locator(".composer").getByRole("button", { name: "Send" }).click();

  // User messages render on the right.
  await expect(page.locator(".msg.me .bubble")).toContainText("passkey enrollment");

  // Feature 1: model-driven summon. With the model offline the summon resolves
  // gracefully (failure notice) and the button re-enables — the gate releases.
  await page.getByTestId("summon-input").fill("Draft an auth threat model");
  await page.getByTestId("summon-btn").click();
  await expect(page.getByTestId("summon-notice")).toBeVisible({ timeout: 15_000 });
  // Gate released (not stuck "Summon Active"); a new prompt can be summoned again.
  await expect(page.getByTestId("summon-btn")).toHaveText("Summon");
  await page.getByTestId("summon-input").fill("try again");
  await expect(page.getByTestId("summon-btn")).toBeEnabled();

  await page.screenshot({ path: `${SHOTS}/chats.png` });
});
