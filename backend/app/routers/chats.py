"""Chats feature (TH-5): team breakout rooms. A room is a Ges-Talt team;
its agents can be summoned to respond via the local model. Persistent history.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..agent_client import AgentUnavailable, agent_client
from ..db import get_session
from ..models import ChatMessage
from ..roster import build_system_prompt, get_agent, teams
from ..schemas import ChatMessageOut

router = APIRouter(prefix="/api", tags=["chats"])


class PostMessage(BaseModel):
    content: str


class Summon(BaseModel):
    agent_id: str


@router.get("/chats/rooms")
def rooms(db: Session = Depends(get_session)) -> list[dict]:
    grouped = teams(db)
    last = dict(
        db.execute(
            select(ChatMessage.room, func.max(ChatMessage.created_at)).group_by(ChatMessage.room)
        ).all()
    )
    return [
        {
            "team": team,
            "agent_count": len(members),
            "agents": [{"id": a.id, "title": a.title} for a in members],
            "last_message_at": last.get(team).isoformat() if last.get(team) else None,
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


@router.post("/chats/{room}/summon", response_model=ChatMessageOut)
async def summon(room: str, body: Summon, db: Session = Depends(get_session)) -> ChatMessage:
    """Have a team agent respond in the room, using the recent transcript."""
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
        text = res.text
    except AgentUnavailable as e:
        raise HTTPException(503, str(e))
    reply = ChatMessage(room=room, sender="agent", agent_id=agent.id, content=text)
    db.add(reply)
    db.commit()
    db.refresh(reply)
    return reply
