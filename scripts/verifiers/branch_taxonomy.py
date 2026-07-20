"""Assert the current git branch matches the branching taxonomy.

Observability (docs/branching.md): a branch whose name doesn't declare its
kind — feature/fix/bug/mvp/plan (or a reserved trunk) — is untyped work you
can't triage at a glance. The offending branch name is the counterexample.
Detached HEAD or a non-git checkout is a SKIP, not a FAIL.
"""
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _lib  # noqa: E402

PROPERTY = "The checked-out branch is a reserved trunk or a typed work branch (feature|fix|bug|mvp|plan|claude)/<slug>."
METHOD = "static"
OWNER = "cd/gitops-engineer"

RESERVED = {"main", "Sprint0", "HEAD"}
TYPED = re.compile(r"^(feature|fix|bug|mvp|plan|claude)/.+")


def check():
    _lib.in_repo_root()
    try:
        branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            stderr=subprocess.DEVNULL,
        ).decode().strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return _lib.SKIP, "not a git checkout"
    if branch == "HEAD":
        return _lib.SKIP, "detached HEAD — no branch to type"
    if branch in RESERVED or TYPED.match(branch):
        return _lib.PASS, f"branch '{branch}' matches taxonomy"
    return (_lib.FAIL,
            f"branch '{branch}' is untyped — prefix it feature/|fix/|bug/|"
            "mvp/|plan/ per docs/branching.md")


if __name__ == "__main__":
    sys.exit(_lib.run_standalone(check))
