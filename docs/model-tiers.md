# Model tiers (GT-33)

## Why

Pinning a vendor model id (`sonnet`, `opus`, `haiku`) directly in every
role's frontmatter is a monoculture: swapping provider or model means
editing dozens of `agent.md` files, and there is no single point where
"what does `reason` mean today" is decided. `scripts/models.toml` is that
single point — a role declares a **capability tier**, not a vendor, and
the tier resolves to a concrete model in one place. Provider sovereignty
= edit one file, not the roster.

## The mapping

`scripts/models.toml` is the authoritative source. Current generation
(the Claude 5 family + Opus 4.8):

| Tier | Resolves to | Used for |
|---|---|---|
| `reason` | `claude-opus-4-8` | reasoning-bound roles: static review, architecture, threat modeling |
| `build` | `claude-sonnet-5` | implementation roles — the common case |
| `cheap` | `claude-haiku-4-5-20251001` | high-volume/low-complexity roles |

Aliases (readable shorthands, resolve to the same current ids):
`opus` → `claude-opus-4-8`, `sonnet` → `claude-sonnet-5`,
`haiku` → `claude-haiku-4-5-20251001`, `fable` → `claude-fable-5`.

**Updating for a new model generation** is a one-line-per-tier edit in
`scripts/models.toml` — nothing in the roster changes, because roles
declare tiers/aliases, not raw ids. That is the model-sovereignty payoff
the Nous review asked for, made concrete.

## What a role may write

A role's frontmatter `model:` may be **any** of:

- an **alias** (`opus`/`sonnet`/`haiku`/`fable`) — the readable default the
  roster uses today, so a model bump doesn't churn 80+ files;
- a **tier** (`reason`/`build`/`cheap`) — declares intent, not a vendor;
- a **concrete id** (`claude-opus-4-8`, …) — when a role must pin a model.

All three resolve to the canonical id; `build_index.py` displays the
readable label and counts by it. An unrecognized value is a lint problem —
a typo would otherwise silently drop a role out of the **reason-tier**
read-only check (the check keys on whichever id `reason` maps to, not the
literal string "opus", so it survives a generation bump).

`agents/ai/ai-engineer/agent.md` is converted as the demonstration role
(`model: sonnet` -> `model: build`). All other roles keep their concrete
model id for now; migrating the rest of the roster is a follow-on, not
part of this change.

## Ownership

`ai/model-evaluator` owns a future **swap-eval**: run a role's acceptance
tests against an alternate (including open-weight) model for its tier and
report the delta, so sovereignty is *tested* — a tier swap is validated
against real acceptance criteria before it's adopted — not merely
asserted by editing `models.toml`. That swap-eval itself is not built by
this change; this change only makes the tier indirection exist and lints
it.
