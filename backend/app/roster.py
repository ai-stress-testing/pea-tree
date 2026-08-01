"""The agent roster — now DB-backed and owned by Takt-Harness.

Agents live in the `agents` SQLite table (seeded once from the former
Ges-Talt roster, then editable here). The app no longer reads the Ges-Talt
repo at runtime: this harness drives a smaller local model and keeps its own
roster. `build_system_prompt` turns a row into the system message passed to
the local model's /v1 route.
"""
from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .models import Agent

SEED_PATH = Path(__file__).resolve().parent / "agents_seed.json"


def seed_agents(db: Session) -> int:
    """Populate the agents table from the committed seed on first run.
    Idempotent: does nothing if the table already has rows."""
    if db.scalar(select(func.count()).select_from(Agent)):
        return 0
    rows = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    for r in rows:
        db.add(
            Agent(
                id=r["id"], name=r["name"], team=r["team"], title=r["title"],
                description=r.get("description", ""), model="local-model",
                actions=r.get("actions", []), skills=r.get("skills", []),
                tools=r.get("tools", []), system_prompt=r.get("system_prompt", ""),
            )
        )
    db.commit()
    return len(rows)


def list_agents(db: Session) -> list[Agent]:
    return list(db.scalars(select(Agent).order_by(Agent.id)))


def get_agent(db: Session, agent_id: str) -> Agent | None:
    return db.get(Agent, agent_id)


def teams(db: Session) -> dict[str, list[Agent]]:
    grouped: dict[str, list[Agent]] = {}
    for a in list_agents(db):
        grouped.setdefault(a.team, []).append(a)
    return grouped


def build_system_prompt(agent: Agent) -> str:
    """The agent row rendered as the system message for the /v1 call. The
    charter (system_prompt) is authoritative; title/actions/skills are folded
    in so a lighter row (no charter) still yields a usable persona."""
    if agent.system_prompt.strip():
        return agent.system_prompt
    parts = [f"You are the {agent.title} ({agent.id})."]
    if agent.actions:
        parts.append("Responsibilities:\n" + "\n".join(f"- {a}" for a in agent.actions))
    if agent.skills:
        parts.append("Skills: " + ", ".join(agent.skills))
    return "\n\n".join(parts)
