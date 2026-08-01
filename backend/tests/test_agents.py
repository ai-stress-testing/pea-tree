"""The agents table seeds from the committed JSON and is self-contained
(no Ges-Talt repo read at runtime)."""
import os
from pathlib import Path

os.environ.setdefault("TAKT_DATA_DIR", "/tmp/takt-test-agents")
Path("/tmp/takt-test-agents").mkdir(parents=True, exist_ok=True)
# Fresh DB per run.
_db = Path("/tmp/takt-test-agents/takt.db")
if _db.exists():
    _db.unlink()

from app.db import SessionLocal, init_db  # noqa: E402
from app.roster import build_system_prompt, get_agent, list_agents, seed_agents  # noqa: E402


def setup_module(_):
    init_db()
    db = SessionLocal()
    try:
        seed_agents(db)
    finally:
        db.close()


def test_seeded_from_json():
    db = SessionLocal()
    try:
        agents = list_agents(db)
        assert len(agents) > 50  # the full roster seeded
        a = get_agent(db, "frontend/react-dev")
        assert a is not None
        # columns the user asked for are populated
        assert a.team == "frontend"
        assert a.title
        assert isinstance(a.actions, list) and a.actions
        assert isinstance(a.skills, list)
    finally:
        db.close()


def test_seed_is_idempotent():
    db = SessionLocal()
    try:
        before = len(list_agents(db))
        added = seed_agents(db)  # already seeded -> no-op
        assert added == 0
        assert len(list_agents(db)) == before
    finally:
        db.close()


def test_system_prompt_built_from_row():
    db = SessionLocal()
    try:
        a = get_agent(db, "logicians/falsifier")
        prompt = build_system_prompt(a)
        assert prompt.strip()  # non-empty; this is what's passed to /v1
    finally:
        db.close()
