"""Proves the write-scope invariant (PRD acceptance #1/#2). Reviewed by the
Ges-Talt roster (security/architect + logicians/falsifier)."""
import os
from pathlib import Path

import pytest

# Point config at temp dirs BEFORE importing the app modules.
TMP = Path(os.environ.setdefault("TAKT_DATA_DIR", "/tmp/takt-test-data"))
GES = Path(os.environ.setdefault("TAKT_GESTALT_ROOT", "/tmp/takt-test-gestalt"))
TMP.mkdir(parents=True, exist_ok=True)
GES.mkdir(parents=True, exist_ok=True)

from app import guard  # noqa: E402
from app.guard import WriteScopeError, writable_path, gestalt_read_path  # noqa: E402


def test_writable_path_inside_is_allowed():
    p = writable_path("projects/doc.md")
    assert str(p).startswith(str(TMP.resolve()))


def test_writable_path_rejects_parent_traversal():
    with pytest.raises(WriteScopeError):
        writable_path("../escape.md")


def test_writable_path_rejects_absolute_escape():
    with pytest.raises(WriteScopeError):
        writable_path("/etc/passwd")


def test_writable_path_rejects_deep_traversal_into_gestalt():
    # Even a crafted relative path that climbs out and into ges-talt is refused.
    rel = os.path.relpath(GES / "agents" / "evil.md", TMP)
    with pytest.raises(WriteScopeError):
        writable_path(rel)


def test_writable_path_rejects_symlink_escape(tmp_path):
    # A symlink under the data tree pointing outside must not grant a write out.
    link = TMP / "sneaky"
    target = tmp_path  # outside the data tree
    if link.exists() or link.is_symlink():
        link.unlink()
    link.symlink_to(target)
    with pytest.raises(WriteScopeError):
        writable_path("sneaky/out.md")
    link.unlink()


def test_gestalt_read_is_scoped_to_gestalt():
    p = gestalt_read_path("agents/INDEX.md")
    assert str(p).startswith(str(GES.resolve()))


def test_gestalt_read_rejects_escape():
    with pytest.raises(WriteScopeError):
        gestalt_read_path("../../etc/passwd")


def test_no_write_helper_targets_gestalt():
    # Structural guarantee: the guard exposes no function that writes under
    # ges-talt. writable_path refuses it; there is no alternative.
    assert not hasattr(guard, "gestalt_write_path")
