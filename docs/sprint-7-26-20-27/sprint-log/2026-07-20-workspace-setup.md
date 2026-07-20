# 2026-07-20 — Adopt Ges-Talt workspace, spec the three MVPs

**Session/agent**: main session (orchestrator role, per Ges-Talt's
`agents/ORCHESTRATION.md`).
**Issues touched**: #1, #2, #3, #4, #5, #6.

```
run-id: 2026-07-20-workspace-setup
prompt: "Based on the 6 issues provided setup the workspace with my gestalt
agents and build specs for the mvps."
agents: main session only (docs/roster authored directly, no subagents spawned)
specs: docs/sprint-7-26-20-27/prd.md, issue-specs/kanban-mvp.md,
       issue-specs/messaging-mvp.md, issue-specs/mermaid-mvp.md
verdicts: n/a — no implementation shipped this run, scripts/verify.py all
          PASS/SKIP on the new scaffold
commits: (see this branch's history)
```

## Done
- Read all 6 open pea-tree issues (#1 vision, #2 kanban, #3 messaging, #4
  Mermaid, #5 linear-iterations queue, #6 harness framing) as the sprint's
  source of truth.
- Adopted the Ges-Talt docs/scripts scaffold: `scripts/{init_docs,
  build_index,build_repo_index,verify,audit_skills,credit,verify_comms}.py`,
  `scripts/verifiers/*`, `scripts/models.toml`, `docs/templates/*`,
  `docs/{branching,model-tiers,depth-packs,credit,feedback-loop}.md`,
  `agents/{README,ORCHESTRATION,WORKFLOW,COMMS,skills-policy}.md`,
  `agents/TEMPLATE/`, and the `lint-agents` CI workflow.
- Curated and wrote a 13-role, 8-team roster tailored to this project
  (not a wholesale port of Ges-Talt's 105 roles): `pm/project-manager`,
  `pm/ticket-workflow-steward`, `ai/multi-agent-systems-architect`,
  `ai/prompt-engineer`, `backend/backend-architect`,
  `backend/realtime-collaboration-engineer`, `frontend/react-dev`,
  `frontend/designer`, `logicians/software-architect`,
  `logicians/falsifier`, `testing/test-automation-engineer`,
  `security/senior-secops`, `legal/product-counsel` — each maps onto
  issue #5's named queue seats (PM/architect/front-end/consultant/Opsec/
  legal) plus the verdict loop's static + empirical review roles.
- Wrote `docs/enterprise.md` (Tiering/Ontology/Taxonomy/Semantics) for
  pea-tree specifically, naming the Board/Card/Thread/Turn/Diagram
  ontology and the linear-iterations vocabulary.
- Wrote the sprint PRD and three issue specs (kanban, messaging, Mermaid),
  each decomposed into granular, assigned, acceptance-criteria-bearing
  sub-issues with negative prompts, per `docs/templates/issue-spec.md`.
- Filed the specs' sub-issues under GitHub issues #2/#3/#4 and added
  backlog rows PT-1..PT-5.
- `python3 scripts/verify.py`: 9 PASS, 0 FAIL, 2 SKIP (ledger and
  tools-baseline SKIP cleanly since no runs/tool-grants exist yet to
  compare against — not fabricated to force a PASS).

## Decisions
- Roster is intentionally a curated subset, not a copy of Ges-Talt's full
  roster — CLAUDE.md documents this explicitly so a later session doesn't
  "fix" it by bulk-importing the other ~90 roles.
- `ai/multi-agent-systems-architect` owns the linear-iterations queue's
  topology/token-budget/re-queue design; `pm/project-manager` does not
  design the queue itself, only decomposes goals against it.
- Backend schema is one shared store across kanban/messaging/Mermaid
  where entities actually overlap (a queue turn *is* a message), kept
  separate where they don't — `backend/backend-architect`'s call, recorded
  as an ADR obligation in the messaging-mvp spec rather than decided here.
- `scripts/tools-baseline.json` was snapshotted intentionally
  (`build_index.py --update-tools-baseline`) against this initial roster,
  not left absent.

## Blocked / carried
- No implementation has started — this run is planning/scaffolding only,
  per the PRD's own success criteria. Kanban/messaging/Mermaid
  implementation sub-issues are `todo` in the backlog, ready for their
  assigned agents.
- `docs/agent-ledger.jsonl` doesn't exist yet (correctly SKIPs the
  `ledger_wellformed` verifier) — starts once a real agent run produces a
  row to log.
