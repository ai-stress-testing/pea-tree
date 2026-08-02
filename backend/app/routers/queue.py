"""Agent-Queue feature (TH-3): which agents iterate over which line items
next, with the retry/skip/escalation rule and manual queue management.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..agent_client import AgentUnavailable, agent_client
from ..db import get_session
from ..models import Agent, Document, Issue, QueueItem
from ..queue_rules import next_candidate, on_failure, on_success
from ..roster import build_system_prompt, get_agent
from ..schemas import QueueItemIn, QueueItemOut, QueueItemUpdate

router = APIRouter(prefix="/api", tags=["queue"])

PAUSED = "paused"


def _ordered(db: Session) -> list[QueueItem]:
    return list(
        db.scalars(select(QueueItem).order_by(QueueItem.priority.desc(), QueueItem.position, QueueItem.id))
    )


@router.get("/queue", response_model=list[QueueItemOut])
def list_queue(db: Session = Depends(get_session)) -> list[QueueItem]:
    return _ordered(db)


@router.post("/queue", response_model=QueueItemOut)
def enqueue(body: QueueItemIn, db: Session = Depends(get_session)) -> QueueItem:
    if not get_agent(db, body.agent_id):
        raise HTTPException(404, f"unknown agent: {body.agent_id}")
    item = QueueItem(
        agent_id=body.agent_id, target_kind=body.target_kind, target_id=body.target_id,
        note=body.note, priority=body.priority, position=len(_ordered(db)),
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/queue/{item_id}", response_model=QueueItemOut)
def manage(item_id: int, body: QueueItemUpdate, db: Session = Depends(get_session)) -> QueueItem:
    item = db.get(QueueItem, item_id)
    if not item:
        raise HTTPException(404, "queue item not found")
    if body.agent_id is not None:
        if not get_agent(db, body.agent_id):
            raise HTTPException(404, f"unknown agent: {body.agent_id}")
        item.agent_id = body.agent_id  # reassign
    if body.priority is not None:
        item.priority = body.priority
    if body.position is not None:
        item.position = body.position
    if body.state is not None:
        item.state = body.state  # pause/resume via "paused"/"idle"
    db.commit()
    db.refresh(item)
    return item


def _target_text(db: Session, item: QueueItem) -> str:
    if item.target_kind == "document":
        d = db.get(Document, item.target_id)
        return f"DOCUMENT: {d.title}\n\n{d.content[:2000]}" if d else "(missing document)"
    if item.target_kind == "issue":
        i = db.get(Issue, item.target_id)
        return f"ISSUE: {i.title}\n\n{i.description}" if i else "(missing issue)"
    return ""  # e.g. a chat summon — the prompt is carried in item.note


async def _process(db: Session, item: QueueItem) -> QueueItem:
    """One iteration of a line item through its assigned agent, applying the
    retry/skip/escalation rule. Any failure (endpoint down, bad response)
    counts as an attempt."""
    agent: Agent | None = get_agent(db, item.agent_id)
    if not agent:
        item.attempts += 1
        t = on_failure(item.attempts)
        item.state, item.last_error = t.state, f"unknown agent: {item.agent_id}"
        db.commit()
        db.refresh(item)
        return item

    item.state = "processing"
    db.commit()
    messages = [
        {"role": "system", "content": build_system_prompt(agent)},
        {"role": "user", "content": f"{item.note}\n\n{_target_text(db, item)}".strip()},
    ]
    try:
        await agent_client.chat(messages)
        t = on_success()
        item.state, item.last_error = t.state, ""
    except Exception as e:  # noqa: BLE001 — any failure counts as one attempt
        item.attempts += 1
        t = on_failure(item.attempts)
        item.state, item.last_error = t.state, str(e)[:600]
    db.commit()
    db.refresh(item)
    return item


@router.post("/queue/{item_id}/process", response_model=QueueItemOut)
async def process(item_id: int, db: Session = Depends(get_session)) -> QueueItem:
    """Process one specific line item."""
    item = db.get(QueueItem, item_id)
    if not item:
        raise HTTPException(404, "queue item not found")
    if item.state == PAUSED:
        raise HTTPException(409, "item is paused")
    return await _process(db, item)


@router.post("/queue/process-next")
async def process_next(db: Session = Depends(get_session)) -> dict:
    """The runner step: pick the next runnable (idle/error, non-paused) item in
    priority order and process it. This is what makes 'skip to next' real —
    a needs_user or paused item is passed over, and an empty result means the
    queue is drained (the runner terminates)."""
    item = next_candidate(_ordered(db))
    if item is None:
        return {"processed": None, "reason": "no runnable items"}
    result = await _process(db, item)
    return {"processed": QueueItemOut.model_validate(result).model_dump(mode="json")}
