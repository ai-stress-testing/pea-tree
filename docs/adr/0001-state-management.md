# ADR 0001 — State management & the persistence seam

**Status**: accepted (sprint-7-26-20-27) · **Owner**: `backend/backend-architect`
**Reviewers**: `logicians/software-architect` (cross-MVP), `pm/ticket-workflow-steward` (board model)

## Context

The harness has two kinds of durable state: the **kanban board**
(board/column/card) and **groupchat run history** (thread/turn). Today it
runs entirely in the browser against a local Ollama — no server. The stated
trajectory is a hosted deployment on **AWS with Postgres**, with a **C++**
service in the hot path. We must build small now without painting the UI
into a corner that a hosted rewrite would have to undo.

The risk to avoid: UI components reaching into `localStorage` (or later
`fetch`) directly, so that "add persistence" or "move to Postgres" means
editing every view.

## Decision

**A single `Repository` interface is the persistence seam. The UI depends
only on it.**

- `web/src/lib/store/repository.ts` — the interface: `getBoard`,
  `saveBoard`, `listThreads`, `saveThread`, `deleteThread`, `clear`. Every
  method is **async** so a network-backed implementation is a drop-in; the
  local one just resolves immediately.
- `web/src/lib/store/local.ts` — the only implementation today:
  `LocalRepository`, backed by `localStorage` through a tiny `KvDriver`
  abstraction (so it is unit-testable with an in-memory driver and degrades
  where no `Storage` exists).
- `web/src/store.ts` — the reactive Vue state is a cache over the
  repository: it loads on `init()` and writes through on every mutation. No
  component touches storage.

**Aggregates are separate; the store is shared.** A kanban `Card` and a
groupchat `Turn` are distinct aggregates with distinct lifecycles, so they
are distinct types and distinct repository methods — not forced into one
table-shaped blob. A groupchat *turn* and a chat *message* share a shape
(the messaging MVP will unify them); a *card* does not, and is kept apart.

**Client-generated ids are the idempotency keys.** Cards use
`crypto.randomUUID()`; a run is `run-<timestamp>`. A retried create/move is
therefore a no-op on the same id — the property the hosted API will need to
honor unchanged when the same mutation arrives twice over the network.

## The scaling path (why this shape)

```
             today                          hosted (later)
  Vue store ──► Repository ◄── LocalRepo     Vue store ──► Repository ◄── RestRepo
                                localStorage                              │ HTTP
                                                                          ▼
                                                          API service (C++) ──► Postgres
```

Moving to AWS is **a new `Repository` implementation, not a UI change**:

1. Write `RestRepository implements Repository`, mapping each method to an
   HTTP call.
2. Stand up the API (the C++ service) + Postgres. The relational schema is a
   direct read of `store/types.ts`: `board`, `column`, `card`, `thread`,
   `turn` tables; the client ids become primary keys, preserving idempotency.
3. Swap the one line in `store.ts` (`__setRepository`) — behind auth/config.

Streaming groupchat turns are orthogonal: they already flow over the Ollama
HTTP API and are persisted per-turn via `saveThread`, so a hosted build
persists the same snapshots server-side.

## Consequences

- **Now**: zero backend to run; state survives reload; fully unit- and
  e2e-tested (`local.test.ts`, `store.kanban.test.ts`, `e2e/`).
- **Not now (accepted gaps)**: single-user, single-board, no auth, no
  cross-device sync, no server-side conflict resolution. All of these land
  with `RestRepository` + the API, and none require touching the views.
- **Constraint honored**: no persona hard-codes a store; the seam is the
  only thing that knows where bytes live.
