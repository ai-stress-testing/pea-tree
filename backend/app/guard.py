"""The filesystem write-scope guard — Takt-Harness's write invariant
(PRD acceptance #2): ALL writes land under the `takt-harness/` data tree.

A path that resolves (after following symlinks and `..`) outside that tree is
rejected, not clamped. Every filesystem write goes through `writable_path()`.
Fail closed: on any escape the caller gets no path back.

(The former Ges-Talt read-only rule is retired: the roster now lives in
SQLite under this same data tree, so there is no external tree to protect.)
"""
from pathlib import Path

from .config import settings


class WriteScopeError(PermissionError):
    """Raised when a path escapes the Takt-Harness write scope."""


def _is_within(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def writable_path(relative: str | Path) -> Path:
    """Resolve a relative path inside the data tree, creating parent dirs.
    Rejects anything that escapes the data tree. Safe to write."""
    data_root = settings.data_dir.resolve()
    candidate = (data_root / Path(relative)).resolve()
    if not _is_within(candidate, data_root):
        raise WriteScopeError(f"write outside takt-harness data tree: {relative!r}")
    candidate.parent.mkdir(parents=True, exist_ok=True)
    return candidate


def assert_db_path_scoped() -> Path:
    """The SQLite file must live under the data tree — checked at startup so a
    misconfigured DB path fails fast."""
    db = settings.db_path.resolve()
    if not _is_within(db, settings.data_dir.resolve()):
        raise WriteScopeError(f"db path escapes data tree: {db}")
    db.parent.mkdir(parents=True, exist_ok=True)
    return db
