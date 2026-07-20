# pea-tree — session operating manual

Agent org + docs conventions adopted from **Ges-Talt**
(ai-stress-testing/Ges-Talt). Read `README.md` for what this project is;
this file is what you *do*.

## What this project is

A mock messaging platform + kanban board that lets a cheap, large-context
planning model (256k-context, GPT-4o class) think an MVP strategy through
— across a queue of specialist personas — *before* an expensive model
starts engineering (issue #1). Three MVPs make up the harness:

- **Kanban** (issue #2) — the board a plan's tickets live on.
- **Messaging** (issue #3) — the transport a "linear iterations" queue
  (issue #5) runs its turns over: PM → architect → front-end → consultant
  → Opsec → legal, each turn in a fresh context window, opsec/legal able
  to re-queue the goal to an earlier position, target ~500-1000
  tokens/cycle growth.
- **Mermaid** (issue #4) — diagram rendering for the specs the queue
  produces.

Issue #6's framing — "every harness is a mix of code, skills, and
agents" — is why this repo carries a curated `agents/` roster rather than
just application code.

## On session start

1. Ensure the docs scaffold exists: `python3 scripts/init_docs.py .`
   (idempotent; safe to run every session).
2. Identify the current sprint folder: `docs/sprint-<m>-<y>-<dd>-<dd>/`
   (month, 2-digit year, start day, end day). If today falls outside
   every sprint window, scaffold the next one before starting work.
3. Run the gate: `python3 scripts/verify.py` (the hard-verifier registry —
   roster, INDEX freshness, sprint window, branch taxonomy, …). A red
   verifier is a to-do, not noise. `docs/repo-map.md` is the token-cheap
   where-is-everything index — read it before grepping the tree;
   regenerate with `python3 scripts/build_repo_index.py` after
   moving/adding files.

## Docs convention

- `docs/backlog.md` — one table row per issue (`PT-<n>`); the spec-driven
  PM owns it.
- `docs/sprint-*/prd.md` — the sprint's requirements; issues cite `§n`.
- `docs/sprint-*/sprint-log/` — one dated entry per working session
  (template: `docs/templates/sprint-log-entry.md`).
- `docs/sprint-*/user-journeys/` — one file per journey
  (template: `docs/templates/user-journey.md`).
- `docs/sprint-*/issue-specs/` — one file per issue, per
  `docs/templates/issue-spec.md`, before it's cut into GitHub sub-issues.

## Workflow (spec-driven)

A user goal enters through `agents/pm/project-manager` (opus,
spec-driven): it reads/drafts the PRD, writes an issue spec per
`docs/templates/issue-spec.md`, and cuts issues + granular sub-issues —
every sub-issue has one assignee from `agents/INDEX.md`, checkable
acceptance criteria, and a negative prompt. Static review is
`agents/logicians/`, empirical verification `agents/testing/`, security
`agents/security/`. Don't hand work to an agent outside its charter —
check the index first. See `agents/ORCHESTRATION.md` for the orchestrator
model, `agents/WORKFLOW.md` for the verdict loop (PASS/FAIL handback,
retry cap, escalation, issue-closing) and PM delegation rules,
`agents/COMMS.md` for the quoted-attribution reporting format, and
`docs/feedback-loop.md` for the closed-loop discipline.

The queue design itself (issue #5) is a spec owned by
`ai/multi-agent-systems-architect`, not by `pm/project-manager` directly —
route "design the linear-iterations queue" goals there first.

## Roster rules

- Agents live in `agents/<team>/<role>/` as `agent.md` + `SPEC.md`
  (template: `agents/TEMPLATE/`). This roster is deliberately a small,
  curated subset of Ges-Talt's — one role is enough to start a team; add
  siblings only when a durable new subclass of work shows up (Ges-Talt's
  full 100+-role roster is the reference set to draw the next role from,
  not a backlog to port wholesale).
- After adding/changing agents: `python3 scripts/build_index.py` must
  exit 0 (it regenerates `agents/INDEX.md` and lints the roster — opus
  never holds Edit/Bash; Write only via documented exception).
- Model policy: cheapest sufficient — a concrete model or a capability
  tier from `scripts/models.toml` (`docs/model-tiers.md`). Opus / `reason`
  tier = reasoning-bound roles only (`pm/project-manager`,
  `logicians/software-architect`, `logicians/falsifier`).
- Skills are rare and only for repeatable procedures
  (`agents/skills-policy.md`): a role's `SKILL.md` must stay ≤500 LoC —
  `scripts/audit_skills.py` fails CI on a violation. Most roles need no
  skill.
