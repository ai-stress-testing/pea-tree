# Backlog — Takt-Harness

One row per feature issue; the spec-driven PM (`agents/pm/project-manager`)
owns this table. Full specs live in `docs/issue-specs/`. Sub-issue
assignees and acceptance criteria are inside each spec.
Status: todo / in-progress / blocked / done.

**Frontend-role note:** the fixed stack is Vue 3 + TS (Constraint C4) but
the roster's only general frontend implementer is `frontend/react-dev`
(React-oriented). It is assigned as narrowest fit; every frontend ticket
is explicitly Vue 3 + TS. Flagged for the human — add a `frontend/vue-dev`
sibling if Vue work becomes durable (roster rule: one role is enough to
start a team).

| ID   | Item (issue-spec)                    | Priority | Assignee (parent)                     | Sprint            | Status |
|------|--------------------------------------|----------|---------------------------------------|-------------------|--------|
| TH-0 | Foundation: compose, SQLite, write-guard, agent client | 0 (blocks all) | `security/senior-secops`            | sprint-8-26-01-15 | todo   |
| TH-1 | Docs (split editor, sidebar, AI-assist) | 1        | `frontend/react-dev`                  | sprint-8-26-01-15 | todo   |
| TH-2 | Kanban (planning pipeline board)     | 2        | `frontend/react-dev`                  | sprint-8-26-01-15 | todo   |
| TH-3 | Agent-Queue (dashboard + retry engine) | 3      | `ai/multi-agent-systems-architect`    | sprint-8-26-01-15 | todo   |
| TH-4 | Zettlebucket (intake → queue)        | 4        | `backend/backend-dev`                 | sprint-8-26-01-15 | todo   |
| TH-5 | Chats (breakout rooms)               | 5        | `backend/realtime-collaboration-engineer` | sprint-8-26-01-15 | todo   |
