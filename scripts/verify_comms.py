#!/usr/bin/env python3
"""Verify agent attribution lines (agents/COMMS.md convention).

    python3 scripts/verify_comms.py [--selfcheck]

Scans docs/ for attribution lines of the shape:

    > "quote" — `team/role` (model), N tokens ✓

Checks: the line is well-formed and carries a token figure; and any line
ending in ✓ has a matching entry in docs/agent-ledger.jsonl (same role,
same token count). A ✓ with no ledger backing is the failure this exists
to catch — an unverifiable claim wearing a verified badge. Exits 1 on any
violation so CI can gate on it.
"""
import glob
import json
import re
import sys
from pathlib import Path

LEDGER = "docs/agent-ledger.jsonl"
# > "quote" — `team/role` (model), 12,345 tokens [✓]
LINE = re.compile(
    r'^>\s*"(?P<quote>.+?)"\s*[—-]+\s*`(?P<role>[a-z0-9-]+/[a-z0-9-]+|main)`'
    r'\s*\((?P<model>[\w.-]+)\),\s*(?P<tokens>[\d,]+)\s*tokens\s*(?P<ok>✓)?\s*$'
)


def load_ledger(root="."):
    entries = []
    p = Path(root) / LEDGER
    if p.exists():
        for line in p.read_text().splitlines():
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


def verified(role, tokens, ledger):
    return any(e.get("role") == role and int(e.get("tokens", -1)) == tokens
               for e in ledger)


def scan(root=".", ledger=None):
    if ledger is None:
        ledger = load_ledger(root)
    problems = []
    for path in glob.glob(f"{root}/docs/**/*.md", recursive=True) + \
            glob.glob(f"{root}/agents/**/*.md", recursive=True):
        for i, raw in enumerate(Path(path).read_text().splitlines(), 1):
            # Only lines that look like an attempt at an attribution line.
            if not raw.lstrip().startswith('> "') or "tokens" not in raw:
                continue
            # Skip the format spec itself: a placeholder quote like "<...>".
            if '"<' in raw:
                continue
            m = LINE.match(raw.strip())
            if not m:
                problems.append(f"{path}:{i}: malformed attribution line")
                continue
            if m.group("ok"):
                tok = int(m.group("tokens").replace(",", ""))
                if not verified(m.group("role"), tok, ledger):
                    problems.append(
                        f"{path}:{i}: ✓ but no ledger match for "
                        f"`{m.group('role')}` @ {tok} tokens"
                    )
    return problems


def selfcheck():
    ledger = [{"role": "design/ux-architect", "tokens": 83038}]
    good = '> "did the thing well enough." — `design/ux-architect` (sonnet), 83,038 tokens ✓'
    bad_badge = '> "lied about the cost." — `design/ux-architect` (sonnet), 99,999 tokens ✓'
    malformed = '> "no cost given." — `design/ux-architect` (sonnet)'
    assert LINE.match(good) and verified("design/ux-architect", 83038, ledger)
    m = LINE.match(bad_badge)
    assert m and not verified(m.group("role"), 99999, ledger), "bad badge must fail"
    assert LINE.match(malformed) is None, "missing token figure must be malformed"
    print("selfcheck ok")


def main():
    if "--selfcheck" in sys.argv:
        selfcheck()
        return 0
    problems = scan()
    ledger = load_ledger()
    print(f"ledger: {len(ledger)} entries; scanned docs/ + agents/")
    if problems:
        print(f"\n{len(problems)} problem(s):", file=sys.stderr)
        for p in problems:
            print(f"  {p}", file=sys.stderr)
        return 1
    print("all attribution lines valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
