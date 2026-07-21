import { reactive } from "vue";
import { Groupchat, RunEvent } from "./lib/pipeline";
import { OllamaClient } from "./lib/ollama";
import { DEFAULT_SETTINGS, Settings } from "./lib/settings";
import { LocalRepository } from "./lib/store/local";
import type { Repository } from "./lib/store/repository";
import type { Board, Card, Column, Thread } from "./lib/store/types";

// Re-export persisted types so existing component imports (`../store`) hold.
export type { UiTurn, Thread, ThreadStatus } from "./lib/store/types";
export type { Board, Column, Card } from "./lib/store/types";

export type View = "messaging" | "mermaid" | "kanban" | "settings";

interface State {
  view: View;
  settings: Settings;
  // groupchat
  threads: Thread[];
  activeThreadId: string | null;
  models: string[];
  ollamaOk: boolean | null;
  // kanban
  board: Board | null;
  columns: Column[];
  cards: Card[];
  boardLoaded: boolean;
}

// The persistence seam. Swap via __setRepository (tests) or, later, a
// RestRepository for the hosted Postgres build — no other code changes.
let repo: Repository = new LocalRepository();
export function __setRepository(r: Repository): void {
  repo = r;
}

const controllers = new Map<string, AbortController>();

export const store = reactive<State>({
  view: "messaging",
  settings: structuredClone(DEFAULT_SETTINGS),
  threads: [],
  activeThreadId: null,
  models: [],
  ollamaOk: null,
  board: null,
  columns: [],
  cards: [],
  boardLoaded: false,
});

