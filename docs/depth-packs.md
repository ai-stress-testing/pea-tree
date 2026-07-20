# Depth packs — depth without a per-call token tax

The solution to #9 (`docs/reviews/nous-research-mcp-solutions.md §9`, GT-39).
Character depth and token economy only trade off if depth must live inline in
every prompt. Drop that assumption: layer the role.

## Two layers

- **L0 — the terse charter** (`agent.md`, ~30 lines). Loaded *every* call.
  Persona in a phrase, responsibilities as verbs, handoff, a short "never".
  Handles the common case. This is the whole prompt today and stays that way.
- **L1 — the depth pack** (`DEPTH.md`, optional, per role). Loaded *only* on a
  **depth trigger**. Worked exemplars, a failure-mode playbook, voice/priors.
  Never resident by default — it is depth on demand, not bloat bolted to L0.

Expected resident cost per call = `L0 + P(hard)·L1`. Most calls are easy, so
`P(hard)` is small and expected cost stays near L0, while full depth is
*available exactly when it changes the outcome*. You pay for depth only in the
moments depth is what's failing you.

## The depth trigger

Load `DEPTH.md` when — and only when — one of these holds:

1. **Novelty off-charter** — the call sits outside the common case the L0
   charter was written for.
2. **High-stakes call** — a money path, a trust boundary, an irreversible
   action, a flagged verdict.
3. **FAIL-retry** — the previous attempt was handed back FAIL
   (`agents/WORKFLOW.md`); reload with depth before retrying.

None of the three → run on L0 alone. Do not preload L1 "to be safe": that
defeats the entire mechanism and reintroduces the per-call tax.

## What goes in a DEPTH.md

Exemplars, not adjectives (§9.B). Character encoded as a few sharp worked
examples compresses far more steerable behavior per token than paragraphs
describing a persona. Headings (see `agents/TEMPLATE/DEPTH.md`):

- **Exemplars** — 2–3 concrete, repo-relevant worked cases showing the role
  done *right* (and the tell that separates right from plausible-but-wrong).
  Show the reasoning, not a bio.
- **Failure-mode playbook** — the specific ways this role goes wrong, each with
  the catch. The negative space the exemplars imply.
- **Priors & voice** — the standing assumptions and tone, in a few lines. Still
  invariants and examples, not vibe copy.

Keep it lean — ~50 lines. A depth pack that grows into a manual has become a
second charter; split or cut it.

## Self-correction

The mechanism finds its own optimum per role, by measurement — it is not set
once.

- The ledger (`docs/agent-ledger.jsonl`) records L1 load frequency per role.
- **Always loading L1** → the L0 charter is miscalibrated: its common case
  needs more resident context, or the trigger is too loose. The feedback loop
  (`docs/feedback-loop.md`) treats that as a surprised setpoint and revises L0.
- **Never loading L1 under novelty** → the role is over-confident, skipping
  depth it should pull. `agents/logicians/falsifier` catches the resulting
  weak output; the feedback loop revises the trigger.

Both failure directions are observable and both have a catcher. The optimum is
found, not asserted — same discipline as `docs/feedback-loop.md`: a
measurement that revises the setpoint, not just a gate.
