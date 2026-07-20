"""Assert every role folder is a complete pair: agent.md + SPEC.md."""
import glob
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _lib  # noqa: E402

PROPERTY = "Every agents/<team>/<role>/ has both agent.md and SPEC.md."
METHOD = "static"
OWNER = "pm/project-manager"


def check():
    _lib.in_repo_root()
    broken = []
    for agent in glob.glob("agents/*/*/agent.md"):
        if "/TEMPLATE/" in agent:
            continue
        if not os.path.exists(agent.replace("agent.md", "SPEC.md")):
            broken.append(agent.replace("agent.md", "") + " (missing SPEC.md)")
    for spec in glob.glob("agents/*/*/SPEC.md"):
        if "/TEMPLATE/" in spec:
            continue
        if not os.path.exists(spec.replace("SPEC.md", "agent.md")):
            broken.append(spec.replace("SPEC.md", "") + " (missing agent.md)")
    n = len([p for p in glob.glob("agents/*/*/agent.md") if "/TEMPLATE/" not in p])
    if n == 0:
        return _lib.FAIL, "no role folders found — empty roster or wrong cwd"
    if broken:
        return _lib.FAIL, f"unpaired role folder(s): {sorted(broken)}"
    return _lib.PASS, f"{n} role folder(s) fully paired"


if __name__ == "__main__":
    sys.exit(_lib.run_standalone(check))
