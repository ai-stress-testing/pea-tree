"""Assert agents/INDEX.md is not stale vs the roster on disk.

Cheap staleness check without re-rendering the whole file: the header counts
must match the filesystem, and every role folder must appear as a row. A
role added, removed, or renamed without regenerating INDEX is the
counterexample.
"""
import glob
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _lib  # noqa: E402

PROPERTY = "agents/INDEX.md header counts and role rows match the roster on disk."
METHOD = "static"
OWNER = "pm/project-manager"


def check():
    _lib.in_repo_root()
    index = "agents/INDEX.md"
    if not os.path.exists(index):
        return _lib.FAIL, "agents/INDEX.md does not exist — run build_index.py"
    text = open(index, encoding="utf-8").read()

    role_paths = [p for p in glob.glob("agents/*/*/agent.md")
                  if "/TEMPLATE/" not in p]
    teams = {p.split("/")[1] for p in role_paths}
    n_roles = len(role_paths)

    m = re.search(r"\*\*(\d+) agents\*\* across \*\*(\d+) teams\*\*", text)
    if not m:
        return _lib.FAIL, "INDEX header line not found or malformed"
    idx_agents, idx_teams = int(m.group(1)), int(m.group(2))
    if (idx_agents, idx_teams) != (n_roles, len(teams)):
        return (_lib.FAIL,
                f"INDEX says {idx_agents} agents/{idx_teams} teams; disk has "
                f"{n_roles}/{len(teams)} — regenerate with build_index.py")

    missing = []
    for p in role_paths:
        _, team, role, _ = p.split("/")
        if f"[{role}]({team}/{role}/)" not in text:
            missing.append(f"{team}/{role}")
    if missing:
        return _lib.FAIL, f"roles absent from INDEX: {sorted(missing)}"
    return _lib.PASS, f"INDEX in sync ({n_roles} roles, {len(teams)} teams)"


if __name__ == "__main__":
    sys.exit(_lib.run_standalone(check))
