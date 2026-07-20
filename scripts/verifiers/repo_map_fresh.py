"""Assert docs/repo-map.md matches a fresh generation.

A stale navigation index sends agents to files that moved — worse than no
index, because it's trusted. Compares the committed map to what
build_repo_index.render() produces now; any diff is the counterexample.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _lib  # noqa: E402

PROPERTY = "docs/repo-map.md is byte-identical to build_repo_index.render()."
METHOD = "static"
OWNER = "design/technical-writer"


def check():
    _lib.in_repo_root()
    scripts_dir = os.path.join(_lib.repo_root(), "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    import build_repo_index  # noqa: E402

    out = build_repo_index.OUT
    if not os.path.exists(out):
        return _lib.FAIL, f"{out} does not exist — run build_repo_index.py"
    current = open(out, encoding="utf-8").read()
    expected = build_repo_index.render()
    if current != expected:
        return (_lib.FAIL,
                f"{out} is stale — regenerate with "
                "`python3 scripts/build_repo_index.py`")
    return _lib.PASS, f"{out} is current"


if __name__ == "__main__":
    sys.exit(_lib.run_standalone(check))
