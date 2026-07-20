#!/usr/bin/env python3
"""Audit SKILL.md files for the 500-LoC ceiling (issue #43).

Skills at 501+ lines measurably hurt performance, so a role's SKILL.md
(see agents/skills-policy.md) must stay lean. LoC = non-blank lines (blank
lines don't count against the budget). Exits 1 if any skill is over, so CI
gates on it — same shape as build_index.py / verify_comms.py.

    python3 scripts/audit_skills.py            # audit the repo
    python3 scripts/audit_skills.py --selfcheck
"""
import glob
import sys
from pathlib import Path

LIMIT = 500  # a SKILL.md at LIMIT+1 non-blank lines is a violation


def loc(text):
    """Lines of content — non-blank lines. A markdown skill's budget is its
    substance, not its blank spacing."""
    return sum(1 for line in text.splitlines() if line.strip())


def audit(root="."):
    """Return [(path, loc)] for every SKILL.md over LIMIT."""
    over = []
    for path in sorted(glob.glob(f"{root}/**/SKILL.md", recursive=True)):
        n = loc(Path(path).read_text())
        if n > LIMIT:
            over.append((path, n))
    return over


def selfcheck():
    import tempfile

    with tempfile.TemporaryDirectory() as d:
        skill = Path(d) / "role" / "SKILL.md"
        skill.parent.mkdir(parents=True)
        # 501 content lines + blanks that must NOT count — still a violation.
        skill.write_text("\n".join(["x"] * 501 + [""] * 50))
        assert audit(d), "a 501-content-line skill must be flagged"
        skill.write_text("\n".join(["x"] * 500 + [""] * 999))
        assert not audit(d), "500 content lines (+ blanks) must pass"
    print("selfcheck ok: 501 flagged, 500 passes, blanks don't count")


def main():
    if "--selfcheck" in sys.argv:
        selfcheck()
        return 0
    over = audit()
    total = len(glob.glob("**/SKILL.md", recursive=True))
    print(f"audited {total} SKILL.md file(s); limit {LIMIT} non-blank LoC")
    if over:
        print(f"\n{len(over)} over limit:", file=sys.stderr)
        for path, n in over:
            print(f"  {path}: {n} LoC (> {LIMIT}) — split it, see agents/skills-policy.md",
                  file=sys.stderr)
        return 1
    print("all skills within limit")
    return 0


if __name__ == "__main__":
    sys.exit(main())
