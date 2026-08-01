#!/usr/bin/env python3
"""ONE-TIME migration: read the Ges-Talt roster and emit a self-contained
`app/agents_seed.json` for Takt-Harness.

After this runs, the app owns its agents in SQLite and never touches the
Ges-Talt repo again (Ges-Talt targets frontier models; this harness drives a
smaller local one and keeps its own, editable roster). Re-run only to refresh
the seed from an updated Ges-Talt checkout.

    python3 backend/scripts/gen_agents_seed.py [GESTALT_ROOT]
"""
import json
import re
import sys
from pathlib import Path

GESTALT = Path(sys.argv[1] if len(sys.argv) > 1 else "/home/user/Ges-Talt")
OUT = Path(__file__).resolve().parents[1] / "app" / "agents_seed.json"
FM = re.compile(r"^---\n(.*?)\n---\n?(.*)$", re.S)


def parse(path: Path) -> dict | None:
    m = FM.match(path.read_text(encoding="utf-8"))
    if not m:
        return None
    fm = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip()
    body = m.group(2).strip()

    # Title = first H1; strip an HTML comment line if present.
    title = fm.get("name", path.stem)
    for line in body.splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
            break

    # actions = the "Responsibilities:" bullet list. Bullets wrap across
    # indented continuation lines; the block ends at the first blank line.
    actions: list[str] = []
    in_resp = False
    for line in body.splitlines():
        if not in_resp:
            if line.strip().lower().startswith("responsibilities"):
                in_resp = True
            continue
        if not line.strip():  # blank line closes the Responsibilities block
            break
        s = line.strip()
        if s.startswith("- "):
            actions.append(s[2:].strip())
        elif actions:  # indented continuation of the current bullet
            actions[-1] = f"{actions[-1]} {s}"

    name = fm.get("name", path.stem)
    return {
        "id": name.replace("-", "/", 1),
        "name": name,
        "team": name.split("-", 1)[0],
        "title": title,
        "description": fm.get("description", ""),
        "model": fm.get("model", "sonnet"),
        "actions": actions,
        "skills": [],  # per-agent skills are none in the source roster
        "tools": [t.strip() for t in fm.get("tools", "").split(",") if t.strip()],
        "system_prompt": body,
    }


def main() -> int:
    src = GESTALT / ".claude" / "agents"
    if not src.is_dir():
        print(f"no roster at {src}", file=sys.stderr)
        return 1
    agents = [a for p in sorted(src.glob("*.md")) if (a := parse(p))]
    OUT.write_text(json.dumps(agents, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {OUT}: {len(agents)} agents")
    return 0


if __name__ == "__main__":
    sys.exit(main())
