# Should agents have skills? (issue #42)

**Decision: yes, but rarely — and only for repeatable *procedures*, never
for knowledge or persona.** Most agents need zero skills.

## The three layers, kept distinct

A role already has two capability layers before "skill" is even the answer:

| Layer | File | Holds | Loaded |
|---|---|---|---|
| Charter | `agent.md` | who it is, what it owns, its Never list | always (resident) |
| Depth pack | `DEPTH.md` | how it reasons on the hard case — exemplars | on a depth trigger (`docs/depth-packs.md`) |
| **Skill** | `SKILL.md` | a **procedure it executes** — the exact repeatable steps/tooling for one recurring task | on invocation |

Persona → charter. Reasoning → depth pack. **A skill is only for a
multi-step procedure a role runs the same way every time** (e.g. "run the
OPSEC egress verifier and file the result", "scaffold the next sprint").
If the thing is knowledge, it's a depth pack; if it's identity, it's the
charter. Reaching for a skill to hold either is the mistake.

## When a role gets a skill

Climb the ladder first (same as `AGENTS.md`/ponytail): does the procedure
recur enough to be worth extracting, or is it a one-off the agent just
does? Only a genuinely repeated, mechanical procedure earns a `SKILL.md`,
placed in the role's folder (`agents/<team>/<role>/SKILL.md`). It obeys the
same discipline as everything else here:

- **One job.** A skill does one procedure, like a verifier does one check.
- **Lean.** ≤ 500 lines — skills at 501+ LoC measurably hurt performance
  (issue #43); the audit `scripts/audit_skills.py` enforces this and fails
  CI on a violation.
- **Loaded on invocation, not resident** — it doesn't tax the per-call
  token budget the way inline charter text would (the same economy as
  depth packs).

## Current state

No role has a skill today, and none needs one yet (YAGNI) — the charter +
depth pack + the shared Method ladder cover the roster. This policy exists
so that when a real repeatable procedure emerges, it's added as a lean
skill rather than bloated into a charter, and the LoC audit keeps it honest
from the first one.
