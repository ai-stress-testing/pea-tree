# Agent communications convention

How agents report to the human and hand off to each other, starting this
sprint. Pairs with `WORKFLOW.md` (the verdict loop) — that governs *what* a
handoff decides; this governs *how* it's said.

## The attribution line

Every relayed subagent result, and every inter-agent handoff, closes with a
quoted attribution in exactly this shape:

> "<1–2 sentences, first person, the agent's own claim>" — `<team/role>` (<model>), <N> tokens ✓

Rules:
- **Quote, don't paraphrase.** 1–2 sentences in the agent's voice, its
  claim about what it did or found. If it takes three sentences, the
  handoff is doing two things — split it (see WORKFLOW.md granularity).
- **Name who said it.** The exact `team/role` from `agents/INDEX.md`, plus
  the model tier. `main` is allowed for the orchestrator relaying.
- **Close with the token cost.** Always. A claim without its cost hides the
  one number the PM is required to weigh (issue #14 — token distribution
  as a selection pressure).
- **The ✓ means verified, nothing else.** Add it only when the figure has
  been checked against `docs/agent-ledger.jsonl` by
  `scripts/verify_comms.py`. An unverified figure is written without a
  check — never decorate an unchecked number.

## Who writes the number

The **parent/orchestrator** writes the token figure from the subagent's
reported usage block — the agent never self-reports its own credited
number. That is the threat-model separation of duties (an agent that
writes its own credit can inflate it): the observer records, the observed
does not. `verify_comms.py` cross-checks every ✓ line against the ledger,
so the check is code, not courtesy.

## Example

> "I turned the ledger into a per-role selection score the PM can read — the feedback loop now acts, not just measures." — `devops/devops-automator` (sonnet), 70,042 tokens ✓

Keep it one line — `verify_comms.py` matches a single line, so a wrapped
quote is silently skipped, not verified. The 70,042 is `devops/devops-automator`'s
real row in `docs/agent-ledger.jsonl`, so the ✓ survives the check; a
hand-typed number would fail it. Verify with `python3 scripts/verify_comms.py`.
