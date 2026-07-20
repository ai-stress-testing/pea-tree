# Issue: Create kanban mvp

**Sprint**: sprint-7-26-20-27 · **Source**: `prd.md` §1
**Assignee (parent)**: `agents/frontend/react-dev`
**Goal**: give the harness a board where a plan's tickets live and move
through a visible, ruled state machine, so a converged linear-iterations
run has somewhere to land as trackable work.

## Spec

- A board has an ordered list of columns; each column has a name and a
  stated entry/exit rule (`pm/ticket-workflow-steward`).
- A card has: title, an issue-ID reference (traces to a GitHub issue or a
  `PT-<n>` backlog row), current column, and a created/updated timestamp.
- Moving a card between columns is a single atomic operation; an
  in-flight move is never left in an ambiguous state on a dropped
  connection.
- The board renders default/loading/empty/error states for the column
  list and for an individual card.

## Sub-issues

### 1. Column/card data model + API contract
- **Assignee**: `agents/backend/backend-architect`
- **Scope**: the board/column/card schema and the REST/event contract for
  create-card, move-card, list-board.
- **Acceptance criteria**:
  - [ ] Schema distinguishes column *definition* (name, order, rule) from
        column *membership* (which cards are in it now).
  - [ ] Every mutating endpoint documents its idempotency key.
  - [ ] ADR states why this schema is shared with (or separate from) the
        messaging MVP's thread/turn model.
- **Negative prompt** (do NOT):
  - Implement the endpoints — this sub-issue is the contract, not the
    code.
  - Introduce a second persistence store; use whatever
    `backend-architect` already chose for the harness.
- **Verify**: ADR + schema doc exist under `docs/`; reviewed by
  `agents/logicians/software-architect` before implementation starts.

### 2. Kanban board design spec
- **Assignee**: `agents/frontend/designer`
- **Scope**: layout, column/card visual states, and the entry/exit rule
  copy shown in the UI for each column.
- **Acceptance criteria**:
  - [ ] Every column's entry/exit rule is stated as UI copy, not just an
        internal doc.
  - [ ] Loading/empty/error states are specified for both the board and
        an individual card.
  - [ ] Keyboard-operable card move is specified (not just drag-and-drop).
- **Negative prompt** (do NOT):
  - Write production component code.
  - Invent a new visual language; reuse whatever design-system patterns
    already exist in the repo.
- **Verify**: design spec doc reviewed and approved by
  `agents/pm/project-manager`.

### 3. Board + card implementation
- **Assignee**: `agents/frontend/react-dev`
- **Scope**: the React implementation of the board, wired to sub-issue 1's
  contract and sub-issue 2's spec.
- **Acceptance criteria**:
  - [ ] A card can be created, moved through every defined column, and
        traced back to its issue ID in the running app.
  - [ ] All states from sub-issue 2 are implemented, not just the happy
        path.
  - [ ] Verified in a running browser, including a card move interrupted
        by a dropped connection.
- **Negative prompt** (do NOT):
  - Add client-side state management beyond what moving/listing cards
    requires.
  - Touch the messaging or Mermaid MVP's components.
- **Verify**: `agents/testing/test-automation-engineer` E2E test for
  create → move-through-every-column → trace-to-issue-ID passes.

### 4. Empirical verification
- **Assignee**: `agents/testing/test-automation-engineer`
- **Scope**: E2E coverage for the board's integration risk: card move
  under a killed connection, and a card's issue-ID trace.
- **Acceptance criteria**:
  - [ ] A test exists that kills the connection mid-move and asserts no
        ambiguous card state on reconnect.
  - [ ] No `waitForTimeout`/hard sleep in the new suite.
- **Negative prompt** (do NOT):
  - Write unit tests for logic better covered lower in the pyramid.
- **Verify**: `python3` test run is green in CI; failure artifacts
  (trace/screenshot) wired for the new suite.

## Dependencies

- #1 blocks #3 (contract before implementation).
- #2 blocks #3 (design spec before implementation).
- #3 blocks #4 (implementation before its E2E coverage).
