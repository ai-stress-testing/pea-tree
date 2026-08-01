# Issue: Foundation — compose, SQLite layer, write-guard, agent client

**Sprint**: sprint-8-26-01-15 · **Source**: `prd.md` §13, §14, §15, §16 (Constraints C1–C6)
**Assignee (parent)**: `security/senior-secops`
**Goal**: Stand up the runtime scaffold every feature depends on — the
container, the SQLite persistence layer, the single filesystem write-guard
that enforces the hard invariant, and the OpenAI-compatible agent client —
so no feature has to re-solve deployment, persistence, path-safety, or
endpoint retry. Owned by secops because the write-guard (Constraint C1) is
security-critical and is acceptance criteria AC1/AC2.

## Spec

When this issue closes:
- `docker-compose up --build` starts the app; frontend and backend are
  reachable and SQLite persists in a named volume across restart (§14, §15).
- Exactly one write-guard module mediates every filesystem write. Given
  any target path, it resolves the real (symlink-followed) absolute path
  and permits the write only if it lies under the `takt-harness/` tree;
  it refuses (raises, no write) any path under `ges-talt/` or outside
  `takt-harness/`. No persistence code writes to disk except through it.
- The agent client posts to `host.docker.internal:1234/v1/chat/completions`
  (OpenAI-compatible), reachable from inside the container, and retries
  transient network/5xx failures with exponential backoff (Constraint C2).
- The container filesystem mounts `ges-talt/` read-only.

## Sub-issues

### 1. Docker Compose + container images
- **Assignee**: `ci/containerization-engineer`
- **Scope**: `docker-compose.yml`, backend + frontend Dockerfiles, named
  SQLite volume, `host.docker.internal` host-gateway mapping, `ges-talt/`
  mounted read-only, `takt-harness/` mounted read-write.
- **Acceptance criteria**:
  - [ ] `docker-compose up --build` exits 0 and serves the frontend and
        the FastAPI backend.
  - [ ] The SQLite volume is named and its data survives
        `docker-compose down && up` (no `-v`).
  - [ ] `ges-talt/` is mounted `:ro`; a shell in the container cannot
        `touch ges-talt/probe`.
  - [ ] From inside the container, `host.docker.internal:1234` resolves.
- **Negative prompt** (do NOT):
  - Do NOT add a Postgres/MySQL service or any DB other than SQLite (C3).
  - Do NOT mount `ges-talt/` read-write "for convenience".
  - Do NOT hardcode secrets or an agent auth token into compose (out of scope).
  - Do NOT implement application logic here — infra only.
- **Verify**: `docker-compose up --build`, then in-container `touch ges-talt/x` fails and `getent hosts host.docker.internal` resolves.

### 2. SQLite persistence layer + schema
- **Assignee**: `backend/backend-dev`
- **Scope**: SQLite connection/session management and the schema/migrations
  for projects, sprints, documents, issues, kanban columns/cards, queue
  items, chat rooms/messages/checkpoints. All disk writes route through
  sub-issue #3's guard.
- **Acceptance criteria**:
  - [ ] Tables for every entity above exist and are created on first boot.
  - [ ] Every function that writes a file (e.g. document body) calls the
        write-guard (#3) and has no direct open-for-write bypassing it.
  - [ ] A round-trip test writes and reads back a document.
- **Negative prompt** (do NOT):
  - Do NOT open any file for write without going through the write-guard.
  - Do NOT read agent definitions by copying them into `takt-harness/`;
    read `ges-talt/` in place, read-only.
  - Do NOT add an ORM-driven second DB engine; SQLite only.
- **Verify**: pytest round-trip test passes; grep shows no `open(...,'w')`
  or equivalent outside the guard module.
- **Depends on**: #3 (guard must exist to be called).

### 3. Filesystem write-guard (hard invariant) — SECURITY-CRITICAL
- **Assignee**: `security/senior-secops`
- **Scope**: One module exposing a single "resolve + authorize + write"
  path-safety function enforcing Constraint C1.
- **Acceptance criteria**:
  - [ ] Resolves symlinks and `..` before the boundary check (canonical
        real path), so `takt-harness/../ges-talt/x` is refused.
  - [ ] Permits a write under `takt-harness/`; refuses (raises, no write)
        any path under `ges-talt/` or outside `takt-harness/`.
  - [ ] Refuses absolute paths, relative-escape paths, and symlinked paths
        that resolve outside `takt-harness/`.
  - [ ] Unit tests cover: normal write, `ges-talt/` target, `..` escape,
        symlink escape, absolute-path escape — all refused except normal.
- **Negative prompt** (do NOT):
  - Do NOT implement per-feature ad-hoc path checks; this is the ONE guard.
  - Do NOT rely on string prefix matching before canonicalization
    (defeated by `..`/symlinks).
  - Do NOT add a config flag that disables the guard.
- **Verify**: pytest guard suite passes; falsifier (#5) cannot construct a
  write outside `takt-harness/`.

### 4. Agent endpoint client (OpenAI-compatible + retry)
- **Assignee**: `ai/ai-engineer`
- **Scope**: A backend client for `host.docker.internal:1234/v1`
  chat-completions with retry + exponential backoff and an availability
  probe used by the per-feature status indicators (§12, §13).
- **Acceptance criteria**:
  - [ ] Sends OpenAI-shaped chat-completion requests and parses responses;
        model name is configurable (interchangeable models, C2).
  - [ ] Transient failures retry with exponential backoff; a bounded,
        recorded final failure surfaces as "unavailable", not a crash.
  - [ ] An availability probe returns reachable/unreachable within the
        SRS §5 2-second budget.
- **Negative prompt** (do NOT):
  - Do NOT hardcode a model name as the only option.
  - Do NOT implement the Agent-Queue retry/skip/intervention policy here —
    that is TH-3's queue engine; this is transport-level retry only.
  - Do NOT open a WebSocket to `:1234` (C6 — endpoint is HTTP).
- **Verify**: unit test with a stubbed endpoint proves backoff sequence and
  unreachable-path handling.

### 5. Adversarial verification of the invariant
- **Assignee**: `logicians/falsifier`
- **Scope**: Presume the write-guard (#3) is bypassable; construct the
  disproof (a code path or input that writes/deletes under `ges-talt/` or
  outside `takt-harness/`).
- **Acceptance criteria**:
  - [ ] Delivers either a concrete bypass (→ FAIL back to #3) or a written
        statement that no bypass was found across enumerated vectors
        (symlink, `..`, absolute path, TOCTOU, alternate write API).
- **Negative prompt** (do NOT):
  - Do NOT fix code — report only (read-only role).
  - Do NOT rubber-stamp; enumerate the vectors checked.
- **Verify**: falsifier report attached to the issue; any bypass reopens #3.

## Dependencies

`#3 blocks #2` · `#3 blocks #5` · `#1 blocks integration boot` ·
`#1, #2, #3, #4 block TH-1..TH-5` · `#5 gates AC1/AC2 sign-off`.
