# Issue: Create messaging mvp

**Sprint**: sprint-7-26-20-27 · **Source**: `prd.md` §2, §4
**Assignee (parent)**: `agents/backend/realtime-collaboration-engineer`
**Goal**: give the harness a thread/turn transport that doubles as a
human-readable chat and as the linear-iterations queue's turn-by-turn
delivery mechanism (issue #5), so a "fake groupchat" planning run is
observable as it happens.

## Spec

- A thread holds an ordered, durable log of turns; a turn carries
  `role` (which queue position or human produced it), `cycle` (position in
  the linear-iterations run), `body`, and `token_cost`.
- Turns deliver in strict cycle order over a resumable WebSocket/SSE
  transport; a client resumes from its last acknowledged sequence number,
  never replaying or dropping a turn.
- Every turn send is idempotent, keyed by a client-generated ID.
- Presence (who's watching a thread) is ephemeral/TTL'd, on a channel
  separate from the durable turn log.
- A re-queue (issue #5: opsec/legal sending the goal back) is visible in
  the thread as a turn referencing the cycle it re-queues to, not a
  silent jump.

## Sub-issues

### 1. Thread/turn schema + realtime contract
- **Assignee**: `agents/backend/backend-architect`
- **Scope**: the thread/turn schema and the WebSocket/SSE event contract
  (turn-sent, turn-delivered, presence-changed, re-queue-issued).
- **Acceptance criteria**:
  - [ ] Turn schema includes `role`, `cycle`, `token_cost`, and a
        client-generated idempotency key.
  - [ ] Re-queue is modeled as an explicit event type, not inferred from
        cycle-number gaps.
  - [ ] Contract states the resume/replay semantics on reconnect.
- **Negative prompt** (do NOT):
  - Implement the transport — this is the contract only.
  - Merge turn and presence state into one channel.
- **Verify**: contract doc reviewed by
  `agents/logicians/software-architect` and
  `agents/ai/multi-agent-systems-architect` (the contract must match the
  queue's own input/output contract from the linear-iterations design).

### 2. Realtime transport implementation
- **Assignee**: `agents/backend/realtime-collaboration-engineer`
- **Scope**: the resumable WebSocket/SSE transport delivering turns per
  sub-issue 1's contract.
- **Acceptance criteria**:
  - [ ] Every client tracks its last acknowledged sequence number and
        resumes from it on reconnect.
  - [ ] Every turn is idempotent, keyed by a client-generated ID; a
        duplicate send is a no-op.
  - [ ] Turns deliver in strict cycle order, never reordered or coalesced
        across a re-queue.
  - [ ] Tested against a connection killed mid-turn, not just localhost.
- **Negative prompt** (do NOT):
  - Trust a client timestamp for ordering.
  - Implement the chat UI itself.
- **Verify**: `agents/testing/test-automation-engineer` E2E test kills the
  connection mid-turn and asserts resume with no duplicate/dropped turns.

### 3. Chat/queue-turn thread view (design + implementation)
- **Assignee**: `agents/frontend/react-dev`
- **Scope**: the UI rendering a thread as human-readable chat, with each
  queue turn attributed to its role/cycle, and re-queue events shown
  distinctly.
- **Acceptance criteria**:
  - [ ] Every turn shows its producing role and cycle number.
  - [ ] A re-queue event is visually distinct from a normal turn.
  - [ ] Loading/empty/error states specified (`frontend/designer`) and
        implemented.
- **Negative prompt** (do NOT):
  - Invent a re-queue UX not specified by `frontend/designer`.
  - Touch the kanban or Mermaid MVP's components.
- **Verify**: `agents/pm/project-manager` acceptance sign-off against the
  design spec.

### 4. Security review of the transport
- **Assignee**: `agents/security/senior-secops`
- **Scope**: scan the transport and thread contents for secret/sensitive-
  data exposure before the messaging MVP ships (issue #5's Opsec seat,
  applied to this specific surface).
- **Acceptance criteria**:
  - [ ] Turn bodies are scanned for accidental secret leakage before
        persistence.
  - [ ] Standard controls (auth on the socket, rate limiting) are in
        place or explicitly deferred with an owner and date.
- **Negative prompt** (do NOT):
  - Redesign the transport contract — flag findings back to sub-issue 1's
    owner instead.
- **Verify**: findings documented, Critical/High findings have no open
  slide-to-later entries.

## Dependencies

- #1 blocks #2 and #3.
- #2 blocks #4 (nothing to scan until the transport exists).
