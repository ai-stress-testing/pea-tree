# Enterprise Doc — pea-tree

This doc UPDATES OVER TIME. The spec-driven PM (`agents/pm/project-manager`)
classifies new work against it during decomposition and extends it when a
decomposition reveals a concept, tier, class, or term that isn't here yet.
Stale entries are deleted, not preserved — this is a living reference, not
an append-only log.

13 agents total (`agents/INDEX.md`).

## Tiering

The strategic / tactical / operational layers of the project: what
decides, what plans, what executes.

- **Strategic** — the human requester + `pm/project-manager` (what the
  harness is *for*: cheap-model planning before expensive-model
  engineering, issue #1).
- **Tactical** — the linear-iterations queue (issue #5): the ordered
  persona sequence (PM → architect → front-end → consultant → Opsec →
  legal) that turns a goal into a converged plan, designed by
  `ai/multi-agent-systems-architect`.
- **Operational** — the implementers per MVP: `backend/`, `frontend/`,
  `testing/`, executing what the queue converged on.

## Ontology

- **Board** —(has many)→ **Column** —(has many)→ **Card**
- **Card** —(cites)→ **Issue** (the tracked GitHub issue it traces back to)
- **Thread** —(has many, ordered)→ **Turn**
- **Turn** —(produced by)→ **queue position** (a persona in the
  linear-iterations sequence) —(carries)→ **token_cost**
- **Diagram** —(rendered from)→ **Mermaid source** —(embedded in)→
  **Card** or **Turn**
- **Queue run** —(bounded by)→ **re-queue cap** (issue #5: opsec/legal may
  send a goal back to an earlier position, up to the cap, before forced
  termination)

## Taxonomy

- MVP
  - Kanban (issue #2)
  - Messaging (issue #3)
  - Mermaid (issue #4)
- Agent team
  - pm, ai, backend, frontend, logicians, testing, security, legal
- Issue class
  - mvp — a minimal-viable surface (kanban/messaging/mermaid)
  - harness — the linear-iterations queue and its orchestration machinery
  - vision — foundational framing (issue #1, #6), not directly actionable

## Semantics

- **Linear iterations** — the queue described in issue #5: an ordered set
  of agent personas, each running in a brand-new context window seeded
  with the initial goal plus the prior agent's output, producing a
  paragraph/list of goals from their expertise; context grows roughly
  linearly, target ~500-1000 tokens/cycle.
- **Turn** — one queue position's single contribution to a run; the unit
  the messaging MVP transports.
- **Re-queue** — opsec or legal appending the goal back onto an earlier
  queue position instead of letting it proceed, per issue #5.
- **Harness** — the combination of code, skills, and agents (issue #6)
  that makes the linear-iterations queue runnable end to end.
