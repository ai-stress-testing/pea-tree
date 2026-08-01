# PRD — sprint-8-26-01-15 (Takt-Harness)

**User goal**: Ship a locally-hosted planning harness — a single
Dockerized web app with five interfaces (Docs, Kanban, Agent-Queue,
Zettlebucket, Chats) — that drives a local 30B-parameter model through
the Ges-Talt agent roster to help a human think a project plan through
before expensive engineering starts. Docs is the core value proposition
and the first thing to build; the other four support the planning
pipeline that feeds it.

**Out of scope** (this sprint):
- Agent-endpoint authentication tokens (named backlog item — SRS §4,
  PRD "Security Considerations"; deferred, not built now).
- Multi-user auth, accounts, or tenancy — single local operator assumed.
- CI/CD pipeline and production hardening beyond `docker-compose up
  --build` (implementation-plan §4.3 is a later sprint).
- Editing or authoring the Ges-Talt agent roster itself — it is
  read-only input (see Constraint C1).
- Any write path outside the `takt-harness/` tree (see Constraint C1).

## Requirements

Numbered, so issues can cite `prd.md §n`.

1. The application exposes five interfaces — Docs, Kanban, Agent-Queue,
   Zettlebucket, Chats — each reachable in the running web app.
2. Docs presents a split-editor view: a draggable divider between a
   left markdown edit pane (syntax highlighting, formatting toolbar) and
   a right live-preview pane that re-renders as the user types.
3. Docs auto-saves each open document every 30 seconds and on blur; no
   explicit "save" click is required to persist edits.
4. Docs preview renders standard markdown plus Mermaid diagrams, and
   sanitizes all rendered HTML so injected `<script>`/event-handler
   markup does not execute (no XSS).
5. Docs left sidebar lists projects, each expandable to its sprints; a
   user can create a new sprint from the UI, and within a sprint select
   any document from the fixed library named in PRD.md §5.
6. Docs supports an AI-assist path: a user highlights a passage and
   either deletes it or sends it to one or more selected agents (chosen
   from a data-list of roster roles) with a correction/consideration
   comment; the agent reply is returned to the editor.
7. Kanban shows a left column of unassigned Zettlebucket issues, allows
   assigning an issue to a project (dropdown or drag-and-drop), and moves
   issues through pipeline columns (e.g. In Review, Drafting, Approved,
   Implemented) with drag-and-drop reordering within and between columns;
   the board is horizontally scrollable.
8. Agent-Queue shows a real-time dashboard of queued agents with state
   (idle/processing/error), notes, and processing-speed metrics; a user
   can reassign agents, reorder the queue (drag-and-drop), pause/resume
   processing, and set line-item priority.
9. Agent-Queue retry policy: on an item error, retry up to 3× with
   exponential backoff; if still failing, skip to the next queue item;
   after 6 further failures the item is flagged for user intervention
   before proceeding.
10. Zettlebucket provides an issue-submission form (title, description,
    priority, tags) with pre-built templates (bug report, feature
    request, performance issue) and `Ctrl+Enter` submit; submitting
    routes the issue to the Agent-Queue.
11. Chats provides a left sidebar of teams (name, active-agent count,
    last-message timestamp) and per-team breakout rooms where agent
    messages render left / user messages render right, visually
    distinct; each room has persistent, searchable message history keyed
    to user-created checkpoints.
12. Every interface displays live agent-endpoint availability status and
    a clear error state when the endpoint is unreachable.
13. Agent calls go to an OpenAI-compatible `/v1` chat-completions
    endpoint at `host.docker.internal:1234`, with retry + exponential
    backoff on network failure (see §9 for queue-level policy).
14. All application state persists in SQLite stored in a named Docker
    volume, surviving container restarts.
15. The entire application builds and runs via `docker-compose up
    --build`.
16. No application code path writes to, creates in, or deletes from the
    `ges-talt/` tree; every write the app performs lands under the
    `takt-harness/` tree.

## Constraints

- **C1 — Hard invariant (security-critical).** Application code must
  NEVER write to, create under, or delete anything within `ges-talt/`;
  it is read-only input for agent definitions and context. ALL writes
  are scoped under the `takt-harness/` tree. This is non-negotiable and
  maps to acceptance criteria #1 and #2. Enforce it with a single
  filesystem write-guard that every persistence path routes through —
  not scattered per-call checks.
- **C2 — Agent endpoint.** OpenAI-compatible `/v1` chat-completions,
  reached from inside the container at `host.docker.internal:1234`.
  Models are interchangeable behind that contract. (PRD/SRS mentions of
  "127/v1" are superseded by this.)
- **C3 — Database.** SQLite in a named Docker volume (SRS §2.1). The
  lone "postgres" mention in PRD "Recommended Tech Stack" is a stray
  recommendation and is not adopted.
- **C4 — Stack.** FastAPI (Python) backend + Vue 3 (TypeScript)
  frontend, Dockerized via `docker-compose`. Frontend implementation
  tickets are Vue 3 + TS even though the general frontend implementer
  role is React-oriented (see backlog note).
- **C5 — Priority order.** Build in this order: (1) Docs, (2) Kanban,
  (3) Agent-Queue, (4) Zettlebucket, (5) Chats. Foundation
  (compose + SQLite layer + write-guard + endpoint client) precedes
  Docs because Docs depends on it.
- **C6 — Realtime transport.** Live-preview, queue, and chat updates use
  the app's own WebSocket channel between the Vue frontend and FastAPI
  backend; this is distinct from C2's HTTP agent endpoint. Do not route
  agent chat-completions over a WebSocket to `:1234`.

## Success criteria

Maps to the PRD's five acceptance criteria (AC1–AC5).

- [ ] **AC1 — No deletions/mods to Ges-Talt.** A test proves no code
      path modifies or deletes any file under `ges-talt/`; the
      write-guard rejects such paths (Constraint C1).
- [ ] **AC2 — Writes scoped to Takt-Harness.** Every document create,
      edit, and new-sprint operation writes only under `takt-harness/`;
      a test asserts a write targeting outside that tree is refused
      (Constraint C1).
- [ ] **AC3 — Docker Compose deployment.** `docker-compose up --build`
      brings the app up and it serves all five interfaces (§1, §15).
- [ ] **AC4 — Agent endpoint reachable.** From inside the container, the
      `/v1` endpoint at `host.docker.internal:1234` is reachable and a
      chat-completion round-trip succeeds; availability status reflects
      it (§12, §13).
- [ ] **AC5 — Docs split editor.** The draggable-divider split editor
      renders markdown in real time and auto-saves on blur and on the
      30-second timer (§2, §3).
