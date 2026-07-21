# Backlog

Rows are added by the spec-driven PM (`agents/pm/project-manager`); one row
per issue. Status: todo / in-progress / blocked / done.

| ID | Item | Assignee (agent) | Sprint | Status | Issue |
|---|---|---|---|---|---|
| PT-1 | Adopt Ges-Talt agent org + docs conventions into pea-tree (roster, scripts, templates) | main session | sprint-7-26-20-27 | done | [#6](https://github.com/ai-stress-testing/pea-tree/issues/6) |
| PT-6 | **Iterative groupchat pipeline (priority #1)**: Vue+TS harness over Ollama — select participants → iterate personas (fresh context) → re-queue → synthesize; Slack-like messaging UI | `agents/ai/multi-agent-systems-architect` (+ `backend/realtime-collaboration-engineer`, `ai/prompt-engineer`, `frontend/react-dev`) | sprint-7-26-20-27 | in-progress | [#5](https://github.com/ai-stress-testing/pea-tree/issues/5) |
| PT-2 | Kanban MVP: board/column/card model, persisted board (localStorage repo), move/edit/WIP, unit + Playwright e2e | `agents/frontend/react-dev` (+ `backend/backend-architect`, `testing/test-automation-engineer`) | sprint-7-26-20-27 | in-progress | [#2](https://github.com/ai-stress-testing/pea-tree/issues/2) |
| PT-7 | State management: `Repository` persistence seam (local now, REST/Postgres later) + ADR 0001; unit + e2e | `agents/backend/backend-architect` (+ `logicians/software-architect`) | sprint-7-26-20-27 | done | [#2](https://github.com/ai-stress-testing/pea-tree/issues/2) |
| PT-8 | QA harness: Playwright e2e (kanban + mocked-Ollama groupchat), vitest units, `npm run qa` | `agents/testing/test-automation-engineer` | sprint-7-26-20-27 | done | [#2](https://github.com/ai-stress-testing/pea-tree/issues/2) |
| PT-3 | Messaging MVP: thread/turn schema, realtime transport, chat/queue-turn view, security review | `agents/backend/realtime-collaboration-engineer` (+ `backend/backend-architect`, `frontend/react-dev`, `security/senior-secops`) | sprint-7-26-20-27 | todo | [#3](https://github.com/ai-stress-testing/pea-tree/issues/3) |
| PT-4 | Mermaid MVP: render-surface architecture call, diagram pane design + implementation | `agents/frontend/react-dev` (+ `backend/backend-architect`, `frontend/designer`) | sprint-7-26-20-27 | todo | [#4](https://github.com/ai-stress-testing/pea-tree/issues/4) |
| PT-5 | Linear-iterations queue design (topology, token budget, re-queue rule) | `agents/ai/multi-agent-systems-architect` | sprint-7-26-20-27 | todo | [#5](https://github.com/ai-stress-testing/pea-tree/issues/5) |
