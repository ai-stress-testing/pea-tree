# Credit — the selection score (GT-32)

Companion to `docs/feedback-loop.md`. That doc named the gap: the loop's
sensor (falsifier + testing verdict + ledger) exists, but nothing
downstream of the verdict *acted* on it — a verdict just sat in
`docs/agent-ledger.jsonl` for a human to read. This is the mechanism that
closes it: `scripts/credit.py` turns ledger rows into a **selection
score** that selection can actually read.

## What the score means

For each role, from `docs/agent-ledger.jsonl`:

```
score = normalized(pass_rate) − w_cost·normalized(mean_tokens) − w_retry·normalized(mean_retries)
```

- **`pass_rate`** — fraction of that role's `verdict` rows that are
  `PASS`. Rewarded.
- **`mean_tokens`** — average `tokens` cost per run. Penalized
  (`W_COST = 0.5` in `scripts/credit.py`).
- **`mean_retries`** — average `retries` before a verdict landed.
  Penalized (`W_RETRY = 0.3`).

All three are min-max normalized across roles before combining, so the
score is a relative ranking within the current ledger, not an absolute
unit. Weights are named constants at the top of `scripts/credit.py` —
change them there, not inline.

`verdict` and `retries` are optional, additive fields on the ledger
schema (see `docs/agent-ledger.jsonl`'s newer rows); older rows without
them still count toward `sample_count` and `mean_tokens`. A role with no
`verdict` rows gets a neutral pass-rate term (neither rewarded nor
punished) instead of a crash or an invented number; a role with no
`retries` rows gets no retry penalty. If *no* role in the whole ledger
has verdicts yet, every role's pass-rate term is the same neutral
constant and the ranking degrades cleanly to cost-only — the documented
fallback, not a special case.

## How it's consulted

`scripts/credit.py` writes `docs/selection-weights.json`
(per-role `score`, `sample_count`, `mean_tokens`, `pass_rate`).
`agents/pm/project-manager` reads it as one input when picking an
assignee: "cheapest *sufficient*" becomes "cheapest *sufficient and
proven*" — a role that's cheap but keeps failing no longer looks like
the cheap option once its FAILs and retries are priced in.

This is the piece the feedback-loop review (sol.2, `docs/reviews/
nous-research-mcp-solutions.md` §2) called for: a mechanism that *writes
something selection reads*, so a verdict changes future assignment
behavior instead of only gating the current run.

## Advisory, not automatic — yet

The PM consults `selection-weights.json`; nothing enforces it choosing
the top-scored role, and nothing runs `credit.py` automatically today.
The natural next step (queued, not built here) is the scheduled
"credit rollup" routine already sketched in `docs/routines-ideas.md` —
recompute on a cadence and open an issue when a role's score drifts past
a threshold. Until then: run `python3 scripts/credit.py` by hand (or
`--selfcheck` to verify the scoring logic) after ledger updates.
