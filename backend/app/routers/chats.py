"""Chats feature (TH-5) + single-summonship (Feature 1).

A room is a Ges-Talt team. A **summon** is model-driven and single-active per
room: the initial prompt goes to the model first, the model chooses which
agents to summon, those are queued in the Agent-Queue, and the summon stays
`active` (gating further summons) until completed. During an active summon,
users and the summoned agents chat back and forth (`/reply`).
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..agent_client import AgentUnavailable, agent_client
from ..chats_logic import GATE_MESSAGE, NO_AGENTS_MESSAGE, parse_agent_ids, selection_prompt
from ..db import get_session
from ..models import ChatMessage, QueueItem, Summon
from ..roster import build_system_prompt, get_agent, list_agents, teams
from ..schemas import ChatMessageOut, SummonOut

router = APIRouter(prefix="/api", tags=["chats"])


class PostMessage(BaseModel):
    content: str


class SummonIn(BaseModel):
    prompt: str


class Reply(BaseModel):
    agent_id: str


def _active_summon(db: Session, room: str) -> Summon | None:
    return db.scalars(
        select(Summon).where(Summon.room == room, Summon.state == "active")
    ).first()


@router.get("/chats/rooms")
def rooms(db: Session = Depends(get_session)) -> list[dict]:
    grouped = teams(db)
    last = dict(
        db.execute(
            select(ChatMessage.room, func.max(ChatMessage.created_at)).group_by(ChatMessage.room)
        ).all()
    )
    active_rooms = {s.room for s in db.scalars(select(Summon).where(Summon.state == "active"))}
    return [
        {
            "team": team,
            "agent_count": len(members),
            "agents": [{"id": a.id, "title": a.title} for a in members],
            "last_message_at": last.get(team).isoformat() if last.get(team) else None,
            "summon_active": team in active_rooms,
        }
        for team, members in sorted(grouped.items())
    ]


@router.get("/chats/{room}/messages", response_model=list[ChatMessageOut])
def history(room: str, db: Session = Depends(get_session)) -> list[ChatMessage]:
    return list(
        db.scalars(select(ChatMessage).where(ChatMessage.room == room).order_by(ChatMessage.id))
    )


@router.post("/chats/{room}/messages", response_model=ChatMessageOut)
def post_message(room: str, body: PostMessage, db: Session = Depends(get_session)) -> ChatMessage:
    msg = ChatMessage(room=room, sender="user", content=body.content)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


@router.get("/chats/{room}/summon", response_model=SummonOut | None)
def current_summon(room: str, db: Session = Depends(get_session)) -> Summon | None:
    return _active_summon(db, room)


@router.post("/chats/{room}/summon", response_model=SummonOut)
async def summon(room: str, body: SummonIn, db: Session = Depends(get_session)) -> Summon:
    # 1. Summonship gate — one active summon per room.
    if _active_summon(db, room):
        raise HTTPException(409, GATE_MESSAGE)

    s = Summon(room=room, prompt=body.prompt, state="active")
    db.add(s)
    db.commit()
    db.refresh(s)

    # 2. Model-driven selection — ask the model BEFORE creating any agents.
    known = {a.id: a for a in list_agents(db)}
    roster = [(a.id, a.description) for a in known.values()]
    try:
        res = await agent_client.chat(selection_prompt(body.prompt, roster), temperature=0)
    except AgentUnavailable as e:
        s.state, s.message = "failed", f"agent endpoint unavailable: {e}"
        db.commit()
        db.refresh(s)
        return s  # gate releases (state != active)

    ids = parse_agent_ids(res.text, set(known))
    if not ids:
        s.state, s.message = "complete", NO_AGENTS_MESSAGE
        db.commit()
        db.refresh(s)
        return s

    # 3. Filter the full roster to the selected agents and queue them.
    s.selected_agents = ids
    for aid in ids:
        db.add(QueueItem(agent_id=aid, target_kind="chat", target_id=s.id, note=body.prompt))
    db.add(ChatMessage(room=room, sender="agent", agent_id="summon",
                       content=f"Summoned: {', '.join(ids)} — queued for processing."))
    db.commit()
    db.refresh(s)
    return s


@router.post("/chats/{room}/summon/complete", response_model=SummonOut)
def complete_summon(room: str, db: Session = Depends(get_session)) -> Summon:
    s = _active_summon(db, room)
    if not s:
        raise HTTPException(404, "no active summon")
    s.state = "complete"
    db.commit()
    db.refresh(s)
    return s


@router.post("/chats/{room}/reply", response_model=ChatMessageOut)
async def reply(room: str, body: Reply, db: Session = Depends(get_session)) -> ChatMessage:
    """Discussion phase: a summoned agent replies using the recent transcript.
    Only agents that were summoned into the active summon may reply."""
    active = _active_summon(db, room)
    if not active or body.agent_id not in active.selected_agents:
        raise HTTPException(409, "agent is not part of an active summon in this room")
    agent = get_agent(db, body.agent_id)
    if not agent:
        raise HTTPException(404, f"unknown agent: {body.agent_id}")
    recent = list(
        db.scalars(
            select(ChatMessage).where(ChatMessage.room == room).order_by(ChatMessage.id.desc()).limit(12)
        )
    )[::-1]
    transcript = "\n".join(
        f"{'User' if m.sender == 'user' else m.agent_id}: {m.content}" for m in recent
    )
    messages = [
        {"role": "system", "content": build_system_prompt(agent)
         + "\n\nYou are debating in a team breakout room. Reply in 120 words or fewer, in character."},
        {"role": "user", "content": f"Room transcript so far:\n{transcript}\n\nAdd your contribution."},
    ]
    try:
        res = await agent_client.chat(messages)
    except AgentUnavailable as e:
        raise HTTPException(503, str(e))
    msg = ChatMessage(room=room, sender="agent", agent_id=agent.id, content=res.text)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg
