"""Assert no reason-tier (opus) role can mutate the repo.

The org-as-target property (hard-verifiers.md): reasoning depth must not buy
blast radius. A reason-tier model paired with Edit/Bash/NotebookEdit — or
Write outside the documented exceptions — is the counterexample.
"""
import glob
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _lib  # noqa: E402

PROPERTY = "No reason-tier role holds mutation tools (Edit/Bash/NotebookEdit; Write only via documented exception)."
METHOD = "static"
OWNER = "security/architect"


def check():
    _lib.in_repo_root()
    bi = _lib.import_build_index()
    tiers, aliases = bi.load_model_config()
    concrete = set(tiers.values()) | set(aliases.values())
    reason_model = tiers.get("reason")
    if not reason_model:
        return _lib.SKIP, "no reason tier defined in models.toml"

    offenders = []
    for path in glob.glob("agents/*/*/agent.md"):
        if "/TEMPLATE/" in path:
            continue
        fm = bi.parse(path)
        resolved, _tier = bi.resolve_model(
            fm.get("model", ""), tiers, aliases, concrete
        )
        if resolved != reason_model:
            continue
        tools = {t.strip() for t in fm.get("tools", "").split(",") if t.strip()}
        bad = tools & bi.MUTATION_TOOLS
        if "Write" in tools and path not in bi.OPUS_WRITE_EXCEPTIONS:
            bad |= {"Write"}
        if bad:
            offenders.append(f"{path} → {sorted(bad)}")
    if offenders:
        return _lib.FAIL, f"reason-tier roles with mutation tools: {offenders}"
    return _lib.PASS, "every reason-tier role is read-only (within exceptions)"


if __name__ == "__main__":
    sys.exit(_lib.run_standalone(check))
