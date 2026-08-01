"""The filesystem write-scope guard — Takt-Harness's single most important
security invariant (PRD acceptance criteria #1 and #2).

Two rules, enforced here and nowhere else so they cannot be bypassed:

  1. NO write or delete ever lands under `ges-talt/`. The roster and its
     context are read-only source material.
  2. ALL writes land under the `takt-harness/` data tree. A path that
     resolves (after following symlinks and `..`) outside that tree is
     rejected, not clamped.

Every filesystem write in the app goes through `writable_path()`; every
read of Ges-Talt goes through `gestalt_read_path()`. There is deliberately
no function here that writes to the Ges-Talt tree — the capability does not
exist, so no code path can reach it.
"""
from pathlib import Path

from .config import settings


class WriteScopeError(PermissionError):
    """Raised when a path escapes the Takt-Harness write scope or targets
    Ges-Talt. Fail closed: the caller gets no path back."""


def _resolved(base: Path) -> Path:
    # resolve() collapses `..` and follows symlinks, so traversal and
    # symlink-escape attempts are normalized before the containment check.
    return base.resolve()


def _is_within(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def writable_path(relative: str | Path) -> Path:
    """Resolve a relative path inside the Takt-Harness data tree, creating
    parent dirs. Rejects anything that escapes the data tree or lands under
    Ges-Talt. The returned path is safe to write."""
    data_root = _resolved(settings.data_dir)
    candidate = _resolved(data_root / Path(relative))

    if not _is_within(candidate, data_root):
        raise WriteScopeError(f"write outside takt-harness data tree: {relative!r}")
    if _is_within(candidate, _resolved(settings.gestalt_root)):
        raise WriteScopeError(f"refusing to write under ges-talt: {relative!r}")

    candidate.parent.mkdir(parents=True, exist_ok=True)
    return candidate


def gestalt_read_path(relative: str | Path) -> Path:
    """Resolve a path inside the Ges-Talt tree for READING ONLY. Rejects
    escapes; never used for writes."""
    gestalt_root = _resolved(settings.gestalt_root)
    candidate = _resolved(gestalt_root / Path(relative))
    if not _is_within(candidate, gestalt_root):
        raise WriteScopeError(f"read outside ges-talt tree: {relative!r}")
    return candidate


def assert_db_path_scoped() -> Path:
    """The SQLite file must live under the data tree — checked at startup so a
    misconfigured DB path fails fast rather than writing somewhere it mustn't."""
    db = _resolved(settings.db_path)
    if not _is_within(db, _resolved(settings.data_dir)):
        raise WriteScopeError(f"db path escapes data tree: {db}")
    if _is_within(db, _resolved(settings.gestalt_root)):
        raise WriteScopeError(f"db path is under ges-talt: {db}")
    db.parent.mkdir(parents=True, exist_ok=True)
    return db
