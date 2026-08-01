"""Zettlebucket feature (TH-4): fast intake. Templates for common issue
types; submitting creates an issue (lands in the Zettlebucket kanban column)
and routes it to the Agent-Queue for triage.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db import get_session
from ..models import Issue, QueueItem
from ..roster import get_agent
from ..schemas import IssueOut

router = APIRouter(prefix="/api", tags=["zettel"])

# Default triage agent an intake routes to (spec-driven PM decomposes it).
TRIAGE_AGENT = "pm/project-manager"

TEMPLATES: dict[str, dict] = {
    "bug-report": {
        "label": "Bug Report",
        "priority": "high",
        "description": "**Steps to reproduce:**\n1. \n\n**Expected:**\n\n**Actual:**\n",
    },
    "feature-request": {
        "label": "Feature Request",
        "priority": "medium",
        "description": "**Problem:**\n\n**Proposed:**\n\n**Value:**\n",
    },
    "performance-issue": {
        "label": "Performance Issue",
        "priority": "high",
        "description": "**Where:**\n\n**Observed latency/throughput:**\n\n**Target:**\n",
    },
}


class ZettelSubmit(BaseModel):
    title: str
    description: str = ""
    priority: str = "medium"
    tags: str = ""
    enqueue: bool = True  # route to Agent-Queue on submit


@router.get("/zettel/templates")
def templates() -> list[dict]:
    return [{"id": k, "label": v["label"], "priority": v["priority"], "description": v["description"]}
            for k, v in TEMPLATES.items()]


@router.post("/zettel/submit", response_model=IssueOut)
def submit(body: ZettelSubmit, db: Session = Depends(get_session)) -> Issue:
    if not body.title.strip():
        raise HTTPException(400, "title required")
    issue = Issue(
        title=body.title.strip(), description=body.description,
        priority=body.priority, tags=body.tags, stage="zettelbucket",
    )
    db.add(issue)
    db.commit()
    db.refresh(issue)

    # Pipeline trigger: route the fresh issue to the Agent-Queue for triage.
    if body.enqueue and get_agent(db, TRIAGE_AGENT):
        db.add(QueueItem(
            agent_id=TRIAGE_AGENT, target_kind="issue", target_id=issue.id,
            note="Triage this intake: classify, size, and suggest pipeline routing.",
        ))
        db.commit()
    return issue
