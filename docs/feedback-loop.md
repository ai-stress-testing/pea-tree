# From feedforward to feedback

Issue #29: "An oven that disregards its temperature burns a house down.
Agents that disregard their output's success (based on proper stresses per
prompt) produce noise."

A feedforward system runs open-loop: prompt in, output out, no reading of
whether the output was any good. That's the oven with no thermostat. This
doc closes the loop — outputs become inputs to the next decision. It is the
PDF scaffolding's **selection** section made operational.

## The control loop

| Control part | In this org |
|---|---|
| Setpoint (desired) | The issue's acceptance criteria + negative prompt |
| Sensor (measure) | `logicians/falsifier` (adversary grader) + `testing/` verdict + `docs/agent-ledger.jsonl` (token cost) |
| Error signal | The WORKFLOW.md FAIL handback: expected vs actual |
| Controller | The orchestrator: retry, re-spec, reassign, or escalate |
| Actuator | The assigned agents |

No sensor → no error signal → feedforward → noise. The adversary grader is
the thermostat: it exists so an output is *measured against its setpoint*
before it propagates.

## Proper stresses per prompt

"Success based on proper stresses" means the setpoint is calibrated to the
prompt, not generic. A money path is stressed for idempotency and rounding;
a parser for malformed input; a concurrency path for interleaving. The
falsifier picks the stresses that actually threaten *this* output — a PASS
lists which stresses were applied (`agents/logicians/falsifier`). A generic
"looks fine" is an unread thermostat.

## What the loop revises (the feedback)

The PDF's selection warnings, applied:

- **Revise success when surprised.** When an output is better or worse than
  expected, update the acceptance criteria / spec — not just this run's
  verdict. A surprise is data about a wrong setpoint, per the PDF's "is the
  experience used to revise the definition of success."
- **Selection pressure = token cost.** The ledger (issue #14) amplifies
  cheap agents that pass and demotes expensive ones that fail — the credit
  rollup routine (`docs/routines-ideas.md`) is the aggregation that makes
  this pressure visible over time.
- **Credit the ensemble, not the part.** The observer writes credit
  (`COMMS.md`), guarding the PDF's named failure mode — crediting one agent
  when the ensemble did the work.
- **Causal, not correlated measures.** Token cost and a green verdict are
  proxies; when they stop tracking real quality (an agent games the
  grader), change the measure, don't trust the proxy.

## Status

The loop's parts exist (verdict, falsifier, ledger, negative prompts); what
this doc adds is the *closed-loop discipline* — treating a verdict as a
signal that revises the setpoint, not just a gate. The mechanical
amplifier (credit rollup that acts on the ledger automatically) is queued
as a routine (`docs/routines-ideas.md`, GT-23).
