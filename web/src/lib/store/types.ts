// Persisted domain types — the single source of truth for what the harness
// stores. Kept in its own module so both the reactive store and the
// Repository depend on it without a cycle.
//
// State strategy (see docs/adr/0001-state-management.md): the UI never talks
// to storage directly. It reads/writes a `Repository` (lib/store/repository.ts)
// whose only implementation today is localStorage-backed (build small). The
// same interface is what a future REST client over a Postgres/C++ service
// implements — so scaling out is a new Repository, not a UI rewrite.

// ---- Kanban ----------------------------------------------------------------

export interface Board {
  id: string;
  name: string;
  createdAt: number;
}

export interface Column {
  id: string;
  boardId: string;
  name: string;
  order: number;
  /** the checkable rule a card must meet to enter this column */
  entryRule: string;
  /** the checkable rule a card must meet to leave this column */
  exitRule: string;
  /** soft WIP limit; over-limit is surfaced, not blocked */
  wipLimit: number | null;
}

export interface Card {
  id: string;
  boardId: string;
  columnId: string;
  title: string;
  body: string;
  /** traceability back to a tracked issue, e.g. "PT-2" or "#5" */
  issueRef: string;
  /** sort order within its column */
  order: number;
  createdAt: number;
  updatedAt: number;
}

export interface BoardData {
  board: Board;
  columns: Column[];
  cards: Card[];
}

// ---- Mermaid ---------------------------------------------------------------

export interface Diagram {
  id: string;
  name: string;
  source: string;
  createdAt: number;
  updatedAt: number;
}

// ---- Groupchat runs (persisted history) ------------------------------------

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

export interface RunTotals {
  tokens: number;
  cycles: number;
  requeues: number;
}

export interface Thread {
  id: string;
  goal: string;
  participants: string[];
  turns: UiTurn[];
  final: string;
  finalStreaming: boolean;
  /** Mermaid source for the execution-loop diagram emitted by synthesis. */
  loopMermaid: string;
  totals: RunTotals | null;
  status: ThreadStatus;
  notices: string[];
  createdAt: number;
}
