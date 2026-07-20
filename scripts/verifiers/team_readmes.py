"""Assert every team folder has a README.md.

The team README is where a team's charter and roster boundaries live; a team
without one is undocumented surface. This property was added after the
repo-map surfaced `backend/` as the lone team missing its README.
"""
import glob
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _lib  # noqa: E402

PROPERTY = "Every agents/<team>/ (except TEMPLATE) has a README.md."
METHOD = "static"
OWNER = "pm/project-manager"


def check():
    _lib.in_repo_root()
    missing = []
    teams = 0
    for team_dir in sorted(glob.glob("agents/*/")):
        team = team_dir.rstrip("/").split("/")[-1]
        if team == "TEMPLATE":
            continue
        teams += 1
        if not os.path.exists(os.path.join(team_dir, "README.md")):
            missing.append(team)
    if teams == 0:
        return _lib.FAIL, "no team folders found — wrong cwd or empty roster"
    if missing:
        return _lib.FAIL, f"team(s) without README.md: {missing}"
    return _lib.PASS, f"all {teams} team(s) have a README.md"


if __name__ == "__main__":
    sys.exit(_lib.run_standalone(check))
