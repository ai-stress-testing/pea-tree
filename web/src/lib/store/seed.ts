import type { BoardData, Diagram } from "./types";

// The default board a fresh install starts with. Column entry/exit rules are
// explicit and checkable (pm/ticket-workflow-steward's charter) rather than
// implied, and seed cards trace back to real issues.
export function seedBoard(): BoardData {
  const boardId = "board-default";
  const now = Date.now();
  const col = (
    id: string,
    name: string,
    order: number,
    entryRule: string,
    exitRule: string,
    wipLimit: number | null,
  ) => ({ id, boardId, name, order, entryRule, exitRule, wipLimit });

  return {
    board: { id: boardId, name: "pea-tree", createdAt: now },
    columns: [
      col("col-backlog", "Backlog", 0,
        "Specced item with an issue ref", "Has an assignee + acceptance criteria", null),
      col("col-doing", "In Progress", 1,
        "Assignee started; typed branch opened", "PR opened, self-review done", 3),
      col("col-review", "Review", 2,
        "PR open + CI green", "Reality-checker PASS", 3),
      col("col-done", "Done", 3,
        "Issue closed as completed", "—", null),
    ],
    cards: [
      {
        id: "card-seed-1", boardId, columnId: "col-doing",
        title: "Iterative groupchat pipeline",
        body: "Vue+TS harness over Ollama: select → iterate → re-queue → synth.",
        issueRef: "#5", order: 0, createdAt: now, updatedAt: now,
      },
      {
        id: "card-seed-2", boardId, columnId: "col-backlog",
        title: "Kanban board MVP",
        body: "Board/column/card model with explicit column rules + issue traceability.",
        issueRef: "#2", order: 0, createdAt: now, updatedAt: now,
      },
    ],
  };
}

// One example diagram so the Mermaid interface isn't empty on first open.
export function seedDiagrams(): Diagram[] {
  const now = Date.now();
  return [
    {
      id: "diagram-seed-1",
      name: "Groupchat pipeline",
      source: `flowchart LR
  U[User message] --> R{Who is involved?}
  R -->|mentions ∪ router| Q[Ordered queue]
  Q --> PM[PM] --> AR[Architect] --> FE[Front-end]
  FE --> Op[Opsec] --> Lg[Legal]
  Op -. re-queue .-> AR
  Lg --> F[[Final plan + loop]]`,
      createdAt: now,
      updatedAt: now,
    },
  ];
}
