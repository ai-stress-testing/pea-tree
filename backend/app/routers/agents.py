"""Roster + agent-endpoint status, shared by every feature's availability
indicator (PRD Agent Integration)."""
from fastapi import APIRouter

from ..agent_client import agent_client
from ..roster import load_agents, teams

router = APIRouter(prefix="/api", tags=["agents"])


@router.get("/agents")
def list_agents() -> dict:
    grouped = teams()
    return {
        "teams": [
            {
                "team": team,
                "agents": [
                    {"id": a.id, "name": a.name, "description": a.description, "model": a.model}
                    for a in members
                ],
            }
            for team, members in sorted(grouped.items())
        ],
        "count": len(load_agents()),
    }


@router.get("/agent/status")
async def agent_status() -> dict:
    ok = await agent_client.available()
    models: list[str] = []
    if ok:
        try:
            models = await agent_client.list_models()
        except Exception:
            models = []
    return {"available": ok, "models": models, "endpoint": agent_client.base_url}
