"""Shared plumbing for the hard-verifier registry (GT-43).

A **verifier** is one single-property machine (see
`docs/opsec/hard-verifiers.md`): it asserts exactly one property, returns a
binary verdict with a counterexample on failure, and fails closed. Each
`scripts/verifiers/<name>.py` module exposes:

    PROPERTY : str   # the assertion, in plain words
    METHOD   : str   # static | ptest | probe | reason
    OWNER    : str   # team/role that authors and owns it
    def check() -> (status, detail)   # status in {PASS, FAIL, SKIP}

`check()` returns `("PASS", msg)`, `("FAIL", counterexample)`, or
`("SKIP", why)` (property N/A in this context — e.g. not a git repo). An
exception raised by `check()` is treated as FAIL by the runner: absence of
a PASS is a FAIL. Compose them with `scripts/verify.py`.
"""
import os
import sys

PASS, FAIL, SKIP = "PASS", "FAIL", "SKIP"


def repo_root():
    """Absolute path to the repo root. This file is scripts/verifiers/_lib.py,
    so the root is three directories up (verifiers → scripts → root)."""
    return os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )


def in_repo_root():
    """chdir to the repo root so relative globs (agents/…, docs/…) resolve
    the same no matter where the verifier was invoked from."""
    os.chdir(repo_root())


def import_build_index():
    """The roster builder's primitives (frontmatter parse, model resolution,
    handoff check, tools baseline) are reused rather than re-implemented — a
    verifier that duplicated them could drift from the thing it verifies."""
    scripts_dir = os.path.dirname(os.path.abspath(__file__ + "/.."))
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    import build_index  # noqa: E402
    return build_index


def run_standalone(check):
    """Let any verifier run on its own: `python3 scripts/verifiers/foo.py`.
    Prints one line, exits 0 (PASS), 1 (FAIL), or 2 (SKIP)."""
    in_repo_root()
    try:
        status, detail = check()
    except Exception as e:  # fail closed
        status, detail = FAIL, f"verifier raised {type(e).__name__}: {e}"
    print(f"{status} {check.__module__ or 'verifier'}: {detail}")
    return {PASS: 0, FAIL: 1, SKIP: 2}[status]
