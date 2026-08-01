"""Data model. Documents/issues are rows (no filesystem writes outside the
DB, which is itself under the Takt-Harness data tree). No hard deletes on
Ges-Talt-derived content — see PRD "No deletions"; app content is soft-close
only where relevant, and nothing here can reach the ges-talt tree.
"""
from datetime import datetime, timezone

from sqlalchemy import ForeignKey, Integer, String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


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
