import { test, expect, Route } from "@playwright/test";

// NDJSON body for a mocked streamed Ollama /api/chat completion.
function ndjson(text: string): string {
  return (
    JSON.stringify({ message: { content: text } }) +
    "\n" +
    JSON.stringify({ done: true, prompt_eval_count: 20, eval_count: 10 }) +
    "\n"
  );
}

// Stand in for a local Ollama so the groupchat runs deterministically in CI.
async function mockOllama(route: Route) {
  const url = route.request().url();
  if (url.endsWith("/api/tags")) {
    return route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        models: [{ name: "qwen2.5:32b" }, { name: "qwen2.5:14b" }, { name: "qwen2.5:7b" }],
      }),
    });
  }
  // /api/chat — branch on the prompt.
  const post = route.request().postDataJSON() as {
    messages: { role: string; content: string }[];
  };
  const sys = post?.messages?.[0]?.content ?? "";
  const user = post?.messages?.[1]?.content ?? "";
  let text = "A concrete contribution.";
  if (sys.includes("You are a router")) text = "[]"; // rely on @mentions
  else if (sys.includes("orchestrator closing")) text = "FINAL PLAN: ship it.";
  else if (user.includes("as security-senior-secops"))
    text = "Security risk found.\nREQUEUE: pm/project-manager";
  return route.fulfill({ status: 200, contentType: "application/x-ndjson", body: ndjson(text) });
}

test("runs a groupchat: streams turns, honors a re-queue, pins the final plan", async ({ page }) => {
  await page.route("**/ollama/**", mockOllama);
  await page.goto("/");

  // Ollama shows connected once /api/tags is mocked.
  await expect(page.locator(".ollama-badge")).toContainText("model");

  const goal = "@pm/project-manager @security/senior-secops plan a small feature";
  await page.getByPlaceholder(/Message the groupchat/).fill(goal);
  await page.keyboard.press("Enter");

  // Participants selected from the @-mentions.
  await expect(page.locator(".participants")).toContainText("pm/project-manager");
  await expect(page.locator(".participants")).toContainText("security/senior-secops");

  // The re-queue notice fires (Opsec sends PM back).
  await expect(page.locator(".notice")).toContainText("re-queued pm/project-manager");

  // PM appears twice (first pass + re-queued), security once => 3 turns.
  await expect(page.locator(".turn")).toHaveCount(3);
  await expect(page.locator(".turn.requeued")).toHaveCount(1);

  // Final plan pinned with run totals.
  await expect(page.locator(".final")).toContainText("FINAL PLAN: ship it.");
  await expect(page.locator(".pane-header")).toContainText("re-queue(s)");

  // Run is persisted: it survives a reload as history.
  await page.reload();
  await expect(page.locator(".thread-row").first()).toContainText(goal);
});
