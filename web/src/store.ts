import { reactive } from "vue";
import { Groupchat, RunEvent, RunTotals } from "./lib/pipeline";
import { OllamaClient } from "./lib/ollama";
import { DEFAULT_SETTINGS, Settings } from "./lib/settings";

export interface UiTurn {
  id: string;
  personaId: string;
  name: string;
  cycle: number;
  text: string;
  tokenCost: number;
  requeued: boolean;
  streaming: boolean;
}

export type ThreadStatus = "running" | "synth" | "done" | "error";

export interface Thread {
  id: string;
  goal: string;
  participants: string[];
  turns: UiTurn[];
  final: string;
  finalStreaming: boolean;
  totals: RunTotals | null;
  status: ThreadStatus;
  notices: string[];
  createdAt: number;
}

export type View = "messaging" | "mermaid" | "kanban" | "settings";

interface State {
  view: View;
  settings: Settings;
  threads: Thread[];
  activeThreadId: string | null;
  models: string[];
  ollamaOk: boolean | null;
}

const controllers = new Map<string, AbortController>();

export const store = reactive<State>({
  view: "messaging",
  settings: structuredClone(DEFAULT_SETTINGS),
  threads: [],
  activeThreadId: null,
  models: [],
  ollamaOk: null,
});

export const actions = {
  setView(v: View) {
    store.view = v;
  },

  activeThread(): Thread | null {
    return store.threads.find((t) => t.id === store.activeThreadId) ?? null;
  },

  select(id: string) {
    store.activeThreadId = id;
  },

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

  cancel(id: string) {
    controllers.get(id)?.abort();
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

    const ctrl = new AbortController();
    controllers.set(thread.id, ctrl);
    const chat = new Groupchat(store.settings);

    const emit = (e: RunEvent) => this.apply(thread, e);
    chat
      .run(trimmed, emit, ctrl.signal)
      .catch((err) => thread.notices.push(`fatal: ${(err as Error).message}`))
      .finally(() => {
        controllers.delete(thread.id);
        if (thread.status !== "error" && thread.status !== "done") thread.status = "done";
      });
    return thread.id;
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
        break;
      case "error":
        // Non-fatal notices (e.g. a tier falling back to another model).
        thread.notices.push(e.message);
        break;
    }
  },
};
