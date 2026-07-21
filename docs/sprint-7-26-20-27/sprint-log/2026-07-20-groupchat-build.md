# 2026-07-20 — Iterative groupchat: Vue+TS+Ollama build

**Session/agent**: main session (orchestrator).
**Issues touched**: #1, #5, #6.

```
run-id: 2026-07-20-groupchat-build
prompt: "typescript vue based harness for ollama models (interchangeable),
3 interfaces (Mermaid, Messaging, Kanban), messaging feels like Slack,
7B–30B model, use the roster agents in a pipeline, iterative groupchat first."
specs: docs/sprint-7-26-20-27/prd.md (tech stack locked),
       issue-specs/iterative-groupchat.md (new priority #1)
verdicts: vitest PASS (engine run: select→iterate→re-queue→synth terminates
          with accounting); vue-tsc PASS; vite build PASS
```

## Done
- Locked the tech stack in the PRD: TypeScript + Vue 3 (Vite), Ollama-only
  backend, models interchangeable via a tier→model map, groupchat first.
- Wrote `issue-specs/iterative-groupchat.md` as priority #1 (4 sub-issues:
  topology/contracts, Ollama client, engine, Slack-like UI) and added
  backlog row PT-6.
- Built the app under `web/`:
  - `scripts/build_personas.mjs` compiles `agents/**/agent.md` →
    `web/src/generated/personas.ts` (13 personas) — the pipeline loads
    the roster, so adding a role makes it selectable with no engine edit.
  - `lib/ollama.ts` — streaming `/api/chat` + `/api/tags` client with a
    tier→model resolver that falls back to an available model (never a
    hard-coded id; leak-free reader release on abort).
  - `lib/pipeline.ts` — the groupchat engine: participant selection
    (`@team/role` mentions ∪ LLM router), proximity/issue-#5 ordering,
    fresh-context iteration, `REQUEUE:` handling by Opsec/legal under a cap
    (queue always terminates), final synthesis, per-turn + per-run token
    accounting.
  - Slack-like Messaging UI (thread list, @-mention composer, live turn
    stream with role/cycle/token badges, distinct re-queue styling, pinned
    final plan), a working live Mermaid view, a Settings panel (Ollama
    origin, tier→model, re-queue cap), and a Kanban stub.
- Verified: `npm test` (scripted 3-cycle run with one re-queue) PASS,
  `npm run typecheck` clean, `npm run build` succeeds. `scripts/verify.py`
  10 PASS / 1 SKIP.

## Decisions
- Model interchange lives entirely in `lib/settings.ts` (tier→Ollama model);
  persona `model:` tiers (opus/sonnet/haiku) map to reason/build/cheap. No
  concrete model id anywhere in engine code — swapping is one setting.
- Run order follows issue #5 (PM opens; Opsec then legal last, both able to
  re-queue) rather than pure consultation-proximity — the two orderings
  disagree and the user's flow is explicit.
- Committed `generated/personas.ts` so typecheck/test run without a prebuild;
  it carries a "regenerate" banner.
- Mermaid rendered live (cheap, and a named interface); Kanban stubbed to
  keep effort on the priority-1 pipeline.

## Blocked / carried
- Kanban view is a stub (spec exists). Mermaid is render-only (no persist).
- The engine runs against a live local Ollama; unit test uses a mocked
  fetch. No end-to-end run against a real 7B–30B model captured yet — that's
  the next verify step (`ai/prompt-engineer` against the real tier).
