# Issue: Mermaid mvp

**Sprint**: sprint-7-26-20-27 · **Source**: `prd.md` §3
**Assignee (parent)**: `agents/frontend/react-dev`
**Goal**: let a converged plan (from the linear-iterations queue or a
human) express itself as a diagram — architecture sketches, the queue's
own topology, a kanban flow — embeddable wherever a card or a turn needs
one, with no silent failure on bad input.

## Spec

- A Mermaid source string renders to a diagram in a pane embeddable in a
  kanban card or a messaging turn.
- Invalid Mermaid source produces a visible, specific error state (which
  line/token failed), never a blank pane or a swallowed exception.
- Rendering happens client-side (no new backend dependency per the PRD's
  constraint) unless `backend/backend-architect` documents a reason
  server-side rendering is required.
- A rendered diagram is cacheable by source hash, so re-rendering an
  unchanged source is a no-op.

## Sub-issues

### 1. Render surface: architecture call
- **Assignee**: `agents/backend/backend-architect`
- **Scope**: decide client-side vs. server-side rendering and, if a
  backend dependency is genuinely needed, name it in an ADR.
- **Acceptance criteria**:
  - [ ] ADR states the decision and, if a new dependency is proposed,
        the specific problem client-side rendering can't solve.
  - [ ] Cache-by-source-hash strategy is specified.
- **Negative prompt** (do NOT):
  - Default to a server-side renderer without justifying it against the
    PRD's "no new dependency" constraint.
- **Verify**: ADR reviewed by `agents/logicians/software-architect`.

### 2. Diagram pane: design spec
- **Assignee**: `agents/frontend/designer`
- **Scope**: layout and states (rendering/rendered/error) for the
  diagram pane, and how the error state surfaces the failing
  line/token.
- **Acceptance criteria**:
  - [ ] Error state spec shows line/token-level detail, not a generic
        "invalid diagram" message.
  - [ ] Pane sizing/embedding behavior specified for both the card and
        turn contexts.
- **Negative prompt** (do NOT):
  - Write production component code.
- **Verify**: design spec reviewed and approved by
  `agents/pm/project-manager`.

### 3. Diagram pane implementation
- **Assignee**: `agents/frontend/react-dev`
- **Scope**: implement the render pane per sub-issues 1-2, embeddable in
  both the kanban card and the messaging turn view.
- **Acceptance criteria**:
  - [ ] A valid Mermaid source renders correctly in both embedding
        contexts.
  - [ ] An invalid source shows the specified error state, never a blank
        pane or an unhandled exception in the console.
  - [ ] Re-rendering an unchanged source is a cache hit, not a re-parse.
  - [ ] Verified in a running browser with at least one deliberately
        malformed source.
- **Negative prompt** (do NOT):
  - Add a new rendering dependency beyond what sub-issue 1 specified.
  - Modify the kanban card or messaging turn schema — embed into what
    already exists.
- **Verify**: `agents/testing/test-automation-engineer` E2E test covers a
  valid render and a malformed-source error state.

## Dependencies

- #1 blocks #3 (architecture call before implementation).
- #2 blocks #3 (design spec before implementation).
