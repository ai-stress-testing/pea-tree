# 2026-07-21 — Kanban MVP, state-management seam, QA harness

**Session/agent**: main session (orchestrator).
**Issues touched**: #2, #5.

```
run-id: 2026-07-21-kanban-qa-state
prompt: "Build the kanban (b). Ensure good code: Playwright, tests, QA.
Clarify state management. Future: hosted AWS + Postgres + C++; for now small."
verdicts: vitest 12 PASS; Playwright 5 PASS; vue-tsc clean; vite build PASS
```

## Done
- **State-management seam** (the "how is state managed" answer). Introduced
  `web/src/lib/store/`: `types.ts` (persisted domain types), `repository.ts`
  (the async `Repository` interface — the seam), `local.ts`
  (`LocalRepository` over `localStorage` via a testable `KvDriver`),
  `seed.ts` (default board). `store.ts` is now a reactive cache that loads
  on `init()` and writes through the repository; no component touches
  storage. Documented in `docs/adr/0001-state-management.md` with the
  drop-in path to a `RestRepository` → C++ API → Postgres on AWS.
- **Kanban MVP** (issue #2): a persisted board — 4 ruled columns
  (explicit entry/exit rules, soft WIP limits surfaced not blocked),
  add/edit/delete cards, move between columns via keyboard-accessible nav
  buttons (deterministic + a11y) plus native drag-and-drop, issue-ref
  traceability, survives reload. Board seeds two cards tracing #5/#2.
- **QA harness**: Playwright wired to the pre-installed Chromium
  (`playwright.config.ts`, pinned binary, dev-server `webServer`). E2e:
  `e2e/kanban.spec.ts` (seed, add+persist-across-reload, move, WIP breach)
  and `e2e/messaging.spec.ts` (full groupchat against a **mocked Ollama** —
  streamed turns, a re-queue, pinned final, persisted history). Vitest
  units for the repository (`local.test.ts`) and kanban store
  (`store.kanban.test.ts`). `npm run qa` = typecheck + unit + e2e.
- **Bug the QA caught**: the groupchat UI never updated live because
  `startRun` mutated the raw thread object while Vue tracked the reactive
  proxy in `store.threads`. Fixed to mutate the proxy; the messaging e2e
  now proves turns stream and the final pins.

## Decisions
- Persistence is a seam (`Repository`), not a library choice. Local today;
  AWS/Postgres/C++ later is a new implementation + one `__setRepository`
  line, no UI churn (ADR 0001).
- Card/thread are separate aggregates; client-generated ids
  (`crypto.randomUUID`) are the idempotency keys the hosted API will honor.
- Card moves are driven by buttons/keyboard as the primary, testable path;
  native drag-and-drop is an untested enhancement (HTML5 DnD is flaky under
  automation).
- Kanban shows WIP breaches (red count) but never blocks a move — the board
  reflects reality rather than enforcing policy in the UI.

## Blocked / carried
- Mermaid is still render-only; messaging (issue #3) transport is the
  in-process pipeline, not yet a persisted realtime server (that arrives
  with `RestRepository`).
- No live end-to-end run against a real 7B–30B model captured in CI (e2e
  mocks Ollama by design); a manual smoke run against local Ollama is the
  next verify step for `ai/prompt-engineer`.
- Within-column card reordering isn't implemented (only cross-column moves
  + append); tracked for the kanban polish pass.
