import type { BoardData, Thread } from "./types";

// The persistence seam. The UI depends only on this interface, never on how
// bytes are stored. Today the sole implementation is LocalRepository
// (localStorage); a hosted deployment swaps in a RestRepository that hits an
// API over Postgres — same methods, no UI change (ADR 0001).
//
// Every method is async so a network-backed implementation is a drop-in: the
// local one just resolves immediately.
export interface Repository {
  /** The single board + its columns + cards. Seeds a default on first use. */
  getBoard(): Promise<BoardData>;
  saveBoard(data: BoardData): Promise<void>;

  /** Persisted groupchat run history, newest first. */
  listThreads(): Promise<Thread[]>;
  saveThread(thread: Thread): Promise<void>;
  deleteThread(id: string): Promise<void>;

  /** Wipe everything (used by tests and a "reset" affordance). */
  clear(): Promise<void>;
}
