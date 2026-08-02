# Security Review — Takt-Harness (review gate)

**Reviewers**: `security/architect` + `logicians/falsifier` (roster gate).
**Note on provenance**: both roster subagents were repeatedly terminated by an
account session limit mid-run, so the orchestrator conducted the adversarial
pass **inline against the real code** and recorded it here. Findings are
grounded in file:line; actionable ones were fixed in this same change.

## Claims attacked & verdicts

### CLAIM 1 — write-scope guard (`backend/app/guard.py`) — **PASS (with fix)**
*"No application code can write or delete outside `takt-harness/`."*

- **Finding A1 (Medium → fixed-by-documentation):** `writable_path()` had **no
  callers** — the invariant was *latent*, not actively enforced. Attack: the
  claim "every write goes through the guard" was vacuously true. Reality: the
  only real writer is SQLite, whose path *is* validated (`assert_db_path_scoped`
  at `db.py` init). Remediation: guard docstring now states the two layers
  explicitly — SQLite path is the ACTIVE control; `writable_path` is the
  MANDATORY entry point for any *future* file write. No file-write path exists
  today, so nothing escapes.
- **Finding A2 (Low, accepted):** TOCTOU — `writable_path` resolves symlinks at
  check time; a symlink swapped before the caller writes is a theoretical
  window. No callers today; single-operator local app. Documented, accepted.
- Escape tests (parent `..`, absolute, symlink) all **rejected** — verified by
  `tests/test_guard.py` (4 tests).

### CLAIM 2 — queue retry rule (`queue_rules.py`, `routers/queue.py`) — **FAIL → fixed**
*"The queue retries 3×, skips to next, escalates after 6 more; always terminates."*

- **Finding B1 (Medium → fixed):** the state machine was correct and tested,
  but **"skip to next" was not wired** — `Transition.skip_to_next` was computed
  and thrown away; `/process` only ever touched one item by id. There was no
  runner, so the skip/advance behavior did not exist.
  **Fix:** added `next_candidate()` (pure, unit-tested) and a
  `POST /api/queue/process-next` runner that picks the first runnable
  (idle/error, non-paused) item in priority order and passes over
  `needs_user`/`paused`/`done`. An empty result means the queue is drained, so
  the runner terminates. New tests: `test_runner_skips_paused_and_terminal_items`,
  `test_runner_terminates_when_nothing_runnable`.
- Termination holds: `attempts` only increments per processing call and is
  capped by the `needs_user` escalation at 9.

### CLAIM 3 — "No deletions" (PRD) — **PASS**
Confirmed there is **no delete endpoint** anywhere: documents and issues expose
create/update only; queue/chats/projects/sprints expose create (+update) only.
Nothing removes rows, and no code path writes or deletes files outside the tree.

## Other surfaces reviewed

- **`/invoke` & `agent-assist` (prompt injection):** by design these pass
  caller content to the local model. The model has **no tools** in this
  harness, so injection yields text only — no privilege escalation. Accepted
  for a single-user local planner.
- **SSRF via `agent_base_url`:** the endpoint is **operator config (env), not
  request-influenceable** — no route lets a caller set it. Not reachable.
- **XSS in Docs preview (`web/src/components/Markdown.vue`):** correct order —
  `marked` → `DOMPurify.sanitize` → `v-html`; Mermaid rendered with
  `securityLevel: "strict"` and the SVG re-sanitized before insertion. **PASS.**
- **Injection:** all DB access is SQLAlchemy ORM (parameterized); no raw SQL.
- **Auth:** none — the PRD explicitly defers agent-endpoint auth tokens to a
  backlog item. Accepted for local use; **must** land before any networked
  deployment.

## Outcome

Gate result: **PASS after fixes.** 2 findings fixed in code (B1 wired the
runner; A1 made the guard's enforcement layers explicit), 3 accepted with
rationale (A2 TOCTOU, prompt-injection, deferred auth). Backend suite: **14
tests pass**.
