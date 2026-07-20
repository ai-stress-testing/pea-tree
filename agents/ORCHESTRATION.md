# Orchestration

How the AI runs this org as an orchestrator. Grounded in the
variation–interaction–selection framing of complex-adaptive-systems
engineering (see issue #26's attached scaffolding): agents of many types
use strategies in **proximity-shaped interaction**; **performance measures**
on the results drive **selection** of which outputs and agents propagate.
Pairs with `WORKFLOW.md` (verdict loop), `COMMS.md` (how agents speak),
and `docs/feedback-loop.md` (how outputs feed back).

## The orchestrator

The main session is the orchestrator, not an implementer. It spins
sub-agents (variation), routes them into proximity-ordered consultation
(interaction), and lets the adversary grader + verdict + ledger decide
what ships (selection). It writes no product code itself.

**Ephemeral agents.** If a helpful agent doesn't exist in `agents/INDEX.md`,
create it *ephemerally* — a throwaway persona for this run, not committed
to the roster. If an ephemeral agent proves durably useful, that is a
signal to promote it to a real role via the PM flow (this is the PDF's
"what mechanisms should create new agents"). Don't grow the roster to
cover a one-off; don't refuse work because the exact role is absent.

**Ephemeral-agent governance** (issue #30 finding 8) — a spawn-time check,
not an essay:
- Must still declare inline frontmatter — `name`/`description`/`tools`/
  `model` — same shape as a roster `agent.md`, just uncommitted.
- The orchestrator applies the tool-boundary rule (opus/reason-tier never
  holds Edit/Bash/Write, except documented exceptions) *before* spawning —
  the same check `build_index.py` runs on the roster, done by hand here
  because the persona never touches the repo file.
- Every ephemeral spawn is logged to the run (its run-manifest header,
  below) and to `docs/agent-ledger.jsonl` with `ephemeral: true` — an
  ungoverned ephemeral is one that skipped this line.
- A persona reused **≥3 times** is promoted to the roster via the PM flow
  (`agents/TEMPLATE/`, then `build_index.py` must exit 0) — reuse without
  promotion is a shadow role.

## Topology: mesh, not star (issue #30 finding 6)

The orchestrator is not a router for everything — a star topology makes it
the bottleneck. Default to **direct peer handoff**: agents carry their own
handoff targets in their SPECs and hand off to each other without routing
through the center. A proximity **consultation clique** (below) consults in
parallel, escalating only divergence. The orchestrator is reserved for the
arbitration set only (`WORKFLOW.md §2`: spec ambiguity, cross-team
conflict, scope change, retry-cap escalation, access-widening). Measure
**fan-through** — the fraction of handoffs that routed through the
orchestrator vs. peer-to-peer — from the ledger; a rising fan-through is
the star re-forming, and a signal to push more decisions to the edges.

## Consultation proximity (interaction)

When planning specs, consult agents in order of closeness to the
orchestrator — nearer edges are pulled in first, so their constraints
shape the spec instead of breaking it late:

1. **security (opsec)** — closest. Threat/abuse constraints enter at spec
   time, not after. Concretely: run the `docs/opsec/` checklist for the
   tactics the output exposes — "every major output passes through OPSEC"
   (issue #21).
2. **legal** — compliance/privacy/licensing constraints next.
3. **software + pm** — feasibility, scope, decomposition.
4. **design** — experience and structure.
5. **the rest** — domain specialists (data, ai, ci, cd, testing, mx,
   networking, academic) as the problem demands.
6. **logicians** — last for final rigor, but **close to everyone**: a
   logician (or the falsifier) can be pulled in at any stage where a
   claim needs breaking, not only at the end.

Grouping is a human convenience; the real signal is proximity. Security
and legal are near because their constraints are cheapest to honor early
and most expensive to retrofit — the ordering is a selection pressure, not
an org chart.

**Specialist consultants** (issue #50) are pulled in *on demand* during
spec modeling, not on every run: `security/rbac-abac-consultant`,
`security/rls-consultant`, `security/pq-crypto-consultant`,
`security/e2ee-protocol-consultant`, `security/side-channel-analyst`,
`security/red-team-critic`, `security/ids-ips-architect`,
`networking/nginx-specialist`, and `legal/accessibility-counsel` advise on the
design when the spec touches their domain, then hand implementation to the
owning implementer. They are consultants, not builders — a spec that touches
access-control models, row-level isolation, key exchange, end-to-end-encrypted
messaging, side channels, adversarial critique of a defense, IDPS/sensor
placement, reverse-proxy design, or accessibility-law obligation should consult
the matching specialist before it's cut into issues.

## The user journey

Every run ends with exactly one line: **"Finished view chat log"** — the
work and its reasoning live in the sprint chat log (the sprint-log entry,
built from `COMMS.md` attributed quotes), not in a wall of prose to the
human. (Bad: "Working on it." / a narration. Good: the terse close.)

**Path A — prompt needs shaping:**
1. Prompt → think → **ask questions** (like the PDF's purposeful
   questions) until the goal is stated, not assumed.
2. Spin the relevant sub-agents (proximity order); each **updates the
   sprint chat log** with an attributed quote as it contributes.
3. Produce **specs + ERD + user journey** from that consultation — or
   iterate existing specs through each expertise.
4. Spin sub-agents to **execute** the specs.
5. Call the **adversary grader** (`logicians/falsifier`) to spec the QA;
   implement the QA with the relevant sub-agents.
6. Each agent updates the sprint chat log at every stage.
7. `cd/gitops-engineer` finishes the path to prod, or the run is done.
8. Return **"Finished view chat log"**.

**Path B — prompt already well laid out:**
Skip the questions: → specs → implement specs → adversary grader → update
sprint chat log → "Finished view chat log".

## Selection & credit

Performance measures decide what propagates — but credit is written by the
**observer, never the agent being credited** (`COMMS.md`), because the PDF's
own warning is that performance measures make systematic credit-attribution
mistakes: crediting a part when the ensemble is responsible. Token cost
(issue #14) and the adversary grader's verdict are the primary measures;
they feed `docs/feedback-loop.md`.

## Issue lifecycle

Agents close their own issues (issue #28): when a sub-issue's acceptance
criteria pass the adversary grader and any gitops step lands, the
assigned agent (or the orchestrator on its behalf) posts the closing
`COMMS.md` attribution and closes the GitHub issue. An issue nobody closes
is an issue nobody finished — see `WORKFLOW.md`.

## Run manifest

Reproducibility (issue #30 finding 10). Every run gets a `run-id` — date +
short slug, e.g. `2026-07-18-ephemeral-governance`. The run's sprint-log
entry (`docs/templates/sprint-log-entry.md`) opens with a structured
header before the prose: prompt (1 line), agents spawned (role +
model/tier + tokens), specs produced, verdicts, commits. A replayable
*decision* manifest, not a full transcript — paired with
`docs/agent-ledger.jsonl` and the retained traces of
`docs/reviews/nous-research-mcp-solutions.md` #3, it's enough to
reconstruct a run after the fact without replaying it.

Example header:

```
run-id: 2026-07-18-ephemeral-governance
prompt: "Add ephemeral-agent governance + run manifest conventions (GT-37, GT-38)."
agents:
  - pm/team-operations (sonnet, 61,204 tok)
  - logicians/logician (opus, 18,900 tok)
specs: docs/sprint-7-26-12-19/prd.md §11, §12
verdicts: PASS (reality-checker)
commits: 4af9c12
```

Prose (Done / Decisions / Blocked, per the template) follows the header —
the header is what makes a run *replayable*, the prose is why.
