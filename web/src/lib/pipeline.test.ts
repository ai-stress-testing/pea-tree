import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { Groupchat, RunEvent } from "./pipeline";
import { DEFAULT_SETTINGS } from "./settings";

// A fake NDJSON streaming Response for POST /api/chat.
function chatResponse(text: string) {
  const enc = new TextEncoder();
  const lines = [
    JSON.stringify({ message: { content: text } }),
    JSON.stringify({ done: true, prompt_eval_count: 20, eval_count: 10 }),
  ];
  const stream = new ReadableStream<Uint8Array>({
    start(c) {
      for (const l of lines) c.enqueue(enc.encode(l + "\n"));
      c.close();
    },
  });
  return { ok: true, status: 200, body: stream } as unknown as Response;
}

function tagsResponse() {
  return {
    ok: true,
    status: 200,
    json: async () => ({
      models: [{ name: "qwen2.5:32b" }, { name: "qwen2.5:14b" }, { name: "qwen2.5:7b" }],
    }),
  } as unknown as Response;
}

describe("Groupchat.run", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string, init?: RequestInit) => {
        if (url.endsWith("/api/tags")) return tagsResponse();
        const body = JSON.parse((init?.body as string) ?? "{}");
        const sys: string = body.messages?.[0]?.content ?? "";
        const user: string = body.messages?.[1]?.content ?? "";
        if (sys.includes("You are a router")) return chatResponse("[]"); // rely on @mentions
        if (sys.includes("orchestrator closing")) return chatResponse("PLAN");
        // Opsec turn re-queues the PM once.
        if (user.includes("as security-senior-secops")) {
          return chatResponse("Risk noted.\nREQUEUE: pm/project-manager");
        }
        return chatResponse("A concrete contribution.");
      }),
    );
  });
  afterEach(() => vi.unstubAllGlobals());

  it("iterates mentioned personas, honors one re-queue, and terminates with accounting", async () => {
    const chat = new Groupchat({ ...DEFAULT_SETTINGS });
    const events: RunEvent[] = [];
    const goal = "@pm/project-manager @security/senior-secops plan a small feature";

    await chat.run(goal, (e) => events.push(e));

    const final = events.find((e) => e.type === "final-end");
    expect(final && final.type === "final-end").toBe(true);
    if (final?.type !== "final-end") throw new Error("no final");

    // pm, security, then pm again (re-queued) => 3 cycles, 1 re-queue.
    expect(final.totals.cycles).toBe(3);
    expect(final.totals.requeues).toBe(1);
    expect(final.totals.tokens).toBeGreaterThan(0);
    expect(final.final).toBe("PLAN");

    const requeued = events.filter(
      (e) => e.type === "turn-end" && e.turn.requeued && e.turn.personaId === "pm/project-manager",
    );
    expect(requeued.length).toBe(1);

    // Synthesis emits an execution loop (default, since the mock final has no
    // ```loop block) as valid Mermaid, before final-end.
    const loop = events.find((e) => e.type === "loop");
    expect(loop && loop.type === "loop").toBe(true);
    if (loop?.type !== "loop") throw new Error("no loop");
    expect(loop.mermaid).toContain("flowchart LR");
    expect(loop.mermaid).toContain('pr(["Prep PR"])');
  });
});
