"""Assert docs/enterprise.md's stated agent count matches the roster.

The "N agents total" figure in enterprise.md is hand-maintained and has
drifted every time the roster grew. Pin it to the number of role folders on
disk so a stale count is a FAIL, not a thing someone remembers to fix.
"""
import glob
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _lib  # noqa: E402

PROPERTY = "docs/enterprise.md's 'N agents total' matches the number of role folders."
METHOD = "static"
OWNER = "design/technical-writer"
DOC = "docs/enterprise.md"


def check():
    _lib.in_repo_root()
    if not os.path.exists(DOC):
        return _lib.SKIP, f"{DOC} does not exist"
    n_roles = len([p for p in glob.glob("agents/*/*/agent.md")
                   if "/TEMPLATE/" not in p])
    text = open(DOC, encoding="utf-8").read()
    m = re.search(r"(\d+)\s+agents total", text)
    if not m:
        return _lib.FAIL, f"no 'N agents total' figure found in {DOC}"
    stated = int(m.group(1))
    if stated != n_roles:
        return (_lib.FAIL,
                f"{DOC} says {stated} agents total; roster has {n_roles} — "
                "update the count")
    return _lib.PASS, f"enterprise.md count matches roster ({n_roles})"


if __name__ == "__main__":
    sys.exit(_lib.run_standalone(check))
