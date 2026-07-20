"""Assert no role has widened its tool set beyond the committed baseline.

Threat-model C6 / GT-13: a role silently gaining Edit/Bash/Write is
privilege creep. A strict superset of the baseline tools is the
counterexample; refresh the baseline intentionally, never to silence this.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _lib  # noqa: E402

PROPERTY = "No role's tools strictly widen scripts/tools-baseline.json."
METHOD = "static"
OWNER = "security/architect"


def check():
    _lib.in_repo_root()
    bi = _lib.import_build_index()
    baseline = bi.load_tools_baseline()
    if not baseline:
        return _lib.SKIP, "no tools-baseline.json to compare against"
    current = bi.collect_role_tools()
    widened = []
    for role, tools in current.items():
        base = baseline.get(role)
        if base is None:
            continue  # new role since last refresh — nothing to compare
        if set(tools) > set(base):
            widened.append(f"{role} added {sorted(set(tools) - set(base))}")
    if widened:
        return _lib.FAIL, f"tool-set widening: {widened}"
    return _lib.PASS, f"{len(current)} role(s) within tools baseline"


if __name__ == "__main__":
    sys.exit(_lib.run_standalone(check))
