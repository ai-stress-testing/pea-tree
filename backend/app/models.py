"""Data model. Documents/issues are rows (no filesystem writes outside the
DB, which is itself under the Takt-Harness data tree). No hard deletes on
Ges-Talt-derived content — see PRD "No deletions"; app content is soft-close
only where relevant, and nothing here can reach the ges-talt tree.
"""
from datetime import datetime, timezone

from sqlalchemy import ForeignKey, Integer, JSON, String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Agent(Base):
    """The harness's agents, owned by Takt-Harness (not the Ges-Talt repo).
    A row is the unit passed to the local model's /v1 route: its
    system_prompt (+ title/actions/skills) parameterizes the call.
    """
    __tablename__ = "agents"
    id: Mapped[str] = mapped_column(String(120), primary_key=True)  # "team/role" slug
    name: Mapped[str] = mapped_column(String(120))
    team: Mapped[str] = mapped_column(String(60), index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    model: Mapped[str] = mapped_column(String(60), default="local-model")
    actions: Mapped[list] = mapped_column(JSON, default=list)   # responsibilities
    skills: Mapped[list] = mapped_column(JSON, default=list)
    tools: Mapped[list] = mapped_column(JSON, default=list)
    system_prompt: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)


class Project(Base):
    __tablename__ = "projects"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    sprints: Mapped[list["Sprint"]] = relationship(back_populates="project")


class Sprint(Base):
    __tablename__ = "sprints"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    project: Mapped[Project] = relationship(back_populates="sprints")
    documents: Mapped[list["Document"]] = relationship(back_populates="sprint")


class Document(Base):
    __tablename__ = "documents"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sprint_id: Mapped[int] = mapped_column(ForeignKey("sprints.id"))
    # one of the library doc types (prd, srs, architecture, ...)
    doc_type: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    content: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)
    sprint: Mapped[Sprint] = relationship(back_populates="documents")


class QueueItem(Base):
    """A line item in the Agent-Queue: an agent assigned to iterate over a
    target (issue/document). Tracks retry state per the PRD rule (retry 3×,
    skip; 6 further failures → user intervention).
    """
    __tablename__ = "queue_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    agent_id: Mapped[str] = mapped_column(String(120))       # roster agent slug
    target_kind: Mapped[str] = mapped_column(String(20), default="issue")  # issue|document
    target_id: Mapped[int] = mapped_column(Integer)
    note: Mapped[str] = mapped_column(String(400), default="")
    priority: Mapped[int] = mapped_column(Integer, default=0)  # higher runs first
    position: Mapped[int] = mapped_column(Integer, default=0)  # manual ordering
    # idle | processing | error | done | needs_user
    state: Mapped[str] = mapped_column(String(20), default="idle")
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str] = mapped_column(String(600), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)


class Summon(Base):
    """A single active summon per room (Feature 1). The model selects which
    agents to summon before any are queued; the summon stays `active` until
    completed, gating further summons in the same room."""
    __tablename__ = "summons"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    room: Mapped[str] = mapped_column(String(60), index=True)
    prompt: Mapped[str] = mapped_column(Text)
    state: Mapped[str] = mapped_column(String(12), default="active")  # active|complete|failed
    selected_agents: Mapped[list] = mapped_column(JSON, default=list)
    message: Mapped[str] = mapped_column(String(400), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class ChatMessage(Base):
    """A message in a team breakout room (Chats, TH-5). Persistent history;
    user messages render right, agent messages left."""
    __tablename__ = "chat_messages"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    room: Mapped[str] = mapped_column(String(60), index=True)   # team slug
    sender: Mapped[str] = mapped_column(String(10))             # "user" | "agent"
    agent_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class Issue(Base):
    __tablename__ = "issues"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    priority: Mapped[str] = mapped_column(String(20), default="medium")
    tags: Mapped[str] = mapped_column(String(300), default="")  # comma-separated
    # kanban/pipeline stage; unassigned issues start in the Zettlebucket.
    stage: Mapped[str] = mapped_column(String(40), default="zettelbucket")
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)
