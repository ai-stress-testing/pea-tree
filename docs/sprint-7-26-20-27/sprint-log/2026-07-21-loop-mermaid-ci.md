# 2026-07-21 — Execution-loop display, Mermaid interface, CI

**Session/agent**: main session (orchestrator).
**Issues touched**: #4, #5, #6.

```
run-id: 2026-07-21-loop-mermaid-ci
prompt: "Add the CI workflow (option a). Complete the Mermaid interface.
Update the final meta-prompt to add a loop display (parallel spins,
handoffs, a lint gate that fails back to an agent / passes on, test, prep
PR) — so the run has the prompt and a loop."
verdicts: vitest 20 PASS; Playwright 8 PASS; vue-tsc clean; vite build PASS
```

## Done
- **CI (option a)**: `.github/workflows/web-qa.yml` runs
  typecheck + unit + Playwright e2e on push/PR (`npm run qa`), installing
  Chromium on the runner. `playwright.config.ts` now uses the sandbox's
  pinned Chromium only when it exists and falls back to Playwright's managed
  browser on CI.
- **Execution-loop display** (the "prompt + a loop" ask). The final
  synthesis meta-prompt now produces the plan **and** an execution loop:
  agents spun in parallel, sequential handoffs, a **lint gate** (fail →
  loop back to the responsible agent, pass → continue), a **test gate**,
  then **prep PR**. `lib/loop.ts` defines the loop spec, a deterministic
  `defaultLoop(participants)`, a `parseLoopSpec` for a model-emitted
  ```loop block, and `compileLoopToMermaid` (always valid Mermaid —
  failures render as dotted loop-back edges). The engine emits a `loop`
  event; Messaging renders it under the final plan. If the model's block is
  missing/invalid, the default loop is used — the diagram is never broken.
- **Mermaid interface completed**: extracted a reusable `MermaidDiagram.vue`
  (source prop, error state, source-hash cache) used by both the Mermaid
  view and the loop display. The view is now a **persisted multi-diagram
  manager** (list / new / rename / edit / delete, live render, visible
  error state) backed by the Repository (`Diagram` type + `listDiagrams` /
  `saveDiagram` / `deleteDiagram`), seeded with one example.
- **Tests**: `lib/loop.test.ts` (default loop shape, Mermaid compile,
  parse/strip, malformed handling), `store.diagrams.test.ts` (CRUD +
  persistence), pipeline test asserts a loop is emitted, messaging e2e
  asserts the loop diagram renders, new `e2e/mermaid.spec.ts` (render,
  edit+persist, invalid→error). 20 unit + 8 e2e all green.

## Decisions
- The loop is **compiled deterministically** from a spec, not free-text
  Mermaid from a 7B model — the model supplies structure (or the default
  does), code guarantees the diagram renders.
- Loop failures (lint/test) are dotted edges back to the responsible agent;
  success edges are solid — the "and a loop" the prompt asked for.
- `MermaidDiagram` renders client-side (no new dep beyond mermaid, already
  present) per the mermaid-mvp spec's no-new-backend constraint.

## Blocked / carried
- The model-emitted ```loop block is best-effort on small models; the
  deterministic default is the reliable path and what CI exercises.
- Messaging (issue #3) is still the in-process pipeline, not a persisted
  realtime server (arrives with `RestRepository`).
- No live run against a real 7B–30B model in CI (e2e mocks Ollama by
  design).
