"""Loads the Ges-Talt roster as the app's available agents — READ ONLY.

Every read goes through guard.gestalt_read_path, so this module physically
cannot escape the ges-talt tree or write to it. Parses the installed
`.claude/agents/*.md` frontmatter (name/description/model/tools) so Takt-Harness
presents exactly the agents Ges-Talt exposes.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache

from .guard import gestalt_read_path

_FM = re.compile(r"^---\n(.*?)\n---", re.S)


@dataclass
class Agent:
    id: str            # e.g. "frontend/react-dev"
    name: str          # frontmatter name, e.g. "frontend-react-dev"
    team: str
    description: str
    model: str
    tools: list[str]


def _parse_frontmatter(text: str) -> dict:
    m = _FM.match(text)
    fm: dict[str, str] = {}
    if not m:
        return fm
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip()
    return fm


@lru_cache(maxsize=1)
def load_agents() -> list[Agent]:
    """Read the installed subagents from ges-talt/.claude/agents (read-only)."""
    agents_dir = gestalt_read_path(".claude/agents")
    out: list[Agent] = []
    if not agents_dir.is_dir():
        return out
    for path in sorted(agents_dir.glob("*.md")):
        fm = _parse_frontmatter(path.read_text(encoding="utf-8"))
        name = fm.get("name", path.stem)
        team = name.split("-", 1)[0]
        out.append(
            Agent(
                id=name.replace("-", "/", 1),
                name=name,
                team=team,
                description=fm.get("description", ""),
                model=fm.get("model", "sonnet"),
                tools=[t.strip() for t in fm.get("tools", "").split(",") if t.strip()],
            )
        )
    return out


def teams() -> dict[str, list[Agent]]:
    grouped: dict[str, list[Agent]] = {}
    for a in load_agents():
        grouped.setdefault(a.team, []).append(a)
    return grouped
