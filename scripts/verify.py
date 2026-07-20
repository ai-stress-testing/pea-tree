#!/usr/bin/env python3
"""Hard-verifier registry runner (GT-43).

Composes the single-property machines in `scripts/verifiers/` into one gate
for the verdict loop (`agents/WORKFLOW.md` §1). Each verifier asserts one
property and returns PASS / FAIL / SKIP with a counterexample; this runner
executes them all, prints a table (failures first), and exits non-zero if
any FAILed — the same way `build_index.py` / `verify_comms.py` already gate
the roster.

Usage:
    python3 scripts/verify.py                 # run every verifier
    python3 scripts/verify.py roster_pairing  # run named verifier(s) only
    python3 scripts/verify.py --json          # machine-readable output
    python3 scripts/verify.py --list          # list registered verifiers

Fail-closed: a verifier that raises is recorded as FAIL, not skipped. SKIP
means the property is not applicable in this context (e.g. not a git repo),
and does not fail the gate.
"""
import glob
import importlib.util
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
VERIFIERS_DIR = os.path.join(ROOT, "verifiers")
PASS, FAIL, SKIP = "PASS", "FAIL", "SKIP"


def discover():
    """Every scripts/verifiers/<name>.py except _private modules, by name."""
    out = []
    for path in sorted(glob.glob(os.path.join(VERIFIERS_DIR, "*.py"))):
        name = os.path.basename(path)[:-3]
        if name.startswith("_"):
            continue
        out.append((name, path))
    return out


def load(name, path):
    spec = importlib.util.spec_from_file_location(f"verifiers.{name}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run_one(name, path):
    """(status, detail, method, owner, property). Fail-closed on any raise."""
    try:
        mod = load(name, path)
        prop = getattr(mod, "PROPERTY", name)
        method = getattr(mod, "METHOD", "?")
        owner = getattr(mod, "OWNER", "?")
        status, detail = mod.check()
        if status not in (PASS, FAIL, SKIP):
            status, detail = FAIL, f"invalid status {status!r} from check()"
    except Exception as e:  # a broken verifier is a FAIL, never a pass
        return (FAIL, f"verifier raised {type(e).__name__}: {e}", "?", "?", name)
    return (status, detail, method, owner, prop)


def main(argv):
    # Verifiers glob relative to repo root; anchor there.
    os.chdir(os.path.dirname(ROOT))
    args = argv[1:]
    as_json = "--json" in args
    do_list = "--list" in args
    wanted = [a for a in args if not a.startswith("-")]

    registry = discover()
    if wanted:
        registry = [(n, p) for (n, p) in registry if n in wanted]
        missing = set(wanted) - {n for n, _ in registry}
        if missing:
            print(f"unknown verifier(s): {sorted(missing)}", file=sys.stderr)
            return 2

    if do_list:
        for name, path in registry:
            mod = load(name, path)
            print(f"{name:24} [{getattr(mod, 'METHOD', '?'):6}] "
                  f"{getattr(mod, 'OWNER', '?')}")
            print(f"    {getattr(mod, 'PROPERTY', '')}")
        return 0

    results = [(name, *run_one(name, path)) for name, path in registry]

    if as_json:
        payload = [
            {"verifier": n, "status": s, "detail": d, "method": m, "owner": o}
            for (n, s, d, m, o, _prop) in results
        ]
        print(json.dumps(payload, indent=2))
    else:
        order = {FAIL: 0, SKIP: 1, PASS: 2}
        for name, status, detail, method, owner, _prop in sorted(
            results, key=lambda r: (order[r[1]], r[0])
        ):
            mark = {PASS: "✓", FAIL: "✗", SKIP: "–"}[status]
            print(f"{mark} {status:4} {name:24} [{method:6}] {owner}")
            if status != PASS:
                print(f"       {detail}")

    n_fail = sum(1 for r in results if r[1] == FAIL)
    n_skip = sum(1 for r in results if r[1] == SKIP)
    n_pass = sum(1 for r in results if r[1] == PASS)
    if not as_json:
        print(f"\n{len(results)} verifier(s): {n_pass} PASS, "
              f"{n_fail} FAIL, {n_skip} SKIP")
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
