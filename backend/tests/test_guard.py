"""Proves the write-scope invariant (PRD acceptance #2): all writes stay
under the Takt-Harness data tree."""
import os
from pathlib import Path

import pytest

TMP = Path(os.environ.setdefault("TAKT_DATA_DIR", "/tmp/takt-test-data"))
TMP.mkdir(parents=True, exist_ok=True)

from app.guard import WriteScopeError, writable_path  # noqa: E402


def test_writable_path_inside_is_allowed():
    assert str(writable_path("projects/doc.md")).startswith(str(TMP.resolve()))


def test_writable_path_rejects_parent_traversal():
    with pytest.raises(WriteScopeError):
        writable_path("../escape.md")


def test_writable_path_rejects_absolute_escape():
    with pytest.raises(WriteScopeError):
        writable_path("/etc/passwd")


def test_writable_path_rejects_symlink_escape(tmp_path):
    link = TMP / "sneaky"
    if link.exists() or link.is_symlink():
        link.unlink()
    link.symlink_to(tmp_path)  # points outside the data tree
    with pytest.raises(WriteScopeError):
        writable_path("sneaky/out.md")
    link.unlink()
