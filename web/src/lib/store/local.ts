import type { Repository } from "./repository";
import type { BoardData, Thread } from "./types";
import { seedBoard } from "./seed";

// Minimal key/value surface we need from localStorage — abstracted so the
// repository is unit-testable with an in-memory driver and degrades cleanly
// where no Storage exists (SSR, tests).
export interface KvDriver {
  getItem(key: string): string | null;
  setItem(key: string, value: string): void;
  removeItem(key: string): void;
}

class MemoryKv implements KvDriver {
  private m = new Map<string, string>();
  getItem(k: string) { return this.m.has(k) ? this.m.get(k)! : null; }
  setItem(k: string, v: string) { this.m.set(k, v); }
  removeItem(k: string) { this.m.delete(k); }
}

function defaultDriver(): KvDriver {
  try {
    if (typeof localStorage !== "undefined") return localStorage;
  } catch {
    /* access can throw in sandboxed contexts */
  }
  return new MemoryKv();
}

const BOARD_KEY = "pea-tree:board";
const THREADS_KEY = "pea-tree:threads";

/**
 * localStorage-backed Repository. "Build small": one board, run history as a
 * JSON array. Deliberately dumb — the interface is where the scaling story
 * lives, not this class.
 */
export class LocalRepository implements Repository {
  constructor(private kv: KvDriver = defaultDriver()) {}

  private read<T>(key: string): T | null {
    const raw = this.kv.getItem(key);
    if (!raw) return null;
    try {
      return JSON.parse(raw) as T;
    } catch {
      return null; // corrupt entry -> treat as absent, don't crash the app
    }
  }

  async getBoard(): Promise<BoardData> {
    const existing = this.read<BoardData>(BOARD_KEY);
    if (existing) return existing;
    const seeded = seedBoard();
    this.kv.setItem(BOARD_KEY, JSON.stringify(seeded));
    return seeded;
  }

  async saveBoard(data: BoardData): Promise<void> {
    this.kv.setItem(BOARD_KEY, JSON.stringify(data));
  }

  async listThreads(): Promise<Thread[]> {
    const all = this.read<Thread[]>(THREADS_KEY) ?? [];
    return all.sort((a, b) => b.createdAt - a.createdAt);
  }

  async saveThread(thread: Thread): Promise<void> {
    const all = this.read<Thread[]>(THREADS_KEY) ?? [];
    const i = all.findIndex((t) => t.id === thread.id);
    // Persist a settled snapshot: never leave a turn marked streaming on disk.
    const snapshot: Thread = {
      ...thread,
      turns: thread.turns.map((t) => ({ ...t, streaming: false })),
      finalStreaming: false,
    };
    if (i >= 0) all[i] = snapshot;
    else all.push(snapshot);
    this.kv.setItem(THREADS_KEY, JSON.stringify(all));
  }

  async deleteThread(id: string): Promise<void> {
    const all = this.read<Thread[]>(THREADS_KEY) ?? [];
    this.kv.setItem(THREADS_KEY, JSON.stringify(all.filter((t) => t.id !== id)));
  }

  async clear(): Promise<void> {
    this.kv.removeItem(BOARD_KEY);
    this.kv.removeItem(THREADS_KEY);
  }
}
