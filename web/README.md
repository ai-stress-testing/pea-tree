# pea-tree web — Vue + TS + Ollama groupchat harness

The harness front-end. Three interfaces (Messaging, Mermaid, Kanban); the
**iterative groupchat** is the priority-1 feature and is fully wired.

## What the groupchat does

`message → who is involved → iterate the involved personas → final result`

1. You post a goal in the Slack-like Messaging view.
2. Participants are selected: explicit `@team/role` mentions ∪ an LLM router
   over the roster, ordered per `agents/ORCHESTRATION.md` proximity.
3. Each involved persona is prompted **in a fresh context** seeded with the
   goal + a digest of prior turns, and streams its turn in.
4. `security/senior-secops` (Opsec) and `legal/product-counsel` may emit
   `REQUEUE: <team/role>` to send the goal back to an earlier agent, up to a
   cap — so the queue always terminates.
5. The orchestrator synthesizes a final plan. Token cost + cycle count are
   reported per turn and per run.

Personas come from `../agents/**/agent.md`, compiled to
`src/generated/personas.ts` by `scripts/build_personas.mjs` — add a role in
`agents/` and it becomes selectable with no code change.

## Prerequisites

- [Ollama](https://ollama.com) running locally, with a 7B–30B model pulled:
  ```
  ollama pull qwen2.5:7b      # cheap tier + router
  ollama pull qwen2.5:14b     # build tier (optional)
  ollama pull qwen2.5:32b     # reason tier + synthesis (optional)
  ```
  Any pulled model works — set the tier→model map in **Settings**. A tier
  whose model isn't pulled falls back to an available one with a notice.
- Node 20+.

## Run

```
cd web
npm install
npm run dev          # regenerates personas, starts Vite on :5173
```

Vite proxies `/ollama` → `http://localhost:11434` (see `vite.config.ts`), so
the browser isn't blocked by CORS. Point elsewhere with
`OLLAMA_ORIGIN=http://host:11434 npm run dev` or the Settings panel.

## Test / typecheck / QA

```
npm run typecheck    # vue-tsc --noEmit
npm test             # vitest — pipeline + repository + kanban store units
npm run test:e2e     # Playwright — kanban + groupchat (mocked Ollama), no live model needed
npm run qa           # all three
```

Playwright uses the environment's pre-installed Chromium (see
`playwright.config.ts`; override with `PW_CHROMIUM=/path/to/chrome`). The
groupchat e2e mocks the Ollama HTTP API, so QA needs no running model.

## State management

The UI never touches storage directly. It reads/writes a **`Repository`**
(`src/lib/store/repository.ts`) — the persistence seam. Today the only
implementation is `LocalRepository` (localStorage); a hosted build swaps in
a `RestRepository` over a Postgres/C++ service with no UI change. See
`docs/adr/0001-state-management.md`. Board and run history survive reload.

## Layout

```
src/
  lib/ollama.ts        Ollama client (streaming /api/chat, /api/tags, resolver)
  lib/settings.ts      tier→model map, re-queue cap, token target
  lib/pipeline.ts      the groupchat engine (select → iterate → re-queue → synth)
  lib/store/           types · repository (seam) · local (localStorage) · seed
  store.ts             reactive cache over the repository; driven by pipeline events
  components/          Messaging (Slack-like), TurnCard, Settings, Mermaid, Kanban
  generated/personas.ts    compiled from ../agents (do not edit by hand)
e2e/                   Playwright specs (kanban, messaging)
```

Mermaid renders live. Kanban is a fully persisted board (columns with
explicit entry/exit rules + WIP limits, move/edit/delete, issue-ref
traceability).
