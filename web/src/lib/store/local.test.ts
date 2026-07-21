import { describe, it, expect } from "vitest";
import { LocalRepository, KvDriver } from "./local";
import type { Thread } from "./types";

function makeKv(): KvDriver {
  const m = new Map<string, string>();
  return {
    getItem: (k) => (m.has(k) ? m.get(k)! : null),
    setItem: (k, v) => void m.set(k, v),
    removeItem: (k) => void m.delete(k),
  };
}

function thread(id: string, createdAt: number): Thread {
  return {
    id, goal: "g", participants: [], turns: [], final: "", finalStreaming: false,
    loopMermaid: "", totals: null, status: "done", notices: [], createdAt,
  };
}

describe("LocalRepository", () => {
  it("seeds a default board on first read and persists it", async () => {
    const kv = makeKv();
    const repo = new LocalRepository(kv);
    const a = await repo.getBoard();
    expect(a.columns.length).toBe(4);
    expect(a.cards.length).toBeGreaterThan(0);
    // A second repo over the same driver sees the seeded board (no reseed).
    const b = await new LocalRepository(kv).getBoard();
    expect(b.board.id).toBe(a.board.id);
  });

  it("round-trips a saved board", async () => {
    const kv = makeKv();
    const repo = new LocalRepository(kv);
    const data = await repo.getBoard();
    data.board.name = "renamed";
    await repo.saveBoard(data);
    expect((await new LocalRepository(kv).getBoard()).board.name).toBe("renamed");
  });

  it("stores threads newest-first and never persists a streaming flag", async () => {
    const repo = new LocalRepository(makeKv());
    await repo.saveThread({
      ...thread("run-1", 100),
      status: "running",
      turns: [{ id: "t", personaId: "pm/project-manager", name: "pm", cycle: 1, text: "x", tokenCost: 5, requeued: false, streaming: true }],
    });
    await repo.saveThread(thread("run-2", 200));
    const all = await repo.listThreads();
    expect(all.map((t) => t.id)).toEqual(["run-2", "run-1"]);
    expect(all.find((t) => t.id === "run-1")!.turns[0].streaming).toBe(false);
  });

  it("deletes a thread and clears everything", async () => {
    const kv = makeKv();
    const repo = new LocalRepository(kv);
    await repo.saveThread(thread("run-1", 100));
    await repo.deleteThread("run-1");
    expect(await repo.listThreads()).toEqual([]);
    await repo.saveThread(thread("run-2", 200));
    await repo.clear();
    expect(await repo.listThreads()).toEqual([]);
  });

  it("treats a corrupt entry as absent instead of throwing", async () => {
    const kv = makeKv();
    kv.setItem("pea-tree:board", "{not json");
    const data = await new LocalRepository(kv).getBoard();
    expect(data.columns.length).toBe(4); // reseeded, no crash
  });
});
