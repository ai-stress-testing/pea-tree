"""Kanban feature (TH-2): the planning pipeline. The left column is the
Zettlebucket (unassigned issues); assigned issues move through pipeline
stages. Issue creation here doubles as quick intake until the dedicated
Zettlebucket feature (TH-4) lands.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_session
from ..models import Issue, Project
from ..schemas import IssueIn, IssueOut, IssueUpdate

router = APIRouter(prefix="/api", tags=["kanban"])

# Ordered pipeline; index 0 (Zettlebucket) is the unassigned intake column.
STAGES: list[tuple[str, str]] = [
    ("zettelbucket", "Zettlebucket"),
    ("in-review", "In Review"),
    ("drafting", "Drafting"),
    ("approved", "Approved"),
    ("implemented", "Implemented"),
]
STAGE_IDS = [s for s, _ in STAGES]


@router.get("/kanban/stages")
def stages() -> list[dict]:
    return [{"id": s, "label": lbl} for s, lbl in STAGES]


@router.get("/issues", response_model=list[IssueOut])
def list_issues(db: Session = Depends(get_session)) -> list[Issue]:
    return list(db.scalars(select(Issue).order_by(Issue.stage, Issue.id)))


@router.post("/issues", response_model=IssueOut)
def create_issue(body: IssueIn, db: Session = Depends(get_session)) -> Issue:
    issue = Issue(
        title=body.title.strip() or "Untitled issue",
        description=body.description,
        priority=body.priority,
        tags=body.tags,
        stage="zettelbucket",  # new issues land in the Zettlebucket
    )
    db.add(issue)
    db.commit()
    db.refresh(issue)
    return issue


@router.put("/issues/{issue_id}", response_model=IssueOut)
def update_issue(
    issue_id: int, body: IssueUpdate, db: Session = Depends(get_session)
) -> Issue:
    issue = db.get(Issue, issue_id)
    if not issue:
        raise HTTPException(404, "issue not found")
    if body.stage is not None:
        if body.stage not in STAGE_IDS:
            raise HTTPException(400, f"unknown stage: {body.stage}")
        issue.stage = body.stage
    if body.project_id is not None:
        if body.project_id and not db.get(Project, body.project_id):
            raise HTTPException(404, "project not found")
        issue.project_id = body.project_id or None
    if body.priority is not None:
        issue.priority = body.priority
    db.commit()
    db.refresh(issue)
    return issue
