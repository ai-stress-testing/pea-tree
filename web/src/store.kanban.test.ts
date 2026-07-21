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
  await actions.loadBoard();
});

describe("kanban store", () => {
  it("loads the seeded board", () => {
    expect(store.columns.map((c) => c.name)).toEqual(["Backlog", "In Progress", "Review", "Done"]);
    expect(actions.cardsIn("col-doing").length).toBe(1);
  });

  it("adds a card to a column and persists it", async () => {
    actions.addCard("col-backlog", "New task", "#9");
    const inBacklog = actions.cardsIn("col-backlog");
    expect(inBacklog.some((c) => c.title === "New task" && c.issueRef === "#9")).toBe(true);
    // persisted through the same driver
    const reloaded = await new LocalRepository(kv).getBoard();
    expect(reloaded.cards.some((c) => c.title === "New task")).toBe(true);
  });

  it("moves a card between columns and appends to the target", () => {
    const card = actions.cardsIn("col-doing")[0];
    actions.moveCard(card.id, "col-done");
    expect(actions.cardsIn("col-doing").length).toBe(0);
    expect(actions.cardsIn("col-done").some((c) => c.id === card.id)).toBe(true);
  });

  it("moveCardDir walks adjacent columns and clamps at the edges", () => {
    const card = actions.cardsIn("col-doing")[0]; // order 1
    actions.moveCardDir(card.id, 1); // -> Review (order 2)
    expect(actions.cardsIn("col-review").some((c) => c.id === card.id)).toBe(true);
    actions.moveCardDir(card.id, -1); // -> back to In Progress
    expect(actions.cardsIn("col-doing").some((c) => c.id === card.id)).toBe(true);
  });

  it("surfaces (does not block) a WIP-limit breach", () => {
    // In Progress has wipLimit 3 and one seed card; add 3 more => 4 > 3.
    expect(actions.overWip("col-doing")).toBe(false);
    for (let i = 0; i < 3; i++) actions.addCard("col-doing", `c${i}`);
    expect(actions.cardsIn("col-doing").length).toBe(4);
    expect(actions.overWip("col-doing")).toBe(true);
  });

  it("edits and deletes a card", () => {
    const card = actions.cardsIn("col-doing")[0];
    actions.editCard(card.id, { title: "renamed" });
    expect(actions.cardsIn("col-doing")[0].title).toBe("renamed");
    actions.deleteCard(card.id);
    expect(store.cards.some((c) => c.id === card.id)).toBe(false);
  });
});
