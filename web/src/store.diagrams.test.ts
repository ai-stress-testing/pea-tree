import { describe, it, expect, beforeEach } from "vitest";
import { store, actions, __setRepository } from "./store";
import { LocalRepository, KvDriver } from "./lib/store/local";

function makeKv(): KvDriver {
  const m = new Map<string, string>();
  return {
    getItem: (k) => (m.has(k) ? m.get(k)! : null),
    setItem: (k, v) => void m.set(k, v),
    removeItem: (k) => void m.delete(k),
  };
}

let kv: KvDriver;
beforeEach(async () => {
  kv = makeKv();
  __setRepository(new LocalRepository(kv));
  store.diagrams = [];
  store.activeDiagramId = null;
  await actions.loadDiagrams();
});

describe("mermaid diagram store", () => {
  it("loads a seeded diagram and selects it", () => {
    expect(store.diagrams.length).toBeGreaterThan(0);
    expect(store.activeDiagramId).toBe(store.diagrams[0].id);
  });

  it("adds a diagram, edits its source, and persists", async () => {
    const id = actions.addDiagram("My flow");
    actions.updateDiagram(id, { source: "flowchart TD\n  X --> Y" });
    const reloaded = await new LocalRepository(kv).listDiagrams();
    const saved = reloaded.find((d) => d.id === id)!;
    expect(saved.name).toBe("My flow");
    expect(saved.source).toContain("X --> Y");
  });

  it("deletes a diagram and reselects", () => {
    const id = actions.addDiagram("temp");
    expect(store.activeDiagramId).toBe(id);
    actions.deleteDiagram(id);
    expect(store.diagrams.some((d) => d.id === id)).toBe(false);
    expect(store.activeDiagramId).not.toBe(id);
  });
});
