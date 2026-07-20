#!/usr/bin/env python3
"""Compute per-role selection scores from docs/agent-ledger.jsonl (GT-32).

The missing piece the feedback-loop review (sol.2) called out: a mechanism
that *writes something selection reads*, instead of a doc a human reads.
This turns ledger rows (verdict, tokens, retries) into a per-role
**selection score** that `pm/project-manager` can consult when picking an
assignee — cheapest *sufficient* becomes cheapest *sufficient and proven*.

    score = normalized(pass_rate)
            - W_COST  * normalized(mean_tokens)
            - W_RETRY * normalized(mean_retries)

`verdict` and `retries` are optional ledger fields (older rows lack them).
Missing data degrades gracefully per role, never crashes:
  - no `verdict` rows for a role  -> pass_rate is None -> neutral 0.5
    (doesn't reward or punish; if *no* role in the ledger has verdicts,
    every role gets the same neutral term, so ranking collapses to
    cost-only, which is the documented fallback).
  - no `retries` rows for a role  -> mean_retries is None -> 0 (no penalty
    invented from absent data).

Run:       python3 scripts/credit.py
Selfcheck: python3 scripts/credit.py --selfcheck

Writes docs/selection-weights.json: per-role {score, sample_count,
mean_tokens, pass_rate}. Advisory only — see docs/credit.md.
"""
import json
import sys
from pathlib import Path

LEDGER = "docs/agent-ledger.jsonl"
OUT = "docs/selection-weights.json"

# Named weights (tune here, not inline). Cost matters more than retries:
# a role that's merely slow-to-converge is cheaper to live with than one
# that's expensive on every call.
W_COST = 0.5
W_RETRY = 0.3


def load_ledger(path=LEDGER):
    entries = []
    p = Path(path)
    if not p.exists():
        return entries
    for line in p.read_text().splitlines():
        line = line.strip()
        if line:
            entries.append(json.loads(line))
    return entries


def normalize(values, default):
    """Min-max normalize a {key: value-or-None} dict to [0, 1].

    Keys with value None (missing data) get `default` rather than being
    dropped, so every role still gets a score. If every present value is
    equal (or nothing is present), normalization can't discriminate —
    fall back to the neutral midpoint instead of dividing by zero.
    """
    present = {k: v for k, v in values.items() if v is not None}
    if not present:
        return {k: default for k in values}
    lo, hi = min(present.values()), max(present.values())
    out = {}
    for k, v in values.items():
        if v is None:
            out[k] = default
        elif hi > lo:
            out[k] = (v - lo) / (hi - lo)
        else:
            out[k] = 0.5
    return out


def per_role_stats(entries):
    by_role = {}
    for e in entries:
        role = e.get("role")
        if not role:
            continue
        by_role.setdefault(role, []).append(e)

    stats = {}
    for role, rows in by_role.items():
        tokens = [r["tokens"] for r in rows if isinstance(r.get("tokens"), (int, float))]
        verdicts = [r["verdict"] for r in rows if r.get("verdict") in ("PASS", "FAIL")]
        retries = [r["retries"] for r in rows if isinstance(r.get("retries"), (int, float))]
        stats[role] = {
            "sample_count": len(rows),
            "mean_tokens": (sum(tokens) / len(tokens)) if tokens else 0,
            "pass_rate": (verdicts.count("PASS") / len(verdicts)) if verdicts else None,
            "mean_retries": (sum(retries) / len(retries)) if retries else None,
        }
    return stats


def compute_scores(entries):
    """Return {role: {score, sample_count, mean_tokens, pass_rate}}."""
    stats = per_role_stats(entries)
    if not stats:
        return {}

    tokens_norm = normalize({r: s["mean_tokens"] for r, s in stats.items()}, default=0.5)
    pass_norm = normalize({r: s["pass_rate"] for r, s in stats.items()}, default=0.5)
    retry_norm = normalize({r: s["mean_retries"] for r, s in stats.items()}, default=0.0)

    scores = {}
    for role, s in stats.items():
        score = pass_norm[role] - W_COST * tokens_norm[role] - W_RETRY * retry_norm[role]
        scores[role] = {
            "score": round(score, 4),
            "sample_count": s["sample_count"],
            "mean_tokens": round(s["mean_tokens"], 1),
            "pass_rate": s["pass_rate"],
        }
    return scores


def selfcheck():
    ledger = [
        {"role": "cheap/passer", "tokens": 10000, "verdict": "PASS", "retries": 0},
        {"role": "cheap/passer", "tokens": 12000, "verdict": "PASS", "retries": 0},
        {"role": "expensive/failer", "tokens": 200000, "verdict": "FAIL", "retries": 3},
        {"role": "expensive/failer", "tokens": 210000, "verdict": "FAIL", "retries": 2},
        # No verdict/retries at all: must not crash, must still get a score.
        {"role": "no-verdict/legacy", "tokens": 50000},
    ]
    scores = compute_scores(ledger)
    assert scores["cheap/passer"]["score"] > scores["expensive/failer"]["score"], (
        "cheap-passing role must outrank expensive-failing role: "
        f"{scores['cheap/passer']['score']} <= {scores['expensive/failer']['score']}"
    )
    assert isinstance(scores["no-verdict/legacy"]["score"], float), (
        "missing verdict/retries must degrade gracefully, not crash"
    )
    print(
        "selfcheck ok: cheap/passer "
        f"({scores['cheap/passer']['score']}) > expensive/failer "
        f"({scores['expensive/failer']['score']}); no-verdict/legacy handled "
        f"without crashing ({scores['no-verdict/legacy']['score']})"
    )


def main():
    entries = load_ledger()
    scores = compute_scores(entries)
    Path(OUT).write_text(json.dumps(scores, indent=2, sort_keys=True) + "\n")

    if not scores:
        print(f"no ledger entries found; wrote empty {OUT}")
        return 0

    ranked = sorted(scores.items(), key=lambda kv: kv[1]["score"], reverse=True)
    print(f"wrote {OUT}: {len(scores)} roles from {len(entries)} ledger rows")
    top_role, top = ranked[0]
    bot_role, bot = ranked[-1]
    print(f"top:    {top_role} (score={top['score']}, pass_rate={top['pass_rate']}, mean_tokens={top['mean_tokens']})")
    print(f"bottom: {bot_role} (score={bot['score']}, pass_rate={bot['pass_rate']}, mean_tokens={bot['mean_tokens']})")
    return 0


if __name__ == "__main__":
    if "--selfcheck" in sys.argv:
        selfcheck()
        sys.exit(0)
    sys.exit(main())
