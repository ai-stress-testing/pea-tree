# PM Team

Owns planning, sequencing, and tracking of work across teams — never the
implementation itself. Every role here is Read/Grep/Glob (+Write for
roles whose deliverable is a document). No role on this team gets Edit or
Bash: a bad plan should never be able to turn into a bad edit.

`project-manager` is the **spec-driven** entry point: it decomposes a
user goal against the current sprint's `docs/sprint-*/prd.md` and
`user-journeys/`, producing issues and granular sub-issues (one
deliverable, one owner) that each carry an assignee from
`agents/INDEX.md`, checkable acceptance criteria, and a negative prompt,
per `docs/templates/issue-spec.md`.

`ticket-workflow-steward` is the narrow specialist: it owns branch/commit/
PR traceability and the kanban MVP's own column/state model (issue #2).

Which sign-offs ride to the human vs. stay with the PM personally (spec
ambiguity, cross-team conflict, scope changes, retry-cap escalations) is
defined in `agents/WORKFLOW.md`, not repeated here.

## Roles

| Role | Model | Tools | One-liner |
|---|---|---|---|
| [project-manager](project-manager/) | opus | Read, Grep, Glob, Write (docs-only), Task tools, GitHub issue tools | Spec-driven: decomposes a goal against sprint docs into issues + granular sub-issues, each with assignee, acceptance criteria, and negative prompt. |
| [ticket-workflow-steward](ticket-workflow-steward/) | sonnet | Read, Grep, Glob, Write | Enforces ticket-linked branch/commit/PR conventions and owns the kanban MVP's column/WIP-limit model. |
