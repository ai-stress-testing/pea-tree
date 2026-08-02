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
  await page.screenshot({ path: `${SHOTS}/chats.png` });
});
