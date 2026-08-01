"""Pydantic request/response shapes for the API."""
from datetime import datetime

from pydantic import BaseModel


class ProjectIn(BaseModel):
    name: str


class SprintIn(BaseModel):
    project_id: int
    name: str


class DocumentIn(BaseModel):
    sprint_id: int
    doc_type: str
    title: str | None = None


class DocumentUpdate(BaseModel):
    content: str
    title: str | None = None


class AgentAssistIn(BaseModel):
    # The highlighted section and what to do with it (SRS §3.5).
    selection: str
    instruction: str
    agent_ids: list[str] = []  # one or more roster agent ids to consult


class DocumentOut(BaseModel):
    id: int
    sprint_id: int
    doc_type: str
    title: str
    content: str
    updated_at: datetime

    class Config:
        from_attributes = True


class IssueIn(BaseModel):
    title: str
    description: str = ""
    priority: str = "medium"
    tags: str = ""


class IssueUpdate(BaseModel):
    stage: str | None = None
    project_id: int | None = None
    priority: str | None = None


class IssueOut(BaseModel):
    id: int
    title: str
    description: str
    priority: str
    tags: str
    stage: str
    project_id: int | None

    class Config:
        from_attributes = True