export const actions = {
  async init(): Promise<void> {
    await Promise.all([this.loadBoard(), this.loadThreads(), this.refreshModels()]);
  },

  setView(v: View) {
    store.view = v;
  },

  // ---- Ollama ----
  async refreshModels(): Promise<void> {
    try {
      const client = new OllamaClient(store.settings.ollamaOrigin);
      store.models = await client.listModels();
      store.ollamaOk = true;
    } catch {
      store.models = [];
      store.ollamaOk = false;
    }
  },

  // ---- Groupchat ----
  activeThread(): Thread | null {
    return store.threads.find((t) => t.id === store.activeThreadId) ?? null;
  },
  select(id: string) {
    store.activeThreadId = id;
  },
  cancel(id: string) {
    controllers.get(id)?.abort();
  },
  async loadThreads(): Promise<void> {
    const persisted = await repo.listThreads();
    // A run persisted mid-flight can't resume — settle its status on load.
    for (const t of persisted) {
      if (t.status === "running" || t.status === "synth") t.status = "done";
    }
    store.threads = persisted;
  },
  async deleteThread(id: string): Promise<void> {
    store.threads = store.threads.filter((t) => t.id !== id);
    if (store.activeThreadId === id) store.activeThreadId = store.threads[0]?.id ?? null;
    await repo.deleteThread(id);
  },

  startRun(goal: string): string {
    const trimmed = goal.trim();
    const thread: Thread = {
      id: `run-${Date.now()}`,
      goal: trimmed,
      participants: [],
      turns: [],
      final: "",
      finalStreaming: false,
      totals: null,
      status: "running",
      notices: [],
      createdAt: Date.now(),
    };
    store.threads.unshift(thread);
    store.activeThreadId = thread.id;
    // Mutate the reactive proxy, not the raw object, so the UI tracks updates.
    const live = store.threads.find((t) => t.id === thread.id)!;
    void repo.saveThread(live);

    const ctrl = new AbortController();
    controllers.set(live.id, ctrl);
    const chat = new Groupchat(store.settings);

    chat
      .run(trimmed, (e) => this.apply(live, e), ctrl.signal)
      .catch((err) => live.notices.push(`fatal: ${(err as Error).message}`))
      .finally(() => {
        controllers.delete(live.id);
        if (live.status !== "error" && live.status !== "done") live.status = "done";
        void repo.saveThread(live);
      });
    return live.id;
  },

  apply(thread: Thread, e: RunEvent) {
    switch (e.type) {
      case "participants":
        thread.participants = e.ids;
        break;
      case "turn-start":
        thread.turns.push({ ...e.turn, streaming: true });
        break;
      case "turn-token": {
        const t = thread.turns.find((x) => x.id === e.id);
        if (t) t.text += e.chunk;
        break;
      }
      case "turn-end": {
        const t = thread.turns.find((x) => x.id === e.turn.id);
        if (t) {
          t.text = e.turn.text;
          t.tokenCost = e.turn.tokenCost;
          t.streaming = false;
        }
        void repo.saveThread(thread);
        break;
      }
      case "requeue":
        thread.notices.push(
          e.accepted
            ? `${e.by} re-queued ${e.target}`
            : `${e.by} wanted to re-queue ${e.target} (cap reached)`,
        );
        break;
      case "final-start":
        thread.status = "synth";
        thread.finalStreaming = true;
        break;
      case "final-token":
        thread.final += e.chunk;
        break;
      case "final-end":
        thread.final = e.final;
        thread.finalStreaming = false;
        thread.totals = e.totals;
        thread.status = "done";
        void repo.saveThread(thread);
        break;
      case "error":
        thread.notices.push(e.message);
        break;
    }
  },

  // ---- Kanban ----
  async loadBoard(): Promise<void> {
    const data = await repo.getBoard();
    store.board = data.board;
    store.columns = data.columns.slice().sort((a, b) => a.order - b.order);
    store.cards = data.cards;
    store.boardLoaded = true;
  },

  cardsIn(columnId: string): Card[] {
    return store.cards
      .filter((c) => c.columnId === columnId)
      .sort((a, b) => a.order - b.order);
  },

  overWip(columnId: string): boolean {
    const col = store.columns.find((c) => c.id === columnId);
    if (!col || col.wipLimit == null) return false;
    return this.cardsIn(columnId).length > col.wipLimit;
  },

  persistBoard(): void {
    if (!store.board) return;
    void repo.saveBoard({ board: store.board, columns: store.columns, cards: store.cards });
  },

  addCard(columnId: string, title: string, issueRef = "", body = ""): void {
    if (!store.board || !title.trim()) return;
    const now = Date.now();
    const order = this.cardsIn(columnId).length;
    store.cards.push({
      id: crypto.randomUUID(),
      boardId: store.board.id,
      columnId,
      title: title.trim(),
      body: body.trim(),
      issueRef: issueRef.trim(),
      order,
      createdAt: now,
      updatedAt: now,
    });
    this.persistBoard();
  },

  moveCard(cardId: string, toColumnId: string): void {
    const card = store.cards.find((c) => c.id === cardId);
    if (!card || card.columnId === toColumnId) return;
    card.columnId = toColumnId;
    card.order = this.cardsIn(toColumnId).length; // append to target
    card.updatedAt = Date.now();
    this.persistBoard();
  },

  /** Move a card to the adjacent column (dir -1 left, +1 right). */
  moveCardDir(cardId: string, dir: -1 | 1): void {
    const card = store.cards.find((c) => c.id === cardId);
    if (!card) return;
    const cur = store.columns.find((c) => c.id === card.columnId);
    if (!cur) return;
    const target = store.columns.find((c) => c.order === cur.order + dir);
    if (target) this.moveCard(cardId, target.id);
  },

  editCard(cardId: string, patch: Partial<Pick<Card, "title" | "body" | "issueRef">>): void {
    const card = store.cards.find((c) => c.id === cardId);
    if (!card) return;
    Object.assign(card, patch, { updatedAt: Date.now() });
    this.persistBoard();
  },

  deleteCard(cardId: string): void {
    store.cards = store.cards.filter((c) => c.id !== cardId);
    this.persistBoard();
  },
};
