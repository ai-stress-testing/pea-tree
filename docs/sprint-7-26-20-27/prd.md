# PRD — sprint-7-26-20-27

**User goal**: Stop wasting expensive-model tokens on imperfect plans. Ship
a mock messaging platform and a kanban board so a cheap, large-context
model (256k-context, GPT-4o class) can think an MVP strategy all the way
through — consulting the same specialist personas a real engineering org
would (PM, architect, front-end, a domain consultant, opsec, legal) —
*before* an expensive model starts writing code (issue #1). The three
MVPs (kanban #2, messaging #3, Mermaid #4) are the harness's UI; the
linear-iterations queue (#5) is its planning engine; #6 frames the whole
thing as a mix of code, skills, and agents, which is why this sprint also
stands up the `agents/` roster, not just application surfaces.

**Out of scope**: Any actual expensive-model engineering handoff (what
happens *after* a plan converges is a later sprint). Multi-tenant/auth,
billing, or production deployment topology. A general-purpose ticket
tracker beyond this project's own kanban needs — this is a planning
harness for one team, not a Jira competitor. Voice/video; text-only
messaging is in scope.

## Requirements

1. **Kanban MVP** (issue #2): a board with columns and cards; each card
   traces to a tracked issue ID. Column entry/exit rules are explicit
   (`pm/ticket-workflow-steward`), not implied.
2. **Messaging MVP** (issue #3): a thread/turn model that supports both a
   human-readable chat view and the linear-iterations queue's turn-by-turn
   delivery — a "turn" and a "message" are the same underlying entity
   (`docs/enterprise.md` ontology).
3. **Mermaid MVP** (issue #4): render a Mermaid diagram source to a
   diagram, embeddable in a card or a turn, with a visible error state for
   invalid source (no silent failure).
4. **Linear-iterations queue** (issue #5): an ordered persona sequence
   (PM → architect → front-end → consultant → Opsec → legal) where each
   position runs in a fresh context window seeded with (initial goal +
   prior agent's output) and returns a paragraph or goal-list from its
   expertise. Opsec and legal may re-queue the goal back to an earlier
   position; the queue has a stated re-queue cap and terminates.
   Target context growth: ~500-1000 tokens/cycle.
5. **Token/cycle observability**: every queue run reports cycle count and
   cumulative token cost (feeds `docs/agent-ledger.jsonl` /
   `docs/credit.md` once the harness has real runs to record).
6. **Agent roster** (issue #6): the harness itself is operated by a
   curated `agents/` roster (this sprint: 13 roles / 8 teams) adopting the
   Ges-Talt docs + verifier conventions, not ad hoc prompting.

## Constraints

- No new backend dependency where the existing store/transport already
  covers the need (`backend/backend-architect`'s call, not asserted by
  implementers).
- The queue must run against the target low-intelligence, large-context
  model tier (issue #1) — a design that only works on a frontier model has
  failed the brief; `ai/prompt-engineer` tests against the real target
  tier, not a stand-in.
- Every sub-issue this sprint cuts must trace to a requirement number
  above; no sub-issue exists only to be tracked.

## Success criteria

- [ ] Kanban MVP: a card can be created, moved through every defined
      column, and traced back to its issue ID.
- [ ] Messaging MVP: a thread delivers turns in strict cycle order,
      resumable after a killed connection, with no duplicate turns on
      retry.
- [ ] Mermaid MVP: a valid source renders a diagram; an invalid source
      shows a visible error, never a blank pane.
- [ ] Linear-iterations queue: a run with at least one re-queue still
      terminates within its stated cap, and per-cycle token growth stays
      within the ~500-1000 token target or the overflow rule fires.
- [ ] `python3 scripts/verify.py` is all-PASS/SKIP (no FAIL) for the
      roster/docs machinery this sprint touches.
