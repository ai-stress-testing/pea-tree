"""Single-summonship (Feature 1): the gate and the model-driven selection."""
import os
from pathlib import Path

os.environ.setdefault("TAKT_DATA_DIR", "/tmp/takt-test-summon")
Path("/tmp/takt-test-summon").mkdir(parents=True, exist_ok=True)
_db = Path("/tmp/takt-test-summon/takt.db")
if _db.exists():
    _db.unlink()

from app.chats_logic import GATE_MESSAGE, parse_agent_ids  # noqa: E402
from app.db import SessionLocal, init_db  # noqa: E402
from app.models import Summon  # noqa: E402
from app.roster import seed_agents  # noqa: E402
from app.routers.chats import _active_summon  # noqa: E402


def setup_module(_):
    init_db()
    db = SessionLocal()
    try:
        seed_agents(db)
    finally:
        db.close()


def test_parse_agent_ids_keeps_only_known_and_dedups():
    known = {"security/senior-secops", "pm/project-manager"}
    text = 'Here: ["security/senior-secops", "security/senior-secops", "nope/nope", "pm/project-manager"]'
    assert parse_agent_ids(text, known) == ["security/senior-secops", "pm/project-manager"]


def test_parse_agent_ids_accepts_objects_with_id():
    known = {"ai/prompt-engineer"}
    text = '[{"id":"ai/prompt-engineer","temp":0.2},{"id":"unknown/x"}]'
    assert parse_agent_ids(text, known) == ["ai/prompt-engineer"]


def test_parse_agent_ids_empty_on_no_array_or_bad_json():
    assert parse_agent_ids("no array here", {"a/b"}) == []
    assert parse_agent_ids("[not json]", {"a/b"}) == []


def test_gate_detects_an_active_summon():
    db = SessionLocal()
    try:
        assert _active_summon(db, "security") is None
        db.add(Summon(room="security", prompt="p", state="active"))
        db.commit()
        assert _active_summon(db, "security") is not None
        # a completed summon does not gate a new one
        s2 = Summon(room="design", prompt="p", state="complete")
        db.add(s2)
        db.commit()
        assert _active_summon(db, "design") is None
    finally:
        db.close()


def test_gate_message_is_the_specified_text():
    assert "already active in this chat" in GATE_MESSAGE
