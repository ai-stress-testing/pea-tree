"""Assert every backticked `team/role` handoff points to a real role.

A dangling handoff (a team dissolved, a role renamed) silently breaks the
peer-handoff mesh. Reuses the roster builder's own check so the verifier
cannot drift from it.
"""
import glob
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _lib  # noqa: E402

PROPERTY = "Every backticked `team/role` handoff reference resolves to an existing role."
METHOD = "static"
OWNER = "pm/project-manager"


def check():
    _lib.in_repo_root()
    bi = _lib.import_build_index()
    team_names = {
        p.rstrip("/").split("/")[-1]
        for p in glob.glob("agents/*/")
        if p.rstrip("/").split("/")[-1] != "TEMPLATE"
    }
    roles = {
        "/".join(p.split("/")[1:3])
        for p in glob.glob("agents/*/*/agent.md")
        if "/TEMPLATE/" not in p
    }
    if not roles:
        return _lib.FAIL, "no roles found — empty roster or wrong cwd"
    problems = bi.check_handoff_references(team_names, roles)
    if problems:
        return _lib.FAIL, "; ".join(problems)
    return _lib.PASS, f"all handoff refs resolve across {len(roles)} roles"


if __name__ == "__main__":
    sys.exit(_lib.run_standalone(check))
