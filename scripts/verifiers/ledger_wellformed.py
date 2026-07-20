"""Assert the agent ledger is machine-valid.

The ledger's integrity is the whole point of the credit/selection loop — a
malformed or under-specified row silently corrupts `credit.py`'s scores. One
JSON object per non-blank line, with the required keys.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _lib  # noqa: E402

PROPERTY = "Every non-blank ledger line is a JSON object with task/role/model/tokens/sprint (tokens an int)."
METHOD = "static"
OWNER = "ai/model-evaluator"
LEDGER = "docs/agent-ledger.jsonl"
REQUIRED = ("task", "role", "model", "tokens", "sprint")


def check():
    _lib.in_repo_root()
    if not os.path.exists(LEDGER):
        return _lib.SKIP, f"{LEDGER} does not exist"
    n = 0
    for i, line in enumerate(open(LEDGER, encoding="utf-8"), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as e:
            return _lib.FAIL, f"line {i}: invalid JSON ({e})"
        if not isinstance(row, dict):
            return _lib.FAIL, f"line {i}: not a JSON object"
        missing = [k for k in REQUIRED if k not in row]
        if missing:
            return _lib.FAIL, f"line {i}: missing keys {missing}"
        if not isinstance(row["tokens"], int):
            return _lib.FAIL, f"line {i}: tokens is not an int ({row['tokens']!r})"
        n += 1
    return _lib.PASS, f"{n} ledger row(s) well-formed"


if __name__ == "__main__":
    sys.exit(_lib.run_standalone(check))
