"""Roster + agent-endpoint status + agent invocation.

An agent row is the unit passed to the local model's /v1 route: /invoke
renders the row's system prompt and calls the endpoint with the caller's
messages.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..agent_client import AgentUnavailable, agent_client
from ..db import get_session
from ..roster import build_system_prompt, get_agent, list_agents, teams

router = APIRouter(prefix="/api", tags=["agents"])


class InvokeIn(BaseModel):
    messages: list[dict]  # [{role, content}, ...] — the user/assistant turns
    temperature: float = 0.4
    model: str | None = None


@router.get("/agents")
def list_all(db: Session = Depends(get_session)) -> dict:
    grouped = teams(db)
    return {
        "count": len(list_agents(db)),
        "teams": [
            {
                "team": team,
                "agents": [
                    {
                        "id": a.id, "title": a.title, "team": a.team,
                        "description": a.description, "model": a.model,
                        "actions": a.actions, "skills": a.skills, "tools": a.tools,
                    }
                    for a in members
                ],
            }
            for team, members in sorted(grouped.items())
        ],
    }


@router.get("/agents/{agent_id:path}")
def get_one(agent_id: str, db: Session = Depends(get_session)) -> dict:
    a = get_agent(db, agent_id)
    if not a:
        raise HTTPException(404, "agent not found")
    return {
        "id": a.id, "name": a.name, "team": a.team, "title": a.title,
        "description": a.description, "model": a.model, "actions": a.actions,
        "skills": a.skills, "tools": a.tools, "system_prompt": a.system_prompt,
    }


@router.post("/agents/{agent_id:path}/invoke")
async def invoke(agent_id: str, body: InvokeIn, db: Session = Depends(get_session)) -> dict:
    """Pass the agent row to the docker.local /v1 route: its system prompt is
    prepended to the caller's messages, then sent to the local model."""
    a = get_agent(db, agent_id)
    if not a:
        raise HTTPException(404, "agent not found")
    messages = [{"role": "system", "content": build_system_prompt(a)}, *body.messages]
    try:
        res = await agent_client.chat(messages, model=body.model, temperature=body.temperature)
    except AgentUnavailable as e:
        raise HTTPException(503, str(e))
    return {"agent": a.id, "model": res.model, "text": res.text}


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
