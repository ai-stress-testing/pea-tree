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

## Test / typecheck

```
npm test             # vitest — drives a scripted run against a mocked Ollama
npm run typecheck    # vue-tsc --noEmit
```

## Layout

```
src/
  lib/ollama.ts       Ollama client (streaming /api/chat, /api/tags, resolver)
  lib/settings.ts     tier→model map, re-queue cap, token target
  lib/pipeline.ts     the groupchat engine (select → iterate → re-queue → synth)
  lib/pipeline.test.ts
  store.ts            reactive UI state driven by pipeline events
  components/         Messaging (Slack-like), TurnCard, Settings, Mermaid, Kanban
  generated/personas.ts   compiled from ../agents (do not edit by hand)
```

Mermaid renders live. Kanban is stubbed pending its sprint slot
(`docs/sprint-7-26-20-27/issue-specs/kanban-mvp.md`).
