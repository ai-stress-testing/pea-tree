"""Docs feature API (priority 1): projects → sprints → documents, plus the
agent-assist flow for a highlighted selection (SRS §3.5).
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..agent_client import AgentUnavailable, agent_client
from ..db import get_session
from ..doc_library import DOC_TYPES, library, starter
from ..models import Document, Project, Sprint
from ..roster import build_system_prompt, get_agent, list_agents
from ..schemas import (
    AgentAssistIn,
    DocumentIn,
    DocumentOut,
    DocumentUpdate,
    ProjectIn,
    SprintIn,
)

router = APIRouter(prefix="/api", tags=["docs"])


def _title_conflict(db: Session, sprint_id: int, title: str, exclude_id: int | None = None) -> bool:
    q = select(Document).where(Document.sprint_id == sprint_id, Document.title == title)
    for d in db.scalars(q):
        if d.id != exclude_id:
            return True
    return False


def _suggest_title(db: Session, sprint_id: int, title: str) -> str:
    n = 2
    while _title_conflict(db, sprint_id, f"{title} ({n})"):
        n += 1
    return f"{title} ({n})"


@router.get("/doc-library")
def get_library() -> list[dict]:
    return library()


@router.get("/projects")
def list_projects(db: Session = Depends(get_session)) -> list[dict]:
    projects = db.scalars(select(Project)).all()
    return [
        {
            "id": p.id,
            "name": p.name,
            "sprints": [{"id": s.id, "name": s.name} for s in p.sprints],
        }
        for p in projects
    ]


@router.post("/projects")
def create_project(body: ProjectIn, db: Session = Depends(get_session)) -> dict:
    p = Project(name=body.name.strip() or "Untitled project")
    db.add(p)
    db.commit()
    db.refresh(p)
    return {"id": p.id, "name": p.name, "sprints": []}


@router.post("/sprints")
def create_sprint(body: SprintIn, db: Session = Depends(get_session)) -> dict:
    if not db.get(Project, body.project_id):
        raise HTTPException(404, "project not found")
    s = Sprint(project_id=body.project_id, name=body.name.strip() or "Sprint")
    db.add(s)
    db.commit()
    db.refresh(s)
    return {"id": s.id, "name": s.name, "project_id": s.project_id}


@router.get("/sprints/{sprint_id}/documents")
def list_documents(sprint_id: int, db: Session = Depends(get_session)) -> list[dict]:
    docs = db.scalars(select(Document).where(Document.sprint_id == sprint_id)).all()
    return [{"id": d.id, "doc_type": d.doc_type, "title": d.title} for d in docs]


@router.post("/documents", response_model=DocumentOut)
def create_document(body: DocumentIn, db: Session = Depends(get_session)) -> Document:
    if body.doc_type not in DOC_TYPES:
        raise HTTPException(400, f"unknown doc_type: {body.doc_type}")
    if not db.get(Sprint, body.sprint_id):
        raise HTTPException(404, "sprint not found")
    title = body.title or DOC_TYPES[body.doc_type]
    if _title_conflict(db, body.sprint_id, title):
        raise HTTPException(409, {
            "message": f"A document titled '{title}' already exists in this sprint.",
            "suggestion": _suggest_title(db, body.sprint_id, title),
        })
    d = Document(
        sprint_id=body.sprint_id,
        doc_type=body.doc_type,
        title=title,
        content=starter(body.doc_type, title),
    )
    db.add(d)
    db.commit()
    db.refresh(d)
    return d


@router.get("/documents/{doc_id}", response_model=DocumentOut)
def get_document(doc_id: int, db: Session = Depends(get_session)) -> Document:
    d = db.get(Document, doc_id)
    if not d:
        raise HTTPException(404, "document not found")
    return d


@router.put("/documents/{doc_id}", response_model=DocumentOut)
def update_document(
    doc_id: int, body: DocumentUpdate, db: Session = Depends(get_session)
) -> Document:
    """Auto-save target. Update only — no delete path (PRD 'No deletions')."""
    d = db.get(Document, doc_id)
    if not d:
        raise HTTPException(404, "document not found")
    if body.title is not None and body.title != d.title:
        if _title_conflict(db, d.sprint_id, body.title, exclude_id=doc_id):
            raise HTTPException(409, {
                "message": f"A document titled '{body.title}' already exists in this sprint.",
                "suggestion": _suggest_title(db, d.sprint_id, body.title),
            })
        d.title = body.title
    d.content = body.content
    db.commit()
    db.refresh(d)
    return d


@router.post("/documents/{doc_id}/agent-assist")
async def agent_assist(
    doc_id: int, body: AgentAssistIn, db: Session = Depends(get_session)
) -> dict:
    """Send a highlighted selection to one or more roster agents (from the DB)
    with a correction/consideration instruction (SRS §3.5)."""
    targets = [a for i in body.agent_ids if (a := get_agent(db, i))]
    if not targets:
        targets = list_agents(db)[:1]
    user = f"INSTRUCTION: {body.instruction}\n\nSELECTION:\n{body.selection}"
    results = []
    for agent in targets:
        system = (
            build_system_prompt(agent)
            + "\n\nYou are reviewing a highlighted section of a planning document. "
            "Respond with a concrete revision or a short considered comment."
        )
        try:
            res = await agent_client.chat(
                [{"role": "system", "content": system}, {"role": "user", "content": user}]
            )
            results.append({"agent": agent.id, "text": res.text})
        except AgentUnavailable as e:
            results.append({"agent": agent.id, "error": str(e)})
    return {"results": results}
