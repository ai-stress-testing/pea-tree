# Branching + worktree convention

Why this exists: an untyped branch and a single working tree give you **poor
observability**. When every change lands on one branch (or on branches whose
names don't say what they are), you can't see at a glance what work is in
flight, triage it, or map it to a deploy. In a big project that's a
correctness and coordination problem, not a style nit. This convention makes
branch *kind* explicit and gives concurrent work its own isolated,
observable tree.

Enforced by `scripts/verifiers/branch_taxonomy.py` (part of the
`scripts/verify.py` gate). Owned by `cd/gitops-engineer` (git is the source
of truth for deployable state) with `ci/pipeline-engineer` gating names at
the pipeline edge.

## Branch taxonomy

Every branch is either a **reserved trunk** or a **typed work branch**
`<type>/<slug>`. The type is the first path segment and declares intent:

| Prefix | For | Lands via |
|---|---|---|
| `feature/` | net-new capability | review → merge |
| `fix/` | corrective change to shipped behavior (the bug fix) | review → merge, often fast-tracked |
| `bug/` | reproduction / investigation of a defect (may not merge) | pairs with an issue; may be discarded once understood |
| `mvp/` | minimal-viable prototype or spike toward a larger initiative | promote to `feature/` or discard |
| `plan/` | spec / PRD / planning only — docs, no product code | review → merge; the PM's spec-driven output |

Reserved trunks (never typed): `main` (protected; prod is a reflection of
it — GitOps source of truth), `Sprint0` (long-lived staging integration),
and the `claude/<slug>` automation prefix these agent sessions push to.

`<slug>` is kebab-case and, where an issue exists, carries its id:
`feature/gt-52-egress-verifier`, `fix/gt-49-handoff-ref`. The slug is for
humans; the issue id is the join key back to the backlog.

## Worktree flow (the observability fix)

One branch checked out in one directory serializes work and hides it. Use a
**worktree per concurrent task** so each in-flight branch is its own
directory you can list, diff, and reason about independently:

```
git worktree add ../gestalt-feature-egress feature/gt-52-egress-verifier
git worktree add ../gestalt-fix-handoff     fix/gt-49-handoff-ref
git worktree list        # every in-flight task, at a glance
```

Why it maps onto this org:
- **Blast radius = one tree.** An agent (or an ephemeral persona per
  `ORCHESTRATION.md`) works in its own worktree; a mistake can't touch a
  sibling task's files. This is the filesystem analogue of the tool-boundary
  rule.
- **Observability.** `git worktree list` and the typed branch names are a
  live map of what's being worked and by whom — the same "make the in-flight
  state legible" goal as the run manifest.
- **Clean parallelism.** Two tasks build/test without stomping each other's
  working tree; the CI pipeline (`ci/pipeline-engineer`) runs each on its own
  ephemeral runner off its own branch.
- **Cleanup is explicit.** `git worktree remove` when the branch merges or
  the spike is abandoned — a dangling worktree is visible, unlike a stale
  stash.

## How it plugs into the verdict loop

`branch_taxonomy` is one of the single-property machines composed by
`scripts/verify.py` (`agents/WORKFLOW.md` §5): a change on an untyped branch
does not pass the gate. Deploy mapping is downstream — `cd/gitops-engineer`
decides which branch reconciles to which environment, and `plan/` branches
never reach a runtime environment because they carry no product code.
